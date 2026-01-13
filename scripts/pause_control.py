import json
import os
import argparse
import sys

# Add engine directory to path to import AlertSystem
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine'))
from alert_system import AlertSystem

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def save_config(config_path, config):
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Titan Hammer - Pause Control")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pause', action='store_true', help="PAUSE the engine (Exit to Safety)")
    group.add_argument('--resume', action='store_true', help="RESUME the engine (Aggressive 3x)")
    parser.add_argument('--status', action='store_true', help="Check current status") # Added status check without exclusivity for checking state

    # Handle status manually to allow running it without modifying the mutual exclusion group logic for actions
    if '--status' in sys.argv:
        # Just check status and exit
        pass # Logic handled below
    
    args = parser.parse_args()

    # Path setup
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config', 'engine_config.json')

    config = load_config(config_path)

    # Initialize Alert System
    alert_system = AlertSystem(config_path)

    if args.pause:
        config['manual_override']['paused'] = True
        print(">>> PAUSING ENGINE. Next run will exit to safety.")
        save_config(config_path, config)
        alert_system.send_email(
            "MANUAL OVERRIDE: PAUSE",
            f"User initiated MANUAL PAUSE.\nEngine will exit to safety on next run.\n\nInitiated via: Dashboard/CLI"
        )
    
    elif args.resume:
        config['manual_override']['paused'] = False
        print(">>> RESUMING ENGINE. Next run will go AGGRESSIVE 3X.")
        save_config(config_path, config)
        alert_system.send_email(
            "MANUAL OVERRIDE: RESUME",
            f"User initiated MANUAL RESUME.\nEngine will re-enter market on next run if valid.\n\nInitiated via: Dashboard/CLI"
        )

    # Always print status
    config = load_config(config_path) # Reload to be sure
    status = "PAUSED" if config['manual_override']['paused'] else "ACTIVE"
    print(f"Current Status: {status}")
    print(f"Details: {json.dumps(config['manual_override'], indent=2)}")

if __name__ == "__main__":
    main()
