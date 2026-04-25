import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import numpy as np

def get_bitcoin_history(days=30):
    """
    Fetch Bitcoin price history from CoinGecko API
    Returns DataFrame with date and price columns
    """
    base_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

    # Calculate date range parameters
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }

    try:
        # Make API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()

        # Process raw data - CoinGecko returns timestamps
        timestamps = data['prices']
        dates = [datetime.fromtimestamp(x[0]/1000) for x in timestamps]  # Convert ms to datetime
        prices = [x[1] for x in timestamps]

        df = pd.DataFrame({
            'date': dates,
            'price_usd': prices
        })

        # Convert to local timezone
        df['date'] = df['date'].dt.tz_localize(None)

        return df

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        print("Using sample data instead...")
        return create_sample_data()

def create_sample_data():
    """Create realistic sample data if API fails"""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    prices = np.linspace(42000, 48000, 30)  # More realistic price movement
    prices = prices + 1000 * np.random.randn(30)  # Add some noise
    return pd.DataFrame({
        'date': dates,
        'price_usd': prices
    })

def plot_bitcoin_history(df):
    """Plot Bitcoin price history"""
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['price_usd'], color='royalblue', linewidth=2)

    plt.title('Bitcoin Price History (Past 30 Days)', fontsize=16, pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Price (USD)', fontsize=12)
    plt.grid(True, alpha=0.3)

    # Format x-axis to show dates
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))
    plt.gcf().autofmt_xdate()

    # Highlight current price
    current_price = df['price_usd'].iloc[-1]
    plt.axhline(y=current_price, color='r', linestyle='--', alpha=0.5)
    plt.text(df['date'].iloc[-1], current_price*1.01,
             f'Current: ${current_price:,.2f}',
             ha='right', va='bottom', color='red')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print("Fetching Bitcoin price history...")
    btc_data = get_bitcoin_history()

    print(f"Retrieved {len(btc_data)} days of data")
    print(f"Price range: ${btc_data['price_usd'].min():,.2f} - ${btc_data['price_usd'].max():,.2f}")

    plot_bitcoin_history(btc_data)