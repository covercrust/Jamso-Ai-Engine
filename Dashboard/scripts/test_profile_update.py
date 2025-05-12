#!/usr/bin/env python3
"""
Script to test updating a user's profile with first_name and last_name

Enhancements:
- Added detailed comments for better understanding.
- Improved logging configuration.
- Enhanced error handling.
"""

import os
import sys
import logging

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_PATH, 'Logs', 'profile_test.log'))
    ]
)
logger = logging.getLogger(__name__)

# Import the User model
from Dashboard.models.user import User

def test_profile_update():
    """
    Test updating a user's profile with first_name and last_name.

    Returns:
        bool: True if the update is successful, False otherwise.
    """
    try:
        logger.info("Starting profile update test.")
        
        # Find the admin user
        admin = User.find_by_username('admin')
        
        if not admin:
            logger.error("Admin user not found")
            return False
        
        # Log current profile info
        logger.info(f"Current profile - Username: {admin.username}, Email: {admin.email}")
        logger.info(f"Current profile - First Name: '{admin.first_name}', Last Name: '{admin.last_name}'")
        
        # Update first_name and last_name
        admin.first_name = "Admin"
        admin.last_name = "User"
        
        # Save changes
        if admin.save():
            logger.info("Profile updated successfully")
        else:
            logger.error("Failed to update profile")
            return False
        
        # Verify the update
        updated_admin = User.find_by_username('admin')
        logger.info(f"Updated profile - First Name: '{updated_admin.first_name}', Last Name: '{updated_admin.last_name}'")
        
        logger.info("Profile update test completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error during profile update test: {e}")
        return False

if __name__ == "__main__":
    success = test_profile_update()
    sys.exit(0 if success else 1)
