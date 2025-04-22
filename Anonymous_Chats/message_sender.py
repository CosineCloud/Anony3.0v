#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3
import os
import traceback
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("message_sender.log")
    ]
)
logger = logging.getLogger("message_sender")

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

def get_peer_info(user_id):
    """
    Get peer information for a user.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        A dictionary with peer information or None if not found
    """
    conn, cursor = connect_database()
    if not conn or not cursor:
        logger.error(f"Failed to connect to database to get peer info for user {user_id}")
        return None
    
    try:
        # Log the database file details
        db_path = 'user_db.db'
        if os.path.exists(db_path):
            file_stats = os.stat(db_path)
            logger.info(f"Database file exists. Size: {file_stats.st_size} bytes, Modified: {datetime.datetime.fromtimestamp(file_stats.st_mtime)}")
        else:
            logger.error(f"Database file does not exist at {db_path}")
        
        # First, get the table schema to see what columns are available
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        logger.info(f"Available columns in users table: {column_names}")
        
        # First, dump all users for debugging
        cursor.execute("SELECT USER_ID, PEER_ID, STATUS FROM users")
        all_users = cursor.fetchall()
        logger.info(f"Total users in database: {len(all_users)}")
        for u in all_users:
            logger.info(f"DB User: USER_ID={u[0]} (type: {type(u[0]).__name__}), PEER_ID={u[1]} (type: {type(u[1]).__name__}), STATUS={u[2]}")
        
        # Try multiple query approaches to find the user
        
        # 1. Try exact match with original user_id
        logger.info(f"Trying to find user with USER_ID={user_id} (type: {type(user_id).__name__})")
        cursor.execute("SELECT USER_ID, STATUS, PEER_ID FROM users WHERE USER_ID = ?", (user_id,))
        user_data = cursor.fetchone()
        
        # 2. If not found and user_id is a string that looks like a number, try with integer
        if not user_data and isinstance(user_id, str) and user_id.isdigit():
            user_id_int = int(user_id)
            logger.info(f"Trying to find user with USER_ID={user_id_int} (converted to int)")
            cursor.execute("SELECT USER_ID, STATUS, PEER_ID FROM users WHERE USER_ID = ?", (user_id_int,))
            user_data = cursor.fetchone()
        
        # 3. If not found and user_id is an integer, try with string
        if not user_data and isinstance(user_id, int):
            user_id_str = str(user_id)
            logger.info(f"Trying to find user with USER_ID='{user_id_str}' (converted to string)")
            cursor.execute("SELECT USER_ID, STATUS, PEER_ID FROM users WHERE USER_ID = ?", (user_id_str,))
            user_data = cursor.fetchone()
        
        # 4. Last resort: try a LIKE query (less precise but might catch formatting differences)
        if not user_data:
            user_id_str = str(user_id)
            logger.info(f"Trying LIKE query for USER_ID with '{user_id_str}'")
            cursor.execute("SELECT USER_ID, STATUS, PEER_ID FROM users WHERE USER_ID LIKE ?", (user_id_str,))
            user_data = cursor.fetchone()
        
        if not user_data:
            logger.error(f"User {user_id} not found in database after multiple query attempts")
            conn.close()
            return None
        
        # Extract data from the result
        found_user_id, status, peer_id = user_data
        
        # Debug log to check values
        logger.info(f"Found user {found_user_id} (original query: {user_id}) - Status: {status}, Peer ID: {peer_id}")
        
        # Check if user is in a valid state for messaging
        if status not in ['CONNECTED', 'AI', 'PRIVATE', 'RANDOM', 'BROADCASTER', 'LISTENER']:
            logger.info(f"User {user_id} is not in a messaging state (status: {status})")
            conn.close()
            return None
        
        # Special handling for LISTENER status - silently ignore messages
        if status == 'LISTENER':
            logger.info(f"User {user_id} is a LISTENER, ignoring message")
            conn.close()
            return {
                'status': 'LISTENER',
                'peer_id': peer_id,
                'anony_name': None,
                'peer_anony_name': None
            }
        
        # Special handling for BROADCASTER status
        if status == 'BROADCASTER':
            # Find all listeners with the same PEER_ID
            cursor.execute(
                "SELECT USER_ID FROM users WHERE PEER_ID = ? AND STATUS = 'LISTENER' AND USER_ID != ?", 
                (peer_id, user_id)
            )
            listeners = cursor.fetchall()
            
            logger.info(f"Found {len(listeners)} listeners for broadcaster {user_id} with PEER_ID {peer_id}")
            
            conn.close()
            return {
                'status': 'BROADCASTER',
                'peer_id': peer_id,
                'anony_name': None,
                'listeners': [listener[0] for listener in listeners]
            }
        
        # Check if peer_id is empty or None
        if peer_id is None or (isinstance(peer_id, str) and not peer_id.strip()):
            logger.info(f"User {user_id} has no peer ID (peer_id is empty or None)")
            conn.close()
            return None
        
        # Try to find the peer in the database
        logger.info(f"Looking up peer with ID: {peer_id} (type: {type(peer_id).__name__})")
        
        # Try multiple approaches to find the peer
        cursor.execute("SELECT USER_ID FROM users WHERE USER_ID = ?", (peer_id,))
        peer_data = cursor.fetchone()
        
        if not peer_data and isinstance(peer_id, str) and peer_id.isdigit():
            peer_id_int = int(peer_id)
            logger.info(f"Trying to find peer with USER_ID={peer_id_int} (converted to int)")
            cursor.execute("SELECT USER_ID FROM users WHERE USER_ID = ?", (peer_id_int,))
            peer_data = cursor.fetchone()
        
        if not peer_data and isinstance(peer_id, int):
            peer_id_str = str(peer_id)
            logger.info(f"Trying to find peer with USER_ID='{peer_id_str}' (converted to string)")
            cursor.execute("SELECT USER_ID FROM users WHERE USER_ID = ?", (peer_id_str,))
            peer_data = cursor.fetchone()
        
        if peer_data:
            found_peer_id = peer_data[0]
            logger.info(f"Found peer {found_peer_id}")
        else:
            logger.warning(f"Peer with ID {peer_id} not found in database, but will still try to send message")
        
        conn.close()
        return {
            'status': status,
            'peer_id': peer_id,
            'anony_name': None,  # No ANONY_NAME column, so set to None
            'peer_anony_name': None  # No ANONY_NAME column, so set to None
        }
    
    except sqlite3.Error as e:
        logger.error(f"Database error when getting peer info for user {user_id}: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        if conn:
            conn.close()
        return None
    except Exception as e:
        logger.error(f"Unexpected error when getting peer info for user {user_id}: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        if conn:
            conn.close()
        return None

def send_text_message(bot, peer_id, text, message=None):
    """
    Send a text message to a peer.
    
    Args:
        bot: The Telegram bot instance
        peer_id: The peer's Telegram ID
        text: The text message to send
        message: The original message object (for reply handling)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Send the message without any prefix
        formatted_message = text
        
        # Try to convert peer_id to integer if it's a string
        try:
            if isinstance(peer_id, str) and peer_id.isdigit():
                peer_id_int = int(peer_id)
                logger.info(f"Converting peer_id from string '{peer_id}' to integer {peer_id_int}")
                peer_id = peer_id_int
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not convert peer_id to integer: {e}")
        
        # Check if this is a reply to another message
        reply_text = None
        if message and message.reply_to_message:
            reply_msg = message.reply_to_message
            
            # Get the text of the message being replied to
            if reply_msg.content_type == 'text':
                reply_text = reply_msg.text
                # Truncate if too long
                if len(reply_text) > 50:
                    reply_text = reply_text[:47] + "..."
                
                # Format the message to include the reply context
                formatted_message = f"↩️ Reply to: \"{reply_text}\"\n\n{text}"
                logger.info(f"Formatted reply message: {formatted_message}")
        
        # Send the message
        logger.info(f"Attempting to send message to peer_id: {peer_id} (type: {type(peer_id).__name__})")
        bot.send_message(peer_id, formatted_message)
        logger.info(f"Text message sent to peer {peer_id}")
        return True
    except Exception as e:
        logger.error(f"Error sending text message to peer {peer_id}: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return False

def send_media_notification(bot, peer_id, media_type, sender_info=None):
    """
    Send a notification about media content instead of the actual media.
    This is only used as a last resort when we can't send the actual media.
    
    Args:
        bot: The Telegram bot instance
        peer_id: The peer's Telegram ID
        media_type: The type of media (sticker, voice, photo, etc.)
        sender_info: Optional information about the sender
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Always use "Anonymous" since there's no ANONY_NAME column
        sender_part = "👤 Anonymous"
        
        # Create appropriate message based on media type
        if media_type == "sticker":
            message = f"{sender_part} sent a sticker 🎭 (Media could not be forwarded)"
        elif media_type == "voice":
            message = f"{sender_part} sent a voice message 🎤 (Media could not be forwarded)"
        elif media_type == "photo":
            message = f"{sender_part} sent a photo 📷 (Media could not be forwarded)"
        elif media_type == "video":
            message = f"{sender_part} sent a video 🎬 (Media could not be forwarded)"
        elif media_type == "animation" or media_type == "gif":
            message = f"{sender_part} sent a GIF 🎭 (Media could not be forwarded)"
        elif media_type == "audio":
            message = f"{sender_part} sent an audio file 🎵 (Media could not be forwarded)"
        elif media_type == "document":
            message = f"{sender_part} sent a document 📄 (Media could not be forwarded)"
        else:
            message = f"{sender_part} sent a {media_type} (Media could not be forwarded)"
        
        # Try to convert peer_id to integer if it's a string
        try:
            if isinstance(peer_id, str) and peer_id.isdigit():
                peer_id_int = int(peer_id)
                logger.info(f"Converting peer_id from string '{peer_id}' to integer {peer_id_int}")
                peer_id = peer_id_int
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not convert peer_id to integer: {e}")
        
        # Send the notification
        logger.info(f"Attempting to send {media_type} notification to peer_id: {peer_id} (type: {type(peer_id).__name__})")
        bot.send_message(peer_id, message)
        logger.info(f"{media_type.capitalize()} notification sent to peer {peer_id}")
        return True
    except Exception as e:
        logger.error(f"Error sending {media_type} notification to peer {peer_id}: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return False

def forward_media(bot, peer_id, message, media_type):
    """
    Forward media content to a peer with spoiler/content warning.
    
    Args:
        bot: The Telegram bot instance
        peer_id: The peer's Telegram ID
        message: The original message object containing media
        media_type: The type of media
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Try to convert peer_id to integer if it's a string
        try:
            if isinstance(peer_id, str) and peer_id.isdigit():
                peer_id_int = int(peer_id)
                logger.info(f"Converting peer_id from string '{peer_id}' to integer {peer_id_int}")
                peer_id = peer_id_int
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not convert peer_id to integer: {e}")
        
        logger.info(f"Forwarding {media_type} to peer_id: {peer_id}")
        
        # Log message details for debugging
        logger.info(f"Message content_type: {message.content_type}")
        
        # Verify that the message has the expected attributes for the media type
        if media_type == 'photo' and (not hasattr(message, 'photo') or not message.photo):
            logger.error(f"Message does not have photo attribute or photo is empty")
            # Try to detect the actual media type
            if hasattr(message, 'content_type'):
                logger.info(f"Actual content type is {message.content_type}, using that instead")
                media_type = message.content_type
        
        # Log additional details for debugging
        if media_type == 'photo' and hasattr(message, 'photo'):
            logger.info(f"Photo array length: {len(message.photo)}")
            if message.photo:
                logger.info(f"First photo file_id: {message.photo[0].file_id}")
        elif media_type == 'video' and hasattr(message, 'video'):
            logger.info(f"Video file_id: {message.video.file_id}")
        elif media_type == 'voice' and hasattr(message, 'voice'):
            logger.info(f"Voice file_id: {message.voice.file_id}")
        elif media_type == 'document' and hasattr(message, 'document'):
            logger.info(f"Document file_id: {message.document.file_id}")
        
        # Get the original caption if any
        caption = message.caption if hasattr(message, 'caption') and message.caption else None
        
        # Check if this is a reply to another message
        if message.reply_to_message:
            reply_msg = message.reply_to_message
            reply_text = None
            
            # Get the text of the message being replied to
            if reply_msg.content_type == 'text':
                reply_text = reply_msg.text
                # Truncate if too long
                if len(reply_text) > 50:
                    reply_text = reply_text[:47] + "..."
                
                # Add reply context to caption
                reply_prefix = f"↩️ Reply to: \"{reply_text}\"\n\n"
                if caption:
                    caption = reply_prefix + caption
                else:
                    caption = reply_prefix.strip()
                
                logger.info(f"Added reply context to caption: {caption}")
        
        logger.info(f"Final caption: {caption}")
        
        # Check user status to determine if we should blur media
        should_blur = False
        try:
            conn = sqlite3.connect(USER_DB_PATH)
            cursor = conn.cursor()
            
            # Get the sender's user_id
            sender_id = message.from_user.id
            
            # Check the sender's status
            cursor.execute("SELECT STATUS FROM users WHERE USER_ID = ?", (sender_id,))
            status_data = cursor.fetchone()
            
            if status_data and status_data[0] in ["RANDOM", "PRIVATE", "CONNECTED"]:
                should_blur = True
                logger.info(f"User {sender_id} has status {status_data[0]}, applying blur to media")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error checking user status for blur: {e}")
            # Default to blur if we can't determine status
            should_blur = True
        
        # No need to add a note about clicking to view blurred media
        # The user will know they can click on it
        
        # Handle different media types with has_spoiler=True where applicable
        if media_type == 'photo':
            # Make sure the photo attribute exists and is not empty
            if hasattr(message, 'photo') and message.photo:
                # Get the largest photo (last item in the array)
                photo = message.photo[-1]
                logger.info(f"Sending photo with file_id: {photo.file_id}, blur: {should_blur}")
                
                # Try sending with all parameters first
                try:
                    bot.send_photo(
                        peer_id, 
                        photo.file_id,
                        has_spoiler=should_blur,  # Add spoiler/blur effect based on status
                        caption=caption
                    )
                except Exception as photo_e:
                    # If that fails, try with minimal parameters
                    logger.error(f"Error sending photo with full parameters: {photo_e}")
                    logger.info("Retrying with minimal parameters")
                    bot.send_photo(peer_id, photo.file_id)
            else:
                # If photo attribute is missing or empty, raise an error to trigger recovery
                logger.error("Message does not have valid photo attribute")
                raise ValueError("Invalid photo message")
            
        elif media_type == 'video':
            # Make sure the video attribute exists
            if hasattr(message, 'video') and message.video:
                logger.info(f"Sending video with file_id: {message.video.file_id}, blur: {should_blur}")
                
                # Try sending with all parameters first
                try:
                    bot.send_video(
                        peer_id, 
                        message.video.file_id,
                        has_spoiler=should_blur,  # Add spoiler/blur effect based on status
                        caption=caption
                    )
                except Exception as video_e:
                    # If that fails, try with minimal parameters
                    logger.error(f"Error sending video with full parameters: {video_e}")
                    logger.info("Retrying with minimal parameters")
                    bot.send_video(peer_id, message.video.file_id)
            else:
                # If video attribute is missing, raise an error to trigger recovery
                logger.error("Message does not have valid video attribute")
                raise ValueError("Invalid video message")
            
        elif media_type == 'animation' or media_type == 'gif':
            # Make sure the animation attribute exists
            if hasattr(message, 'animation') and message.animation:
                logger.info(f"Sending animation with file_id: {message.animation.file_id}, blur: {should_blur}")
                
                # Try sending with all parameters first
                try:
                    bot.send_animation(
                        peer_id, 
                        message.animation.file_id,
                        has_spoiler=should_blur,  # Add spoiler/blur effect based on status
                        caption=caption
                    )
                except Exception as anim_e:
                    # If that fails, try with minimal parameters
                    logger.error(f"Error sending animation with full parameters: {anim_e}")
                    logger.info("Retrying with minimal parameters")
                    bot.send_animation(peer_id, message.animation.file_id)
            else:
                # If animation attribute is missing, raise an error to trigger recovery
                logger.error("Message does not have valid animation attribute")
                raise ValueError("Invalid animation message")
            
        elif media_type == 'sticker':
            # Make sure the sticker attribute exists
            if hasattr(message, 'sticker') and message.sticker:
                # Stickers don't support has_spoiler or caption, so we send as is
                logger.info(f"Sending sticker with file_id: {message.sticker.file_id}")
                
                try:
                    bot.send_sticker(peer_id, message.sticker.file_id)
                    
                    # If this is a reply and we couldn't add caption to sticker, send a separate message with reply context
                    if message.reply_to_message and caption:
                        bot.send_message(peer_id, caption)
                except Exception as sticker_e:
                    # If that fails, log the error and try again with just the essential parameters
                    logger.error(f"Error sending sticker: {sticker_e}")
                    logger.info("Retrying sticker with minimal parameters")
                    bot.send_sticker(peer_id, message.sticker.file_id)
            else:
                # If sticker attribute is missing, raise an error to trigger recovery
                logger.error("Message does not have valid sticker attribute")
                raise ValueError("Invalid sticker message")
            
        elif media_type == 'voice':
            # Make sure the voice attribute exists
            if hasattr(message, 'voice') and message.voice:
                logger.info(f"Sending voice with file_id: {message.voice.file_id}")
                
                # Try sending with all parameters first
                try:
                    bot.send_voice(peer_id, message.voice.file_id, caption=caption)
                except Exception as voice_e:
                    # If that fails, try with minimal parameters
                    logger.error(f"Error sending voice with full parameters: {voice_e}")
                    logger.info("Retrying with minimal parameters")
                    bot.send_voice(peer_id, message.voice.file_id)
            else:
                # If voice attribute is missing, raise an error to trigger recovery
                logger.error("Message does not have valid voice attribute")
                raise ValueError("Invalid voice message")
            
        elif media_type == 'audio':
            # Make sure the audio attribute exists
            if hasattr(message, 'audio') and message.audio:
                logger.info(f"Sending audio with file_id: {message.audio.file_id}")
                
                try:
                    bot.send_audio(peer_id, message.audio.file_id, caption=caption)
                except Exception as audio_e:
                    # If that fails, try with minimal parameters
                    logger.error(f"Error sending audio with full parameters: {audio_e}")
                    logger.info("Retrying with minimal parameters")
                    bot.send_audio(peer_id, message.audio.file_id)
            else:
                # If audio attribute is missing, raise an error to trigger recovery
                logger.error("Message does not have valid audio attribute")
                raise ValueError("Invalid audio message")
            
        elif media_type == 'document':
            # Make sure the document attribute exists
            if hasattr(message, 'document') and message.document:
                logger.info(f"Sending document with file_id: {message.document.file_id}")
                
                try:
                    bot.send_document(peer_id, message.document.file_id, caption=caption)
                except Exception as doc_e:
                    # If that fails, try with minimal parameters
                    logger.error(f"Error sending document with full parameters: {doc_e}")
                    logger.info("Retrying with minimal parameters")
                    bot.send_document(peer_id, message.document.file_id)
            else:
                # If document attribute is missing, raise an error to trigger recovery
                logger.error("Message does not have valid document attribute")
                raise ValueError("Invalid document message")
            
        elif hasattr(message, 'text') and message.text:
            # Handle text messages that might have been passed to this function
            logger.info(f"Forwarding text message: {message.text[:30]}...")
            bot.send_message(peer_id, message.text)
            
        else:
            # Try to determine the media type from the message object
            for possible_type in ['photo', 'video', 'voice', 'audio', 'document', 'animation', 'sticker']:
                if hasattr(message, possible_type) and getattr(message, possible_type):
                    logger.info(f"Detected media type {possible_type} from message attributes")
                    # Recursive call with the correct media type
                    return forward_media(bot, peer_id, message, possible_type)
            
            # If we still can't determine the type, send a notification as last resort
            logger.warning(f"Could not determine media type for message, using notification as fallback")
            send_media_notification(bot, peer_id, media_type)
            return True
            
        logger.info(f"{media_type.capitalize()} forwarded to peer {peer_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error forwarding {media_type} to peer {peer_id}: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        
        # Try to recover by detecting the correct media type
        try:
            logger.info(f"Attempting to recover by detecting correct media type")
            
            # Check if the message has any media attributes
            detected_type = None
            for possible_type in ['photo', 'video', 'voice', 'audio', 'document', 'animation', 'sticker']:
                if hasattr(message, possible_type) and getattr(message, possible_type):
                    detected_type = possible_type
                    logger.info(f"Detected media type {detected_type} from message attributes")
                    break
            
            if detected_type and detected_type != media_type:
                logger.info(f"Retrying with detected media type: {detected_type}")
                return forward_media(bot, peer_id, message, detected_type)
            
            # If we can't detect a different type or already tried the correct type,
            # try one more time with the original media type but with minimal parameters
            if media_type == 'photo' and hasattr(message, 'photo') and message.photo:
                logger.info(f"Retrying photo with minimal parameters")
                photo = message.photo[-1]
                bot.send_photo(peer_id, photo.file_id)
                return True
            elif media_type == 'video' and hasattr(message, 'video'):
                logger.info(f"Retrying video with minimal parameters")
                bot.send_video(peer_id, message.video.file_id)
                return True
            elif media_type == 'voice' and hasattr(message, 'voice'):
                logger.info(f"Retrying voice with minimal parameters")
                bot.send_voice(peer_id, message.voice.file_id)
                return True
            elif media_type == 'sticker' and hasattr(message, 'sticker'):
                logger.info(f"Retrying sticker with minimal parameters")
                bot.send_sticker(peer_id, message.sticker.file_id)
                return True
            
            # If all recovery attempts fail, fall back to notification
            logger.info(f"All recovery attempts failed, sending notification as last resort")
            send_media_notification(bot, peer_id, media_type)
            
        except Exception as inner_e:
            logger.error(f"Recovery attempts failed: {inner_e}")
            logger.error(f"Recovery error details: {traceback.format_exc()}")
            try:
                send_media_notification(bot, peer_id, media_type)
            except Exception as notif_e:
                logger.error(f"Even notification failed: {notif_e}")
        
        return False

def handle_message(bot, message, user_id=None):
    """
    Main function to handle and forward messages to peers.
    
    Args:
        bot: The Telegram bot instance
        message: The Telegram message object
        user_id: Optional user ID override (if not using message.from_user.id)
    
    Returns:
        True if message was handled and sent, False otherwise
    """
    try:
        # Get the user ID from the message if not provided
        if not user_id:
            user_id = message.from_user.id
        
        logger.info(f"Handling message from user {user_id} (type: {type(user_id).__name__})")
        logger.info(f"Message content type: {message.content_type}")
        
        # Check if this is a reply message
        if message.reply_to_message:
            logger.info(f"Message is a reply to another message")
        
        # Get peer information using the standard function
        peer_info = get_peer_info(user_id)
        if not peer_info:
            logger.info(f"No valid peer found for user {user_id} using get_peer_info function")
            return False
        
        # Check if user is a LISTENER - silently ignore messages
        if peer_info['status'] == 'LISTENER':
            logger.info(f"User {user_id} is a LISTENER, ignoring message")
            return True  # Return True to indicate message was handled (by ignoring it)
        
        # Check if user is a BROADCASTER - send message to all listeners
        if peer_info['status'] == 'BROADCASTER':
            if 'listeners' in peer_info and peer_info['listeners']:
                listeners = peer_info['listeners']
                logger.info(f"Broadcasting message from user {user_id} to {len(listeners)} listeners")
                
                success_count = 0
                for listener_id in listeners:
                    try:
                        if message.content_type == 'text':
                            # Send text message to listener
                            bot.send_message(listener_id, message.text)
                        else:
                            # Forward media to listener
                            forward_media(bot, listener_id, message, message.content_type)
                        success_count += 1
                    except Exception as listener_error:
                        logger.error(f"Error sending message to listener {listener_id}: {listener_error}")
                
                logger.info(f"Successfully sent message to {success_count} out of {len(listeners)} listeners")
                return success_count > 0
            else:
                logger.info(f"Broadcaster {user_id} has no listeners")
                return False
        
        # Handle regular peer messaging
        peer_id = peer_info['peer_id']
        logger.info(f"Found peer_id {peer_id} for user {user_id}")
        
        # Forward the message based on content type
        if message.content_type == 'text':
            logger.info(f"Sending text message from user {user_id} to peer {peer_id}")
            return send_text_message(bot, peer_id, message.text, message)
        else:
            logger.info(f"Forwarding {message.content_type} from user {user_id} to peer {peer_id}")
            return forward_media(bot, peer_id, message, message.content_type)
    
    except Exception as e:
        logger.error(f"Error handling message from user {user_id}: {e}")
        logger.error(traceback.format_exc())
        return False

# For testing purposes
if __name__ == "__main__":
    print("This module is designed to be imported, not run directly.")