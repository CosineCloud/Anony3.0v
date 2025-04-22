# Telegram integration for anony_AI.py
import logging
import sqlite3
from anony_AI import ask_bella, load_chat_history, save_to_memory, bella_intro

# Set up logging
logger = logging.getLogger('telegram_bot')

def handle_ai_message(bot, message, user_id):
    """
    Handle a message sent to the AI chatbot.
    
    Args:
        bot: The Telegram bot instance
        message: The message from the user
        user_id: The user's ID
        
    Returns:
        The AI's response
    """
    user_input = message.text
    
    # Show typing indicator during processing
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Load the user's chat history
    chat_history = load_chat_history(user_id)
    
    # If this is the first message, add the system message
    if not chat_history:
        chat_history = [bella_intro]
    
    # Show typing indicator again before getting AI response
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Get Bella's response
    bella_response = ask_bella(user_input, chat_history)
    
    # Add the exchange to the chat history
    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": bella_response})
    
    # Save the updated chat history
    memory_reset = save_to_memory(chat_history, user_id)
    
    # If memory was reset, notify the user
    if memory_reset:
        bot.send_message(
            message.chat.id,
            "Memory is full! I've cleared some old messages to make space. 🧹"
        )
    
    # Note: We no longer update the status here because it's already done in the callback handler
    # This function now just processes the message and returns the response
    
    return bella_response

def start_ai_chat(bot, message):
    """
    Start an AI chat session for a user.
    
    Args:
        bot: The Telegram bot instance
        message: The message that triggered the AI chat
        
    Returns:
        True if successful, False otherwise
    """
    user_id = message.from_user.id
    
    try:
        # Show typing indicator
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Send a welcome message
        bot.send_message(
            message.chat.id,
            "Bella 🤙: yo! what's good? I'm your AI chat buddy. Just send me a message and we can chat!"
        )
        
        # Note: We no longer update the status here because it's already done in the callback handler
        # This function now just sends the welcome message
        
        # No logging here - main telegram_bot.py will handle logging
        return True
    except Exception as e:
        # Let the main function handle the error logging
        return False