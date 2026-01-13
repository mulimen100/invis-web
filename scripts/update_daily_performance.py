import json
import os
import datetime
import yfinance as yf

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # titan_hammer/
WEB_DATA_PATH = os.path.join(os.path.dirname(BASE_DIR), 'invis-web', 'public', 'data', 'backtest_results.json')
ENGINE_STATE_PATH = os.path.join(BASE_DIR, 'state', 'engine_state.json')

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    print(f">>> START: Logging Daily Performance")
    
    # 1. Load Data
    history_data = load_json(WEB_DATA_PATH)
    engine_state = load_json(ENGINE_STATE_PATH)
    
    if not history_data or 'history' not in history_data:
        print("ERROR: Could not load valid backtest_results.json")
        return

    # 2. Get Current Date and Data
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # Check if we already logged today
    last_entry = history_data['history'][-1]
    if last_entry['date'] == today_str:
        print(f"INFO: Already logged for today ({today_str}). Updating existing entry.")
        # We will overwrite the last entry if needed, but for now let's just warn and exit or update?
        # Let's update it to support re-runs.
        pass
    
    # Fetch SPY Live Price for accurate Index tracking
    # Ideally we should simulate the "Hold SPY" strategy
    # The 'spy' field in history tracks $10,000 investment in SPY from '93
    # We need to calculate the % change from yesterday to update it correctly.
    
    # Get Yesterday's SPY Price
    # This is tricky without a dedicated price DB.
    # Alternative: Use yfinance to get today's close and prev close.
    try:
        spy_ticker = yf.Ticker("SPY")
        hist = spy_ticker.history(period="5d") # Get last few days
        if len(hist) < 2:
            print("WARNING: Not enough market data to calculate SPY change. Using 0%.")
            spy_pct_change = 0
        else:
            # We want change from Prev Close to Current (or Close)
            # If run at night 23:05, market is closed.
            today_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            spy_pct_change = (today_close - prev_close) / prev_close
            print(f"INFO: SPY Change: {spy_pct_change:.2%}")

    except Exception as e:
        print(f"ERROR Fetching SPY: {e}")
        spy_pct_change = 0

    # Calculate New SPY Equity
    # If overwriting today, we need yesterday's value. 
    # If appending, use last_entry.
    if last_entry['date'] == today_str:
        # Get yesterday's entry to calc change from
        prev_entry = history_data['history'][-2]
        new_spy_equity = prev_entry['spy'] * (1 + spy_pct_change)
    else:
        new_spy_equity = last_entry['spy'] * (1 + spy_pct_change)
        
    # --- PAPER TRADING SIMULATION ---
    # Determine Leverage
    current_state = engine_state.get('state', 'ON')
    leverage = 3.0 if current_state == 'ON' else 0.0 # 3x UPRO or Cash
    
    # Calculate Titan Change
    # UPRO approx = 3 * SPY change (ignoring fees/drag for simplicity)
    titan_pct_change = spy_pct_change * leverage
    
    # Get Previous Equity
    if last_entry['date'] == today_str:
        prev_titan_equity = history_data['history'][-2]['titan']
    else:
        prev_titan_equity = last_entry['titan']

    # Update Equity
    new_titan_equity = prev_titan_equity * (1 + titan_pct_change)
    
    print(f"INFO: Simulation - State: {current_state} | Leverage: {leverage}x | SPY: {spy_pct_change:.2%} | Titan: {titan_pct_change:.2%}")
    print(f"INFO: Equity Update - Prev: ${prev_titan_equity:,.2f} -> New: ${new_titan_equity:,.2f}")

    # Update Engine State with new Equity for next run
    engine_state['equity'] = new_titan_equity
    # Also update ATH/Drawdown if needed, but AdvisorEngine handles that on next run
    try:
        save_json(ENGINE_STATE_PATH, engine_state)
        print("SUCCESS: Updated engine_state.json with new simulated equity.")
    except Exception as e:
        print(f"ERROR: Failed to update engine_state.json: {e}")

    # 3. Create Entry
    daily_entry = {
        "date": today_str,
        "spy": new_spy_equity,
        "titan": new_titan_equity,
        "spy_dd": 0, # Simplify or calc real DD if needed
        "state": current_state,
        "event": engine_state.get('event', None)
    }
    
    # 4. Append or Update
    if last_entry['date'] == today_str:
        history_data['history'][-1] = daily_entry
    else:
        history_data['history'].append(daily_entry)
        
    # Update Stats Summary
    history_data['stats']['spy_final'] = new_spy_equity
    history_data['stats']['titan_final'] = new_titan_equity
    
    # 5. Save
    save_json(WEB_DATA_PATH, history_data)
    print(f"SUCCESS: Logged {today_str} | Titan: ${new_titan_equity:,.0f} | SPY: ${new_spy_equity:,.0f}")

if __name__ == "__main__":
    main()
