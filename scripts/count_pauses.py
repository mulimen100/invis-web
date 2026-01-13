
import pandas as pd
import numpy as np
import os

def count_pauses():
    # Setup Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'SPY.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    # Load Data
    try:
        df = pd.read_csv(data_path, skiprows=3, header=None, index_col=0, parse_dates=True)
        spy_series = df.iloc[:, 0]
        spy_series.name = "Close"
        spy_series = spy_series.astype(float)
        spy_series = spy_series.sort_index()
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Filter Start Date (2005-2025 like in WFA)
    start_date = "1995-01-01" # Going back further to see longer history if available, but user asked for 30 years
    # 30 years from 2026 is 1996. Let's try to get as much as possible.
    spy_series = spy_series[spy_series.index >= start_date]

    if spy_series.empty:
        print("No data found for the date range.")
        return

    sma200 = spy_series.rolling(window=200).mean()

    # Simulation State
    initial_capital = 200000.0
    equity = initial_capital
    ath = initial_capital
    
    state = "ON"
    days_paused = 0
    trend_confirmation_days = 0
    
    pause_events = []
    
    print(f"Analyzing from {spy_series.index[0].date()} to {spy_series.index[-1].date()}")
    
    for d in spy_series.index:
        current_sma = sma200.loc[d]
        current_price = spy_series.loc[d]
        
        # We need to simulate equity to get drawdown
        # BUT wait, the rule is based on "Score -25". 
        # In wfa_blind_simulation.py: drawdown = (equity / ath) - 1
        # This implies the PAUSE is based on STRATEGY DRAWDOWN, not just SPY drawdown?
        # Let's check wfa_blind_simulation.py again.
        # Yes: equity *= (1 + (daily_ret * 3.0)) if state == "ON"
        # drawdown = (equity / ath) - 1
        # if drawdown <= -0.25: state = "PAUSED"
        
        # So I need to simulate the returns to trigger the pause.
        
        daily_ret = spy_series.pct_change().loc[d]
        if np.isnan(daily_ret): daily_ret = 0.0

        if state == "ON":
            equity *= (1 + (daily_ret * 3.0))
            if equity > ath:
                ath = equity
            
            drawdown = (equity / ath) - 1 if ath > 0 else 0
            
            if drawdown <= -0.25:
                state = "PAUSED"
                days_paused = 0
                trend_confirmation_days = 0
                pause_events.append({"date": d, "equity": equity, "drawdown": drawdown})
        
        elif state == "PAUSED":
            # Apply 0 return (cash)
            # Check Resume Condition
            is_uptrend = (current_price > current_sma)
            days_paused += 1
            if is_uptrend:
                trend_confirmation_days += 1
            else:
                trend_confirmation_days = 0
            
            if days_paused >= 60 and trend_confirmation_days >= 20:
                state = "ON"
                ath = equity # Reset ATH on resume? 
                # In wfa_blind_simulation.py: ath = equity. 
                # This is CRITICAL. It resets ATH, meaning drawdown resets to 0.
                days_paused = 0
                trend_confirmation_days = 0

    print(f"\nTotal PAUSE Events: {len(pause_events)}")
    print("\nEvent List:")
    for i, event in enumerate(pause_events):
        print(f"{i+1}. {event['date'].date()} | Drawdown: {event['drawdown']*100:.2f}% | Equity: {event['equity']:.2f}")

    years = (spy_series.index[-1] - spy_series.index[0]).days / 365.25
    print(f"\nAverage PAUSE events per year: {len(pause_events) / years:.2f}")

if __name__ == "__main__":
    count_pauses()
