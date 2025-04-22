# Pilot.py

import subprocess
import time

def run_bot():
    while True:
        print("Starting telegram_bot.py...")
        process = subprocess.Popen(["python", "telegram_bot.py"])
        process.wait()

        print("telegram_bot.py has stopped. Restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("Pilot stopped by user.")
