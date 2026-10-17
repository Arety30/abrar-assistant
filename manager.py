import multiprocessing
import subprocess
import time
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_discord_bot():
    """Runs the discord bot process."""
    logging.info("Starting Discord Bot process...")
    # Using the standalone bot file we validated
    subprocess.run(["~/Workspace/AbrarAssistant/venv/bin/python", "~/Workspace/AbrarAssistant/bot_only.py"])

def run_voice_bridge():
    """Runs the voice bridge process."""
    logging.info("Starting Voice Bridge process...")
    # Using the original backup code (assuming it contains the bridge logic)
    subprocess.run(["~/Workspace/AbrarAssistant/venv/bin/python", "~/Workspace/AbrarAssistant/main_backup.py"])

if __name__ == "__main__":
    # Create processes
    bot_process = multiprocessing.Process(target=run_discord_bot)
    bridge_process = multiprocessing.Process(target=run_voice_bridge)

    # Start processes
    bot_process.start()
    bridge_process.start()

    try:
        bot_process.join()
        bridge_process.join()
    except KeyboardInterrupt:
        logging.info("Stopping processes...")
        bot_process.terminate()
        bridge_process.terminate()
        bot_process.join()
        bridge_process.join()
