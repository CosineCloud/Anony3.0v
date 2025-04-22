#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import sqlite3
import random_connection

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

def get_user_status(user_id):
    """Get the current status of a user."""
    conn, cursor = connect_database()
    if not conn or not cursor:
        return None
    
    try:
        cursor.execute("SELECT STATUS FROM users WHERE USER_ID = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error in get_user_status: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_user_status(user_id, new_status):
    """Update the status of a user."""
    conn, cursor = connect_database()
    if not conn or not cursor:
        return False
    
    try:
        cursor.execute("UPDATE users SET STATUS = ? WHERE USER_ID = ?", (new_status, user_id))
        conn.commit()
        logger.info(f"Updated status of user {user_id} to {new_status}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error in update_user_status: {e}")
        return False
    finally:
        if conn:
            conn.close()

def handle_eject_button(bot, call):
    """
    Handle the ⏏️ (Eject) button click.
    
    Args:
        bot: The Telegram bot instance
        call: The callback query from the user
    """
    user_id = int(call.from_user.id)
    logger.info(f"Eject button clicked by user {user_id}")
    
    # Show service error message
    bot.answer_callback_query(
        call.id,
        text="Service Error",
        show_alert=True
    )

def handle_stop_button(bot, call):
    """
    Handle the ⏹️ (Stop) button click.
    
    Args:
        bot: The Telegram bot instance
        call: The callback query from the user
    """
    user_id = int(call.from_user.id)
    logger.info(f"Stop button clicked by user {user_id}")
    
    # Get current status
    current_status = get_user_status(user_id)
    
    # If status is already CLOSED, show message
    if current_status == "CLOSED":
        bot.answer_callback_query(
            call.id,
            text="⚠️\n\nYour connection is already closed!!",
            show_alert=True
        )
        return
    
    # Connect to database to get PEER_ID and check if user is a broadcaster
    conn, cursor = connect_database()
    if not conn or not cursor:
        bot.answer_callback_query(
            call.id,
            text="Error connecting to database. Please try again.",
            show_alert=True
        )
        return
    
    try:
        # Check if user is a broadcaster
        cursor.execute("SELECT PEER_ID, STATUS FROM users WHERE USER_ID = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            bot.answer_callback_query(
                call.id,
                text="User not found in database.",
                show_alert=True
            )
            return
        
        peer_id, status = user_data
        
        # Special handling for broadcasters
        if status == "BROADCASTER" and peer_id:
            # Get all listeners with the same PEER_ID
            cursor.execute(
                "SELECT USER_ID FROM users WHERE PEER_ID = ? AND STATUS = 'LISTENER'", 
                (peer_id,)
            )
            listeners = cursor.fetchall()
            
            # Notify all listeners that the broadcaster has stopped
            for listener in listeners:
                listener_id = listener[0]
                try:
                    bot.send_message(
                        listener_id,
                        "🚫 Your broadcaster has stopped broadcasting. Please join later or wait until broadcasting starts again!!",
                        disable_notification=False  # Make sure listeners get notified
                    )
                    logger.info(f"Notified listener {listener_id} that broadcaster {user_id} has stopped")
                except Exception as notify_error:
                    logger.error(f"Error notifying listener {listener_id}: {notify_error}")
        
        # Special handling for listeners
        elif status == "LISTENER" and peer_id:
            # Find the broadcaster for this PEER_ID
            cursor.execute(
                "SELECT USER_ID FROM users WHERE PEER_ID = ? AND STATUS = 'BROADCASTER'", 
                (peer_id,)
            )
            broadcaster_data = cursor.fetchone()
            
            if broadcaster_data:
                broadcaster_id = broadcaster_data[0]
                
                # Count remaining listeners after this one leaves
                cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE PEER_ID = ? AND STATUS = 'LISTENER' AND USER_ID != ?", 
                    (peer_id, user_id)
                )
                remaining_listeners = cursor.fetchone()[0]
                
                # Notify the broadcaster that a listener has left
                try:
                    bot.send_message(
                        broadcaster_id,
                        f"1 Listener has left your broadcast. You now have {remaining_listeners} listeners.",
                        disable_notification=False  # Make sure broadcaster gets notified
                    )
                    logger.info(f"Notified broadcaster {broadcaster_id} that listener {user_id} has left, remaining: {remaining_listeners}")
                except Exception as notify_error:
                    logger.error(f"Error notifying broadcaster {broadcaster_id}: {notify_error}")
    except sqlite3.Error as e:
        logger.error(f"Database error checking broadcaster/listener status: {e}")
    
    # Update status to CLOSED
    success = update_user_status(user_id, "CLOSED")
    
    if success:
        # Show success message
        bot.answer_callback_query(
            call.id,
            text="⚠️\n\nConnection Closed",
            show_alert=True
        )
        
        # Also send a message to the chat
        bot.send_message(
            call.message.chat.id,
            "⏹️ Your connection has been closed."
        )
        
        # If the user was connected to someone (not a broadcaster), notify the peer
        if conn and cursor:
            try:
                if status != "BROADCASTER" and peer_id:
                    # Update peer's status and notify them
                    cursor.execute("UPDATE users SET STATUS = 'CLOSED', PEER_ID = NULL WHERE USER_ID = ?", (peer_id,))
                    conn.commit()
                    
                    # Notify the peer
                    bot.send_message(
                        peer_id,
                        "⏹️ Your partner has ended the connection."
                    )
                
                # Clear the user's peer_id
                cursor.execute("UPDATE users SET PEER_ID = NULL WHERE USER_ID = ?", (user_id,))
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Database error in handle_stop_button: {e}")
            finally:
                if conn:
                    conn.close()
    else:
        # Show error message
        bot.answer_callback_query(
            call.id,
            text="Error closing connection. Please try again.",
            show_alert=True
        )

def handle_forward_button(bot, call):
    """
    Handle the ⏩️ (Forward) button click.
    
    Args:
        bot: The Telegram bot instance
        call: The callback query from the user
    """
    user_id = int(call.from_user.id)
    logger.info(f"Forward button clicked by user {user_id}")
    
    # Get current status
    current_status = get_user_status(user_id)
    
    # Check if status is RANDOM
    if current_status == "RANDOM":
        # Update status to OPEN
        success = update_user_status(user_id, "OPEN")
        
        if success:
            # Show success message
            bot.answer_callback_query(
                call.id,
                text="Status changed to OPEN",
                show_alert=True
            )
            
            # Also send a message to the chat
            bot.send_message(
                call.message.chat.id,
                "⏩️ Your status has been changed to OPEN"
            )
            return
        else:
            # Show error message
            bot.answer_callback_query(
                call.id,
                text="Error changing status. Please try again.",
                show_alert=True
            )
            return
    else:
        # For any other status, show error message
        bot.answer_callback_query(
            call.id,
            text="⚠️\n\nNot valid for current service",
            show_alert=True
        )

# Handler functions to be called from telegram_bot.py
def handle_eject_callback(bot, call):
    """Handler for the ⏏️ button callback."""
    # Show alert directly instead of just acknowledging the callback
    bot.answer_callback_query(
        call.id,
        text="❌\n\nService Error",
        show_alert=True
    )
    # No need to call handle_eject_button since it does the same thing

def handle_stop_callback(bot, call):
    """Handler for the ⏹️ button callback."""
    # Don't answer the callback query here, let handle_stop_button do it with the appropriate message
    handle_stop_button(bot, call)

def handle_forward_callback(bot, call):
    """Handler for the ⏩️ button callback."""
    # Don't answer the callback query here, let handle_forward_button do it with the appropriate message
    handle_forward_button(bot, call)

if __name__ == "__main__":
    print("This module is designed to be imported, not run directly.")