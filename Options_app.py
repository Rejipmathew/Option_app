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

    # Drop-down menu to select data type (Stock data or Options data)
    data_type = st.selectbox("Select Data Type", ["Stock Data", "Options Data"])

    # Options selection if "Options Data" is selected
    show_options = data_type == "Options Data"
    option_type = st.selectbox("Select Option Type", ("Call", "Put"), index=0) if show_options else None

# Helper function to safely format numerical values
def safe_format(value, decimal_places=2):
    if isinstance(value, (int, float)):
        return f"{value:.{decimal_places}f}"
    return "N/A"

# Format market cap and enterprise value into something readable
def format_value(value):
    if isinstance(value, (int, float)):
        suffixes = ["", "K", "M", "B", "T"]
        suffix_index = 0
        while value >= 1000 and suffix_index < len(suffixes) - 1:
            value /= 1000
            suffix_index += 1
        return f"${value:.1f}{suffixes[suffix_index]}"
    return "N/A"

# Fetch and display stock data with moving averages
def display_stock_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Fetch stock history
        history = stock.history(period=period)
        history['SMA_50'] = history['Close'].rolling(window=50).mean()
        history['EMA_20'] = history['Close'].ewm(span=20, adjust=False).mean()

        st.line_chart(history[['Close', 'SMA_50', 'EMA_20']])

        # Historical Volatility Calculation
        history['LogReturns'] = np.log(history['Close'] / history['Close'].shift(1))
        hist_vol = history['LogReturns'].std() * np.sqrt(252)  # Annualized
        st.write(f"**Historical Volatility**: {safe_format(hist_vol * 100)}%")

        # Display stock information in columns
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
        st.error(f"An error occurred: {e}")

# Black-Scholes Model for Greeks calculation
def calculate_greeks(S, K, T, r, sigma, option_type):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    delta = norm.cdf(d1) if option_type == "Call" else -norm.cdf(-d1)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T)
    theta = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
    return delta, gamma, vega, theta

# Fetch and display options data
def display_options_data(ticker, option_type):
    try:
        stock = yf.Ticker(ticker)
        expiration_dates = stock.options
        expiration_date = st.selectbox("Select an expiration date", expiration_dates)

        if expiration_date:
            options_chain = stock.option_chain(expiration_date)
            options_data = options_chain.calls if option_type == "Call" else options_chain.puts

            # Calculate Greeks
            r = 0.05  # Assume a constant risk-free rate
            S = stock.history(period='1d')['Close'].iloc[-1]
            T = (datetime.strptime(expiration_date, "%Y-%m-%d") - datetime.now()).days / 365

            options_data['Delta'], options_data['Gamma'], options_data['Vega'], options_data['Theta'] = zip(
                *options_data.apply(lambda x: calculate_greeks(
                    S, x['strike'], T, r, x['impliedVolatility'], option_type), axis=1))

            st.write(f"**{option_type}s for {expiration_date} - Top Options by Volume**")
            st.dataframe(options_data[['contractSymbol', 'strike', 'lastPrice', 'volume', 'impliedVolatility', 'Delta', 'Gamma', 'Vega', 'Theta']], height=400)

    except Exception as e:
        st.error(f"An error occurred while fetching options data: {e}")

# Display data based on the selected type
if ticker.strip():
    if data_type == "Stock Data":
        display_stock_data(ticker, period)
    elif data_type == "Options Data" and show_options:
        display_options_data(ticker, option_type)
