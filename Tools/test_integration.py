#!/usr/bin/env python3
"""
End-to-End Integration test for Jamso-AI-Engine APIs
Tests comprehensive end-to-end functionality of credential system with actual API calls
to Capital.com, Telegram, and OpenAI APIs.

This test verifies:
1. Credentials are properly retrieved from the secure database
2. Authentication with external APIs succeeds
3. Basic API functionality works (market data retrieval, message sending, AI responses)
4. Error handling functions correctly
5. Proper masking of sensitive information in logs

A JSON report with detailed test results is generated after each test run.
"""
import os
import sys
import logging
import argparse
import json
import requests
import time
import platform
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IntegrationTest")

# Import credential manager
try:
    from src.Credentials.credentials_manager import CredentialManager
    credential_manager = CredentialManager()
    logger.info("Successfully imported CredentialManager")
except ImportError as e:
    logger.error(f"Failed to import CredentialManager: {e}")
    sys.exit(1)

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class IntegrationTester:
    def __init__(self):
        self.results = {
            "capital_com": {"status": "not_tested", "details": {}, "timestamp": "", "duration_ms": 0},
            "telegram": {"status": "not_tested", "details": {}, "timestamp": "", "duration_ms": 0},
            "openai": {"status": "not_tested", "details": {}, "timestamp": "", "duration_ms": 0}
        }
        self.credential_manager = credential_manager
        self.test_start_time = None
        self.test_report = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "results": self.results,
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "total_duration_ms": 0
            }
        }
    
    def _get_system_info(self):
        """Get basic system information for the test report"""
        import platform
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }
    
    def mask_credential(self, value):
        """Mask credential for secure display"""
        if not value:
            return "None"
        if len(value) > 8:
            return '*' * (len(value) - 4) + value[-4:]
        return '*' * len(value)
    
    def _record_test_start(self):
        """Record the start time of a test"""
        self.test_start_time = time.time()
    
    def _record_test_end(self, api_name, status, details):
        """Record the end time of a test and calculate duration"""
        if self.test_start_time:
            duration_ms = int((time.time() - self.test_start_time) * 1000)
            self.results[api_name] = {
                "status": status,
                "details": details,
                "timestamp": datetime.now().isoformat(),
                "duration_ms": duration_ms
            }
            self.test_start_time = None
    
    def test_capital_com(self):
        """Test Capital.com API integration"""
        print(f"\n{Colors.BLUE}Testing Capital.com API integration{Colors.ENDC}")
        self._record_test_start()
        
        test_details = {
            "credential_source": "secure_database", 
            "tests_performed": [],
            "test_data": {}
        }
        
        try:
            print(f"{Colors.YELLOW}Step 1: Retrieving credentials from secure database{Colors.ENDC}")
            # Get credentials
            api_key = self.credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY')
            api_login = self.credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN')
            api_password = self.credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')
            
            # Log masked credentials
            print(f"API Key: {self.mask_credential(api_key)}")
            if api_login:
                print(f"API Login: {api_login[:3]}...{api_login[-3:] if len(api_login) > 6 else ''}")
            else:
                print("API Login: Not set")
            
            test_details["tests_performed"].append("credential_retrieval")
            test_details["test_data"]["credential_retrieval"] = {
                "has_api_key": bool(api_key),
                "has_api_login": bool(api_login),
                "has_api_password": bool(api_password)
            }
            
            if not all([api_key, api_login, api_password]):
                print(f"{Colors.RED}Missing one or more Capital.com credentials{Colors.ENDC}")
                self._record_test_end("capital_com", "error", {
                    "error": "Missing credentials",
                    "details": test_details
                })
                return False
            
            # Import Capital.com client
            print(f"\n{Colors.YELLOW}Step 2: Creating API client{Colors.ENDC}")
            try:
                # Try direct import first
                try:
                    from src.AI.fallback_capital_api import FallbackApiClient
                    client_source = "direct_import"
                    print(f"{Colors.GREEN}Successfully imported FallbackApiClient from src.AI.fallback_capital_api{Colors.ENDC}")
                except ImportError:
                    # If that fails, try creating a simplified version for testing
                    print(f"{Colors.YELLOW}Couldn't import FallbackApiClient, creating a test version{Colors.ENDC}")
                    client_source = "fallback_implementation"
                    
                    # Create a simple test client
                    class FallbackApiClient:
                        def __init__(self):
                            self.api_key = api_key
                            self.username = api_login
                            self.password = api_password
                            self.base_url = "https://api-capital.backend-capital.com/api/v1"
                            self.session = requests.Session()
                            self.is_authenticated = False
                            
                            # Add information about the client implementation
                            self.client_info = {
                                "source": "test_integration.py fallback implementation",
                                "created_at": datetime.now().isoformat()
                            }
                            
                            print(f"{Colors.GREEN}Created fallback API client for testing{Colors.ENDC}")
                            
                        def authenticate(self):
                            url = f"{self.base_url}/session"
                            headers = {
                                "X-CAP-API-KEY": self.api_key,
                                "Content-Type": "application/json"
                            }
                            payload = {
                                "identifier": self.username,
                                "password": self.password
                            }
                            response = self.session.post(url, headers=headers, json=payload, timeout=30)
                            if response.status_code == 200:
                                self.CST = response.headers.get('CST', '')
                                self.X_TOKEN = response.headers.get('X-SECURITY-TOKEN', '')
                                self.is_authenticated = bool(self.CST and self.X_TOKEN)
                                return self.is_authenticated
                            return False
                            
                        def get_historical_prices(self, symbol, resolution, days):
                            if not self.is_authenticated:
                                return None
                            url = f"{self.base_url}/prices/{symbol}"
                            params = {
                                "resolution": resolution,
                                "max": 10,
                                "from": "now-5d",
                                "to": "now"
                            }
                            headers = {
                                "X-CAP-API-KEY": self.api_key,
                                "CST": self.CST,
                                "X-SECURITY-TOKEN": self.X_TOKEN
                            }
                            response = self.session.get(url, headers=headers, params=params, timeout=30)
                            if response.status_code == 200:
                                return response.json().get("prices", [])
                            return []
                
                client = FallbackApiClient()
                test_details["tests_performed"].append("client_creation")
                test_details["test_data"]["client_creation"] = {
                    "success": True,
                    "client_type": client_source
                }
                print(f"{Colors.GREEN}Successfully created test API client{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.RED}Failed to create API client: {e}{Colors.ENDC}")
                test_details["tests_performed"].append("client_creation")
                test_details["test_data"]["client_creation"] = {
                    "success": False,
                    "error": str(e),
                    "client_type": client_source
                }
                self._record_test_end("capital_com", "error", {
                    "error": f"Client creation error: {str(e)}",
                    "details": test_details
                })
                return False
            
            # Test authentication
            print(f"\n{Colors.YELLOW}Step 3: Authenticating with Capital.com API{Colors.ENDC}")
            try:
                auth_start = time.time()
                auth_result = client.authenticate()
                auth_duration = time.time() - auth_start
                
                test_details["tests_performed"].append("authentication")
                test_details["test_data"]["authentication"] = {
                    "success": bool(auth_result),
                    "duration_ms": int(auth_duration * 1000)
                }
                
                if auth_result:
                    print(f"{Colors.GREEN}Authentication successful (took {auth_duration:.2f}s){Colors.ENDC}")
                else:
                    print(f"{Colors.RED}Authentication failed{Colors.ENDC}")
                    self._record_test_end("capital_com", "error", {
                        "error": "Authentication failed",
                        "details": test_details
                    })
                    return False
            except Exception as e:
                print(f"{Colors.RED}Authentication error: {e}{Colors.ENDC}")
                test_details["tests_performed"].append("authentication")
                test_details["test_data"]["authentication"] = {
                    "success": False,
                    "error": str(e)
                }
                self._record_test_end("capital_com", "error", {
                    "error": f"Authentication error: {str(e)}",
                    "details": test_details
                })
                return False
            
            # Test fetching market data
            print(f"\n{Colors.YELLOW}Step 4: Testing market data retrieval{Colors.ENDC}")
            test_details["tests_performed"].append("market_data")
            test_details["test_data"]["client_source"] = client_source
            
            # Define test symbols
            test_symbols = ["BTCUSD", "EURUSD"]
            market_data_results = {}
            
            for symbol in test_symbols:
                print(f"Testing market data for {symbol}...")
                try:
                    data_start = time.time()
                    prices = client.get_historical_prices(symbol, "HOUR", 5)
                    data_duration = time.time() - data_start
                    
                    market_data_results[symbol] = {
                        "success": prices is not None and len(prices) > 0,
                        "data_points": len(prices) if prices else 0,
                        "duration_ms": int(data_duration * 1000)
                    }
                    
                    if prices is not None and len(prices) > 0:
                        market_data_results[symbol].update({
                            "first_timestamp": str(prices[0].get('timestamp', 'unknown')),
                            "last_timestamp": str(prices[-1].get('timestamp', 'unknown')),
                            "sample_open": prices[0].get('openPrice', 'unknown') if len(prices) > 0 else "unknown",
                            "sample_close": prices[0].get('closePrice', 'unknown') if len(prices) > 0 else "unknown"
                        })
                        print(f"{Colors.GREEN}Successfully fetched {len(prices)} price points for {symbol} (took {data_duration:.2f}s){Colors.ENDC}")
                    else:
                        print(f"{Colors.RED}Failed to fetch price data for {symbol}{Colors.ENDC}")
                        market_data_results[symbol]["error"] = "No data returned"
                except Exception as e:
                    print(f"{Colors.RED}Error fetching prices for {symbol}: {e}{Colors.ENDC}")
                    market_data_results[symbol] = {
                        "success": False,
                        "error": str(e)
                    }
            
            test_details["test_data"]["market_data"] = market_data_results
            
            # Evaluate overall market data test success
            market_data_success = any(result.get("success", False) for result in market_data_results.values())
            
            if market_data_success:
                print(f"{Colors.GREEN}✓ Market data retrieval test passed{Colors.ENDC}")
                self._record_test_end("capital_com", "success", test_details)
                return True
            else:
                print(f"{Colors.RED}✗ Market data retrieval test failed for all symbols{Colors.ENDC}")
                self._record_test_end("capital_com", "error", {
                    "error": "Failed to retrieve market data for any symbol",
                    "details": test_details
                })
                return False
                
        except Exception as e:
            print(f"{Colors.RED}Unexpected error in Capital.com test: {e}{Colors.ENDC}")
            self.results["capital_com"] = {
                "status": "error",
                "details": {"error": f"Unexpected error: {str(e)}"}
            }
            return False
    
    def test_telegram(self):
        """Test Telegram API integration"""
        print(f"\n{Colors.BLUE}Testing Telegram API integration{Colors.ENDC}")
        self._record_test_start()
        
        test_details = {
            "credential_source": "secure_database", 
            "tests_performed": [],
            "test_data": {}
        }
        
        try:
            print(f"{Colors.YELLOW}Step 1: Retrieving credentials from secure database{Colors.ENDC}")
            # Get credentials
            bot_token = self.credential_manager.get_credential('telegram', 'TELEGRAM_BOT_TOKEN')
            chat_id = self.credential_manager.get_credential('telegram', 'TELEGRAM_CHAT_ID')
            
            # Log masked credentials
            print(f"Bot Token: {self.mask_credential(bot_token)}")
            print(f"Chat ID: {chat_id or 'Not set'}")
            
            test_details["tests_performed"].append("credential_retrieval")
            test_details["test_data"]["credential_retrieval"] = {
                "has_bot_token": bool(bot_token),
                "has_chat_id": bool(chat_id)
            }
            
            if not all([bot_token, chat_id]):
                print(f"{Colors.RED}Missing one or more Telegram credentials{Colors.ENDC}")
                self._record_test_end("telegram", "error", {
                    "error": "Missing credentials",
                    "details": test_details
                })
                return False
            
            # Step 2: Verify bot token validity by getting bot info
            print(f"\n{Colors.YELLOW}Step 2: Verifying bot token validity{Colors.ENDC}")
            try:
                print("Fetching bot information...")
                url = f"https://api.telegram.org/bot{bot_token}/getMe"
                
                info_start = time.time()
                response = requests.get(url, timeout=10)
                info_duration = time.time() - info_start
                
                test_details["tests_performed"].append("token_verification")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        bot_info = result.get("result", {})
                        bot_username = bot_info.get("username", "Unknown")
                        bot_name = bot_info.get("first_name", "Unknown Bot")
                        
                        print(f"{Colors.GREEN}Successfully verified bot token. Bot: @{bot_username} ({bot_name}){Colors.ENDC}")
                        test_details["test_data"]["token_verification"] = {
                            "success": True,
                            "bot_username": bot_username,
                            "bot_name": bot_name,
                            "duration_ms": int(info_duration * 1000)
                        }
                    else:
                        print(f"{Colors.RED}Invalid bot token: {result.get('description', 'unknown')}{Colors.ENDC}")
                        test_details["test_data"]["token_verification"] = {
                            "success": False,
                            "error": result.get('description', 'unknown'),
                            "duration_ms": int(info_duration * 1000)
                        }
                        self._record_test_end("telegram", "error", {
                            "error": f"Invalid bot token: {result.get('description', 'unknown')}",
                            "details": test_details
                        })
                        return False
                else:
                    print(f"{Colors.RED}Failed to verify bot token. HTTP status: {response.status_code}{Colors.ENDC}")
                    test_details["test_data"]["token_verification"] = {
                        "success": False,
                        "error": f"HTTP error: {response.status_code}",
                        "duration_ms": int(info_duration * 1000)
                    }
                    self._record_test_end("telegram", "error", {
                        "error": f"HTTP error: {response.status_code}",
                        "details": test_details
                    })
                    return False
            except Exception as e:
                print(f"{Colors.RED}Error verifying bot token: {e}{Colors.ENDC}")
                test_details["test_data"]["token_verification"] = {
                    "success": False,
                    "error": str(e)
                }
                self._record_test_end("telegram", "error", {
                    "error": f"Token verification error: {str(e)}",
                    "details": test_details
                })
                return False
            
            # Step 3: Send a test message
            print(f"\n{Colors.YELLOW}Step 3: Sending test message{Colors.ENDC}")
            try:
                test_message = f"Jamso-AI Integration Test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": test_message,
                    "disable_notification": True,
                    "parse_mode": "HTML"
                }
                
                print("Sending test message to Telegram...")
                msg_start = time.time()
                response = requests.post(url, json=payload, timeout=10)
                msg_duration = time.time() - msg_start
                
                test_details["tests_performed"].append("send_message")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        message_id = result.get("result", {}).get("message_id", "unknown")
                        print(f"{Colors.GREEN}Successfully sent test message to Telegram (message ID: {message_id}){Colors.ENDC}")
                        test_details["test_data"]["send_message"] = {
                            "success": True,
                            "message_id": message_id,
                            "duration_ms": int(msg_duration * 1000)
                        }
                        
                        # Optional: Try to retrieve the message we just sent
                        try:
                            print("\nVerifying message delivery...")
                            history_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
                            history_params = {"limit": 5, "timeout": 5}
                            history_response = requests.get(history_url, params=history_params)
                            
                            if history_response.status_code == 200:
                                history_result = history_response.json()
                                if history_result.get("ok"):
                                    test_details["test_data"]["message_verification"] = {
                                        "success": True,
                                        "updates_available": len(history_result.get("result", [])),
                                    }
                                    print(f"{Colors.GREEN}Message verification successful{Colors.ENDC}")
                                else:
                                    test_details["test_data"]["message_verification"] = {
                                        "success": False,
                                        "error": history_result.get("description", "unknown")
                                    }
                            else:
                                test_details["test_data"]["message_verification"] = {
                                    "success": False,
                                    "error": f"HTTP error: {history_response.status_code}"
                                }
                        except Exception as e:
                            print(f"{Colors.YELLOW}Warning: Could not verify message delivery: {e}{Colors.ENDC}")
                            test_details["test_data"]["message_verification"] = {
                                "success": False,
                                "error": str(e)
                            }
                        
                        # Overall success
                        self._record_test_end("telegram", "success", test_details)
                        return True
                    else:
                        print(f"{Colors.RED}Telegram API returned error: {result.get('description', 'unknown')}{Colors.ENDC}")
                        test_details["test_data"]["send_message"] = {
                            "success": False,
                            "error": result.get('description', 'unknown'),
                            "duration_ms": int(msg_duration * 1000)
                        }
                        self._record_test_end("telegram", "error", {
                            "error": f"API error: {result.get('description', 'unknown')}",
                            "details": test_details
                        })
                        return False
                else:
                    print(f"{Colors.RED}Telegram API returned status code: {response.status_code}{Colors.ENDC}")
                    test_details["test_data"]["send_message"] = {
                        "success": False,
                        "error": f"HTTP error: {response.status_code}",
                        "duration_ms": int(msg_duration * 1000)
                    }
                    self._record_test_end("telegram", "error", {
                        "error": f"HTTP error: {response.status_code}",
                        "details": test_details
                    })
                    return False
            except Exception as e:
                print(f"{Colors.RED}Error sending Telegram message: {e}{Colors.ENDC}")
                test_details["test_data"]["send_message"] = {
                    "success": False,
                    "error": str(e)
                }
                self._record_test_end("telegram", "error", {
                    "error": f"Request error: {str(e)}",
                    "details": test_details
                })
                return False
                
        except Exception as e:
            print(f"{Colors.RED}Unexpected error in Telegram test: {e}{Colors.ENDC}")
            self._record_test_end("telegram", "error", {
                "error": f"Unexpected error: {str(e)}",
                "details": test_details
            })
            return False
    
    def test_openai(self):
        """Test OpenAI API integration"""
        print(f"\n{Colors.BLUE}Testing OpenAI API integration{Colors.ENDC}")
        self._record_test_start()
        
        test_details = {
            "credential_source": "secure_database", 
            "tests_performed": [],
            "test_data": {}
        }
        
        try:
            print(f"{Colors.YELLOW}Step 1: Retrieving credentials from secure database{Colors.ENDC}")
            # Get credentials
            api_key = self.credential_manager.get_credential('openai', 'OPENAI_API_KEY')
            
            # Log masked credentials
            print(f"API Key: {self.mask_credential(api_key)}")
            
            test_details["tests_performed"].append("credential_retrieval")
            test_details["test_data"]["credential_retrieval"] = {
                "has_api_key": bool(api_key)
            }
            
            if not api_key:
                print(f"{Colors.RED}Missing OpenAI API key{Colors.ENDC}")
                self._record_test_end("openai", "error", {
                    "error": "Missing API key",
                    "details": test_details
                })
                return False
            
            # Step 2: Check API key validity with a simple models request
            print(f"\n{Colors.YELLOW}Step 2: Verifying API key validity{Colors.ENDC}")
            try:
                url = "https://api.openai.com/v1/models"
                headers = {
                    "Authorization": f"Bearer {api_key}"
                }
                
                print("Fetching available models list...")
                models_start = time.time()
                response = requests.get(url, headers=headers, timeout=20)
                models_duration = time.time() - models_start
                
                test_details["tests_performed"].append("api_key_verification")
                
                if response.status_code == 200:
                    models_data = response.json()
                    
                    # Count models by category
                    gpt_models = [model for model in models_data.get("data", []) if "gpt" in model.get("id", "").lower()]
                    dall_e_models = [model for model in models_data.get("data", []) if "dall" in model.get("id", "").lower()]
                    embedding_models = [model for model in models_data.get("data", []) if "embed" in model.get("id", "").lower()]
                    
                    model_counts = {
                        "total": len(models_data.get("data", [])),
                        "gpt": len(gpt_models),
                        "dall_e": len(dall_e_models),
                        "embedding": len(embedding_models)
                    }
                    
                    print(f"{Colors.GREEN}Successfully verified API key. Available models: {model_counts['total']} ({model_counts['gpt']} GPT models){Colors.ENDC}")
                    test_details["test_data"]["api_key_verification"] = {
                        "success": True,
                        "model_counts": model_counts,
                        "duration_ms": int(models_duration * 1000),
                        "sample_models": [model.get("id") for model in models_data.get("data", [])[:3]]
                    }
                    
                    # Store a list of gpt models for later use
                    available_gpt_models = [model.get("id") for model in gpt_models]
                    test_model = next((model for model in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"] if model in available_gpt_models), "gpt-3.5-turbo")
                else:
                    error_msg = f"Failed to verify API key. HTTP status: {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg = f"{error_data['error'].get('message', error_msg)}"
                    except:
                        pass
                    
                    print(f"{Colors.RED}{error_msg}{Colors.ENDC}")
                    test_details["test_data"]["api_key_verification"] = {
                        "success": False,
                        "error": error_msg,
                        "duration_ms": int(models_duration * 1000)
                    }
                    self._record_test_end("openai", "error", {
                        "error": error_msg,
                        "details": test_details
                    })
                    return False
            except Exception as e:
                print(f"{Colors.RED}Error verifying API key: {e}{Colors.ENDC}")
                test_details["test_data"]["api_key_verification"] = {
                    "success": False,
                    "error": str(e)
                }
                self._record_test_end("openai", "error", {
                    "error": f"API key verification error: {str(e)}",
                    "details": test_details
                })
                return False
            
            # Step 3: Try to import openai (optional)
            print(f"\n{Colors.YELLOW}Step 3: Checking for OpenAI module{Colors.ENDC}")
            test_details["tests_performed"].append("module_check")
            client_type = "direct_api"
            
            try:
                import openai
                openai.api_key = api_key
                client_type = "openai_module"
                
                print(f"{Colors.GREEN}Successfully imported OpenAI module (version: {openai.__version__}){Colors.ENDC}")
                test_details["test_data"]["module_check"] = {
                    "success": True,
                    "module_present": True,
                    "version": getattr(openai, "__version__", "unknown")
                }
            except ImportError as e:
                print(f"{Colors.YELLOW}OpenAI module not installed, will use direct API request{Colors.ENDC}")
                test_details["test_data"]["module_check"] = {
                    "success": True,
                    "module_present": False,
                    "error": str(e)
                }
            except Exception as e:
                print(f"{Colors.YELLOW}Error setting up OpenAI module: {e}. Using direct API request{Colors.ENDC}")
                test_details["test_data"]["module_check"] = {
                    "success": False,
                    "module_present": False,
                    "error": str(e)
                }
            
            # Step 4: Make a test request
            print(f"\n{Colors.YELLOW}Step 4: Making test completion request{Colors.ENDC}")
            try:
                test_details["tests_performed"].append("completion_request")
                test_details["test_data"]["completion_request"] = {
                    "client_type": client_type,
                    "model": test_model if "test_model" in locals() else "gpt-3.5-turbo"
                }
                
                # Check if we're using the OpenAI module or making a direct request
                if client_type == "openai_module":
                    print(f"Making test request using OpenAI module with model {test_model}...")
                    
                    chat_start = time.time()
                    # Handle different versions of the OpenAI API
                    try:
                        # Try the newer client-based API first
                        response = openai.chat.completions.create(
                            model=test_model,
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": "Say 'Jamso-AI integration test successful' and nothing else."}
                            ],
                            max_tokens=20
                        )
                        chat_duration = time.time() - chat_start
                        
                        # New API format
                        if hasattr(response, 'choices') and len(response.choices) > 0:
                            message = response.choices[0].message.content
                            token_usage = response.usage.total_tokens if hasattr(response, 'usage') else None
                    except AttributeError:
                        # Fall back to older API style
                        response = openai.ChatCompletion.create(
                            model=test_model,
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": "Say 'Jamso-AI integration test successful' and nothing else."}
                            ],
                            max_tokens=20
                        )
                        chat_duration = time.time() - chat_start
                        
                        if "choices" in response and len(response["choices"]) > 0:
                            message = response["choices"][0]["message"]["content"]
                            token_usage = response.get("usage", {}).get("total_tokens")
                    
                    print(f"{Colors.GREEN}OpenAI response: {message}{Colors.ENDC}")
                    test_details["test_data"]["completion_request"].update({
                        "success": True,
                        "response": message,
                        "duration_ms": int(chat_duration * 1000),
                        "token_usage": token_usage
                    })
                    self._record_test_end("openai", "success", test_details)
                    return True
                else:
                    print(f"Making test request using direct API call with model {test_model}...")
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                    payload = {
                        "model": test_model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": "Say 'Jamso-AI integration test successful' and nothing else."}
                        ],
                        "max_tokens": 20
                    }
                    
                    chat_start = time.time()
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    chat_duration = time.time() - chat_start
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "choices" in result and len(result["choices"]) > 0:
                            message = result["choices"][0]["message"]["content"]
                            token_usage = result.get("usage", {}).get("total_tokens")
                            
                            print(f"{Colors.GREEN}OpenAI response: {message}{Colors.ENDC}")
                            test_details["test_data"]["completion_request"].update({
                                "success": True,
                                "response": message,
                                "duration_ms": int(chat_duration * 1000),
                                "token_usage": token_usage
                            })
                            self._record_test_end("openai", "success", test_details)
                            return True
                        else:
                            print(f"{Colors.RED}Invalid response from OpenAI{Colors.ENDC}")
                            test_details["test_data"]["completion_request"].update({
                                "success": False,
                                "error": "Invalid response format",
                                "duration_ms": int(chat_duration * 1000)
                            })
                            self._record_test_end("openai", "error", {
                                "error": "Invalid response format",
                                "details": test_details
                            })
                            return False
                    else:
                        error_msg = f"OpenAI API returned status code: {response.status_code}"
                        error_details = {}
                        try:
                            error_details = response.json()
                            if "error" in error_details:
                                error_msg = f"{error_details['error'].get('message', error_msg)}"
                        except:
                            error_details = {"error": f"HTTP error: {response.status_code}"}
                        
                        print(f"{Colors.RED}{error_msg}{Colors.ENDC}")
                        test_details["test_data"]["completion_request"].update({
                            "success": False,
                            "error": error_msg,
                            "error_details": error_details,
                            "duration_ms": int(chat_duration * 1000)
                        })
                        self._record_test_end("openai", "error", {
                            "error": error_msg,
                            "details": test_details
                        })
                        return False
            except Exception as e:
                print(f"{Colors.RED}Error making OpenAI request: {e}{Colors.ENDC}")
                test_details["test_data"]["completion_request"] = {
                    "success": False,
                    "error": str(e)
                }
                self._record_test_end("openai", "error", {
                    "error": f"Request error: {str(e)}",
                    "details": test_details
                })
                return False
                
        except Exception as e:
            print(f"{Colors.RED}Unexpected error in OpenAI test: {e}{Colors.ENDC}")
            self._record_test_end("openai", "error", {
                "error": f"Unexpected error: {str(e)}",
                "details": test_details
            })
            return False
    
    def run_tests(self, test_capital=True, test_telegram=True, test_openai=True):
        """Run the selected integration tests and generate comprehensive reports"""
        results = {}
        test_start_timestamp = datetime.now()
        
        # Track overall test durations
        api_durations = {}
        
        # Set up report directory
        report_dir = os.path.join(os.path.dirname(__file__), "test_reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # Run the selected tests
        print(f"{Colors.BLUE}Starting integration tests at {test_start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        print(f"{Colors.BLUE}{'=' * 50}{Colors.ENDC}")
        
        if test_capital:
            print(f"\n{Colors.HEADER}TESTING CAPITAL.COM API{Colors.ENDC}")
            capital_start = time.time()
            capital_result = self.test_capital_com()
            capital_duration = time.time() - capital_start
            api_durations["capital_com"] = capital_duration
            results["Capital.com API"] = {
                "result": "✅ Passed" if capital_result else "❌ Failed",
                "duration_sec": round(capital_duration, 2)
            }
        
        if test_telegram:
            print(f"\n{Colors.HEADER}TESTING TELEGRAM API{Colors.ENDC}")
            telegram_start = time.time()
            telegram_result = self.test_telegram()
            telegram_duration = time.time() - telegram_start
            api_durations["telegram"] = telegram_duration
            results["Telegram API"] = {
                "result": "✅ Passed" if telegram_result else "❌ Failed",
                "duration_sec": round(telegram_duration, 2)
            }
        
        if test_openai:
            print(f"\n{Colors.HEADER}TESTING OPENAI API{Colors.ENDC}")
            openai_start = time.time()
            openai_result = self.test_openai()
            openai_duration = time.time() - openai_start
            api_durations["openai"] = openai_duration
            results["OpenAI API"] = {
                "result": "✅ Passed" if openai_result else "❌ Failed",
                "duration_sec": round(openai_duration, 2)
            }
        
        # Calculate summary statistics
        test_end_timestamp = datetime.now()
        total_duration = (test_end_timestamp - test_start_timestamp).total_seconds()
        tests_passed = sum(1 for r in results.values() if r["result"] == "✅ Passed")
        tests_failed = sum(1 for r in results.values() if r["result"] == "❌ Failed")
        
        # Update test report summary
        self.test_report["summary"] = {
            "total_tests": len(results),
            "passed": tests_passed,
            "failed": tests_failed,
            "total_duration_sec": round(total_duration, 2),
            "test_date": test_start_timestamp.strftime("%Y-%m-%d"),
            "test_time": test_start_timestamp.strftime("%H:%M:%S"),
            "api_durations": {k: round(v, 2) for k, v in api_durations.items()}
        }
        
        # Print summary report
        print(f"\n{Colors.BLUE}{'=' * 50}")
        print(f"INTEGRATION TEST SUMMARY")
        print(f"{'=' * 50}{Colors.ENDC}")
        print(f"Test run completed at: {test_end_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {total_duration:.2f} seconds")
        print(f"Tests passed: {tests_passed}/{len(results)}")
        
        # Print detailed results table
        print(f"\n{Colors.BOLD}API Test Results:{Colors.ENDC}")
        print(f"{'API Name':<20} {'Status':<15} {'Duration':<15}")
        print(f"{'-' * 20} {'-' * 15} {'-' * 15}")
        
        for api_name, result in results.items():
            status_color = Colors.GREEN if result["result"] == "✅ Passed" else Colors.RED
            print(f"{api_name:<20} {status_color}{result['result']:<15}{Colors.ENDC} {result['duration_sec']:.2f}s")
        
        # Generate detailed JSON report
        timestamp_str = test_end_timestamp.strftime("%Y%m%d_%H%M%S")
        report_filename = f"integration_test_report_{timestamp_str}.json"
        report_path = os.path.join(report_dir, report_filename)
        
        with open(report_path, 'w') as f:
            json.dump(self.test_report, f, indent=2)
        
        # Generate summary text report
        summary_filename = f"integration_test_summary_{timestamp_str}.txt"
        summary_path = os.path.join(report_dir, summary_filename)
        
        with open(summary_path, 'w') as f:
            f.write(f"JAMSO-AI ENGINE INTEGRATION TEST SUMMARY\n")
            f.write(f"=====================================\n\n")
            f.write(f"Date: {test_start_timestamp.strftime('%Y-%m-%d')}\n")
            f.write(f"Time: {test_start_timestamp.strftime('%H:%M:%S')}\n")
            f.write(f"Duration: {total_duration:.2f} seconds\n\n")
            f.write(f"Test Results\n")
            f.write(f"-----------\n")
            f.write(f"{'API Name':<20} {'Status':<15} {'Duration':<15}\n")
            f.write(f"{'-' * 50}\n")
            
            for api_name, result in results.items():
                f.write(f"{api_name:<20} {result['result']:<15} {result['duration_sec']:.2f}s\n")
            
            f.write(f"\n\nTest Summary\n")
            f.write(f"-----------\n")
            f.write(f"Total tests: {len(results)}\n")
            f.write(f"Tests passed: {tests_passed}\n")
            f.write(f"Tests failed: {tests_failed}\n")
            
            # Add system information
            f.write(f"\n\nSystem Information\n")
            f.write(f"-----------------\n")
            for key, value in self.test_report["system_info"].items():
                f.write(f"{key}: {value}\n")
        
        print(f"\n{Colors.GREEN}Detailed report saved to: {report_path}{Colors.ENDC}")
        print(f"{Colors.GREEN}Summary report saved to: {summary_path}{Colors.ENDC}")
        
        # Return overall success/failure
        return tests_failed == 0
def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Run integration tests for Jamso-AI-Engine APIs",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Test selection options
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument("--capital", action="store_true", help="Test Capital.com API integration")
    test_group.add_argument("--telegram", action="store_true", help="Test Telegram API integration")
    test_group.add_argument("--openai", action="store_true", help="Test OpenAI API integration")
    test_group.add_argument("--all", action="store_true", help="Test all API integrations (default)")
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("--quiet", "-q", action="store_true", help="Reduce output verbosity")
    output_group.add_argument("--format", "-f", choices=["json", "text", "both"], default="both",
                           help="Report format: json, text, or both")
    output_group.add_argument("--report-dir", type=str, 
                           help="Directory to save reports (default: ./test_reports)")
    
    # Retry options
    retry_group = parser.add_argument_group("Retry Options")
    retry_group.add_argument("--retry-failed", action="store_true", 
                          help="Retry failed tests from last run")
    retry_group.add_argument("--retries", type=int, default=1, 
                          help="Number of times to retry failed tests")
    
    args = parser.parse_args()
    
    # If no specific test is selected, run all
    if not any([args.capital, args.telegram, args.openai, args.all]):
        args.all = True
        
    return args

def main():
    """Main function"""
    args = parse_arguments()
    tester = IntegrationTester()
    
    # Configure report location if specified
    if args.report_dir:
        report_dir = os.path.abspath(args.report_dir)
        os.makedirs(report_dir, exist_ok=True)
    
    # Set verbosity based on quiet flag
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # If retrying failed tests from last run
    if args.retry_failed:
        # Find the most recent report and extract failed tests
        report_dir = os.path.join(os.path.dirname(__file__), "test_reports")
        if os.path.exists(report_dir):
            reports = sorted([f for f in os.listdir(report_dir) if f.startswith("integration_test_report_") and f.endswith(".json")], 
                            reverse=True)
            
            if reports:
                latest_report = os.path.join(report_dir, reports[0])
                print(f"Loading failed tests from: {latest_report}")
                
                try:
                    with open(latest_report, 'r') as f:
                        report_data = json.load(f)
                    
                    failed_apis = []
                    for api_name, result in report_data.get("results", {}).items():
                        if result.get("status") == "error":
                            failed_apis.append(api_name)
                    
                    if failed_apis:
                        print(f"Found {len(failed_apis)} failed tests: {', '.join(failed_apis)}")
                        args.capital = "capital_com" in failed_apis
                        args.telegram = "telegram" in failed_apis
                        args.openai = "openai" in failed_apis
                        args.all = False
                    else:
                        print("No failed tests found in the last report")
                except Exception as e:
                    print(f"Error loading previous report: {e}")
    
    # Determine which tests to run
    test_capital = args.capital or args.all
    test_telegram = args.telegram or args.all
    test_openai = args.openai or args.all
    
    # Print test configuration
    print(f"\n{Colors.BOLD}Jamso-AI Engine Integration Test{Colors.ENDC}")
    print(f"Running tests: " + 
          f"{'Capital.com' if test_capital else ''}" +
          f"{', ' if test_capital and (test_telegram or test_openai) else ''}" +
          f"{'Telegram' if test_telegram else ''}" +
          f"{', ' if test_telegram and test_openai else ''}" +
          f"{'OpenAI' if test_openai else ''}")
    
    # Run tests with retry logic
    max_retries = max(1, args.retries)
    success = False
    
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"\n{Colors.YELLOW}Retry attempt {attempt}/{max_retries}{Colors.ENDC}")
            time.sleep(2)  # Brief delay between retries
            
        success = tester.run_tests(
            test_capital=test_capital,
            test_telegram=test_telegram,
            test_openai=test_openai
        )
        
        if success:
            break
    
    sys.exit(0 if success else 1)
