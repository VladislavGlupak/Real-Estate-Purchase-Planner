import os
import requests
import streamlit as st
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from datetime import datetime
from dateutil.relativedelta import relativedelta

# web page name
st.set_page_config(page_title="Real Estate Purchase Planner in California", page_icon=":eyeglasses:")

# app title
st.markdown('## Real Estate Purchase Planner in California')

# fist part of sidebar
st.sidebar.markdown("# Portfolio")

# define the inputs
cont_monthly = st.sidebar.slider('Monthly Contribution to Investments?', 0, 10000, 5000) # min, max, default
pf_type_cont = st.sidebar.radio('Portfolio Type for Contributions?', ['Low risk', 'Medium risk', 'High risk'])
curr_holdings = st.sidebar.slider('Current Holdings of Portfolio?', 0, 10000, 5000) # min, max, default
pf_type_hold = st.sidebar.radio('Portfolio Type for Current Holdings?', ['Low risk', 'Medium risk', 'High risk'])

# desired house
st.sidebar.markdown("# Desired house")

total_price = st.sidebar.slider('Insert a desired prise of house', 0, 10000000, 5000000)
down_payment = st.sidebar.slider('Down Payment %', 0, 100, 50)
num_years = st.sidebar.slider('How many yesrs?', 0, 50, 25) # min, max, default

st.markdown('### Your entered data:')
st.write('Monthly Contribution to Investments, $ - ', cont_monthly)
st.write('Portfolio Type for Contributions - ', pf_type_cont)
st.write('Current Holdings of Portfolio, $ - ', curr_holdings)
st.write('Portfolio Type for Current Holdings - ', pf_type_hold)
st.write('You entered the desired price $: - ', total_price)
st.write('Down Payment % - ', down_payment)
st.write('Number of years - ', num_years)

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
tickers = ["SPY", "AGG"]

# Set timeframe to one day ('1D') for the Alpaca API
timeframe = "1D"

# Get current closing prices for FB and TWTR
stocks_portfolio = alpaca.get_barset(
    tickers,
    timeframe,
    start = start_date,
    end = end_date
).df

# checking the timeframe start and end dates
st.markdown('### Timeframe:')
st.write('Start date: ', start_date)
st.write('End date: ', end_date)

# Display sample data
st.markdown('### Data frame - Stocks')
stocks_portfolio