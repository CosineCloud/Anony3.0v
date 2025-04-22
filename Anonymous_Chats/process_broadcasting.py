#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process Broadcasting Module

This module contains functions for processing broadcasting channel IDs
and handling listener notifications.
"""

import logging
import sqlite3

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_broadcasting_channel_id(bot, message, user_id):
    """
    Process the broadcasting channel ID input by the listener.
    
    Args:
        bot: The Telegram bot instance
        message: The Telegram message object
        user_id: The user's Telegram ID
    """
    try:
        channel_id = message.text.strip()
        
        # Import the broadcasting module
        import create_broadcasting
        
        # Validate the channel ID
        if not create_broadcasting.validate_listener_channel_id(channel_id):
            bot.send_message(message.chat.id, "Invalid broadcasting channel ID. It must start with '/BCST'.")
            return
            
        # Convert to fixed 6-digit code
        fixed_code = create_broadcasting.convert_to_fixed_code(channel_id)
        
        if not fixed_code:
            bot.send_message(message.chat.id, "Error generating fixed code. Please try again.")
            return
        
        # Connect to the database
        conn = sqlite3.connect('user_db.db')
        cursor = conn.cursor()
        
        # Check if there's a broadcaster with this code
        broadcaster_exists = False
        broadcaster_id = None
        
        # Find broadcaster with this code
        cursor.execute(
            "SELECT USER_ID FROM users WHERE PEER_ID = ? AND STATUS = 'BROADCASTER'", 
            (fixed_code,)
        )
        broadcaster_data = cursor.fetchone()
        
        if broadcaster_data:
            broadcaster_exists = True
            broadcaster_id = broadcaster_data[0]
            logger.info(f"Found active broadcaster {broadcaster_id} for code {fixed_code}")
        else:
            logger.info(f"No active broadcaster found for code {fixed_code}")
        
        # Update user's PEER_ID and STATUS in the database
        cursor.execute(
            "UPDATE users SET PEER_ID = ?, STATUS = 'LISTENER' WHERE USER_ID = ?", 
            (fixed_code, user_id)
        )
        conn.commit()
        logger.info(f"Updated user {user_id} as LISTENER with PEER_ID {fixed_code}")
        
        # If broadcaster exists, count total listeners and notify the broadcaster
        if broadcaster_exists and broadcaster_id:
            # Count total listeners
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE PEER_ID = ? AND STATUS = 'LISTENER'", 
                (fixed_code,)
            )
            listener_count = cursor.fetchone()[0]
            
            # Notify the broadcaster
            try:
                bot.send_message(
                    broadcaster_id,
                    f"1 Listener joins you, total listeners are {listener_count}",
                    disable_notification=False  # Make sure broadcaster gets notified
                )
                logger.info(f"Notified broadcaster {broadcaster_id} about new listener, total: {listener_count}")
            except Exception as notify_error:
                logger.error(f"Error notifying broadcaster {broadcaster_id}: {notify_error}")
        
        # Close the database connection
        conn.close()
        
        # Prepare response based on whether broadcaster exists
        if broadcaster_exists:
            response = f"Successfully connected to broadcasting channel: {channel_id}\n\nYour broadcaster is 🎙️ live, may send messages anytime."
        else:
            response = f"Successfully connected to broadcasting channel: {channel_id}\n\nYour broadcaster is not 🚫 live."
        
        # Send the response
        bot.send_message(message.chat.id, response)
        
    except Exception as e:
        logger.error(f"Error processing broadcasting channel ID: {e}")
        bot.send_message(message.chat.id, "Error processing request. Please try again later.")