import sys
import os
import json
import unittest
from unittest.mock import MagicMock

# Add engine to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine'))
from advisor_engine import AdvisorEngine

class TestAdvisorLogic(unittest.TestCase):
    def setUp(self):
        self.state_path = "test_state.json"
        # Create a dummy state
        self.initial_state = {
            "date": "2026-01-12",
            "state": "PAUSED",
            "ath": 10000.0,
            "drawdown": -0.30,
            "pause_start_date": "2025-12-12",
            "counters": {
                "days_paused": 0,
                "trend_days": 0
            },
            "event": "NO_CHANGE",
            "notes": "Initialized."
        }
        with open(self.state_path, 'w') as f:
            json.dump(self.initial_state, f)

    def tearDown(self):
        if os.path.exists(self.state_path):
            os.remove(self.state_path)

    def test_resume_condition_met(self):
        # Scenario: 30 days paused, 10 days trend -> SHOULD RESUME (Scenario B)
        engine = AdvisorEngine(self.state_path, current_equity=10000)
        engine.state['counters']['days_paused'] = 30
        engine.state['counters']['trend_days'] = 10
        
        # Mock fetch_spy_data to return uptrend
        engine._fetch_spy_data = MagicMock()
        engine._fetch_spy_data.return_value = None # We mock the logic usage of it
        # The logic uses locally calc'd variables for last_close > sma200
        # actually advisor_engine calls _fetch_spy_data then calcs is_uptrend
        # We need to mock _fetch_spy_data to return a DF that produces uptrend
        
        # Easier: Just verify the logic block for RESUME
        # But wait, logic block is inside run().
        
        # Let's bypass the data fetch part by mocking the data fetch AND the logging
        # We will manually set state and call the specific logic block? 
        # No, run() is monolithic.
        # Let's mock _fetch_spy_data to return a valid dataframe
        import pandas as pd
        df = pd.DataFrame({'Close': [100.0]*200})
        df.iloc[-1, 0] = 110.0 # Price 110, SMA 100 -> Uptrend
        
        engine._fetch_spy_data = MagicMock(return_value=df)
        engine.logger = MagicMock()
        
        engine.run()
        
        # Assertions
        self.assertEqual(engine.state['state'], 'ON', "Engine should have RESUMED at 30d/10d")
        self.assertEqual(engine.state['event'], 'RESUME_TRIGGERED')

    def test_resume_condition_not_met_trend(self):
        # Scenario: 30 days paused, 8 days trend -> SHOULD STAY PAUSED
        engine = AdvisorEngine(self.state_path, current_equity=10000)
        engine.state['counters']['days_paused'] = 30
        engine.state['counters']['trend_days'] = 8 # < 10 (will become 9)
        
        # Mock Uptrend
        import pandas as pd
        df = pd.DataFrame({'Close': [100.0]*200})
        df.iloc[-1, 0] = 110.0 
        
        engine._fetch_spy_data = MagicMock(return_value=df)
        engine.logger = MagicMock()
        
        engine.run()
        
        self.assertEqual(engine.state['state'], 'PAUSED', "Engine should stay PAUSED if trend < 10")

    def test_resume_condition_not_met_time(self):
        # Scenario: 28 days paused, 10 days trend -> SHOULD STAY PAUSED
        engine = AdvisorEngine(self.state_path, current_equity=10000)
        engine.state['counters']['days_paused'] = 28 # Will become 29
        engine.state['counters']['trend_days'] = 10
        
        import pandas as pd
        df = pd.DataFrame({'Close': [100.0]*200})
        df.iloc[-1, 0] = 110.0 
        
        engine._fetch_spy_data = MagicMock(return_value=df)
        engine.logger = MagicMock()
        
        engine.run()
        
        self.assertEqual(engine.state['state'], 'PAUSED', "Engine should stay PAUSED if days_paused < 30")


if __name__ == '__main__':
    unittest.main()
