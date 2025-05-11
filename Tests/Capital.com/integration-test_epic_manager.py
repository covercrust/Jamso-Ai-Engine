import unittest
import sqlite3
import os
import sys
from unittest.mock import patch, MagicMock
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.insert(0, PROJECT_ROOT)

# This is a module-level global that will be used by the epic_manager module
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'src/Database/Capital.com/market_data.db')

from src.Exchanges.capital_com_api.epic_manager import (
    get_db,
    create_table,
    save_market_data,
    fetch_and_save_market_details
)

class TestEpicManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database and create fresh table."""
        cls.db_dir = Path('/Users/jamesphilippi/Desktop/Jamso_AI_Bot/Database/capital_com')
        cls.db_dir.mkdir(parents=True, exist_ok=True)
        cls.test_db = cls.db_dir / 'test_market_data.db'
        global DATABASE_PATH
        DATABASE_PATH = str(cls.test_db)
        create_table()
        logger.info(f"Test database created at {cls.test_db}")

    def setUp(self):
        """Set up test case."""
        self.test_epic = "BTCUSD"
        self.test_market_data = {
            "epic": self.test_epic,
            "name": "Bitcoin",
            "instrument_type": "CRYPTOCURRENCIES",
            "lot_size": 1.0,
            "currency": "USD",
            "leverage": 10,
            "margin_rate": 0.1,
            "timestamp": 1604671398,
            "bid": 44500.0,
            "ask": 44550.0,
            "last": 44525.0,
            "high": 45000.0,
            "low": 44000.0,
            "volume": 1000.0
        }

    def test_save_market_data(self):
        """Test saving market data to database."""
        result = save_market_data(**self.test_market_data)
        self.assertTrue(result)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM market_data WHERE epic=?", (self.test_epic,))
        saved_data = cursor.fetchone()
        self.assertIsNotNone(saved_data)
        conn.close()

    @patch('src.Exchanges.capital_com_api.epic_manager.requests.get')
    def test_fetch_market_details(self, mock_get):
        """Test fetching market details from API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.test_market_data
        mock_get.return_value = mock_response
        
        result = fetch_and_save_market_details(self.test_epic)
        self.assertTrue(result)
        mock_get.assert_called_once()

    def test_error_handling(self):
        """Test error handling for invalid data."""
        invalid_data = {"epic": self.test_epic, "name": "Test"}
        with self.assertRaises(ValueError):
            save_market_data(**invalid_data)

    def test_duplicate_entry(self):
        """Test handling duplicate market data entries."""
        save_market_data(**self.test_market_data)
        modified_data = self.test_market_data.copy()
        modified_data["bid"] = 45000.0
        result = save_market_data(**modified_data)
        self.assertTrue(result)

    @classmethod
    def tearDownClass(cls):
        """Clean up the test database."""
        try:
            os.remove(cls.test_db)
            logger.info("Test database cleaned up")
        except FileNotFoundError:
            logger.warning("Test database not found during cleanup")

if __name__ == '__main__':
    unittest.main()