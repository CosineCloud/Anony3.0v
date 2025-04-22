import os
import re
import glob

def update_paths_in_file(file_path):
    """
    Update all absolute paths in a file to relative paths.
    
    Args:
        file_path: Path to the file to update
    """
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all instances of the absolute path with relative paths
    updated_content = content.replace('', '')
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"Updated paths in {file_path}")

# Get all Python files in the current directory
python_files = glob.glob('*.py')

# Update paths in each file
for file in python_files:
    update_paths_in_file(file)

print("Path updates completed!")