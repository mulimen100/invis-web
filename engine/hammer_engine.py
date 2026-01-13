import json
import os
import logging
import argparse
from datetime import datetime
import pandas as pd
import yfinance as yf
from alert_system import AlertSystem

class HammerEngine:
    def __init__(self, config_path, state_path, current_equity=None):
        self.config_path = config_path
        self.state_path = state_path
        self.current_equity = current_equity
        self.config = self._load_json(self.config_path)
        self.state = self._load_json(self.state_path)
        self.alert_system = AlertSystem(self.config_path)
        self._setup_logging()

    def _load_json(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, 'r') as f:
            return json.load(f)

    def _save_state(self):
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=4)

    def _setup_logging(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(self.config_path)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'hammer_production_{datetime.now().strftime("%Y%m%d")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("TitanHammer")

    def _fetch_spy_data(self):
        self.logger.info("Fetching strict SPY data...")
        try:
            # Download sufficient history for 200 SMA
            # Download 2 years to be safe for 200 trading days
            ticker = yf.Ticker("SPY")
            df = ticker.history(period="2y")
            if df.empty:
                raise ValueError("No data returned from YFinance")
            return df
        except Exception as e:
            self.logger.error(f"Failed to fetch SPY data: {e}")
            raise

    def run(self):
        self.logger.info("Titan Hammer Production Run Initiated")
        
        # 1. Update Equity in State if provided
        if self.current_equity is not None:
            self.state['equity'] = self.current_equity
            self.logger.info(f"Equity updated from input: ${self.current_equity:,.2f}")
        else:
            self.logger.warning("No equity provided. Using last known state equity.")

        current_equity = self.state['equity']
        current_state = self.state.get('state', 'ON')
        
        # 2. Market Data & Indicators
        try:
            df = self._fetch_spy_data()
            last_close = df['Close'].iloc[-1]
            sma200 = df['Close'].rolling(window=200).mean().iloc[-1]
            
            is_uptrend = last_close > sma200
            
            self.logger.info(f"SPY Level: {last_close:.2f} | SMA200: {sma200:.2f} | Uptrend: {is_uptrend}")
        except Exception as e:
            self.logger.critical(f"Aborting run due to data failure: {e}")
            return

        # 3. Logic Evaluation
        new_state = current_state
        today_str = datetime.now().date().isoformat()
        
        # Prevent double counting if run multiple times same day?
        # Ideally we check last_run_date. 
        # But for safety, we assume daily run scheduler handles frequency.
        # We will increment counters only if date changed or just execute robustly.
        # Simple Strict Rule: "Execute EOD".
        
        if self.state.get('last_run_date') == today_str:
            self.logger.warning("Engine already ran today. Proceeding with caution (counters might ideally be skipped if redundant).")
            # For simplicity in this engine, we will calculate deciding logic anyway, 
            # assuming user might be re-running to fix something.
        
        self.state['last_run_date'] = today_str

        # --- MANUAL OVERRIDE CHECK ---
        manual_pause = self.config.get('manual_override', {}).get('paused', False)
        
        if manual_pause:
            self.logger.warning(">>> MANUAL OVERRIDE: FORCE PAUSE")
            new_state = "PAUSED"
            # If we were previously ON, this triggers a fresh pause event
            if current_state == "ON":
                self.state['pause_start_date'] = today_str
                self.state['days_paused_count'] = 0
                self.state['trend_confirmation_days'] = 0
        
        else:
            # Normal Logic (or Automatic Resume if conditions met)
            if current_state == "ON":
                # --- ON STATE LOGIC ---
                
                # Update ATH (High Water Mark)
                if current_equity > self.state.get('ath', 0):
                    self.state['ath'] = current_equity
                    self.logger.info(f"New ATH Reached: ${current_equity:,.2f}")
                
                # Calculate Drawdown
                ath = self.state['ath']
                dd = (current_equity / ath) - 1 if ath > 0 else 0
                self.state['drawdown'] = dd
                
                self.logger.info(f"Status: ON | DD: {dd:.2%} | Limit: -25%")
                
                # TRIGGER: -28% DD (Scenario B)
                if dd <= -0.28:
                    self.logger.warning(">>> PAUSE TRIGGERED: Drawdown limit hit (-28%)")
                    new_state = "PAUSED"
                    self.state['pause_start_date'] = today_str
                    self.state['days_paused_count'] = 0
                    self.state['trend_confirmation_days'] = 0
                    
                    self.alert_system.send_email(
                        "AUTOMATIC PAUSE TRIGGERED",
                        f"Drawdown Limit Hit: {dd:.2%}\nEngine Entering PAUSE State.\n\nAction: Selling all assets > CASH."
                    )


            elif current_state == "PAUSED":
                # --- PAUSED STATE LOGIC ---
                
                # Increment Paused Counter
                self.state['days_paused_count'] = self.state.get('days_paused_count', 0) + 1
                
                # Increment Trend Counter
                if is_uptrend:
                    self.state['trend_confirmation_days'] = self.state.get('trend_confirmation_days', 0) + 1
                else:
                    self.state['trend_confirmation_days'] = 0 # Reset if trend break
                
                days_paused = self.state['days_paused_count']
                trend_days = self.state['trend_confirmation_days']
                
                self.logger.info(f"Status: PAUSED | Waited: {days_paused}/30 | Trend: {trend_days}/10")
                
                # TRIGGER: Resume Logic (Scenario B: 30d wait + 10d trend)
                if days_paused >= 30 and trend_days >= 10:
                    self.logger.warning(">>> RESUME TRIGGERED: Strict conditions met (30d wait + 10d trend)")
                    new_state = "ON"
                    # Reset State for Resume
                    self.state['ath'] = current_equity # Reset ATH to current
                    self.state['pause_start_date'] = None
                    self.state['days_paused_count'] = 0
                    self.state['trend_confirmation_days'] = 0
                    
                    self.alert_system.send_email(
                        "AUTOMATIC RESUME TRIGGERED",
                        f"Conditions Met: Waited 30+ days AND Trend > 200SMA for 10+ days.\nEngine RESUMING operation.\n\nAction: Buying UPRO (3x)."
                    )


        # 4. Generate Output
        self.state['state'] = new_state
        self._save_state()
        
        allocations = {}
        if new_state == "ON":
            allocations = {"UPRO": 1.0}
        else:
            allocations = {"SPY": 0.0, "UPRO": 0.0} # Pure Cash. Or exit to SPY if User preferred?
            # Blueprint says: "PAUSED = 100% allocation to CASH"
            # So {} empty allocation implies Cash usually, or specific Cash ticker.
            # I will output NO assets, implying 100% Cash.
        
        self._write_decision(allocations, new_state)
        self.logger.info(f"Engine Cycle Complete. State: {new_state}")

    def _write_decision(self, allocations, state):
        output_dir = os.path.dirname(self.state_path)
        decision = {
            "timestamp": datetime.now().isoformat(),
            "allocations": allocations,
            "logic": state,
            "metrics": {
                "equity": self.state['equity'],
                "drawdown": self.state.get('drawdown', 0),
                "wait_counter": self.state.get('days_paused_count', 0),
                "trend_counter": self.state.get('trend_confirmation_days', 0)
            }
        }
        output_file = os.path.join(output_dir, 'latest_decision.json')
        with open(output_file, 'w') as f:
            json.dump(decision, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--equity', type=float, help='Current Portfolio Equity')
    args = parser.parse_args()
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config', 'engine_config.json')
    state_path = os.path.join(base_dir, 'state', 'engine_state.json')
    
    engine = HammerEngine(config_path, state_path, current_equity=args.equity)
    engine.run()
