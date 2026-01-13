import pandas as pd
import numpy as np
import os

def run_walk_trailing():
    # Load Data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'SPY.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    # 1. Robust Data Loading (Same as walk_test.py fix)
    try:
        # YFinance uses a multi-level header (Row 0: Price Type, Row 1: Ticker)
        df = pd.read_csv(data_path, index_col=0, parse_dates=True, header=[0, 1])
        
        # Check standard names
        if 'Adj Close' in df.columns.get_level_values(0):
            spy_series = df['Adj Close'].iloc[:, 0]
        elif 'Close' in df.columns.get_level_values(0):
            spy_series = df['Close'].iloc[:, 0]
        else:
            print("Warning: Could not identify Close/Adj Close. Using first column.")
            spy_series = df.iloc[:, 0]
            
    except Exception as e:
        print(f"Error reading CSV with MultiIndex: {e}")
        try:
            df = pd.read_csv(data_path, skiprows=3, header=None, index_col=0, parse_dates=True)
            spy_series = df.iloc[:, 0]
            print("Fallback successful: Read raw data skipping headers.")
        except Exception as e2:
            print(f"Fatal error reading data: {e2}")
            return

    spy_series = spy_series.sort_index()
    
    # 2. Pre-calculate Indicators
    spy_ret = spy_series.pct_change().fillna(0)
    sma200 = spy_series.rolling(window=200).mean()
    
    # 3. Simulation Variables
    upro_mult = 3.0
    initial_equity = 10000.0
    equity = initial_equity
    
    # State
    state = "ACTIVE" # ACTIVE or PAUSED
    peak_equity = initial_equity # High Water Mark since last resume
    
    # Tracking
    equity_curve = []
    events = []
    
    dates = spy_series.index
    
    # 4. Simulation Loop
    for i in range(len(dates)):
        date = dates[i]
        
        # Skip first day (no return) or logic check
        if i == 0:
            equity_curve.append(equity)
            continue
            
        current_spy_price = spy_series.iloc[i]
        current_sma = sma200.iloc[i]
        daily_ret = spy_ret.iloc[i]
        
        if state == "ACTIVE":
            # Apply 3x Return
            upro_ret = daily_ret * upro_mult
            equity = equity * (1 + upro_ret)
            
            # Update Peak (High Water Mark logic for Trailing Pause)
            if equity > peak_equity:
                peak_equity = equity
            
            # Check Drawdown
            dd = (equity / peak_equity) - 1
            
            # PAUSE TRIGGER: -25% Trailing
            if dd <= -0.25:
                state = "PAUSED"
                events.append({
                    "Date": date,
                    "Type": "PAUSE",
                    "Equity": equity, 
                    "Peak": peak_equity, 
                    "Drawdown": dd,
                    "Info": "Hit -25% Trailing"
                })
        
        elif state == "PAUSED":
            # Apply 0% Return (Cash)
            # equity unchanged
            
            # RESUME TRIGGER: SPY > SMA200
            # Note: We check if TODAY's close > SMA. Resume NEXT day (effectively immediate for sim step).
            if pd.notna(current_sma) and current_spy_price > current_sma:
                state = "ACTIVE"
                # RESET PEAK on Resume (The blueprint says: "Reset ATH to current portfolio value")
                peak_equity = equity 
                events.append({
                    "Date": date,
                    "Type": "RESUME",
                    "Equity": equity,
                    "Peak": peak_equity,
                    "Drawdown": 0.0,
                    "Info": "SPY > SMA200"
                })

        equity_curve.append(equity)

    # 5. Metrics Calculation
    equity_series = pd.Series(equity_curve, index=dates)
    
    final_equity = equity_series.iloc[-1]
    years = (dates[-1] - dates[0]).days / 365.25
    cagr = (final_equity / initial_equity) ** (1 / years) - 1
    
    # Max Drawdown
    rolling_peak = equity_series.cummax()
    dd_series = (equity_series - rolling_peak) / rolling_peak
    max_dd = dd_series.min()
    
    # Pause Stats
    pause_count = len([e for e in events if e['Type'] == 'PAUSE'])
    
    # Compare against Baseline (Pure 3x) - Recalculate roughly for instant comparison
    # (Or just trust previous run, but better to re-compute in same script for exact alignment)
    base_cum = (1 + spy_ret * 3.0).cumprod() * initial_equity
    base_final = base_cum.iloc[-1]
    base_cagr = (base_final / initial_equity) ** (1 / years) - 1
    base_peak = base_cum.cummax()
    base_dd = ((base_cum - base_peak) / base_peak).min()

    # SPY 1x
    spy_cum = (1 + spy_ret).cumprod() * initial_equity
    spy_final = spy_cum.iloc[-1]
    spy_cagr = (spy_final / initial_equity) ** (1 / years) - 1
    spy_peak = spy_cum.cummax()
    spy_dd = ((spy_cum - spy_peak) / spy_peak).min()

    # Reporting
    print("-" * 65)
    print("TITAN HAMMER - WALK TEST (TRAILING PAUSE 25%)")
    print("-" * 65)
    print(f"Period: {dates[0].date()} to {dates[-1].date()} ({years:.1f} years)")
    print(f"Resume Logic: SPY > SMA200")
    print("-" * 65)
    print(f"{'Metric':<15} | {'SPY (1x)':<15} | {'TITAN 3x (Base)':<15} | {'TITAN PAUSE':<15}")
    print("-" * 65)
    print(f"{'Final ($)':<15} | ${spy_final:<14,.0f} | ${base_final:<14,.0f} | ${final_equity:<14,.0f}")
    print(f"{'CAGR':<15} | {spy_cagr:.2%}           | {base_cagr:.2%}           | {cagr:.2%}")
    print(f"{'Max Drawdown':<15} | {spy_dd:.2%}          | {base_dd:.2%}          | {max_dd:.2%}")
    print(f"{'Trades/Pauses':<15} | {'-':<15} | {'0':<15} | {pause_count}")
    print("-" * 65)

    print("\nEvent Log (Last 10 Events):")
    for e in events[-10:]:
        print(f"{e['Date'].date()} [{e['Type']:<6}] Eq: ${e['Equity']:<10,.0f} DD: {e['Drawdown']:<7.2%} Info: {e['Info']}")

    # Save Log
    log_path = os.path.join(base_dir, 'logs', 'walk_test_trailing_results.txt')
    with open(log_path, 'w') as f:
        f.write("TITAN HAMMER - WALK TEST (TRAILING PAUSE 25%)\n")
        f.write(f"Final: ${final_equity:,.0f}\n")
        f.write(f"CAGR: {cagr:.2%}\n")
        f.write(f"MaxDD: {max_dd:.2%}\n")
        f.write(f"Pauses: {pause_count}\n")
        f.write("-" * 20 + "\n")
        f.write("Events:\n")
        for e in events:
             f.write(f"{e['Date'].date()} {e['Type']} ${e['Equity']:.0f} {e['Drawdown']:.2%} {e['Info']}\n")

if __name__ == "__main__":
    run_walk_trailing()
