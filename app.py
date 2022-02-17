from ast import Break
import os
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from datetime import datetime
from dateutil.relativedelta import relativedelta
from MCForecastTools import MCSimulation
from PIL import Image
from alpaca_trade_api.rest import TimeFrame

# web page name
st.set_page_config(page_title="Real Estate Purchase Planner in California", page_icon=":house:")
st.image(Image.open('pics/picture.jpg'))

# app title
st.markdown('## Real Estate Purchase Planner in California')
st.markdown('---')

# fist part of sidebar
st.sidebar.markdown("# Portfolio")

# define the inputs
savings = int(st.sidebar.text_input('current savings, $', '1000'))
cont_monthly = int(st.sidebar.slider('Monthly contribution to savings, $', 0, 10000, 1000, step=100)) # min, max, default
pf_risk_type = st.sidebar.radio('Portfolio Type?', ['Low risk', 'Medium risk', 'High risk'])
curr_btc = int(st.sidebar.text_input('Number of BTC in your portfolio', '1'))
curr_eth = int(st.sidebar.text_input('Number of Ethereum in your portfolio', '1'))
curr_spy = int(st.sidebar.text_input('Number of S&P500 in your portfolio', '1'))
curr_agg = int(st.sidebar.text_input('Number of AGG in your portfolio', '1'))

#if (pf_risk_type == "Low risk") and (curr_btc !=0 or curr_eth !=0):
#    st.markdown('BTC and ETH should be ZERO!!!')
#    exit()

# desired house
st.sidebar.markdown("# Desired house")
total_price = int(st.sidebar.text_input('Desired house price $', '2000000'))
st.sidebar.markdown("# Time period")
num_years = int(st.sidebar.slider('How many years?', 0, 50, 10, step=1)) # min, max, default

if savings >= total_price:
    st.markdown('## You have anougth money!')
    exit()

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

# The Free Crypto API Call endpoint URLs for the held cryptocurrency assets
btc_url = "https://api.alternative.me/v2/ticker/Bitcoin/?convert=USD"
eth_url = "https://api.alternative.me/v2/ticker/Ethereum/?convert=USD"

# Calculate dates
now = datetime.now() # end date
now_to_string = now.strftime("%Y-%m-%d") # convert end date to string
years_ago = now - relativedelta(years=num_years) # calculate start date
years_ago_to_string = years_ago.strftime("%Y-%m-%d") # convert end date to string

# Format current date as ISO format
start_date = pd.Timestamp(years_ago_to_string, tz="America/New_York").isoformat()
end_date = pd.Timestamp(now_to_string, tz="America/New_York").isoformat()

# Set the tickers (Alpaca's API standart)
tickers_stocks = ["SPY", "AGG"]
tickers_crypto = ["BTCUSD", "ETHUSD"]

# Portfolio types
#Low risk = 100% stocks (SPY, AGG)
#Medium risk = 80% stocks (SPY, AGG), 20% crypto (ETH, BTC)
#High risk = 40% stocks (SPY, AGG), 60% crypto (ETH, BTC)

low_risk = [.00, .00, .50, .50]
medium_risk = [.10, 0.10, .40, 0.40]
high_risk = [.30, 0.30, .20, 0.20]

# Set portfolio risk type
weight = []
if pf_risk_type == "Low risk":
    weight = low_risk
if pf_risk_type == "Medium risk":
    weight = medium_risk
if pf_risk_type == "High risk":
    weight = high_risk

# Using the Python requests library, make an API call to access the current price of BTC and Eth
btc_response = requests.get(btc_url).json()
eth_response = requests.get(eth_url).json()

# Navigate the BTC response object to access the current price of BTC and Eth
btc_price = btc_response["data"]["1"]["quotes"]["USD"]["price"]
eth_price = eth_response["data"]["1027"]["quotes"]["USD"]["price"]

# Compute the current value of the BTC holding 
btc_value = curr_btc * btc_price
eth_value = curr_eth * eth_price

# calculating stocks and bonds values
stocks_today = alpaca.get_barset(
    tickers_stocks,
    '1D',
    start = pd.Timestamp(now_to_string, tz="America/New_York").isoformat(),
    end = pd.Timestamp(now_to_string, tz="America/New_York").isoformat()
).df
agg_close_price = stocks_today["AGG"]["close"]
spy_close_price = stocks_today["SPY"]["close"]
spy_value = curr_spy * spy_close_price
agg_value = curr_agg * agg_close_price
total_stocks_bonds = agg_value + spy_value

# Get closing prices for SPY and AGG
stocks = alpaca.get_barset(
    tickers_stocks,
    '1D',
    start = start_date,
    end = end_date,
    limit = 1000
).df

# Get closing prices for BTC and ETH
btc = alpaca.get_crypto_bars(
    tickers_crypto[0],
    TimeFrame.Day,
    start=start_date,
    end=end_date,
    limit=1000
).df

eth = alpaca.get_crypto_bars(
    tickers_crypto[1],
    TimeFrame.Day,
    start=start_date,
    end=end_date,
    limit=1000
).df

# Formatting and concat all dataframes
btc = btc.drop(columns=['trade_count','exchange', 'vwap'])
eth = eth.drop(columns=['trade_count','exchange', 'vwap'])

btc = pd.concat([btc], keys=['BTC'], axis=1) # add layer
eth = pd.concat([eth], keys=['ETH'], axis=1)

stocks = stocks.reset_index(drop=True) # reset index and drop index column
btc = btc.reset_index(drop=True)
eth = eth.reset_index(drop=True)

concat_df = pd.concat([btc, eth, stocks], verify_integrity=True, axis=1) # concatinate all dfs
concat_df = concat_df.dropna() # drop N/A

# Run Monte Carlo simulation for df c
simulation = MCSimulation(
    portfolio_data=concat_df,
    weights=weight,
    num_simulation=50,
    num_trading_days=252*num_years
)
simulation.portfolio_data.head()
simulation.calc_cumulative_return() # run calculating of cumulative return

# MC summary statistics
MC_summary_statistics = simulation.summarize_cumulative_return()

# Calculate if user can afford the house after desired number of years
sum_savings = savings + ((cont_monthly * 12) * num_years) # sum of savings

cum_return = (btc_value + eth_value + total_stocks_bonds) * MC_summary_statistics[1] # cumulative return

result = sum_savings + cum_return # result without crypto
result_with_crypto = sum_savings + cum_return + btc_value + eth_value # results with crypto value

# check if user will able to buy the house in desired time period
if result >= total_price:
    st.markdown('Result (Without intial value of crypto)')
    st.markdown(f'### Congratulations! You will be able to buy a house in {num_years} years. :)))')
    st.balloons()
else:
    st.markdown('Result (Without intial value of crypto)')
    st.markdown(f'### Sorry! You need more time or higher portfolio to buy a house in {num_years} years. :(((')

st.markdown('---')

# check if user will able to buy the house in desired time period (with initial crypto value)
if result_with_crypto >= total_price:
    st.markdown('Result')
    st.markdown(f'Congratulations! You will be able to buy a house in {num_years} years. :)))')
else:
    st.markdown('Result')
    st.markdown(f'Sorry! You need more time or higher portfolio to buy a house in {num_years} years. :(((')

st.markdown('---')



# for testing
st.write('')
st.write('')
st.write('')
st.write('')
st.write('')
st.write('## --- For testing ---')
st.write('Cumulative return: ', cum_return)
st.write('Result without intitial crypto amount: ', result)
st.write('Result with intitial crypto amount: ', result_with_crypto)
st.write(f'Type of {pf_risk_type} portfolio: ', weight)
st.markdown('### Timeframe:')
st.write('Start date: ', start_date)
st.write('End date: ', end_date)