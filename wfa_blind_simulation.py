import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def run_blind_simulation():
    # Setup Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'SPY.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    # Load Data
    # Format: 3 header lines, then data.
    # Line 0: Price,Close,High,Low,Open,Volume
    # Line 1: Ticker,SPY,SPY,SPY,SPY,SPY
    # Line 2: Date,,,,,
    # Line 3: 1993-01-29...
    try:
        df = pd.read_csv(data_path, skiprows=3, header=None, index_col=0, parse_dates=True)
        # Column 0 is the first data column (Close)
        spy_series = df.iloc[:, 0]
        spy_series.name = "Close"
        spy_series = spy_series.astype(float) # Ensure float
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    spy_series = spy_series.sort_index()
    
    # 2. FILTER START DATE (User Request Alignment)
    # User requested reports starting 2005. Starting in 1993 generated confused large numbers.
    # We will start the "Walk" from 2005-01-01 to ensure the 200k start is clearly strictly for this period.
    start_date = "2005-01-01"
    spy_series = spy_series[spy_series.index >= start_date]

    spy_ret = spy_series.pct_change().fillna(0)
    sma200 = spy_series.rolling(window=200).mean()

    # --- SIMULATION PARAMETERS ---
    initial_capital = 200000.0 # ILS
    upro_leverage = 3.0
    
    equity = initial_capital
    ath = initial_capital
    
    state = "ON"
    days_paused = 0
    trend_confirmation_days = 0
    
    dates = spy_series.index
    
    print(f"Data Loaded. Range: {spy_series.index[0].date()} to {spy_series.index[-1].date()}")

    # --- SIMULATION FUNCTION ---
    def run_period_sim(start_date, end_date):
        # Filter for period
        # We need data slightly before start_date for 200SMA if possible, 
        # but the logic loop calculates SMA on the fly from the full series or pre-calculated?
        # Better: Slice the *results* of indicators, but run logic only on the slice.
        
        period_mask = (dates >= start_date) & (dates < end_date)
        period_dates = dates[period_mask]
        
        if len(period_dates) == 0:
            return None, None
            
        initial_capital = 200000.0
        equity = initial_capital
        ath = initial_capital
        
        # SPY Benchmark for this specific period
        spy_start_price = spy_series.loc[period_dates[0]]
        spy_shares = initial_capital / spy_start_price
        
        state = "ON"
        days_paused = 0
        trend_confirmation_days = 0
        
        for d in period_dates:
            daily_ret = spy_ret.loc[d]
            current_sma = sma200.loc[d]
            current_price = spy_series.loc[d]
            
            # 1. Apply Returns
            if d != period_dates[0]: # Skip first day PnL (buy on open/close of first day)
                if state == "ON":
                    equity *= (1 + (daily_ret * 3.0)) # 3x leverage
            
            # 2. Update High Water Mark
            if equity > ath:
                ath = equity
            
            drawdown = (equity / ath) - 1 if ath > 0 else 0
            
            is_uptrend = (current_price > current_sma)
            
            # 3. Decision Logic
            if state == "ON":
                if drawdown <= -0.25:
                    state = "PAUSED"
                    days_paused = 0
                    trend_confirmation_days = 0
            
            elif state == "PAUSED":
                days_paused += 1
                if is_uptrend:
                    trend_confirmation_days += 1
                else:
                    trend_confirmation_days = 0
                
                if days_paused >= 60 and trend_confirmation_days >= 20:
                    state = "ON"
                    ath = equity
                    days_paused = 0
                    trend_confirmation_days = 0
        
        # Final Stats
        spy_final = spy_shares * spy_series.loc[period_dates[-1]]
        return equity, spy_final


    # --- REPORTING ---
    print("\n" + "=" * 80)
    print("INDEPENDENT 5-YEAR SIMULATIONS (Reset to 200k ILS each block)")
    print("=" * 80)
    header = f"| {'Period':<11} | {'Start Capital':<15} | {'Titan End':<15} | {'Growth':<8} | {'SPY Growth':<10} |"
    print(header)
    print("-" * len(header))
    
    years_5 = [2005, 2010, 2015, 2020, 2025]
    for i in range(len(years_5)-1):
        s_str = f"{years_5[i]}-01-01"
        e_str = f"{years_5[i+1]}-01-01"
        
        # Handle 2025 (check if we have data)
        # Using 2026-01-01 as theoretical end for the 2020-2025 block? 
        # Actually user said "2020-2025", usually implying full years.
        # But our data goes to 2026-01-09. So 2025-01-01 is a valid end for the 2020 block.
        
        titan_res, spy_res = run_period_sim(s_str, e_str)
        
        if titan_res:
            titan_growth = ((titan_res / 200000) - 1) * 100
            spy_growth = ((spy_res / 200000) - 1) * 100
            label = f"{years_5[i]}-{years_5[i+1]}"
            print(f"| {label:<11} | 200,000 ILS     | {titan_res:,.0f} ILS      | {titan_growth:>6.1f}% | {spy_growth:>6.1f}%     |")

    print("\n" + "=" * 80)
    print("INDEPENDENT 10-YEAR SIMULATIONS (Reset to 200k ILS each block)")
    print("=" * 80)
    print(header)
    print("-" * len(header))
    
    years_10 = [2005, 2015, 2025]
    for i in range(len(years_10)-1):
        s_str = f"{years_10[i]}-01-01"
        e_str = f"{years_10[i+1]}-01-01"
        
        titan_res, spy_res = run_period_sim(s_str, e_str)
        
        if titan_res:
            titan_growth = ((titan_res / 200000) - 1) * 100
            spy_growth = ((spy_res / 200000) - 1) * 100
            label = f"{years_10[i]}-{years_10[i+1]}"
            print(f"| {label:<11} | 200,000 ILS     | {titan_res:,.0f} ILS      | {titan_growth:>6.1f}% | {spy_growth:>6.1f}%     |")
    
    print("=" * 80)


if __name__ == "__main__":
    run_blind_simulation()
