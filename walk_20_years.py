import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

def run_20_year_backtest():
    # --- CONFIGURATION (Scenario B) ---
    SCENARIO_NAME = "Scenario B (20 Years)"
    PAUSE_THRESHOLD = 0.28
    RESUME_WAIT_DAYS = 30
    RESUME_TREND_DAYS = 10
    INITIAL_CAPITAL = 10000.0
    START_DATE = "2005-01-01"
    LEVERAGE = 3.0

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'SPY.csv')
    
    # Target Output for Frontend
    # i:\INVIS SPY\invis-web\public\data\backtest_results.json
    # Assuming valid path relative to this script
    web_data_dir = os.path.join(base_dir, '..', 'invis-web', 'public', 'data')
    os.makedirs(web_data_dir, exist_ok=True)
    output_path = os.path.join(web_data_dir, 'backtest_results.json')

    print(f"Loading Data from {data_path}...")
    try:
        df = pd.read_csv(data_path, skiprows=3, header=None, index_col=0, parse_dates=True)
        spy_series = df.iloc[:, 0]
        spy_series.name = "Close"
        spy_series = spy_series.astype(float)
        spy_series = spy_series.sort_index()
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Filter Data
    start_date_dt = pd.Timestamp(START_DATE)
    spy_ret = spy_series.pct_change().fillna(0)
    sma200 = spy_series.rolling(window=200).mean()

    # Simulation State
    equity = INITIAL_CAPITAL
    ath = INITIAL_CAPITAL
    state = "ON"
    days_paused = 0
    trend_confirmation_days = 0
    
    # Tracking
    history = []
    events_list = []
    
    # Run Simulation
    sim_dates = spy_series[spy_series.index >= start_date_dt].index
    print(f"Running 20-Year WALK: {min(sim_dates).date()} to {max(sim_dates).date()}...")
    
    trade_count = 0
    
    # SPY Benchmark
    spy_start_price = spy_series.loc[sim_dates[0]]
    spy_shares = INITIAL_CAPITAL / spy_start_price

    for d in sim_dates:
        price = spy_series.loc[d]
        curr_sma = sma200.loc[d]
        daily_ret = spy_ret.loc[d]
        
        # 1. Apply Performance (Skip first day)
        if d != sim_dates[0]: 
            if state == "ON":
                equity *= (1 + (daily_ret * LEVERAGE))
        
        # 2. Update ATH
        if equity > ath:
            ath = equity
            
        current_dd = (equity / ath) - 1 if ath > 0 else 0
        
        is_uptrend = price > curr_sma
        
        # 3. Logic & State Machine
        event_type = None
        event_info = None

        if state == "ON":
            if current_dd <= -PAUSE_THRESHOLD:
                state = "PAUSED"
                days_paused = 0
                trend_confirmation_days = 0
                trade_count += 1
                
                event_type = "PAUSE"
                event_info = f"DD {current_dd:.1%} (Limit -{PAUSE_THRESHOLD:.0%})"
        
        elif state == "PAUSED":
            days_paused += 1
            if is_uptrend:
                trend_confirmation_days += 1
            else:
                trend_confirmation_days = 0
            
            if days_paused >= RESUME_WAIT_DAYS and trend_confirmation_days >= RESUME_TREND_DAYS:
                state = "ON"
                ath = equity
                trade_count += 1
                
                event_type = "RESUME"
                event_info = f"Wait {days_paused}d + Trend {trend_confirmation_days}d"
                
                days_paused = 0
                trend_confirmation_days = 0

        # Record Data
        bench_val = spy_shares * price
        
        # Daily History Point
        history.append({
            "date": d.strftime("%Y-%m-%d"),
            "spy": round(bench_val, 2),
            "titan": round(equity, 2),
            "state": state,
            "event": event_type
        })
        
        if event_type:
            events_list.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Type": event_type,
                "Equity": round(equity, 2),
                "Info": event_info
            })

    # --- FINAL CALCULATIONS ---
    final_equity = equity
    bench_final = spy_shares * spy_series.loc[sim_dates[-1]]
    total_years = (sim_dates[-1] - sim_dates[0]).days / 365.25
    cagr_titan = (final_equity / INITIAL_CAPITAL) ** (1/total_years) - 1
    cagr_spy = (bench_final / INITIAL_CAPITAL) ** (1/total_years) - 1
    
    # Snapshots for Milestones Table (5, 10, 15, 20 years)
    milestones = {}
    years_to_check = [5, 10, 15, 20]
    
    start_year = sim_dates[0].year
    
    # We will approximate by finding the date closest to StartYear + N
    # Since 'history' list corresponds to 'sim_dates', we can search there.
    for y in years_to_check:
        target_year = start_year + y
        # Find last entry of that year or closest
        # Better: Find the entry where date is closest to 'target_year-01-01'? 
        # Actually user wants "After 5 years", "After 10 years"
        
        # Simple approach: Find row where year == target_year. Take last day of that year.
        candidates = [h for h in history if h['date'].startswith(str(target_year))]
        if candidates:
            # Take year-end value
            snap = candidates[-1]
            milestones[str(y)] = {
                "Year": target_year,
                "Date": snap['date'],
                "SPY": snap['spy'],
                "Titan": snap['titan'],
                "Delta": snap['titan'] - snap['spy']
            }
        else:
            # If we haven't reached 20 years yet (e.g. 2025 is year 20 exactly)
            # Check if we passed it.
            # If target_year > last_sim_year, maybe we just take the very last available?
            # Or omit.
            if target_year <= sim_dates[-1].year:
                # Could capture if start date was mid-year.
                pass

    # JSON Structure
    output_data = {
        "metadata": {
            "period": f"{sim_dates[0].date()} to {sim_dates[-1].date()}",
            "years": round(total_years, 1),
            "initial_investment": INITIAL_CAPITAL
        },
        "stats": {
            "spy_final": round(bench_final, 2),
            "titan_final": round(final_equity, 2),
            "spy_cagr": round(cagr_spy * 100, 2),
            "titan_cagr": round(cagr_titan * 100, 2)
        },
        "milestones": milestones,
        "events": events_list,
        "history": history
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)

    print("\n" + "="*80)
    print("BACKTEST DATA GENERATED")
    print(f"Output: {output_path}")
    print(f"Titan Final: ${final_equity:,.2f}")
    print(f"SPY Final: ${bench_final:,.2f}")
    print("="*80)

if __name__ == "__main__":
    run_20_year_backtest()
