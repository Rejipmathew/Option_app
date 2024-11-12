import streamlit as st
import yfinance as yf
import pandas as pd

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

# Fetch and display stock data
def display_stock_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Fetch stock history based on selected period
        if period == "1D":
            history = stock.history(period="1d", interval="1h")
        elif period == "5D":
            history = stock.history(period="5d", interval="1d")
        elif period == "1M":
            history = stock.history(period="1mo", interval="1d")
        elif period == "6M":
            history = stock.history(period="6mo", interval="1wk")
        elif period == "YTD":
            history = stock.history(period="ytd", interval="1mo")
        elif period == "1Y":
            history = stock.history(period="1y", interval="1mo")
        elif period == "5Y":
            history = stock.history(period="5y", interval="3mo")

        st.line_chart(history["Close"])

        # Display stock information in columns
        col1, col2, col3 = st.columns(3)

        # Stock information
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

        # Price information
        current_price = safe_format(info.get('currentPrice'))
        prev_close = safe_format(info.get('previousClose'))
        day_high = safe_format(info.get('dayHigh'))
        day_low = safe_format(info.get('dayLow'))
        ft_week_high = safe_format(info.get('fiftyTwoWeekHigh'))
        ft_week_low = safe_format(info.get('fiftyTwoWeekLow'))

        price_info = [
            ("Price Info", "Value"),
            ("Current Price", f"${current_price}"),
            ("Previous Close", f"${prev_close}"),
            ("Day High", f"${day_high}"),
            ("Day Low", f"${day_low}"),
            ("52 Week High", f"${ft_week_high}"),
            ("52 Week Low", f"${ft_week_low}")
        ]
        df_price = pd.DataFrame(price_info[1:], columns=price_info[0])
        col2.dataframe(df_price, width=400, hide_index=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")

# Fetch and display options data
def display_options_data(ticker, option_type):
    try:
        stock = yf.Ticker(ticker)
        expiration_dates = stock.options
        expiration_date = st.selectbox("Select an expiration date", expiration_dates)

        if expiration_date:
            options_chain = stock.option_chain(expiration_date)
            options_data = options_chain.calls if option_type == "Call" else options_chain.puts
            options_data = options_data.sort_values(by="volume", ascending=False)

            st.write(f"**{option_type}s for {expiration_date}**")
            st.dataframe(options_data[['contractSymbol', 'strike', 'lastPrice', 'volume']])

            if not options_data.empty:
                highest_option = options_data.iloc[0]
                st.write(f"**Highest Volume {option_type} Option**: {highest_option['contractSymbol']} - Volume: {highest_option['volume']}")

    except Exception as e:
        st.error(f"An error occurred while fetching options data: {e}")

# Display data based on the selected type
if ticker.strip():
    if data_type == "Stock Data":
        display_stock_data(ticker, period)
    elif data_type == "Options Data" and show_options:
        display_options_data(ticker, option_type)
