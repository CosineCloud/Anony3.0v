#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import time
import logging
import sys
import os
import traceback

# Configure logging with more detailed information
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("otp_clean.log")  # Use absolute path
    ]
)
logger = logging.getLogger("otp_clean")

# Database path
USER_DB_PATH = 'user_db.db'

def connect_database():
    """Connect to the user database."""
    try:
        # Check if database file exists
        if not os.path.exists(USER_DB_PATH):
            logger.error(f"Database file does not exist: {USER_DB_PATH}")
            return None, None
            
        # Log file permissions
        try:
            file_stats = os.stat(USER_DB_PATH)
            logger.info(f"Database file permissions: {oct(file_stats.st_mode)}")
            logger.info(f"Database file size: {file_stats.st_size} bytes")
        except Exception as e:
            logger.error(f"Error checking database file: {e}")
        
        # Connect to database with timeout
        conn = sqlite3.connect(USER_DB_PATH, timeout=30)
        cursor = conn.cursor()
        
        # Verify connection
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()
        logger.info(f"Connected to SQLite version: {version[0]}")
        
        return conn, cursor
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        logger.error(traceback.format_exc())
        return None, None

def verify_user_exists(cursor, user_id):
    """Verify that the user exists in the database."""
    try:
        cursor.execute("SELECT USER_ID, OTP, OTP_EXP FROM users WHERE USER_ID = ?", (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            logger.info(f"User {user_id} found in database. Current OTP: {user_data[1]}, OTP_EXP: {user_data[2]}")
            return True
        else:
            logger.error(f"User {user_id} not found in database")
            return False
    except sqlite3.Error as e:
        logger.error(f"Error verifying user: {e}")
        return False

def clean_otp(user_id):
    """
    Clean up OTP and OTP_EXP for a specific user after waiting 10 seconds,
    but only if the user's status is not one of the specified statuses.
    
    Args:
        user_id: The Telegram user ID to clean up
    """
    logger.info(f"OTP cleanup started for user {user_id}")
    logger.info(f"Will check user status after 10 seconds")
    
    # Wait for 10 seconds (light wait)
    time.sleep(10)
    
    logger.info(f"10 seconds passed, now checking user status for {user_id}")
    
    # Connect to database
    conn, cursor = connect_database()
    if not conn or not cursor:
        logger.error(f"Failed to connect to database for OTP cleanup for user {user_id}")
        return
    
    try:
        # First verify the user exists and check their status
        cursor.execute("SELECT USER_ID, STATUS, OTP, OTP_EXP FROM users WHERE USER_ID = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.error(f"User {user_id} not found in database")
            conn.close()
            return
        
        # Extract user status
        user_status = user_data[1]
        logger.info(f"User {user_id} has status: {user_status}")
        
        # Only clean OTP if status is not one of the specified statuses
        if user_status in ["RANDOM", "PRIVATE", "CONNECTED", "CLOSED", "AI"]:
            logger.info(f"User {user_id} has status {user_status}, keeping OTP valid")
            conn.close()
            return
        
        # If we get here, the status is not one of the specified ones, so clean up OTP
        logger.info(f"User {user_id} has status {user_status}, cleaning up OTP")
        
        # Clear OTP and OTP_EXP fields using empty strings instead of NULL
        cursor.execute("""
        UPDATE users 
        SET OTP = '', OTP_EXP = '' 
        WHERE USER_ID = ?
        """, (user_id,))
        
        # Check if any rows were affected
        rows_affected = cursor.rowcount
        logger.info(f"Update affected {rows_affected} rows")
        
        conn.commit()
        
        # Verify the update was successful
        cursor.execute("SELECT OTP, OTP_EXP FROM users WHERE USER_ID = ?", (user_id,))
        updated_data = cursor.fetchone()
        if updated_data:
            logger.info(f"After update - OTP: '{updated_data[0]}', OTP_EXP: '{updated_data[1]}'")
        
        logger.info(f"OTP and OTP_EXP cleared for user {user_id}")
        conn.close()
    except Exception as e:
        logger.error(f"Error during OTP cleanup for user {user_id}: {e}")
        logger.error(traceback.format_exc())
        if conn:
            conn.close()

if __name__ == "__main__":
    # Log startup information
    logger.info(f"OTP cleanup script started with arguments: {sys.argv}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Check if user_id was provided as command line argument
    if len(sys.argv) != 2:
        logger.error("Usage: python otp_clean.py <user_id>")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        logger.info(f"Starting OTP cleanup for user {user_id}")
        clean_otp(user_id)
        logger.info(f"OTP cleanup completed for user {user_id}")
    except ValueError:
        logger.error(f"Invalid user_id: {sys.argv[1]}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)