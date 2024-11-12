import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

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

    # Technical indicators
    st.header("Select Technical Indicators")
    show_bollinger = st.checkbox("Bollinger Bands")
    show_put_call_ratio = st.checkbox("Put/Call Ratio")
    show_imi = st.checkbox("Intraday Momentum Index (IMI)")
    show_mfi = st.checkbox("Money Flow Index (MFI)")
    show_open_interest = st.checkbox("Open Interest")

# Helper functions for technical indicators
def calculate_bollinger_bands(data):
    """Calculate Bollinger Bands."""
    data['20_SMA'] = data['Close'].rolling(window=20).mean()
    data['Upper_Band'] = data['20_SMA'] + (data['Close'].rolling(window=20).std() * 2)
    data['Lower_Band'] = data['20_SMA'] - (data['Close'].rolling(window=20).std() * 2)
    return data

def calculate_put_call_ratio(stock):
    """Calculate Put/Call Ratio using options data."""
    expiration_dates = stock.options
    put_volumes, call_volumes = [], []
    
    for date in expiration_dates:
        options_chain = stock.option_chain(date)
        call_volumes.append(options_chain.calls['volume'].sum())
        put_volumes.append(options_chain.puts['volume'].sum())
    
    total_calls = sum(call_volumes)
    total_puts = sum(put_volumes)
    
    return total_puts / total_calls if total_calls > 0 else None

def calculate_imi(data):
    """Calculate Intraday Momentum Index (IMI)."""
    up_move = (data['Close'] > data['Open']).astype(int)
    down_move = (data['Close'] < data['Open']).astype(int)
    gains = (data['Close'] - data['Open']) * up_move
    losses = (data['Open'] - data['Close']) * down_move
    imi = (gains.rolling(window=14).sum() / (gains.rolling(window=14).sum() + losses.rolling(window=14).sum())) * 100
    data['IMI'] = imi
    return data

def calculate_mfi(data):
    """Calculate Money Flow Index (MFI)."""
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    money_flow = typical_price * data['Volume']
    positive_flow = money_flow.where(data['Close'] > data['Close'].shift(1), 0)
    negative_flow = money_flow.where(data['Close'] < data['Close'].shift(1), 0)
    
    mfi = 100 * (positive_flow.rolling(window=14).sum() /
                 (positive_flow.rolling(window=14).sum() + negative_flow.rolling(window=14).sum()))
    data['MFI'] = mfi
    return data

# Fetch and display stock data with indicators
def display_stock_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        
        if show_bollinger:
            history = calculate_bollinger_bands(history)
            st.line_chart(history[['Close', 'Upper_Band', 'Lower_Band']])
        
        if show_imi:
            history = calculate_imi(history)
            st.line_chart(history['IMI'], title="Intraday Momentum Index (IMI)")
        
        if show_mfi:
            history = calculate_mfi(history)
            st.line_chart(history['MFI'], title="Money Flow Index (MFI)")
        
        st.write("**Stock Data**")
        st.dataframe(history[['Open', 'High', 'Low', 'Close', 'Volume']])
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Fetch and display options data with indicators
def display_options_data(ticker, option_type):
    try:
        stock = yf.Ticker(ticker)
        expiration_dates = stock.options
        expiration_date = st.selectbox("Select an expiration date", expiration_dates)
        
        if expiration_date:
            options_chain = stock.option_chain(expiration_date)
            options_data = options_chain.calls if option_type == "Call" else options_chain.puts
            st.dataframe(options_data[['contractSymbol', 'strike', 'lastPrice', 'volume', 'openInterest']])

            # Calculate Put/Call Ratio
            if show_put_call_ratio:
                put_call_ratio = calculate_put_call_ratio(stock)
                st.write(f"**Put/Call Ratio**: {put_call_ratio:.2f}" if put_call_ratio else "N/A")
            
            if show_open_interest:
                st.write(f"**Open Interest for {option_type} Options**")
                st.dataframe(options_data[['contractSymbol', 'openInterest']])
    
    except Exception as e:
        st.error(f"An error occurred while fetching options data: {e}")

# Display data based on the selected type
if ticker.strip():
    if data_type == "Stock Data":
        display_stock_data(ticker, period)
    elif data_type == "Options Data" and show_options:
        display_options_data(ticker, option_type)
