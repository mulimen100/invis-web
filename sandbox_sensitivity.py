import pandas as pd
import numpy as np
import os
from datetime import datetime

def run_sensitivity_test():
    # --- SETUP DATA ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'SPY.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    print("Loading Data...")
    try:
        # Load Data (Format matches wfa_blind_simulation.py)
        df = pd.read_csv(data_path, skiprows=3, header=None, index_col=0, parse_dates=True)
        spy_series = df.iloc[:, 0] # Close is col 0
        spy_series.name = "Close"
        spy_series = spy_series.astype(float)
        spy_series = spy_series.sort_index()
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Filter for 30 Years (approx 1995)
    start_date = "1994-01-01" # Start a bit early to have 200SMA ready by 1995
    spy_series = spy_series[spy_series.index >= start_date]
    
    spy_ret = spy_series.pct_change().fillna(0)
    sma200 = spy_series.rolling(window=200).mean()

    # Define Simulation Window (Actual Trading Start)
    sim_start = "1995-01-01"
    
    # Common Params
    initial_capital = 10000.0 # User requested 10k
    upro_leverage = 3.0

    # Scenarios to Test
    scenarios = [
        {"name": "BASELINE (Original)", "pause": 0.25, "wait": 60, "trend": 20},
        {"name": "TEST A (Lo/Short)",   "pause": 0.22, "wait": 30, "trend": 10},
        {"name": "TEST B (Hi/Short)",   "pause": 0.28, "wait": 30, "trend": 10},
        # Optional: Mixes to isolate variables if needed
        {"name": "VAR C (Orig/Short)",  "pause": 0.25, "wait": 30, "trend": 10}, 
    ]

    print(f"\n{'='*100}")
    print(f"SENSITIVITY ANALYSIS (SANDBOX) | Start: {sim_start} | Initial Capital: {initial_capital:,.0f} ILS")
    print(f"{'='*100}")
    print(f"| {'Scenario':<20} | {'Pause':<6} | {'Resume':<8} | {'Final Equity':<15} | {'CAGR':<6} | {'MaxDD':<7} | {'Trades':<6} |")
    print(f"{'-'*100}")

    for scen in scenarios:
        equity = initial_capital
        ath = initial_capital
        
        state = "ON"
        days_paused = 0
        trend_confirmation_days = 0
        
        trade_count = 0
        max_dd_hit = 0.0
        
        # Slicing for simulation period
        sim_mask = spy_series.index >= sim_start
        # We assume data goes up to present
        sim_dates = spy_series.index[sim_mask]
        
        # Pre-calc daily logic loop
        for d in sim_dates:
            daily_ret = spy_ret.loc[d]
            current_sma = sma200.loc[d]
            current_price = spy_series.loc[d]
            
            # --- 1. Apply Returns first (if ON) ---
            if d != sim_dates[0]: # Skip first day PnL
                if state == "ON":
                    equity *= (1 + (daily_ret * upro_leverage))
            
            # --- 2. Update High Water Mark & DD ---
            if equity > ath:
                ath = equity
            
            drawdown = (equity / ath) - 1 if ath > 0 else 0
            max_dd_hit = min(max_dd_hit, drawdown)
            
            is_uptrend = (current_price > current_sma)
            
            # --- 3. Engine Logic (End of Day) ---
            if state == "ON":
                if drawdown <= -(scen["pause"]):
                    state = "PAUSED"
                    days_paused = 0
                    trend_confirmation_days = 0
                    trade_count += 1 # Count a "Sell"
            
            elif state == "PAUSED":
                days_paused += 1
                if is_uptrend:
                    trend_confirmation_days += 1
                else:
                    trend_confirmation_days = 0 # Trend must be consecutive? 
                    # Original logic: "if is_uptrend: trend_days+=1 else: trend_days=0"
                    # Yes, strict consecutive days above SMA.
                
                if days_paused >= scen["wait"] and trend_confirmation_days >= scen["trend"]:
                    state = "ON"
                    ath = equity # Reset ATH on re-entry (Standard Titan logic)
                    days_paused = 0
                    trend_confirmation_days = 0
                    trade_count += 1 # Count a "Buy"

        # Calc Stats
        years = (sim_dates[-1] - sim_dates[0]).days / 365.25
        cagr = (equity / initial_capital) ** (1 / years) - 1 if equity > 0 else -1
        
        resume_str = f"{scen['wait']}+{scen['trend']}"
        print(f"| {scen['name']:<20} | {scen['pause']:<6.0%} | {resume_str:<8} | {equity:,.0f} ILS      | {cagr:>6.1%} | {max_dd_hit:>7.1%} | {trade_count:<6} |")

    print(f"{'-'*100}")
    
    # SPY Buy & Hold for comparison
    spy_start = spy_series.loc[sim_dates[0]]
    spy_end = spy_series.loc[sim_dates[-1]]
    spy_hold_equity = initial_capital * (spy_end / spy_start)
    spy_cagr = (spy_hold_equity / initial_capital) ** (1 / years) - 1
    
    print(f"| {'SPY Buy & Hold':<20} | {'N/A':<6} | {'N/A':<8} | {spy_hold_equity:,.0f} ILS      | {spy_cagr:>6.1%} | {'N/A':>7} | {'0':<6} |")
    print(f"{'='*100}")

if __name__ == "__main__":
    run_sensitivity_test()
