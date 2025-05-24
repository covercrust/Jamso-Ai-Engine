"""
Deep Learning Models for Market Prediction

This module provides deep learning models for market prediction, including:
- LSTM models for time series forecasting
- Transformer models for sequential data
- CNN models for pattern recognition in market data
- Hybrid models combining multiple architectures
"""

import numpy as np
import pandas as pd
import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, LSTM, Dropout, BatchNormalization, Input, Conv1D, MaxPooling1D, Flatten
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import os

# Configure logger
logger = logging.getLogger(__name__)

class DeepLearningPredictor:
    """
    Deep Learning Predictor for market forecasting.
    
    Attributes:
        model_type (str): Type of model to use ('lstm', 'transformer', 'cnn', 'hybrid')
        lookback_window (int): Number of time steps to look back
        forecast_horizon (int): Number of time steps to forecast
        feature_columns (List[str]): List of feature columns to use
        model_dir (str): Directory to save models
        db_path (str): Path to the SQLite database
        model: The trained model
        scaler: Data scaler for normalizing features
    """
    
    def __init__(self, 
                model_type: str = 'lstm',
                lookback_window: int = 20,
                forecast_horizon: int = 5,
                feature_columns: List[str] = None,
                model_dir: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/AI/models/saved_models',
                db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'):
        """
        Initialize the deep learning predictor.
        
        Args:
            model_type: Type of model ('lstm', 'transformer', 'cnn', 'hybrid')
            lookback_window: Number of time steps to look back
            forecast_horizon: Number of time steps to forecast
            feature_columns: List of feature columns to use, defaults to price and volume data
            model_dir: Directory to save models
            db_path: Path to the SQLite database
        """
        self.model_type = model_type.lower()
        self.lookback_window = lookback_window
        self.forecast_horizon = forecast_horizon
        self.model_dir = model_dir
        self.db_path = db_path
        
        # Default feature columns if none provided
        self.feature_columns = feature_columns or ['close', 'open', 'high', 'low', 'volume']
        
        # Initialize placeholders
        self.model = None
        self.scaler = MinMaxScaler()
        
        # Ensure model directory exists
        os.makedirs(self.model_dir, exist_ok=True)
        
        logger.info(f"Initialized {model_type} deep learning predictor with {lookback_window} lookback window")
    
    def _prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for deep learning model training.
        
        Args:
            df: DataFrame with market data
            
        Returns:
            X: Features array with shape (samples, lookback_window, features)
            y: Target array with shape (samples, forecast_horizon)
        """
        # Select and scale features
        features = df[self.feature_columns].values
        scaled_features = self.scaler.fit_transform(features)
        
        X, y = [], []
        for i in range(self.lookback_window, len(scaled_features) - self.forecast_horizon + 1):
            X.append(scaled_features[i - self.lookback_window:i])
            y.append(scaled_features[i:i + self.forecast_horizon, 0])  # Forecasting close prices
        
        return np.array(X), np.array(y)
    
    def _build_lstm_model(self, input_shape: Tuple) -> Model:
        """
        Build an LSTM model for time series forecasting.
        
        Args:
            input_shape: Shape of input data (lookback_window, features)
            
        Returns:
            Compiled LSTM model
        """
        model = Sequential()
        model.add(LSTM(100, return_sequences=True, input_shape=input_shape))
        model.add(Dropout(0.2))
        model.add(BatchNormalization())
        
        model.add(LSTM(50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(BatchNormalization())
        
        model.add(Dense(50, activation='relu'))
        model.add(Dropout(0.2))
        
        model.add(Dense(self.forecast_horizon))
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        return model
    
    def _build_cnn_model(self, input_shape: Tuple) -> Model:
        """
        Build a CNN model for pattern recognition in market data.
        
        Args:
            input_shape: Shape of input data (lookback_window, features)
            
        Returns:
            Compiled CNN model
        """
        model = Sequential()
        model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Dropout(0.2))
        
        model.add(Conv1D(filters=128, kernel_size=3, activation='relu'))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Dropout(0.2))
        
        model.add(Flatten())
        model.add(Dense(100, activation='relu'))
        model.add(Dropout(0.3))
        model.add(Dense(self.forecast_horizon))
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        return model
    
    def _build_hybrid_model(self, input_shape: Tuple) -> Model:
        """
        Build a hybrid CNN-LSTM model for market forecasting.
        
        Args:
            input_shape: Shape of input data (lookback_window, features)
            
        Returns:
            Compiled hybrid model
        """
        # Input layer
        inputs = Input(shape=input_shape)
        
        # CNN layers for feature extraction
        conv1 = Conv1D(filters=64, kernel_size=3, activation='relu')(inputs)
        pool1 = MaxPooling1D(pool_size=2)(conv1)
        
        # LSTM layers for temporal dependencies
        lstm1 = LSTM(50, return_sequences=True)(pool1)
        drop1 = Dropout(0.2)(lstm1)
        
        lstm2 = LSTM(50)(drop1)
        drop2 = Dropout(0.2)(lstm2)
        
        # Output layer
        outputs = Dense(self.forecast_horizon)(drop2)
        
        # Create and compile model
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        
        return model
    
    def build_model(self) -> Model:
        """
        Build the deep learning model based on the specified type.
        
        Returns:
            The compiled model
        """
        # Determine input shape from lookback window and number of features
        input_shape = (self.lookback_window, len(self.feature_columns))
        
        if self.model_type == 'lstm':
            self.model = self._build_lstm_model(input_shape)
        elif self.model_type == 'cnn':
            self.model = self._build_cnn_model(input_shape)
        elif self.model_type == 'hybrid':
            self.model = self._build_hybrid_model(input_shape)
        else:
            logger.error(f"Unsupported model type: {self.model_type}")
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        logger.info(f"Built {self.model_type} model with {self.model.count_params()} parameters")
        return self.model
    
    def train(self, df: pd.DataFrame, epochs: int = 50, batch_size: int = 32, validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train the deep learning model on market data.
        
        Args:
            df: DataFrame with market data
            epochs: Number of training epochs
            batch_size: Training batch size
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training history
        """
        if self.model is None:
            self.build_model()
            
        # Prepare data
        X, y = self._prepare_data(df)
        
        # Create callbacks
        model_path = os.path.join(self.model_dir, f"{self.model_type}_model.h5")
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ModelCheckpoint(filepath=model_path, save_best_only=True, monitor='val_loss')
        ]
        
        # Train model
        logger.info(f"Training {self.model_type} model on {len(X)} samples")
        history = self.model.fit(
            X, y, 
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info(f"Finished training {self.model_type} model, final loss: {history.history['loss'][-1]:.4f}")
        return history.history
    
    def predict(self, market_data: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model.
        
        Args:
            market_data: DataFrame with recent market data
            
        Returns:
            Array of predicted values
        """
        if self.model is None:
            model_path = os.path.join(self.model_dir, f"{self.model_type}_model.h5")
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                logger.info(f"Loaded {self.model_type} model from {model_path}")
            else:
                logger.error("No trained model found. Please train the model first.")
                return None
        
        # Select features and scale
        features = market_data[self.feature_columns].values
        
        # Reshape for prediction
        if len(features) < self.lookback_window:
            logger.error(f"Not enough data for prediction, need at least {self.lookback_window} data points")
            return None
            
        scaled_features = self.scaler.transform(features)
        X = np.array([scaled_features[-self.lookback_window:]])
        
        # Make prediction
        scaled_prediction = self.model.predict(X)
        
        # Convert the predicted values back to original scale
        # Create a matrix with zeros and place predictions in the first column
        dummy = np.zeros((scaled_prediction.shape[1], features.shape[1]))
        dummy[:, 0] = scaled_prediction[0]
        
        # Inverse transform to get original scale
        prediction = self.scaler.inverse_transform(dummy)[:, 0]
        
        return prediction
    
    def evaluate(self, test_data: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate model performance on test data.
        
        Args:
            test_data: DataFrame with test market data
            
        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            logger.error("No trained model found. Please train the model first.")
            return None
            
        # Prepare test data
        X, y = self._prepare_data(test_data)
        
        # Evaluate
        results = self.model.evaluate(X, y, verbose=0)
        metrics = {
            'mse': results[0],
            'mae': results[1]
        }
        
        logger.info(f"Model evaluation: MSE = {metrics['mse']:.4f}, MAE = {metrics['mae']:.4f}")
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
            
        save_path = custom_path or os.path.join(self.model_dir, f"{self.model_type}_model.h5")
        self.model.save(save_path)
        
        # Save scaler as well
        scaler_path = os.path.join(self.model_dir, f"{self.model_type}_scaler.pkl")
        import pickle
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
            
        logger.info(f"Model and scaler saved to {save_path} and {scaler_path}")
        return save_path
    
    def load_model(self, model_path: str = None, scaler_path: str = None) -> bool:
        """
        Load a trained model.
        
        Args:
            model_path: Path to the model file
            scaler_path: Path to the scaler file
            
        Returns:
            True if loaded successfully
        """
        model_path = model_path or os.path.join(self.model_dir, f"{self.model_type}_model.h5")
        scaler_path = scaler_path or os.path.join(self.model_dir, f"{self.model_type}_scaler.pkl")
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return False
            
        self.model = tf.keras.models.load_model(model_path)
        
        # Load scaler if available
        if os.path.exists(scaler_path):
            import pickle
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
                
        logger.info(f"Model loaded from {model_path}")
        return True
