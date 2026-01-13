import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

def update_market_flags():
    print("Fetching SPY data for Market Flags...")
    
    # Fetch Data (last ~60 days to be safe for 30 trading days)
    try:
        data = yf.download("SPY", period="3mo", progress=False)
        
        # Handle potential MultiIndex columns in newer yfinance versions
        if isinstance(data.columns, pd.MultiIndex):
            # Flatten or select 'Close' / 'Adj Close'
            # Typically 'Close' is at level 0, Ticker at level 1
            # We'll just grab 'Close'
            if 'Close' in data.columns.get_level_values(0):
                 df = data['Close']
            else:
                 df = data.iloc[:, 0] # Fallback
        else:
             df = data['Close']
            
        # Ensure it's a Series
        if isinstance(df, pd.DataFrame):
             df = df.iloc[:, 0]
             
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Calculate Returns
    returns = df.pct_change().dropna()
    
    # Get last 30 days
    last_30 = returns.tail(30)
    
    flags = []
    
    for date, ret in last_30.items():
        # Classification Logic
        # Green: >= 0
        # Yellow: < 0 and > -1.5%
        # Red: <= -1.5%
        
        flag_type = "GREEN"
        if ret < -0.015:
            flag_type = "RED"
        elif ret < 0:
            flag_type = "YELLOW"
            
        flags.append({
            "date": date.strftime("%Y-%m-%d"),
            "return": round(float(ret), 4),
            "flag": flag_type
        })
    
    # Reverse to show newest first? Or oldest first? 
    # Usually "Last 30 days" implies timeline left-to-right (old to new) or list top-to-bottom (new to old).
    # Let's keep chronological order (oldest -> newest) for a timeline view.
    
    # Export Path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Navigate to web/public/data
    web_data_dir = os.path.join(base_dir, '..', 'invis-web', 'public', 'data')
    os.makedirs(web_data_dir, exist_ok=True)
    json_path = os.path.join(web_data_dir, 'market_flags.json')
    
    output = {
        "updated": datetime.now().isoformat(),
        "count": len(flags),
        "flags": flags
    }
    
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)
        
    print(f"Successfully exported {len(flags)} flags to {json_path}")
    print(f"Last Flag: {flags[-1]}")

if __name__ == "__main__":
    update_market_flags()
