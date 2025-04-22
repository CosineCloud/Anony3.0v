"""
Administrative operations module for Anonymous Chats.
This module provides administrative commands for authorized users only.
"""

import logging
import sqlite3
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("operations.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Admin user ID
ADMIN_USER_ID = 584429967

# Configuration file path
CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            config = {
                "ai_api_key": "",
                "ai_model": "gpt-3.5-turbo",
                "bot_status": "normal",
                "ads_enabled": False,
                "logs_enabled": True
            }
            save_config(config)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def is_admin(user_id):
    """Check if the user is an admin."""
    return str(user_id) == str(ADMIN_USER_ID)

def handle_operation_command(bot, message):
    """Handle the /operation command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        logger.warning(f"Unauthorized access attempt to operations by user {user_id}")
        return
    
    operations_text = """
*Admin Operations*

Available commands:
/change_ai_API - Change AI API key
/change_ai_model - Change AI model
/update_status - Update bot status
/Ads1 - Toggle advertisements
/logs_on - Enable logging
/logs_off - Disable logging
/show_db - Show database statistics
    """
    
    bot.send_message(
        message.chat.id,
        operations_text,
        parse_mode="Markdown"
    )
    logger.info(f"Operations menu sent to admin {user_id}")

def handle_change_ai_api(bot, message):
    """Handle the /change_ai_API command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    # Check if there's a parameter (the new API key)
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) < 2:
        # No API key provided, ask for it
        msg = bot.send_message(
            message.chat.id,
            "Please enter the new AI API key:",
            reply_markup={"force_reply": True}
        )
        bot.register_next_step_handler(msg, process_new_api_key, bot)
    else:
        # API key provided with command
        new_api_key = command_parts[1].strip()
        update_api_key(bot, message.chat.id, new_api_key)

def process_new_api_key(message, bot):
    """Process the new API key from user input."""
    new_api_key = message.text.strip()
    update_api_key(bot, message.chat.id, new_api_key)

def update_api_key(bot, chat_id, new_api_key):
    """Update the AI API key in the configuration."""
    config = load_config()
    config["ai_api_key"] = new_api_key
    
    if save_config(config):
        bot.send_message(
            chat_id,
            "AI API key updated successfully."
        )
        logger.info("AI API key updated by admin")
    else:
        bot.send_message(
            chat_id,
            "Failed to update AI API key. Check logs for details."
        )

def handle_change_ai_model(bot, message):
    """Handle the /change_ai_model command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    # Available AI models
    available_models = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "claude-2",
        "claude-instant"
    ]
    
    # Create inline keyboard with available models
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    markup = InlineKeyboardMarkup()
    for model in available_models:
        markup.add(InlineKeyboardButton(model, callback_data=f"model_{model}"))
    
    bot.send_message(
        message.chat.id,
        "Select an AI model:",
        reply_markup=markup
    )
    logger.info(f"AI model selection menu sent to admin {user_id}")

def handle_model_selection(bot, call):
    """Handle the AI model selection callback."""
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    # Extract model name from callback data
    model_name = call.data.split('_', 1)[1]
    
    config = load_config()
    config["ai_model"] = model_name
    
    if save_config(config):
        bot.answer_callback_query(
            call.id,
            text=f"AI model updated to {model_name}",
            show_alert=True
        )
        bot.edit_message_text(
            f"AI model updated to {model_name}",
            call.message.chat.id,
            call.message.message_id
        )
        logger.info(f"AI model updated to {model_name} by admin {user_id}")
    else:
        bot.answer_callback_query(
            call.id,
            text="Failed to update AI model. Check logs for details.",
            show_alert=True
        )

def handle_update_status(bot, message):
    """Handle the /update_status command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    # Available statuses
    statuses = [
        "normal",
        "maintenance",
        "limited",
        "testing"
    ]
    
    # Create inline keyboard with available statuses
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    markup = InlineKeyboardMarkup()
    for status in statuses:
        markup.add(InlineKeyboardButton(status, callback_data=f"status_{status}"))
    
    bot.send_message(
        message.chat.id,
        "Select bot status:",
        reply_markup=markup
    )
    logger.info(f"Status selection menu sent to admin {user_id}")

def handle_status_selection(bot, call):
    """Handle the status selection callback."""
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    # Extract status from callback data
    status = call.data.split('_', 1)[1]
    
    config = load_config()
    config["bot_status"] = status
    
    if save_config(config):
        bot.answer_callback_query(
            call.id,
            text=f"Bot status updated to {status}",
            show_alert=True
        )
        bot.edit_message_text(
            f"Bot status updated to {status}",
            call.message.chat.id,
            call.message.message_id
        )
        logger.info(f"Bot status updated to {status} by admin {user_id}")
    else:
        bot.answer_callback_query(
            call.id,
            text="Failed to update bot status. Check logs for details.",
            show_alert=True
        )

def handle_ads_toggle(bot, message):
    """Handle the /Ads1 command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    config = load_config()
    current_status = config.get("ads_enabled", False)
    
    # Toggle ads status
    config["ads_enabled"] = not current_status
    
    if save_config(config):
        new_status = "enabled" if config["ads_enabled"] else "disabled"
        bot.send_message(
            message.chat.id,
            f"Advertisements are now {new_status}."
        )
        logger.info(f"Advertisements {new_status} by admin {user_id}")
    else:
        bot.send_message(
            message.chat.id,
            "Failed to update advertisement settings. Check logs for details."
        )

def handle_logs_toggle(bot, message, enable):
    """Handle the /logs_on and /logs_off commands."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    config = load_config()
    config["logs_enabled"] = enable
    
    if save_config(config):
        status = "enabled" if enable else "disabled"
        bot.send_message(
            message.chat.id,
            f"Logging is now {status}."
        )
        logger.info(f"Logging {status} by admin {user_id}")
    else:
        bot.send_message(
            message.chat.id,
            "Failed to update logging settings. Check logs for details."
        )

def handle_show_db(bot, message):
    """Handle the /show_db command."""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect('user_db.db')
        cursor = conn.cursor()
        
        # Get total users count
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Get active connections count
        cursor.execute("SELECT COUNT(*) FROM users WHERE STATUS IN ('CONNECTED', 'PRIVATE', 'RANDOM', 'AI')")
        active_connections = cursor.fetchone()[0]
        
        # Get users by status
        cursor.execute("SELECT STATUS, COUNT(*) FROM users GROUP BY STATUS")
        status_counts = cursor.fetchall()
        
        # Format status counts
        status_text = "\n".join([f"- {status}: {count}" for status, count in status_counts])
        
        # Get database file size
        db_size = os.path.getsize('user_db.db') / (1024 * 1024)  # Size in MB
        
        # Prepare the database statistics message
        db_stats = f"""
*Database Statistics*

Total users: {total_users}
Active connections: {active_connections}

*Users by status:*
{status_text}

Database size: {db_size:.2f} MB
Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        bot.send_message(
            message.chat.id,
            db_stats,
            parse_mode="Markdown"
        )
        logger.info(f"Database statistics sent to admin {user_id}")
        
        conn.close()
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"Error retrieving database statistics: {e}"
        )
        logger.error(f"Error retrieving database statistics: {e}")

def register_operation_handlers(bot):
    """Register all operation handlers with the bot."""
    from telebot.types import BotCommand
    
    # Register command handlers
    bot.register_message_handler(
        lambda message: handle_operation_command(bot, message),
        commands=['operation'],
        func=lambda message: is_admin(message.from_user.id)
    )
    
    bot.register_message_handler(
        lambda message: handle_change_ai_api(bot, message),
        commands=['change_ai_API'],
        func=lambda message: is_admin(message.from_user.id)
    )
    
    bot.register_message_handler(
        lambda message: handle_change_ai_model(bot, message),
        commands=['change_ai_model'],
        func=lambda message: is_admin(message.from_user.id)
    )
    
    bot.register_message_handler(
        lambda message: handle_update_status(bot, message),
        commands=['update_status'],
        func=lambda message: is_admin(message.from_user.id)
    )
    
    bot.register_message_handler(
        lambda message: handle_ads_toggle(bot, message),
        commands=['Ads1'],
        func=lambda message: is_admin(message.from_user.id)
    )
    
    bot.register_message_handler(
        lambda message: handle_logs_toggle(bot, message, True),
        commands=['logs_on'],
        func=lambda message: is_admin(message.from_user.id)
    )
    
    bot.register_message_handler(
        lambda message: handle_logs_toggle(bot, message, False),
        commands=['logs_off'],
        func=lambda message: is_admin(message.from_user.id)
    )
    
    bot.register_message_handler(
        lambda message: handle_show_db(bot, message),
        commands=['show_db'],
        func=lambda message: is_admin(message.from_user.id)
    )
    
    # Register callback handlers
    bot.register_callback_query_handler(
        lambda call: handle_model_selection(bot, call),
        func=lambda call: call.data.startswith('model_') and is_admin(call.from_user.id)
    )
    
    bot.register_callback_query_handler(
        lambda call: handle_status_selection(bot, call),
        func=lambda call: call.data.startswith('status_') and is_admin(call.from_user.id)
    )
    
    # Add commands to bot menu for admin
    try:
        bot.set_my_commands(
            [
                BotCommand("operation", "Admin operations menu"),
                BotCommand("change_ai_API", "Change AI API key"),
                BotCommand("change_ai_model", "Change AI model"),
                BotCommand("update_status", "Update bot status"),
                BotCommand("Ads1", "Toggle advertisements"),
                BotCommand("logs_on", "Enable logging"),
                BotCommand("logs_off", "Disable logging"),
                BotCommand("show_db", "Show database statistics")
            ],
            scope={"type": "chat", "chat_id": ADMIN_USER_ID}
        )
    except Exception as e:
        logger.error(f"Error setting admin commands: {e}")