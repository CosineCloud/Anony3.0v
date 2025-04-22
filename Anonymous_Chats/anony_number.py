#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import sqlite3
import re
import telebot

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

def get_user_info(user_id):
    """Get user information from the database."""
    conn, cursor = connect_database()
    if not conn or not cursor:
        return None
    
    try:
        # Ensure user_id is treated as an integer
        user_id = int(user_id)
        cursor.execute("SELECT USER_ID, PEER_ID, STATUS, ANONY_NAME FROM users WHERE USER_ID = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            user_info = {
                'user_id': user_data[0],
                'peer_id': user_data[1],
                'status': user_data[2],
                'anony_id': user_data[3]  # We're using ANONY_NAME but keeping the key as anony_id for compatibility
            }
            return user_info
        else:
            logger.warning(f"User {user_id} not found in database")
            return None
    except (sqlite3.Error, ValueError) as e:
        logger.error(f"Database error when getting user info: {e}")
        return None
    finally:
        if conn:
            conn.close()

def show_anony_number(bot, message):
    """Show the user's anonymous number and offer to share it if connected."""
    try:
        # Ensure we're using the correct user ID
        if not hasattr(message, 'from_user') or not message.from_user:
            logger.error("Message object doesn't have from_user attribute")
            bot.send_message(message.chat.id, "Sorry, there was an error processing your request. Please try again later.")
            return
        
        # Make sure we're not using the bot's ID
        user_id = int(message.from_user.id)
        logger.info(f"Processing anony_number request for user_id: {user_id}")
        
        # Check if this is the bot's ID (which would be an error)
        if str(user_id).startswith("5768243722"):
            logger.error(f"Attempted to use bot token as user_id: {user_id}")
            bot.send_message(message.chat.id, "Sorry, there was an error processing your request. Please try again later.")
            return
        
        user_info = get_user_info(user_id)
        
        if not user_info:
            logger.warning(f"User {user_id} not found in database when showing anony number")
            bot.send_message(message.chat.id, "Sorry, your user information could not be found. Please try again later.")
            return
        
        anony_name = user_info.get('anony_id')  # We're using the key 'anony_id' but it contains ANONY_NAME
        status = user_info.get('status')
        
        if not anony_name:
            logger.warning(f"User {user_id} has no anony_name in database")
            bot.send_message(message.chat.id, "Sorry, your Anonymous Name could not be found. Please try again later.")
            return
    except Exception as e:
        logger.error(f"Error in show_anony_number: {e}")
        bot.send_message(message.chat.id, "Sorry, there was an error processing your request. Please try again later.")
        return
    
    try:
        # Format the anonymous number
        anony_number = f"/AN{anony_name}"
        
        # Send the anonymous number to the user
        bot.send_message(message.chat.id, f"ℹ️ Your Anony Number is: {anony_number}")
        
        
        # If user is in RANDOM or PRIVATE status, offer to share the number
        # For other statuses, don't ask - just show the number
        if status in ['RANDOM', 'PRIVATE']:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(
                telebot.types.InlineKeyboardButton("Yes", callback_data=f"share_yes_{anony_name}"),
                telebot.types.InlineKeyboardButton("No", callback_data="share_no")
            )
            
            bot.send_message(
                message.chat.id,
                "Do you want to share your anonymous number with your connected partner?",
                reply_markup=markup
            )
        
        logger.info(f"Successfully showed anony number {anony_number} to user {user_id}")
    except Exception as e:
        logger.error(f"Error sending anony number to user: {e}")
        bot.send_message(message.chat.id, "Sorry, there was an error processing your request. Please try again later.")

def handle_share_decision(bot, call):
    """Handle the user's decision to share their anonymous number."""
    # If user chose not to share, delete the message
    if call.data == "share_no":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return
    
    # If user chose to share, get the anonymous name from the callback data
    # Format: share_yes_[anony_name]
    anony_name = call.data.split('_')[2]
    user_id = int(call.from_user.id)
    
    # Get user information to find the peer
    user_info = get_user_info(user_id)
    if not user_info or not user_info.get('peer_id'):
        bot.edit_message_text(
            "Sorry, your partner information could not be found. Please try again later.",
            call.message.chat.id,
            call.message.message_id
        )
        return
    
    peer_id = user_info.get('peer_id')
    anony_number = f"/AN{anony_name}"
    
    # Update the message to show that the request has been sent
    bot.edit_message_text(
        "Your anonymous number has been sent to your partner. Waiting for their response...",
        call.message.chat.id,
        call.message.message_id
    )
    
    # Send request to the peer
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("View", callback_data=f"save_yes_{user_id}_{anony_name}"),
        telebot.types.InlineKeyboardButton("Dismiss", callback_data="save_no")
    )
    
    bot.send_message(
        peer_id,
        "Your partner wants to send you their Anonymous Number to connect with them any time. Do you want to view it?",
        reply_markup=markup
    )

def handle_save_decision(bot, call):
    """Handle the peer's decision to view the anonymous number."""
    # If peer chose not to view, delete the message
    if call.data == "save_no":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        # We don't have the original user ID here, so we need to extract it from the message
        # This is a limitation of the current implementation
        # In a real implementation, we would store this in a database or cache
        return
    
    # If peer chose to view, get the user_id and anony_name from the callback data
    # Format: save_yes_[user_id]_[anony_name]
    data_parts = call.data.split('_')
    original_user_id = int(data_parts[2])
    anony_name = data_parts[3]
    peer_id = int(call.from_user.id)
    
    # Create the anonymous number
    anony_number = f"/AN{anony_name}"
    
    # Disabled file saving functionality
    try:
        # Instead of saving to a file, just show the number to the user
        logger.info(f"File saving disabled - User {peer_id} would have saved anony number {anony_number}")
        
        # Update the message to show the anonymous number (without saying it was saved to a file)
        bot.edit_message_text(
            f"Your partner's anonymous number is: {anony_number}\n\nPlease make a note of it if you want to contact them later.",
            call.message.chat.id,
            call.message.message_id
        )
        
        # Notify the original user that their partner received the number
        bot.send_message(
            original_user_id,
            "Your partner has received your anonymous number."
        )
    except Exception as e:
        logger.error(f"Error displaying anonymous number: {e}")
        bot.edit_message_text(
            "Sorry, there was an error displaying the anonymous number. Please try again later.",
            call.message.chat.id,
            call.message.message_id
        )
        
        # Notify the original user about the error
        bot.send_message(
            original_user_id,
            "There was an error when your partner tried to view your anonymous number."
        )

def handle_an_command(bot, message):
    """Handle the /AN command to connect with a user by their anonymous number."""
    message_text = message.text
    user_id = int(message.from_user.id)
    
    # Extract the ANONY_NAME from the message
    match = re.match(r'/AN(\w+)', message_text)
    if not match:
        bot.send_message(message.chat.id, "Invalid Anonymous Number format. Please use /AN followed by the number.")
        return
    
    anony_name = match.group(1)
    logger.info(f"User {user_id} is trying to connect with Anonymous Number: /AN{anony_name}")
    
    # Check if the ANONY_NAME exists in the database
    conn, cursor = connect_database()
    if not conn or not cursor:
        bot.send_message(message.chat.id, "Sorry, there was a database error. Please try again later.")
        return
    
    try:
        # Find the user with this ANONY_NAME
        cursor.execute("SELECT USER_ID, STATUS FROM users WHERE ANONY_NAME = ?", (anony_name,))
        target_user = cursor.fetchone()
        
        if not target_user:
            bot.send_message(message.chat.id, "This Anonymous Number does not exist or is no longer valid.")
            conn.close()
            return
        
        target_user_id, target_status = target_user
        
        # Check if the user is trying to connect to themselves
        if int(target_user_id) == user_id:
            bot.send_message(message.chat.id, "You cannot connect to yourself.")
            conn.close()
            return
        
        # We'll allow connection requests regardless of the target user's status
        # Instead of blocking, we'll just inform the user that the target might be busy
        if target_status not in ['IDLE', 'PRIVATE']:
            logger.info(f"User {user_id} is trying to connect with user {target_user_id} who has status {target_status}")
            # Continue with the connection request instead of returning
        
        # Get the current user's status
        cursor.execute("SELECT STATUS FROM users WHERE USER_ID = ?", (user_id,))
        user_status = cursor.fetchone()
        
        if not user_status:
            bot.send_message(message.chat.id, "Your user profile could not be found. Please try again later.")
            conn.close()
            return
        
        user_status = user_status[0]
        
        # Allow the current user to send connection requests regardless of their status
        if user_status not in ['IDLE', 'PRIVATE']:
            logger.info(f"User {user_id} with status {user_status} is trying to send a connection request")
            # Continue with the connection request instead of returning
        
        # Send connection request to the target user
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("Accept", callback_data=f"accept_an_{user_id}"),
            telebot.types.InlineKeyboardButton("Decline", callback_data=f"decline_an_{user_id}")
        )
        
        # Get the requester's ANONY_NAME to include in the message
        cursor.execute("SELECT ANONY_NAME FROM users WHERE USER_ID = ?", (user_id,))
        requester_anony_name_data = cursor.fetchone()
        requester_anony_name = requester_anony_name_data[0] if requester_anony_name_data else "Anonymous"
        
        # Send a more informative message that mentions they can accept regardless of current status
        bot.send_message(
            target_user_id,
            f"Someone with Anony Number /AN{requester_anony_name} wants to connect with you. " +
            f"You can accept this connection even if you're currently in another chat. " +
            f"If you accept, your current connection will be closed. Do you want to accept?",
            reply_markup=markup
        )
        
        # Customize the message based on the target user's status
        if target_status in ['IDLE', 'PRIVATE']:
            bot.send_message(message.chat.id, "Your connection request has been sent. Please wait for a response.")
        else:
            bot.send_message(
                message.chat.id, 
                "Your connection request has been sent. The user is currently in another chat or activity, " +
                "but they can still choose to accept your connection. Please wait for a response."
            )
        
        conn.close()
        
    except sqlite3.Error as e:
        logger.error(f"Database error in handle_an_command: {e}")
        bot.send_message(message.chat.id, "Sorry, there was a database error. Please try again later.")
        if conn:
            conn.close()

def handle_an_connection_response(bot, call):
    """Handle the response to an Anonymous Number connection request."""
    # Extract data from callback
    data = call.data.split('_')
    action = data[0]  # 'accept' or 'decline'
    requester_id = int(data[2])
    responder_id = int(call.from_user.id)
    
    if action == "decline":
        bot.edit_message_text(
            "You declined the connection request.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(requester_id, "Your connection request was declined.")
        return
    
    # If accepted, connect the users
    conn, cursor = connect_database()
    if not conn or not cursor:
        bot.edit_message_text(
            "Sorry, there was a database error. Please try again later.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(requester_id, "There was an error processing your connection request.")
        return
    
    try:
        # Check if the responder is already connected to someone
        cursor.execute("SELECT STATUS, PEER_ID FROM users WHERE USER_ID = ?", (responder_id,))
        responder_data = cursor.fetchone()
        
        # Check if the requester is already connected to someone
        cursor.execute("SELECT STATUS, PEER_ID FROM users WHERE USER_ID = ?", (requester_id,))
        requester_data = cursor.fetchone()
        
        # If responder is already connected to someone, notify their current peer
        if responder_data and responder_data[0] in ['CONNECTED', 'PRIVATE', 'RANDOM'] and responder_data[1]:
            current_peer_id = responder_data[1]
            try:
                # Notify the current peer that they've been disconnected
                bot.send_message(
                    current_peer_id,
                    "Your peer disconnected with you. Your status is closed now."
                )
                # Update the current peer's status
                cursor.execute("UPDATE users SET STATUS = 'CLOSED', PEER_ID = NULL WHERE USER_ID = ?", (current_peer_id,))
                logger.info(f"Disconnected user {current_peer_id} from user {responder_id}")
            except Exception as e:
                logger.error(f"Error notifying previous peer {current_peer_id}: {e}")
        
        # If requester is already connected to someone, notify their current peer
        if requester_data and requester_data[0] in ['CONNECTED', 'PRIVATE', 'RANDOM'] and requester_data[1]:
            current_peer_id = requester_data[1]
            try:
                # Notify the current peer that they've been disconnected
                bot.send_message(
                    current_peer_id,
                    "Your peer disconnected with you. Your status is closed now."
                )
                # Update the current peer's status
                cursor.execute("UPDATE users SET STATUS = 'CLOSED', PEER_ID = NULL WHERE USER_ID = ?", (current_peer_id,))
                logger.info(f"Disconnected user {current_peer_id} from user {requester_id}")
            except Exception as e:
                logger.error(f"Error notifying previous peer {current_peer_id}: {e}")
        
        # Update both users' status and set them as peers
        cursor.execute("UPDATE users SET STATUS = 'CONNECTED', PEER_ID = ? WHERE USER_ID = ?", 
                      (responder_id, requester_id))
        cursor.execute("UPDATE users SET STATUS = 'CONNECTED', PEER_ID = ? WHERE USER_ID = ?", 
                      (requester_id, responder_id))
        conn.commit()
        
        # Notify both users
        bot.edit_message_text(
            "You are now connected! You can start chatting anonymously.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(
            requester_id, 
            "Your connection request was accepted! You are now connected and can start chatting anonymously."
        )
        
    except sqlite3.Error as e:
        logger.error(f"Database error in handle_an_connection_response: {e}")
        bot.edit_message_text(
            "Sorry, there was a database error. Please try again later.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(requester_id, "There was an error processing your connection request.")
    finally:
        if conn:
            conn.close()

# Function to be called from telegram_bot.py
def handle_anony_number_command(bot, message):
    """Handler for the Anony Number button in the main menu."""
    # Make sure we're using the correct user ID from the message
    if hasattr(message, 'from_user') and message.from_user:
        return show_anony_number(bot, message)
    else:
        # If message doesn't have from_user, it might be a callback_query
        # In this case, we need to create a mock message with the correct user ID
        logger.warning("Message object doesn't have from_user attribute, using chat.id instead")
        # Use a safer approach by getting the user ID from the chat
        if hasattr(message, 'chat') and message.chat:
            # Create a mock message with the correct user ID
            class MockMessage:
                def __init__(self, chat_id):
                    self.chat = type('obj', (object,), {'id': chat_id})
                    self.from_user = type('obj', (object,), {'id': chat_id})
            
            return show_anony_number(bot, MockMessage(message.chat.id))
        else:
            logger.error("Cannot determine user ID from message object")
            return None

if __name__ == "__main__":
    print("This module is designed to be imported, not run directly.")