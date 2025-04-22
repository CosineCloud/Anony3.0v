# Anonymous Chats

## Updating Paths

To update all absolute paths to relative paths, run:

```bash
chmod +x run_update.sh
./run_update.sh
```

This will update all Python files in the project to use relative paths instead of absolute paths.

## AI Chat Integration

The AI chat integration allows users to chat with an AI assistant named Bella. Features include:

- Typing indicators during processing
- "Not Allowed" message for media messages
- Centralized logging in telegram_bot.py
- Memory management to prevent excessive file sizes

## Database Structure

The project uses two SQLite databases:
- `user_db.db`: Stores user information and connection status
- `user_def.db`: Stores membership information and credits