import os
from git import Repo
import shutil

# Clone repo
repo_url = 'https://github.com/CosineCloud/Anony2.5v.git'
clone_dir = 'Anony2.5v'
target_folder = 'Anonymous_Chats'

if os.path.exists(clone_dir):
    shutil.rmtree(clone_dir)  # Clean up if it already exists

print("Cloning the repo...")
Repo.clone_from(repo_url, clone_dir)

# Move just the Anonymous_Chats folder out
shutil.move(os.path.join(clone_dir, target_folder), target_folder)
shutil.rmtree(clone_dir)  # Optional: clean up the rest

print(f"'{target_folder}' folder downloaded successfully!")
