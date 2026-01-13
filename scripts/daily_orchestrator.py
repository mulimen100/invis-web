import os
import subprocess
import json
import logging
from datetime import datetime
import sys

import shutil

# Setup logging
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger('DailyOrchestrator')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, 'state', 'engine_state.json')

# Path to the Web Application's public data folder
# Assumes structure: /parent/titan_hammer/scripts/../../invis-web/public/data/
WEB_DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'invis-web', 'public', 'data')
WEB_STATE_FILE = os.path.join(WEB_DATA_DIR, 'engine_state.json')

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def git_sync(message):
    try:
        logger.info(f"Syncing to Git: {message}")
        subprocess.run(['git', 'add', STATE_FILE], check=True, cwd=BASE_DIR)
        subprocess.run(['git', 'commit', '-m', message], check=True, cwd=BASE_DIR)
        subprocess.run(['git', 'push'], check=True, cwd=BASE_DIR)
        logger.info("Git sync successful.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git sync failed: {e}")

def run_engine():
    logger.info("Starting Daily Engine Run...")
    
    # 1. Load current equity from state (or API in future)
    state = load_state()
    # Ensure current_equity is a float
    current_equity = float(state.get('equity', 10000.0)) 
    
    # 2. Run Main Engine
    main_script = os.path.join(BASE_DIR, 'main.py')
    cmd = [sys.executable, main_script, '--advisor', '--equity', str(current_equity)]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Engine Output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Engine Run Failed:\n{e.stderr}")
        return

    # 3. Check for Changes
    new_state = load_state()
    
    # 4. Update Daily Performance Log (Paper Trading Simulation)
    perf_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_daily_performance.py')
    try:
        logger.info("Updating Daily Performance Log...")
        subprocess.run([sys.executable, perf_script], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Performance Update Failed:\n{e.stderr}")
    
    # 4. Update Market Flags (Independent of Engine State)
    flags_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_flags.py')
    try:
        logger.info("Running Market Flags Update...")
        subprocess.run([sys.executable, flags_script], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Flags Update Failed:\n{e.stderr}")

    # 5. Sync to Web Directory
    if os.path.exists(WEB_DATA_DIR):
        try:
            # Sync State
            shutil.copy2(STATE_FILE, WEB_STATE_FILE)
            logger.info(f"State copied to Web Dir: {WEB_STATE_FILE}")
            
            # Sync Flags
            FLAGS_FILE = os.path.join(BASE_DIR, 'data', 'market_flags.json') # Assuming update_flags puts it here
            if os.path.exists(FLAGS_FILE):
                WEB_FLAGS_FILE = os.path.join(WEB_DATA_DIR, 'market_flags.json')
                shutil.copy2(FLAGS_FILE, WEB_FLAGS_FILE)
                logger.info(f"Flags copied to Web Dir: {WEB_FLAGS_FILE}")
        except Exception as e:
             logger.error(f"Failed to copy data to web dir: {e}")
    else:
        logger.warning(f"Web Data Dir not found at {WEB_DATA_DIR}, skipping copy.")


    

    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    sync_msg = f"Titan Engine Update: {timestamp} | State: {new_state.get('state', 'UNKNOWN')}"
    
    git_sync(sync_msg)
    logger.info(f"Titan Hammer Cycle Complete. {timestamp}")

if __name__ == "__main__":
    run_engine()
