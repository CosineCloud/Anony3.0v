import os
import re

def update_paths_in_file(file_path):
    """
    Update all absolute paths in a file to relative paths.
    
    Args:
        file_path: Path to the file to update
    """
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace all instances of the absolute path with relative paths
    updated_content = content.replace('', '')
    
    # Write the updated content back to the file
    with open(file_path, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated paths in {file_path}")

# List of files to update
files_to_update = [
    'telegram_bot.py',
    'ai_integration.py',
    'anony_AI.py'
]

# Update paths in each file
for file in files_to_update:
    if os.path.exists(file):
        update_paths_in_file(file)
    else:
        print(f"File not found: {file}")

print("Path updates completed!")