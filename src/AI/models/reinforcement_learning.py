"""
Reinforcement Learning Models for Trading Strategy Optimization

This module provides reinforcement learning models for optimizing trading strategies, including:
- Trading environment that simulates market conditions
- RL agents that learn optimal trading policies
- Training and evaluation utilities
"""

import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces
import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import os
import random
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

# Configure logger
logger = logging.getLogger(__name__)

class TradingEnvironment(gym.Env):
    """
    Trading environment for reinforcement learning.
    
    Attributes:
        data (pd.DataFrame): Market data
        initial_balance (float): Initial account balance
        transaction_fee (float): Trading transaction fee percentage
        window_size (int): Observation window size
        reward_scaling (float): Scaling factor for rewards
        max_steps (int): Maximum steps in an episode
    """
    
    def __init__(self, 
                data: pd.DataFrame,
                initial_balance: float = 10000.0,
                transaction_fee: float = 0.001,
                window_size: int = 20,
                reward_scaling: float = 0.01,
                max_steps: int = None):
        """
        Initialize the trading environment.
        
        Args:
            data: DataFrame with market data
            initial_balance: Initial account balance
            transaction_fee: Trading transaction fee percentage
            window_size: Observation window size
            reward_scaling: Scaling factor for rewards
            max_steps: Maximum steps in an episode, defaults to data length
        """
        super(TradingEnvironment, self).__init__()
        
        # Market data
        self.data = data
        self.max_steps = max_steps or len(data) - window_size
        self.window_size = window_size
        
        # Account parameters
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        self.reward_scaling = reward_scaling
        
        # Action space: 0 = hold, 1 = buy, 2 = sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: market data window + position info
        self.features = data.shape[1]  # Number of features in data
        self.position_info = 3  # Position (0/1), Balance, Portfolio Value
        
        # Define observation space with normalized values
        low = np.full((self.window_size * self.features + self.position_info,), -np.inf)
        high = np.full((self.window_size * self.features + self.position_info,), np.inf)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)
        
        # Initialize state variables
        self.reset()
        
    def _get_observation(self) -> np.ndarray:
        """
        Get current observation.
        
        Returns:
            Observation array
        """
        # Get market data window
        data_window = self.data.iloc[self.current_step - self.window_size:self.current_step].values.flatten()
        
        # Position information
        position_info = np.array([self.position, self.balance, self.portfolio_value])
        
        # Combine market data and position info
        observation = np.concatenate([data_window, position_info])
        
        return observation.astype(np.float32)
    
    def _calculate_reward(self) -> float:
        """
        Calculate reward based on portfolio value change and action taken.
        
        Returns:
            Reward value
        """
        # Calculate portfolio value
        new_portfolio_value = self.balance
        if self.position == 1:
            new_portfolio_value += self.shares * self.current_price
            
        # Calculate reward as change in portfolio value
        reward = (new_portfolio_value - self.portfolio_value) * self.reward_scaling
        
        # Update portfolio value
        self.portfolio_value = new_portfolio_value
        
        return reward
    
    def _take_action(self, action: int) -> float:
        """
        Take trading action and calculate reward.
        
        Args:
            action: Trading action (0=hold, 1=buy, 2=sell)
            
        Returns:
            Reward value
        """
        # Get current price
        self.current_price = self.data.iloc[self.current_step]['close']
        
        # Initialize reward
        reward = 0
        
        # Execute action
        if action == 1:  # Buy
            if self.position == 0:
                # Calculate max shares to buy
                max_shares = self.balance / (self.current_price * (1 + self.transaction_fee))
                self.shares = max_shares * 0.95  # Use 95% of available funds
                
                # Update balance
                cost = self.shares * self.current_price * (1 + self.transaction_fee)
                self.balance -= cost
                self.position = 1
                
                logger.debug(f"Buy: {self.shares:.4f} shares at {self.current_price:.4f}")
                
        elif action == 2:  # Sell
            if self.position == 1:
                # Sell all shares
                sale_value = self.shares * self.current_price * (1 - self.transaction_fee)
                self.balance += sale_value
                self.shares = 0
                self.position = 0
                
                logger.debug(f"Sell: {self.shares:.4f} shares at {self.current_price:.4f}")
        
        # Calculate reward
        reward = self._calculate_reward()
        
        return reward
    
    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, Dict]:
        """
        Reset environment to initial state.
        
        Args:
            seed: Random seed
            options: Additional options
            
        Returns:
            Initial observation and info
        """
        super().reset(seed=seed)
        
        # Reset position
        self.position = 0  # 0=no position, 1=long position
        self.shares = 0
        self.balance = self.initial_balance
        self.portfolio_value = self.balance
        
        # Start at window_size to have enough data for first observation
        self.current_step = self.window_size
        self.current_price = self.data.iloc[self.current_step]['close']
        
        # Get initial observation
        observation = self._get_observation()
        
        # Information dictionary
        info = {}
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Take a step in the environment.
        
        Args:
            action: Trading action (0=hold, 1=buy, 2=sell)
            
        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        # Take action and get reward
        reward = self._take_action(action)
        
        # Move to next step
        self.current_step += 1
        
        # Check if episode is done
        done = self.current_step >= len(self.data) - 1
        
        # Get new observation
        observation = self._get_observation()
        
        # Information dictionary
        info = {
            'portfolio_value': self.portfolio_value,
            'balance': self.balance,
            'position': self.position,
            'current_price': self.current_price
        }
        
        return observation, reward, done, False, info


class RLTradingAgent:
    """
    Reinforcement Learning Trading Agent.
    
    Attributes:
        model_type (str): Type of RL algorithm to use
        env: Trading environment
        model: Trained RL model
        model_dir (str): Directory to save models
    """
    
    def __init__(self, 
                 model_type: str = 'ppo', 
                 model_dir: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/AI/models/saved_models'):
        """
        Initialize the RL trading agent.
        
        Args:
            model_type: Type of RL algorithm ('ppo', 'a2c', or 'dqn')
            model_dir: Directory to save models
        """
        self.model_type = model_type.lower()
        self.model_dir = model_dir
        self.env = None
        self.model = None
        
        # Ensure model directory exists
        os.makedirs(self.model_dir, exist_ok=True)
        
        logger.info(f"Initialized {model_type} RL trading agent")
    
    def create_environment(self, 
                         data: pd.DataFrame,
                         initial_balance: float = 10000.0,
                         transaction_fee: float = 0.001,
                         window_size: int = 20) -> TradingEnvironment:
        """
        Create a trading environment for RL training.
        
        Args:
            data: DataFrame with market data
            initial_balance: Initial account balance
            transaction_fee: Trading transaction fee percentage
            window_size: Observation window size
            
        Returns:
            Trading environment
        """
        # Create base environment
        env = TradingEnvironment(
            data=data,
            initial_balance=initial_balance,
            transaction_fee=transaction_fee,
            window_size=window_size
        )
        
        # Wrap environment for monitoring
        log_dir = os.path.join(self.model_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        env = Monitor(env, log_dir)
        
        # Vectorize environment
        env = DummyVecEnv([lambda: env])
        
        # Normalize environment for stable training
        env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0, clip_reward=10.0)
        
        self.env = env
        return env
    
    def build_model(self):
        """
        Build the RL model based on the specified type.
        """
        if self.env is None:
            logger.error("Environment not created. Call create_environment first.")
            return
            
        if self.model_type == 'ppo':
            self.model = PPO('MlpPolicy', self.env, verbose=1, 
                            learning_rate=0.0003, n_steps=2048, batch_size=64,
                            gamma=0.99, gae_lambda=0.95, clip_range=0.2,
                            tensorboard_log=os.path.join(self.model_dir, 'tensorboard'))
        elif self.model_type == 'a2c':
            self.model = A2C('MlpPolicy', self.env, verbose=1,
                           learning_rate=0.0007, gamma=0.99,
                           tensorboard_log=os.path.join(self.model_dir, 'tensorboard'))
        elif self.model_type == 'dqn':
            self.model = DQN('MlpPolicy', self.env, verbose=1,
                           learning_rate=0.0001, buffer_size=50000, learning_starts=1000,
                           batch_size=32, target_update_interval=500, exploration_fraction=0.2,
                           tensorboard_log=os.path.join(self.model_dir, 'tensorboard'))
        else:
            logger.error(f"Unsupported model type: {self.model_type}")
            raise ValueError(f"Unsupported model type: {self.model_type}")
            
        logger.info(f"Built {self.model_type} model")
    
    def train(self, total_timesteps: int = 100000) -> None:
        """
        Train the RL model.
        
        Args:
            total_timesteps: Total number of training timesteps
        """
        if self.model is None:
            self.build_model()
            
        # Setup callbacks
        eval_env = self.env
        callback_best = StopTrainingOnRewardThreshold(reward_threshold=200, verbose=1)
        eval_callback = EvalCallback(eval_env, callback_on_new_best=callback_best, verbose=1,
                                   eval_freq=10000, deterministic=True, render=False)
        
        # Train the model
        logger.info(f"Training {self.model_type} model for {total_timesteps} timesteps")
        self.model.learn(total_timesteps=total_timesteps, callback=eval_callback, 
                      tb_log_name=f"{self.model_type}_training")
        
        # Save the model
        self.save_model()
        
        logger.info(f"Finished training {self.model_type} model")
    
    def predict(self, observation: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        Make a prediction using the trained model.
        
        Args:
            observation: Environment observation
            
        Returns:
            Tuple of (action, state)
        """
        if self.model is None:
            logger.error("No trained model found. Please train or load a model first.")
            return None, None
            
        action, state = self.model.predict(observation, deterministic=True)
        return action, state
    
    def evaluate(self, test_data: pd.DataFrame, episodes: int = 10) -> Dict[str, float]:
        """
        Evaluate the model on test data.
        
        Args:
            test_data: DataFrame with test market data
            episodes: Number of evaluation episodes
            
        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            logger.error("No trained model found. Please train or load a model first.")
            return None
            
        # Create test environment
        test_env = TradingEnvironment(
            data=test_data,
            initial_balance=10000.0,
            transaction_fee=0.001,
            window_size=20
        )
        
        # Run evaluation episodes
        returns = []
        for episode in range(episodes):
            obs, _ = test_env.reset()
            done = False
            episode_return = 0
            
            while not done:
                action, _states = self.model.predict(obs, deterministic=True)
                obs, reward, done, truncated, info = test_env.step(action)
                episode_return += reward
                
            returns.append(episode_return)
            logger.debug(f"Episode {episode}: Return = {episode_return:.2f}, Final Value = {info['portfolio_value']:.2f}")
            
        # Calculate metrics
        metrics = {
            'mean_return': np.mean(returns),
            'std_return': np.std(returns),
            'min_return': np.min(returns),
            'max_return': np.max(returns),
            'median_return': np.median(returns)
        }
        
        logger.info(f"Model evaluation: Mean Return = {metrics['mean_return']:.2f}")
        return metrics
    
    def save_model(self, custom_path: str = None) -> str:
        """
        Save the trained model.
        
        Args:
            custom_path: Optional custom path to save the model
            
        Returns:
            Path where the model was saved
        """
        if self.model is None:
            logger.error("No trained model to save")
            return None
            
        save_path = custom_path or os.path.join(self.model_dir, f"{self.model_type}_model")
        self.model.save(save_path)
        
        # Save environment normalization parameters
        if hasattr(self.env, 'save'):
            self.env.save(os.path.join(self.model_dir, f"{self.model_type}_env"))
            
        logger.info(f"Model saved to {save_path}")
        return save_path
    
    def load_model(self, model_path: str = None, env_path: str = None) -> bool:
        """
        Load a trained model.
        
        Args:
            model_path: Path to the model file
            env_path: Path to the environment normalization parameters
            
        Returns:
            True if loaded successfully
        """
        model_path = model_path or os.path.join(self.model_dir, f"{self.model_type}_model")
        env_path = env_path or os.path.join(self.model_dir, f"{self.model_type}_env")
        
        if not os.path.exists(model_path + ".zip"):
            logger.error(f"Model file not found: {model_path}.zip")
            return False
        
        # Load the appropriate model type
        if self.model_type == 'ppo':
            self.model = PPO.load(model_path)
        elif self.model_type == 'a2c':
            self.model = A2C.load(model_path)
        elif self.model_type == 'dqn':
            self.model = DQN.load(model_path)
        else:
            logger.error(f"Unsupported model type: {self.model_type}")
            return False
            
        # Load environment normalization parameters if available
        if self.env is not None and os.path.exists(env_path):
            self.env = VecNormalize.load(env_path, self.env)
            # Don't update normalization statistics during prediction
            self.env.training = False
            self.env.norm_reward = False
                
        logger.info(f"Model loaded from {model_path}")
        return True
