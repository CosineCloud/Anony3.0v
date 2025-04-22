#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import sqlite3
import random

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'user_db.db'

def connect_database():
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        return conn, cursor
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None, None

def find_random_partner(user_id):
    """
    Find a random partner for the user who clicked the Random Connection button.
    
    Args:
        user_id (int): The ID of the user requesting a random connection
        
    Returns:
        dict: A dictionary containing the result of the operation
            {
                'status': 'success' or 'error',
                'message': A message describing the result,
                'partner_id': The ID of the partner (if found)
            }
    """
    conn, cursor = connect_database()
    if not conn or not cursor:
        return {
            'status': 'error',
            'message': 'Database connection error'
        }
    
    try:
        # First, check if the user is already in a connection
        cursor.execute("SELECT STATUS, PEER_ID FROM users WHERE USER_ID = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return {
                'status': 'error',
                'message': f'User {user_id} not found in database'
            }
        
        user_status, user_peer_id = user_data
        
        # If user is already in a connection, return an error
        if user_status not in ['OPEN', 'IDLE']:
            return {
                'status': 'error',
                'message': f'You are already in a connection (status: {user_status})'
            }
        
        # Find all users with STATUS="OPEN" except the current user
        cursor.execute(
            "SELECT USER_ID FROM users WHERE STATUS = 'OPEN' AND USER_ID != ?",
            (user_id,)
        )
        available_users = cursor.fetchall()
        
        if not available_users:
            # Update the user's status to OPEN if it's not already
            if user_status != 'OPEN':
                cursor.execute(
                    "UPDATE users SET STATUS = 'OPEN' WHERE USER_ID = ?",
                    (user_id,)
                )
                conn.commit()
                
            return {
                'status': 'waiting',
                'message': 'No users available for random connection. Your status has been set to OPEN and you will be connected when someone becomes available.'
            }
        
        # Select a random user from the available users
        partner_id = random.choice(available_users)[0]
        
        # Update both users' PEER_ID and STATUS
        # Update the user who clicked the button
        cursor.execute(
            "UPDATE users SET PEER_ID = ?, STATUS = 'RANDOM' WHERE USER_ID = ?",
            (partner_id, user_id)
        )
        
        # Update the randomly selected partner
        cursor.execute(
            "UPDATE users SET PEER_ID = ?, STATUS = 'RANDOM' WHERE USER_ID = ?",
            (user_id, partner_id)
        )
        
        conn.commit()
        logger.info(f"Random connection established between users {user_id} and {partner_id}")
        
        return {
            'status': 'success',
            'message': 'Random connection established',
            'partner_id': partner_id
        }
        
    except sqlite3.Error as e:
        logger.error(f"Database error in find_random_partner: {e}")
        return {
            'status': 'error',
            'message': f'Database error: {e}'
        }
    finally:
        if conn:
            conn.close()

def handle_random_connection(bot, message):
    """
    Handle the Random Connection button click.
    
    Args:
        bot: The Telegram bot instance
        message: The message object from the user
        
    Returns:
        bool: True if the operation was successful, False otherwise
    """
    try:
        user_id = int(message.from_user.id)
        logger.info(f"Random connection requested by user {user_id}")
        
        # Find a random partner
        result = find_random_partner(user_id)
        
        if result['status'] == 'success':
            # Connection established
            bot.send_message(
                message.chat.id,
                "🔀 You have been randomly connected with another user! Say hello! 👋\n\n"
                "Use /end to end this conversation when you're done."
            )
            
            # Also notify the partner
            partner_id = result['partner_id']
            bot.send_message(
                partner_id,
                "🔀 You have been randomly connected with another user! Say hello! 👋\n\n"
                "Use /end to end this conversation when you're done."
            )
            return True
            
        elif result['status'] == 'waiting':
            # No users available, user is now in waiting mode
            bot.send_message(
                message.chat.id,
                "🔍 Looking for a random connection...\n\n"
                "You'll be notified when someone connects with you. "
                "You can continue using other features while you wait."
            )
            return True
            
        else:
            # Error occurred
            bot.send_message(
                message.chat.id,
                f"❌ Sorry, {result['message']}\n"
                "Please Click ⏹️ and try again later."
            )
            return False
            
    except Exception as e:
        logger.error(f"Error in handle_random_connection: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Sorry, there was an error processing your request. Please try again later."
        )
        return False

if __name__ == "__main__":
    print("This module is designed to be imported, not run directly.")