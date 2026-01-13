import pandas as pd
import numpy as np
import os
import json
from datetime import timedelta

def run_authentic_walk():
    # Load Data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'SPY.csv')
    
    # Ensure web data dir exists
    web_data_dir = os.path.join(base_dir, '..', 'invis-web', 'public', 'data')
    os.makedirs(web_data_dir, exist_ok=True)
    json_path = os.path.join(web_data_dir, 'backtest_results.json')
    
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    # 1. Robust Data Loading
    try:
        df = pd.read_csv(data_path, index_col=0, parse_dates=True, header=[0, 1])
        if 'Adj Close' in df.columns.get_level_values(0):
            spy_series = df['Adj Close'].iloc[:, 0]
        elif 'Close' in df.columns.get_level_values(0):
            spy_series = df['Close'].iloc[:, 0]
        else:
            spy_series = df.iloc[:, 0]
    except Exception as e:
        try:
            df = pd.read_csv(data_path, skiprows=3, header=None, index_col=0, parse_dates=True)
            spy_series = df.iloc[:, 0]
        except Exception as e2:
            print(f"Fatal error reading data: {e2}")
            return

    spy_series = spy_series.sort_index()
    
    # 2. Pre-calculate Indicators
    spy_ret = spy_series.pct_change().fillna(0)
    sma200 = spy_series.rolling(window=200).mean()
    
    # 3. Simulation Variables
    upro_mult = 3.0
    initial_equity = 10000.0  # User requested 10k
    
    titan_equity = initial_equity
    spy_benchmark_equity = initial_equity
    
    # State
    state = "ACTIVE"
    titan_peak = initial_equity
    spy_peak = initial_equity
    
    # Resume Logic Counters
    days_paused = 0
    consecutive_days_above_ma = 0
    
    # Data Collection
    sim_data = []
    events = []
    
    years_processed = 0
    start_date = spy_series.index[0]
    dates = spy_series.index
    
    # Milestones (Closest available date will be captured)
    milestones = {5: None, 10: None, 15: None, 20: None}
    
    print("Starting Authentic Walk-Forward Simulation...")
    
    # 4. Simulation Loop
    for i in range(len(dates)):
        date = dates[i]
        
        # Track Years for Milestones
        years_elapsed = (date - start_date).days / 365.25
        for m in milestones.keys():
            if milestones[m] is None and years_elapsed >= m:
                milestones[m] = {
                    "Year": m,
                    "Date": str(date.date()),
                    "SPY": spy_benchmark_equity,
                    "Titan": titan_equity,
                    "Delta": titan_equity - spy_benchmark_equity
                }

        # Skip first day for returns
        if i == 0:
            sim_data.append({
                "date": str(date.date()),
                "spy": round(spy_benchmark_equity, 2),
                "titan": round(titan_equity, 2),
                "spy_dd": 0,
                "titan_dd": 0,
                "event": None
            })
            continue
            
        current_spy_price = spy_series.iloc[i]
        current_sma = sma200.iloc[i]
        daily_ret = spy_ret.iloc[i]
        
        # --- BENCHMARK LOGIC (SPY Buy & Hold) ---
        spy_benchmark_equity *= (1 + daily_ret)
        if spy_benchmark_equity > spy_peak:
            spy_peak = spy_benchmark_equity
        spy_dd = (spy_benchmark_equity / spy_peak) - 1
        
        # --- TITAN ENGINE LOGIC ---
        
        # Track MA Trend
        is_above_ma = False
        if pd.notna(current_sma) and current_spy_price > current_sma:
            is_above_ma = True
        
        event_today = None
        
        if state == "ACTIVE":
            # Apply 3x Return
            upro_ret = daily_ret * upro_mult
            titan_equity *= (1 + upro_ret)
            
            # Update Peak
            if titan_equity > titan_peak:
                titan_peak = titan_equity
            
            # Check Drawdown
            titan_dd = (titan_equity / titan_peak) - 1
            
            # PAUSE TRIGGER: -25% Trailing
            if titan_dd <= -0.25:
                state = "PAUSED"
                days_paused = 0
                consecutive_days_above_ma = 0 
                event_today = "PAUSE"
                events.append({
                    "Date": str(date.date()),
                    "Type": "PAUSE",
                    "Equity": titan_equity,
                    "Info": "Hit -25% Trailing"
                })
        
        elif state == "PAUSED":
            # Cash (0% return)
            # titan_equity remains same
            
            # Update Counters
            days_paused += 1
            if is_above_ma:
                consecutive_days_above_ma += 1
            else:
                consecutive_days_above_ma = 0
                
            # RESUME TRIGGER: (Time >= 60) AND (Trend >= 20)
            if days_paused >= 60 and consecutive_days_above_ma >= 20:
                state = "ACTIVE"
                titan_peak = titan_equity # Reset Peak
                event_today = "RESUME"
                events.append({
                    "Date": str(date.date()),
                    "Type": "RESUME",
                    "Equity": titan_equity, 
                    "Info": f"Waited {days_paused} days + 20 days > SMA"
                })
        
        # Store Data
        sim_data.append({
            "date": str(date.date()),
            "spy": round(spy_benchmark_equity, 2),
            "titan": round(titan_equity, 2),
            "spy_dd": round(spy_dd, 4),
            "state": state,
            "event": event_today
        })

    # Catch end-of-period milestones if not hit (e.g. strict 20th year)
    final_years = (dates[-1] - start_date).days / 365.25
    if final_years >= 20 and milestones[20] is None:
         milestones[20] = {
            "Year": 20,
            "Date": str(dates[-1].date()),
            "SPY": spy_benchmark_equity,
            "Titan": titan_equity,
            "Delta": titan_equity - spy_benchmark_equity
        }

    # Prepare Final Report
    final_output = {
        "metadata": {
            "period": f"{dates[0].date()} to {dates[-1].date()}",
            "years": round(final_years, 2),
            "initial_investment": initial_equity
        },
        "stats": {
            "spy_final": round(spy_benchmark_equity, 2),
            "titan_final": round(titan_equity, 2),
            "spy_cagr": round(((spy_benchmark_equity/initial_equity)**(1/final_years) - 1) * 100, 2),
            "titan_cagr": round(((titan_equity/initial_equity)**(1/final_years) - 1) * 100, 2)
        },
        "milestones": milestones,
        "events": events,
        "history": sim_data
    }
    
    with open(json_path, 'w') as f:
        json.dump(final_output, f, indent=2)
        
    print(f"Simulation Complete. Data exported to {json_path}")
    print(f"Final Titan: ${titan_equity:,.2f}")
    print(f"Final SPY: ${spy_benchmark_equity:,.2f}")

    # Count Pauses
    pause_count = len([e for e in events if e['Type'] == 'PAUSE'])
    print("-" * 50)
    print(f"Total PAUSE Events: {pause_count}")
    print("-" * 50)
    print("Milestones (Year | SPY | Titan):")
    for m in [5, 10, 15, 20]:
        if milestones[m]:
            print(f"Year {m:<2} | ${milestones[m]['SPY']:<10,.0f} | ${milestones[m]['Titan']:<10,.0f}")
    print("-" * 50)

if __name__ == "__main__":
    run_authentic_walk()
