import telebot
import sqlite3

# Initialize the bot with the provided API key
bot = telebot.TeleBot("5768243722:AAGuPYWlGCH9x7I-N5bJ3u6royTuEfQ5ZFw")

# Create or connect to the SQLite database
conn = sqlite3.connect('user_db.db', check_same_thread=False)
cursor = conn.cursor()

# Create the user table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    USER_ID INTEGER PRIMARY KEY,
    PEER_ID TEXT,
    TYPE TEXT,
    STATUS TEXT,
    TIMER INTEGER,
    OTP TEXT
)
''')
conn.commit()

# Modified insert_user function with error handling
def insert_user(user_id):
    try:
        cursor.execute('''
        INSERT OR IGNORE INTO users (USER_ID, PEER_ID, TYPE, STATUS, TIMER, OTP)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, '', 'SILVER', 'OPEN', 120, ''))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# Define the /start command handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    insert_user(user_id)
    # Create the menu options
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("🔐 Private Connection", callback_data="private_connection"))
    markup.row(telebot.types.InlineKeyboardButton("🔀 Random Connection", callback_data="random_connection"))
    markup.row(
        telebot.types.InlineKeyboardButton("⏏️", callback_data="eject"),
        telebot.types.InlineKeyboardButton("⏹️", callback_data="stop"),
        telebot.types.InlineKeyboardButton("⏩️", callback_data="forward")
    )
    markup.row(telebot.types.InlineKeyboardButton("📲 Anony Number", callback_data="anony_number"))
    markup.row(telebot.types.InlineKeyboardButton("🔊 Broadcasting", callback_data="broadcasting"))
    markup.row(telebot.types.InlineKeyboardButton("✨AI Chat bot", callback_data="ai_chat_bot"))
    markup.row(
        telebot.types.InlineKeyboardButton("🚹 About", callback_data="about"),
        telebot.types.InlineKeyboardButton("📝 Privacy", callback_data="privacy")
    )
    markup.row(telebot.types.InlineKeyboardButton("More >>", callback_data="more"))
    #markup.row(telebot.types.InlineKeyboardButton("<< Back", callback_data="back"))
    
    # Send the welcome message with the menu
    bot.send_message(message.chat.id, "||             𝓐𝓷𝓸𝓷𝔂𝓶𝓸𝓾𝓼 𝓒𝓱𝓪𝓽𝓼.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🚹\nAbout")
@bot.callback_query_handler(func=lambda call: call.data == "more")
def handle_more_callback(call):
    bot.answer_callback_query(call.id)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("Membership", callback_data="membership"))
    markup.row(telebot.types.InlineKeyboardButton("Settings", callback_data="settings"))
    markup.row(telebot.types.InlineKeyboardButton("Help" , callback_data="help_contact"),
               telebot.types.InlineKeyboardButton(" Contact Us", callback_data="help_contact")
    )
    markup.row(telebot.types.InlineKeyboardButton("<< Back", callback_data="back"))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def handle_back_callback(call):
    bot.answer_callback_query(call.id)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("🔐 Private Connection", callback_data="private_connection"))
    markup.row(telebot.types.InlineKeyboardButton("🔀 Random Connection", callback_data="random_connection"))
    markup.row(
        telebot.types.InlineKeyboardButton("⏏️", callback_data="eject"),
        telebot.types.InlineKeyboardButton("⏹️", callback_data="stop"),
        telebot.types.InlineKeyboardButton("⏩️", callback_data="forward")
    )
    markup.row(telebot.types.InlineKeyboardButton("📲 Anony Number", callback_data="anony_number"))
    markup.row(telebot.types.InlineKeyboardButton("🔊 Broadcasting", callback_data="broadcasting"))
    markup.row(telebot.types.InlineKeyboardButton("✨AI Chat bot", callback_data="ai_chat_bot"))
    markup.row(
        telebot.types.InlineKeyboardButton("🚹 About", callback_data="about"),
        telebot.types.InlineKeyboardButton("📝 Privacy", callback_data="privacy")
    )
    markup.row(telebot.types.InlineKeyboardButton("More >>", callback_data="more"))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "settings")
def handle_settings_callback(call):
    bot.answer_callback_query(call.id)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("🔴 Pictures", callback_data="pictures"),
               telebot.types.InlineKeyboardButton("🔴 Video", callback_data="video")
    )
    markup.row(telebot.types.InlineKeyboardButton("🔴 Text", callback_data="text"),
               telebot.types.InlineKeyboardButton("🔴 Voice", callback_data="voice")
    )
    markup.row(telebot.types.InlineKeyboardButton("🔴 Add to Block List", callback_data="block_list"))
    markup.row(telebot.types.InlineKeyboardButton("🔴 Auto Translate", callback_data="auto_translate"))
    markup.row(telebot.types.InlineKeyboardButton("🔴 Censor", callback_data="censor"))
    markup.row(telebot.types.InlineKeyboardButton("<< Back", callback_data="back"))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
def send_about(message):
    bot.reply_to(message, "Hey")

@bot.callback_query_handler(func=lambda call: call.data == "about")
def handle_about_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Hey")

# Add error handling for the main bot loop
def main():
    try:
        print("Bot started successfully!")
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Bot error: {e}")
        # You might want to implement a retry mechanism here

if __name__ == "__main__":
    main()
