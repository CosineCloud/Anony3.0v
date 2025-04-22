#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import random
import logging
import os
import time
import subprocess
import datetime
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("private_connection.log")
    ]
)
logger = logging.getLogger("private_connection")

# Database path
USER_DB_PATH = 'user_db.db'

def connect_database():
    """Connect to the user database."""
    try:
        conn = sqlite3.connect(USER_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        return conn, cursor
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None, None

def generate_otp():
    """Generate a 4-digit OTP."""
    return str(random.randint(1000, 9999))

def generate_random_number(digits):
    """Generate a random number with specified number of digits."""
    min_val = 10 ** (digits - 1)
    max_val = (10 ** digits) - 1
    return str(random.randint(min_val, max_val))

def generate_connection_string(otp, user_id):
    """Generate a connection string using OTP and user ID."""
    six_digit = generate_random_number(6)
    five_digit = generate_random_number(5)
    return f"/92{six_digit}{otp}{user_id}{five_digit}"

def clean_otp_directly(user_id):
    """
    Clean up OTP and OTP_EXP directly in this process after waiting 10 seconds,
    but only if the user's status is not one of the specified statuses.
    
    Args:
        user_id: The Telegram user ID
    """
    def _clean_task():
        try:
            logger.info(f"Direct OTP cleanup scheduled for user {user_id} in 10 seconds")
            time.sleep(10)
            
            conn, cursor = connect_database()
            if not conn or not cursor:
                logger.error(f"Failed to connect to database for direct OTP cleanup for user {user_id}")
                return
            
            try:
                # First check the user's status
                cursor.execute("SELECT STATUS FROM users WHERE USER_ID = ?", (user_id,))
                status_data = cursor.fetchone()
                
                if not status_data:
                    logger.error(f"User {user_id} not found in database for direct OTP cleanup")
                    conn.close()
                    return
                
                user_status = status_data[0]
                logger.info(f"User {user_id} has status: {user_status}")
                
                # Only clean OTP if status is not one of the specified statuses
                if user_status in ["RANDOM", "PRIVATE", "CONNECTED", "CLOSED", "AI"]:
                    logger.info(f"User {user_id} has status {user_status}, keeping OTP valid")
                    conn.close()
                    return
                
                # If we get here, the status is not one of the specified ones, so clean up OTP
                logger.info(f"User {user_id} has status {user_status}, cleaning up OTP")
                
                # Clear OTP and OTP_EXP fields using empty strings
                cursor.execute("""
                UPDATE users 
                SET OTP = '', OTP_EXP = '' 
                WHERE USER_ID = ?
                """, (user_id,))
                
                rows_affected = cursor.rowcount
                conn.commit()
                
                logger.info(f"Direct OTP cleanup completed for user {user_id}, affected {rows_affected} rows")
                
                # Verify the update
                cursor.execute("SELECT OTP, OTP_EXP FROM users WHERE USER_ID = ?", (user_id,))
                data = cursor.fetchone()
                if data:
                    logger.info(f"After direct cleanup - OTP: '{data[0]}', OTP_EXP: '{data[1]}'")
                
                conn.close()
            except Exception as e:
                logger.error(f"Error in direct OTP cleanup for user {user_id}: {e}")
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Unexpected error in direct OTP cleanup thread for user {user_id}: {e}")
    
    # Start the cleanup in a separate thread
    import threading
    cleanup_thread = threading.Thread(target=_clean_task)
    cleanup_thread.daemon = True  # Make thread a daemon so it doesn't block program exit
    cleanup_thread.start()
    logger.info(f"Started direct OTP cleanup thread for user {user_id}")
    return cleanup_thread

def start_otp_cleanup_task(user_id):
    """
    Start a separate process to clean up OTP after 10 seconds.
    First tries to use the external script, falls back to direct method if that fails.
    
    Args:
        user_id: The Telegram user ID
    """
    try:
        # Get the absolute path to the script
        script_path = os.path.abspath("otp_clean.py")
        logger.info(f"Starting OTP cleanup task with script: {script_path}")
        
        # Start the otp_clean.py script as a separate process with full paths
        # Redirect output to a log file instead of discarding it
        log_file = open("otp_clean_subprocess.log", "a")
        
        process = subprocess.Popen(
            [sys.executable, script_path, str(user_id)],
            stdout=log_file,
            stderr=log_file,
            cwd="/Users/talha/Anonymous_Chats"  # Set working directory explicitly
        )
        
        # Log the process ID for debugging
        logger.info(f"Started OTP cleanup task for user {user_id} with PID {process.pid}")
        
        # Don't wait for the process to complete
        return process.pid
    except Exception as e:
        logger.error(f"Failed to start external OTP cleanup task for user {user_id}: {e}")
        logger.error(traceback.format_exc())
        
        # Fall back to direct method
        logger.info(f"Falling back to direct OTP cleanup for user {user_id}")
        return clean_otp_directly(user_id)

def check_user_status(user_id):
    """
    Check the user's current status in the database.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        A dictionary with status information and appropriate message
    """
    conn, cursor = connect_database()
    if not conn or not cursor:
        return {
            "status": "error",
            "message": "Database connection failed"
        }
    
    try:
        # Check if user exists and get OTP if available
        cursor.execute("SELECT PEER_ID, STATUS, OTP FROM users WHERE USER_ID = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return {
                "status": "error",
                "message": "User not found in database"
            }
        
        peer_id, status, existing_otp = user_data
        
        # Case 1: User is already in a private connection
        if peer_id and status == "PRIVATE":
            conn.close()
            return {
                "status": "already_connected",
                "message": "You are in private connection already!! , Please stop this before request for new one"
            }
        
        # Case 2: Check if user already has an OTP
        if existing_otp and existing_otp.strip():
            logger.info(f"User {user_id} already has OTP: {existing_otp}, reusing it")
            
            # Show popup message that current link is still valid
            conn.close()
            return {
                "status": "otp_exists",
                "message": "Current link still valid",
                "otp": existing_otp,
                "connection_string": generate_connection_string(existing_otp, user_id)
            }
        else:
            # Case 3: Generate new OTP and update user status
            otp = generate_otp()
            
            # Update user status - no expiration time as OTP will be kept until status changes
            cursor.execute("""
            UPDATE users 
            SET STATUS = 'PRIVATE', TIMER = 5760, OTP = ?
            WHERE USER_ID = ?
            """, (otp, user_id))
            
            conn.commit()
            
            logger.info(f"Generated new OTP {otp} for user {user_id}")
            
            # Generate connection string
            connection_string = generate_connection_string(otp, user_id)
            
            conn.close()
            return {
                "status": "success",
                "message": f"To connect to the peer as private connection pass below text to peer\n\n{connection_string}",
                "otp": otp,
                "connection_string": connection_string
            }
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        conn.close()
        return {
            "status": "error",
            "message": f"Database error: {e}"
        }

def handle_private_connection_request(user_id):
    """
    Handle a request for private connection.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        A message to send to the user
    """
    result = check_user_status(user_id)
    
    if result["status"] == "error":
        logger.error(f"Error handling private connection for user {user_id}: {result['message']}")
    elif result["status"] == "already_connected":
        logger.info(f"User {user_id} is already in a private connection")
    elif result["status"] == "otp_exists":
        logger.info(f"User {user_id} already has a valid OTP: {result['otp']}")
    elif result["status"] == "success":
        logger.info(f"Created private connection for user {user_id} with OTP {result['otp']}")
    
    return result

# For testing purposes
if __name__ == "__main__":
    test_user_id = 123456789  # Replace with a test user ID
    print(handle_private_connection_request(test_user_id))