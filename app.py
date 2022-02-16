import os
import requests
import streamlit as st
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from datetime import datetime
from dateutil.relativedelta import relativedelta
from MCForecastTools import MCSimulation
from PIL import Image

# web page name
st.set_page_config(page_title="Real Estate Purchase Planner in California", page_icon=":house:")
st.image(Image.open('pics/picture.jpg'))

# app title
st.markdown('## Real Estate Purchase Planner in California')
st.markdown('---')

# fist part of sidebar
st.sidebar.markdown("# Portfolio")

# define the inputs
savings = int(st.sidebar.text_input('Savings, $', '1000'))
cont_monthly = st.sidebar.slider('Monthly Contribution to Investments, $', 0, 10000, 5000, step=100) # min, max, default
pf_risk_type = st.sidebar.radio('Portfolio Type?', ['Low risk', 'Medium risk', 'High risk'])
curr_crypto = cont_monthly = int(st.sidebar.text_input('Number of Ethereum in your portfolio', '10'))
curr_stocks = cont_monthly = int(st.sidebar.text_input('Number of S&P500 in your portfolio', '10'))

# desired house
st.sidebar.markdown("# Desired house")

total_price = int(st.sidebar.text_input('Desired house price $', '1000000'))
num_years = st.sidebar.slider('How many yesrs?', 0, 50, 25, step=1) # min, max, default

# Load .env environment variables
load_dotenv()

# Set Alpaca API key and secret
alpaca_api_key = os.getenv("ALPACA_API_KEY")
alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")

# Create the Alpaca API object
alpaca = tradeapi.REST(
    alpaca_api_key,
    alpaca_secret_key,
    api_version="v2")

# minus years
now = datetime.now()
now_to_string = now.strftime("%Y-%m-%d")
years_ago = now - relativedelta(years=num_years)
years_ago_to_string = years_ago.strftime("%Y-%m-%d")

# Format current date as ISO format
start_date = pd.Timestamp(years_ago_to_string, tz="America/New_York").isoformat()
end_date = pd.Timestamp(now_to_string, tz="America/New_York").isoformat()

# Set the tickers
tickers = ["ETH", "SPY"]

# Set timeframe to one day ('1D') for the Alpaca API
timeframe = "1D"

# Get current closing prices for FB and TWTR
stocks_portfolio = alpaca.get_barset(
    tickers,
    timeframe,
    start = start_date,
    end = end_date,
    limit = 1000
).df

# checking the timeframe start and end dates
st.markdown('### Timeframe:')
st.write('Start date: ', start_date)
st.write('End date: ', end_date)

# Display sample data
st.markdown('### Data frame - Stocks')
stocks_portfolio