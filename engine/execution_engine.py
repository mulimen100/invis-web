import json
import os
import logging
from datetime import datetime

class ExecutionEngine:
    def __init__(self, advisor_state_path, output_path):
        self.advisor_state_path = advisor_state_path
        self.output_path = output_path
        self._setup_logging()

    def _setup_logging(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(self.advisor_state_path)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'execution_{datetime.now().strftime("%Y%m%d")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("TitanExecution")

    def run(self):
        self.logger.info("Execution Engine: Cycle Started")
        
        # 1. Read Advisor State
        if not os.path.exists(self.advisor_state_path):
            self.logger.critical(f"Advisor State not found at {self.advisor_state_path}. Cannot execute.")
            return

        with open(self.advisor_state_path, 'r') as f:
            advisor_state = json.load(f)
            
        current_state = advisor_state.get('state', 'UNKNOWN')
        last_event = advisor_state.get('event', 'NONE')
        
        self.logger.info(f"Advisor says: {current_state} (Event: {last_event})")
        
        # 2. Determine Allocation (Blind Obedience)
        allocations = {}
        if current_state == "ON":
            allocations = {"UPRO": 1.0}
            self.logger.info("Target: 100% UPRO")
        elif current_state == "PAUSED":
            allocations = {"UPRO": 0.0, "SPY": 0.0} # 100% Cash
            self.logger.info("Target: 100% CASH (Paused)")
        else:
            self.logger.error(f"Unknown state '{current_state}'. Defaulting to nothing/safety.")
            allocations = {} 

        # 3. Output Order/Target
        output = {
            "timestamp": datetime.now().isoformat(),
            "source": "ExecutionEngine",
            "advisor_state": current_state,
            "allocations": allocations,
            "mode": os.environ.get("TITAN_MODE", "LIVE")
        }
        
        mode = os.environ.get("TITAN_MODE", "LIVE")
        if mode == "SHADOW":
            self.logger.info(f"SHADOW MODE: Not writing to {self.output_path}. Output would be: {json.dumps(output)}")
        else:
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=4)
            self.logger.info(f"Execution Orders Generated: {allocations}")

if __name__ == "__main__":
    pass
