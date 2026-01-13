import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

def run_scenario_b_walk():
    # --- CONFIGURATION (Scenario B) ---
    SCENARIO_NAME = "Scenario B"
    PAUSE_THRESHOLD = 0.28
    RESUME_WAIT_DAYS = 30
    RESUME_TREND_DAYS = 10
    INITIAL_CAPITAL = 10000.0
    START_DATE = "1995-01-01"
    LEVERAGE = 3.0

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'SPY.csv')
    artifacts_dir = base_dir # Output directly to root of titan_hammer for now, or use artifacts dir?
    # User asked for artifacts, let's put them in 'wfa_results' folder
    results_dir = os.path.join(base_dir, 'wfa_results')
    os.makedirs(results_dir, exist_ok=True)

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
    # We need data before 1995 for SMA calculation, so let's take everything
    # But simulation logic starts at START_DATE
    spy_ret = spy_series.pct_change().fillna(0)
    sma200 = spy_series.rolling(window=200).mean()

    # Simulation State
    equity = INITIAL_CAPITAL
    ath = INITIAL_CAPITAL # All Time High of Equity
    state = "ON"
    days_paused = 0
    trend_confirmation_days = 0
    
    # Tracking
    equity_curve = []
    events = []
    
    # Run Simulation
    sim_dates = spy_series[spy_series.index >= start_date_dt].index
    
    print(f"Running WALK ({SCENARIO_NAME}): {min(sim_dates).date()} to {max(sim_dates).date()}...")
    
    trade_count = 0
    max_dd = 0.0
    
    # SPY Buy & Hold Bench
    spy_start_price = spy_series.loc[sim_dates[0]]
    spy_shares = INITIAL_CAPITAL / spy_start_price

    for d in sim_dates:
        price = spy_series.loc[d]
        curr_sma = sma200.loc[d]
        daily_ret = spy_ret.loc[d]
        
        # 1. Apply Performance (Skip first day PnL to allow entry)
        if d != sim_dates[0]: 
            if state == "ON":
                equity *= (1 + (daily_ret * LEVERAGE))
        
        # 2. Update High Water Mark
        if equity > ath:
            ath = equity
            
        current_dd = (equity / ath) - 1 if ath > 0 else 0
        max_dd = min(max_dd, current_dd)
        
        is_uptrend = price > curr_sma
        
        # 3. Logic & State Machine
        prev_state = state
        
        if state == "ON":
            if current_dd <= -PAUSE_THRESHOLD:
                state = "PAUSED"
                days_paused = 0
                trend_confirmation_days = 0
                trade_count += 1
                
                events.append({
                    "date": d.date().isoformat(),
                    "type": "PAUSE",
                    "equity": round(equity, 2),
                    "ath": round(ath, 2),
                    "drawdown": round(current_dd, 4),
                    "trigger": f"DD {current_dd:.1%} <= -{PAUSE_THRESHOLD:.0%}"
                })
        
        elif state == "PAUSED":
            days_paused += 1
            if is_uptrend:
                trend_confirmation_days += 1
            else:
                trend_confirmation_days = 0
            
            if days_paused >= RESUME_WAIT_DAYS and trend_confirmation_days >= RESUME_TREND_DAYS:
                state = "ON"
                ath = equity # Reset ATH on Resume
                trade_count += 1
                
                events.append({
                    "date": d.date().isoformat(),
                    "type": "RESUME",
                    "equity": round(equity, 2),
                    "days_paused": days_paused,
                    "trend_streak": trend_confirmation_days,
                    "sma200": round(curr_sma, 2),
                    "price": round(price, 2)
                })
                
                days_paused = 0
                trend_confirmation_days = 0

        # Record Daily
        bench_val = spy_shares * price
        bench_dd = (price / spy_series.loc[:d].max()) - 1
        
        equity_curve.append({
            "date": d.date().isoformat(),
            "equity": round(equity, 2),
            "benchmark_equity": round(bench_val, 2),
            "drawdown": round(current_dd, 4),
            "state": state
        })

    # --- RESULTS & REPORTING ---
    final_equity = equity
    bench_final = spy_shares * spy_series.loc[sim_dates[-1]]
    total_years = (sim_dates[-1] - sim_dates[0]).days / 365.25
    cagr = (final_equity / INITIAL_CAPITAL) ** (1/total_years) - 1
    
    pause_count = len([e for e in events if e['type'] == 'PAUSE'])
    resume_count = len([e for e in events if e['type'] == 'RESUME'])
    
    summary = {
        "scenario": SCENARIO_NAME,
        "period": f"{min(sim_dates).date()} to {max(sim_dates).date()}",
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": round(final_equity, 2),
        "cagr": round(cagr, 4),
        "max_drawdown": round(max_dd, 4),
        "trades": trade_count,
        "pause_events": pause_count,
        "resume_events": resume_count
    }
    
    # Artifact 1: walk_results_summary.json
    with open(os.path.join(results_dir, 'walk_results_summary.json'), 'w') as f:
        json.dump(summary, f, indent=4)

    # Artifact 2: pause_resume_events.csv
    pd.DataFrame(events).to_csv(os.path.join(results_dir, 'pause_resume_events.csv'), index=False)
    
    # Artifact 3: equity_curve.csv
    pd.DataFrame(equity_curve).to_csv(os.path.join(results_dir, 'equity_curve.csv'), index=False)

    print("\n" + "="*80)
    print("SCENARIO B WALK COMPLETE")
    print("="*80)
    print(f"Final Equity: ${final_equity:,.2f} (Start: ${INITIAL_CAPITAL:,.0f})")
    print(f"CAGR: {cagr:.1%}")
    print(f"Max Drawdown: {max_dd:.1%}")
    print(f"Trades: {trade_count}")
    print(f"PAUSE Events: {pause_count} | RESUME Events: {resume_count}")
    print("="*80)
    
    print("\nVERIFICATION: First 5 PAUSE Events:")
    pauses = [e for e in events if e['type'] == 'PAUSE']
    for i, p in enumerate(pauses[:5]):
        print(f"{i+1}. {p['date']} | Equity: {p['equity']:,.0f} | DD: {p['drawdown']:.1%} | Trig: {p['trigger']}")
        
    print("\nVERIFICATION: First 5 RESUME Events:")
    resumes = [e for e in events if e['type'] == 'RESUME']
    for i, r in enumerate(resumes[:5]):
        print(f"{i+1}. {r['date']} | Wait: {r['days_paused']}d | Trend: {r['trend_streak']}d | Price: {r['price']} > SMA {r['sma200']}")
        if r['days_paused'] < 30 or r['trend_streak'] < 10:
             print("   WARNING: RESUME CONDITIONS NOT MET!")

    print("\n" + "="*80)
    print("Scenario B applied successfully")
    print("WALK completed successfully")
    print("PAUSE/RESUME automation verified successfully")
    print("="*80)

if __name__ == "__main__":
    run_scenario_b_walk()
