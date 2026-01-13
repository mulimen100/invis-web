import pandas as pd
import numpy as np
import os
from datetime import timedelta

def run_simulation_logic(spy_series):
    """
    Runs the Titan Hammer logic on a given SPY price series.
    Returns:
        equity_series (pd.Series): Daily equity curve
        spy_buy_hold_series (pd.Series): SPY Buy & Hold equity curve (normalized to initial equity)
        pause_events (list): List of pause events
    """
    # Parameters
    upro_mult = 3.0
    initial_equity = 10000.0
    
    # Data Prep
    spy_ret = spy_series.pct_change().fillna(0)
    sma200 = spy_series.rolling(window=200).mean()
    
    # State tracking
    equity = initial_equity
    peak_equity = initial_equity
    state = "ACTIVE"
    
    # Resume Logic Counters
    days_paused = 0
    consecutive_days_above_ma = 0
    
    equity_curve = []
    events = []
    
    dates = spy_series.index
    
    # Main Loop
    for i in range(len(dates)):
        date = dates[i]
        
        # On day 0, performance is flat
        if i == 0:
            equity_curve.append(equity)
            continue
            
        # Market Data
        current_spy_price = spy_series.iloc[i]
        current_sma = sma200.iloc[i]
        daily_ret = spy_ret.iloc[i]
        
        # Trend Status
        is_above_ma = False
        if pd.notna(current_sma) and current_spy_price > current_sma:
            is_above_ma = True
            
        # Strategy Logic
        if state == "ACTIVE":
            # 3x Exposure
            upro_ret = daily_ret * upro_mult
            equity = equity * (1 + upro_ret)
            
            # Update Peak
            if equity > peak_equity:
                peak_equity = equity
            
            # Check Drawdown
            if peak_equity > 0:
                dd = (equity / peak_equity) - 1
            else:
                dd = 0.0
                
            # Trailing Stop Trigger
            if dd <= -0.25:
                state = "PAUSED"
                days_paused = 0
                consecutive_days_above_ma = 0
                events.append({"Date": date, "Type": "PAUSE", "DD": dd})
                
        elif state == "PAUSED":
            # Cash (0% return)
            # equity stays same
            days_paused += 1
            
            if is_above_ma:
                consecutive_days_above_ma += 1
            else:
                consecutive_days_above_ma = 0
                
            # Resume Trigger: 60 days wait AND 20 days > SMA
            if days_paused >= 60 and consecutive_days_above_ma >= 20:
                state = "ACTIVE"
                peak_equity = equity # Reset peak on resume
                events.append({"Date": date, "Type": "RESUME", "DD": 0.0})
        
        equity_curve.append(equity)
        
    equity_series = pd.Series(equity_curve, index=dates)
    
    # SPY Buy & Hold (normalized)
    spy_normalized = (spy_series / spy_series.iloc[0]) * initial_equity
    
    return equity_series, spy_normalized, events

def calculate_stats(series):
    if len(series) < 2:
        return 0.0, 0.0
        
    # CAGR
    total_ret = (series.iloc[-1] / series.iloc[0]) - 1
    days = (series.index[-1] - series.index[0]).days
    if days > 0:
        cagr = (1 + total_ret) ** (365.25 / days) - 1
    else:
        cagr = 0.0
        
    # Max DD
    rolling_peak = series.cummax()
    dd_series = (series - rolling_peak) / rolling_peak
    max_dd = dd_series.min()
    
    return cagr, max_dd

def get_yearly_stats(series):
    """
    Returns a DataFrame with Year, Return, MaxDD
    """
    yearly_res = series.resample('Y').last()
    
    stats_list = []
    
    for year_end_date in yearly_res.index:
        year = year_end_date.year
        # Get data for this year
        year_data = series[series.index.year == year]
        
        if len(year_data) == 0:
            continue
            
        # Calculate Return
        # We need the last price of previous year to calc return accurately, 
        # or the first price of this year if it's the start.
        # Ideally: (End Price / Start of Year Price) - 1 ??
        # Or more accurately: (End Price / Last Price of Prev Year) - 1
        
        # Find start reference
        start_date = pd.Timestamp(f"{year}-01-01")
        # Get data just before this year to link returns?
        # Simpler: (Last value of year / First value of year) - 1  <-- approximates
        # Better: Daily pct_change().sum()? No, compounding.
        
        # Let's use the daily series for the year
        daily_rets = year_data.pct_change().fillna(0)
        # However, for the very first day of the year, pct_change needs prev day.
        # If we just take the subset `year_data`, the first day's return is NaN/0 unless we preserve context.
        # But `series` is the equity curve. So:
        
        year_start_val = year_data.iloc[0]
        # Check if we have a previous day outside this year
        prev_idx = series.index.get_loc(year_data.index[0]) - 1
        if prev_idx >= 0:
            year_start_val = series.iloc[prev_idx]
            
        year_end_val = year_data.iloc[-1]
        
        year_ret = (year_end_val / year_start_val) - 1
        
        # Max DD for the year
        # Re-base peak for the year? Or absolute DD during the year?
        # Usually "Yearly Max DD" means the deepest drawdown occurring *within* that year.
        # relative to the peak *within* that year (or all time?). 
        # Usually it's "Max Drawdown FROM PEAK developed IN THAT YEAR".
        rolling_peak_yr = year_data.cummax()
        dd_series_yr = (year_data - rolling_peak_yr) / rolling_peak_yr
        max_dd_yr = dd_series_yr.min()
        
        stats_list.append({
            "Year": year,
            "Return": year_ret,
            "Max DD": max_dd_yr
        })
        
    return pd.DataFrame(stats_list)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'SPY.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    # Load Data
    try:
        df = pd.read_csv(data_path, index_col=0, parse_dates=True, header=[0, 1])
        # Try to locate 'Adj Close' or 'Close'
        if 'Adj Close' in df.columns.get_level_values(0):
            spy_full = df['Adj Close'].iloc[:, 0]
        elif 'Close' in df.columns.get_level_values(0):
            spy_full = df['Close'].iloc[:, 0]
        else:
            spy_full = df.iloc[:, 0]
    except:
        # Fallback for simple csv
        df = pd.read_csv(data_path, index_col=0, parse_dates=True)
        spy_full = df.iloc[:, 0]
    
    spy_full = spy_full.sort_index()
    
    # Periods to test
    periods_years = [5, 10, 15, 20]
    last_date = spy_full.index[-1]
    
    # Print Header
    print("=" * 100)
    print("TITAN HAMMER - MULTI-PERIOD SIMULATION REPORT")
    print(f"Data End Date: {last_date.date()}")
    print("=" * 100)

    for years in periods_years:
        start_date_cutoff = last_date - timedelta(days=years*365.25)
        
        # Slice Data
        # We need a bit of buffer for SMA200 calculation if we want it to be accurate from day 1 of the period.
        # But `run_simulation_logic` calculates SMA on the passed series. 
        # So we should pass a slice that includes buffer, but only track equity from the cut-off.
        # Actually simplest is to pass the whole series to a helper that returns the whole curves, 
        # then we slice the curves? 
        # No, "Simulation for last 5 years" usually means "Start with $10k 5 years ago".
        # So we should slice the data first, but include 200 days prior for SMA.
        
        buffer_days = 365 # ample buffer for 200 trading days
        slice_start_buffered = start_date_cutoff - timedelta(days=buffer_days)
        
        spy_slice_buffered = spy_full[spy_full.index >= slice_start_buffered].copy()
        
        if len(spy_slice_buffered) == 0:
            print(f"\n[!] Not enough data for {years} Years simulation.")
            continue
            
        # Run Simulation on buffered data
        eq_curve_buf, spy_curve_buf, _ = run_simulation_logic(spy_slice_buffered)
        
        # Now trim results to the actual start date
        eq_curve = eq_curve_buf[eq_curve_buf.index >= start_date_cutoff]
        spy_curve = spy_curve_buf[spy_curve_buf.index >= start_date_cutoff]
        
        if len(eq_curve) == 0:
            print(f"\n[!] Data gap for {years} Years simulation.")
            continue

        # Re-normalize to starting equity of $10,000 for the period view
        eq_curve = (eq_curve / eq_curve.iloc[0]) * 10000
        spy_curve = (spy_curve / spy_curve.iloc[0]) * 10000
        
        # Calculate Overall Stats
        strat_cagr, strat_mdd = calculate_stats(eq_curve)
        spy_cagr, spy_mdd = calculate_stats(spy_curve)
        
        # Calculate Yearly Stats
        yearly_stats = get_yearly_stats(eq_curve)
        spy_yearly_stats = get_yearly_stats(spy_curve)
        
        print(f"\n>>> PERIOD: LAST {years} YEARS ({eq_curve.index[0].date()} to {eq_curve.index[-1].date()})")
        print("-" * 100)
        
        # 1. Comparison Table
        print(f"{'METRIC':<20} | {'TITAN STRATEGY':<20} | {'SPY (BENCHMARK)':<20}")
        print("-" * 75)
        print(f"{'CAGR':<20} | {strat_cagr:<20.2%} | {spy_cagr:<20.2%}")
        print(f"{'Max Drawdown':<20} | {strat_mdd:<20.2%} | {spy_mdd:<20.2%}")
        print(f"{'Final Equity':<20} | ${eq_curve.iloc[-1]:<19,.0f} | ${spy_curve.iloc[-1]:<19,.0f}")
        print("-" * 75)
        
        # 2. Yearly Breakdown
        print("\nYearly Performance Breakdown:")
        print(f"{'Year':<6} | {'Titan Return':<15} | {'Titan MaxDD':<15} | {'SPY Return':<15} | {'SPY MaxDD':<15}")
        print("-" * 80)
        
        # Merge stats for printing
        # yearly_stats and spy_yearly_stats should align on Year
        common_years = sorted(list(set(yearly_stats['Year']) | set(spy_yearly_stats['Year'])))
        
        for y in common_years:
            t_row = yearly_stats[yearly_stats['Year'] == y]
            s_row = spy_yearly_stats[spy_yearly_stats['Year'] == y]
            
            t_ret = t_row.iloc[0]['Return'] if not t_row.empty else 0.0
            t_dd = t_row.iloc[0]['Max DD'] if not t_row.empty else 0.0
            
            s_ret = s_row.iloc[0]['Return'] if not s_row.empty else 0.0
            s_dd = s_row.iloc[0]['Max DD'] if not s_row.empty else 0.0
            
            print(f"{y:<6} | {t_ret:<15.2%} | {t_dd:<15.2%} | {s_ret:<15.2%} | {s_dd:<15.2%}")
            
        print("\n")

if __name__ == "__main__":
    main()
