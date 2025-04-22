#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fix_database_types.log")
    ]
)
logger = logging.getLogger("fix_database_types")

# Import the change_column_type function
try:
    from telegram_db_manager import change_column_type
except ImportError:
    logger.error("Failed to import change_column_type function")
    sys.exit(1)

def fix_database_types():
    """Fix the data types in the user_db.db database."""
    logger.info("Starting database type fix process")
    
    # Fix USER_ID column type to INTEGER
    result = change_column_type("users", "USER_ID", "INTEGER")
    logger.info(f"USER_ID type change result: {result['status']} - {result['message']}")
    
    # Fix PEER_ID column type to INTEGER
    result = change_column_type("users", "PEER_ID", "INTEGER")
    logger.info(f"PEER_ID type change result: {result['status']} - {result['message']}")
    
    logger.info("Database type fix process completed")

if __name__ == "__main__":
    fix_database_types()