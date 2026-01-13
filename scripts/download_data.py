import yfinance as yf
import os
import pandas as pd

def download_data():
    ticker = "SPY"
    print(f"Downloading {ticker} data from Yahoo Finance...")
    
    # Download max history
    data = yf.download(ticker, period="max")
    
    if data.empty:
        print("Error: No data downloaded.")
        return

    # Ensure data dir exists
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, "SPY.csv")
    data.to_csv(file_path)
    print(f"Saved {ticker} data to {file_path}")
    print(f"Rows: {len(data)}")
    print(f"Start Date: {data.index[0]}")
    print(f"End Date: {data.index[-1]}")

if __name__ == "__main__":
    download_data()
