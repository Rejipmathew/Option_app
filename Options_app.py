import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime

# Streamlit app details
st.set_page_config(page_title="Financial Analysis", layout="wide")

# Sidebar Inputs
with st.sidebar:
    st.title("Financial Analysis")
    ticker = st.text_input("Enter a stock ticker (e.g., AAPL)", "AAPL")
    period = st.selectbox("Enter a time frame", ("1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"), index=2)
    data_type = st.selectbox("Select Data Type", ["Stock Data", "Options Data"])
    show_options = data_type == "Options Data"
    option_type = st.selectbox("Select Option Type", ("Call", "Put"), index=0) if show_options else None

# Helper function to safely format numerical values
def safe_format(value, decimal_places=2):
    if isinstance(value, (int, float)):
        return f"{value:.{decimal_places}f}"
    return "N/A"

def format_value(value):
    if isinstance(value, (int, float)):
        suffixes = ["", "K", "M", "B", "T"]
        suffix_index = 0
        while value >= 1000 and suffix_index < len(suffixes) - 1:
            value /= 1000
            suffix_index += 1
        return f"${value:.1f}{suffixes[suffix_index]}"
    return "N/A"

# Enhanced function to fetch stock data
def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return stock, info
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return None, None

# Fetch and display stock data with moving averages and error handling
def display_stock_data(ticker, period):
    stock, info = fetch_stock_data(ticker)
    if stock is None or info is None:
        st.error("Failed to fetch stock data. Please check the ticker symbol and try again.")
        return

    try:
        history = stock.history(period=period)
        if history.empty:
            st.warning("No historical data available for the selected period.")
            return

        history['SMA_50'] = history['Close'].rolling(window=50).mean()
        history['EMA_20'] = history['Close'].ewm(span=20, adjust=False).mean()

        st.line_chart(history[['Close', 'SMA_50', 'EMA_20']])

        history['LogReturns'] = np.log(history['Close'] / history['Close'].shift(1))
        hist_vol = history['LogReturns'].std() * np.sqrt(252)
        st.write(f"**Historical Volatility**: {safe_format(hist_vol * 100)}%")

        col1, col2, col3 = st.columns(3)

        country = info.get('country', 'N/A')
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        market_cap = format_value(info.get('marketCap', 'N/A'))
        ent_value = format_value(info.get('enterpriseValue', 'N/A'))
        employees = info.get('fullTimeEmployees', 'N/A')

        stock_info = [
            ("Stock Info", "Value"),
            ("Country", country),
            ("Sector", sector),
            ("Industry", industry),
            ("Market Cap", market_cap),
            ("Enterprise Value", ent_value),
            ("Employees", employees)
        ]
        df_info = pd.DataFrame(stock_info[1:], columns=stock_info[0])
        col1.dataframe(df_info, width=400, hide_index=True)

    except Exception as e:
        st.error(f"An error occurred while displaying stock data: {e}")

# Display data based on the selected type
if ticker.strip():
    if data_type == "Stock Data":
        display_stock_data(ticker, period)
