import json
import os
import logging
import yfinance as yf
from datetime import datetime

class AdvisorEngine:
    def __init__(self, state_path, current_equity=None):
        self.state_path = state_path
        self.current_equity = current_equity
        self.state = self._load_state()
        self._setup_logging()

    def _load_state(self):
        if not os.path.exists(self.state_path):
            # strict initialization if missing
            return {
                "date": datetime.now().date().isoformat(),
                "state": "ON",
                "ath": self.current_equity if self.current_equity else 10000.0,
                "drawdown": 0.0,
                "pause_start_date": None,
                "counters": {
                    "days_paused": 0,
                    "trend_days": 0
                },
                "event": "NO_CHANGE",
                "notes": "Initialized."
            }
        with open(self.state_path, 'r') as f:
            return json.load(f)

    def _save_state(self):
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=4)

    def _setup_logging(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(self.state_path)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'advisor_{datetime.now().strftime("%Y%m%d")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("TitanAdvisor")

    def _fetch_spy_data(self):
        try:
            ticker = yf.Ticker("SPY")
            df = ticker.history(period="2y")
            if df.empty:
                raise ValueError("No data returned from YFinance")
            return df
        except Exception as e:
            self.logger.error(f"Failed to fetch SPY data: {e}")
            raise

    def run(self):
        self.logger.info("Advisor Engine: Cycle Started")

        # 1. Update Inputs
        if self.current_equity is not None:
             self.logger.info(f"Input Equity: ${self.current_equity:,.2f}")
        else:
             self.logger.warning("No equity provided. Using last state assumption.")
             # In production, this might be fatal, but we'll soft-fail to last ATH/calc
             self.current_equity = self.state.get('ath', 10000.0) * (1 + self.state.get('drawdown', 0))

        current_state = self.state.get('state', 'ON')
        
        # 2. Market Data
        try:
            df = self._fetch_spy_data()
            last_close = df['Close'].iloc[-1]
            sma200 = df['Close'].rolling(window=200).mean().iloc[-1]
            is_uptrend = last_close > sma200
            self.logger.info(f"SPY: {last_close:.2f} | SMA200: {sma200:.2f} | Uptrend: {is_uptrend}")
        except Exception as e:
            self.logger.critical("Data fetch failed. Aborting Advisor run.")
            return

        # 3. Logic Evaluation
        today_str = datetime.now().date().isoformat()
        
        # Reset transient fields
        self.state['date'] = today_str
        self.state['event'] = "NO_CHANGE"
        self.state['notes'] = "Routine check."
        
        next_state = current_state

        if current_state == "ON":
            # Update ATH
            ath = self.state.get('ath', 0)
            if self.current_equity > ath:
                ath = self.current_equity
                self.state['ath'] = ath
            
            # Calc Drawdown
            dd = (self.current_equity / ath) - 1 if ath > 0 else 0
            self.state['drawdown'] = dd
            
            self.logger.info(f"State: ON | DD: {dd:.2%} | Limit: -25%")
            
            # TRIGGER: -25%
            if dd <= -0.25:
                next_state = "PAUSED"
                self.state['pause_start_date'] = today_str
                self.state['counters']['days_paused'] = 0
                self.state['counters']['trend_days'] = 0
                self.state['event'] = "PAUSE_TRIGGERED"
                self.state['notes'] = f"Drawdown {dd:.2%} exceeded -25% limit."
                self.logger.warning(self.state['notes'])

        elif current_state == "PAUSED":
            # Increment Counters
            self.state['counters']['days_paused'] += 1
            if is_uptrend:
                self.state['counters']['trend_days'] += 1
            else:
                self.state['counters']['trend_days'] = 0
                
            days_paused = self.state['counters']['days_paused']
            trend_days = self.state['counters']['trend_days']
            
            self.logger.info(f"State: PAUSED | Waited: {days_paused}/30 | Trend: {trend_days}/10")
            
            # TRIGGER: Resume
            if days_paused >= 30 and trend_days >= 10:
                next_state = "ON"
                # Reset ATH on resume
                self.state['ath'] = self.current_equity
                self.state['pause_start_date'] = None
                self.state['counters']['days_paused'] = 0
                self.state['counters']['trend_days'] = 0
                self.state['event'] = "RESUME_TRIGGERED"
                self.state['notes'] = "Scenario B Resume conditions met (30d time + 10d trend)."
                self.logger.warning(self.state['notes'])

        self.state['state'] = next_state
        self._save_state()
        self.logger.info(f"Advisor Run Complete. Final State: {next_state}")

if __name__ == "__main__":
    # Internal test usage or strictly imported
    pass
