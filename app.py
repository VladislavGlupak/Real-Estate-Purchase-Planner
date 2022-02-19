import os
import pandas as pd
import requests
import json
from pydoc import describe
import requests
import streamlit as st
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
savings = int(st.sidebar.text_input('Current savings, $', '1000'))
cont_monthly = int(st.sidebar.slider('Monthly contribution to the current savings, $', 0, 10000, 1000, step=100)) # min, max, default
pf_risk_type = st.sidebar.radio('Portfolio Type?', ['Low risk', 'Medium risk', 'High risk'])
curr_btc = float(st.sidebar.text_input('Number of BTC in your portfolio', '0'))
curr_eth = float(st.sidebar.text_input('Number of Ethereum in your portfolio', '0'))
curr_spy = int(st.sidebar.text_input('Number of S&P500 in your portfolio', '1'))
curr_agg = int(st.sidebar.text_input('Number of AGG in your portfolio', '1'))

# desired house
st.sidebar.markdown("# Desired house")
total_price = int(st.sidebar.text_input('Desired house price $', '2000000'))
pct_down = float(st.sidebar.slider('Percent down on the house?', 0, 100, 20)) # min, max, default # divide by 100 later
desired_city = st.sidebar.text_input('Desired city, "example: San Francisco, CA"', 'San Jose, CA')
st.sidebar.markdown("# Time period")
num_years = int(st.sidebar.slider('How many years?', 0, 50, 10, step=1)) # min, max, default

if (pf_risk_type == "Low risk") and (curr_btc !=0 or curr_eth !=0):
    st.markdown('### BTC and ETH should be ZERO!! (low risk only includes stocks)')
else:
    if savings >= total_price:
        st.markdown(f'### You have enough money in savings alone to buy the house at ${total_price}!')
    else:
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

        with st.spinner('### Please wait...'):

            # Calculate dates
            now = datetime.now() # end date
            now_to_string = now.strftime("%Y-%m-%d") # convert end date to string
            years_ago = now - relativedelta(years=num_years) # calculate start date
            years_ago_to_string = years_ago.strftime("%Y-%m-%d") # convert end date to string

            # date for stock and bonds (we are taking yesterday's close price)
            yesterday = now - relativedelta(days=1)
            yesterday_to_string = yesterday.strftime("%Y-%m-%d")

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
            stocks_yesterday = alpaca.get_barset(
                tickers_stocks,
                '1D',
                start = pd.Timestamp(yesterday_to_string, tz="America/New_York").isoformat(),
                end = pd.Timestamp(yesterday_to_string, tz="America/New_York").isoformat()
            ).df
            
            # parsing stocks_today df
            agg_close_price = stocks_yesterday.iloc[0,3]
            spy_close_price = stocks_yesterday.iloc[0,8]

            # calculating value of AGG and SPY
            spy_value = curr_spy * spy_close_price
            agg_value = curr_agg * agg_close_price
            total_stocks_bonds = agg_value + spy_value

            # Collecting data for MC simulation
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

            simulation.calc_cumulative_return() # run calculating of cumulative return

            # MC summary statistics
            MC_summary_statistics = simulation.summarize_cumulative_return()

            # Calculate if user can afford the house after desired number of years
            sum_savings = savings + ((cont_monthly * 12) * num_years) # sum of savings

            cum_return = (btc_value + eth_value + total_stocks_bonds) * MC_summary_statistics[1] # cumulative return

            result = sum_savings + cum_return # result without crypto

            amount_needed = (pct_down/100) * total_price # amount needed for down payment

            monthly_payment_after_dp = (total_price - amount_needed)/(12*num_years) # 

            # check if user will able to buy the house in desired time period
            if result >= total_price:
                st.markdown('### Result:')
                st.markdown(f'### Congratulations! You will be able to buy a house with desired price ${total_price} in {num_years} years. :)))')
                st.markdown(f'### You will have from investing and savings ${result: .2f}.')
                st.markdown('This data is for informational purposes only.')
            elif result >= amount_needed:
                st.markdown('### Result:')
                st.markdown(f'### Congratulations! You can afford the {pct_down}% down payment on a house with desired price of ${total_price} in {num_years} years. :)))')
                st.markdown(f'### You will have from investing and savings ${result: .2f}.')
                st.markdown(
                    f'''### Make sure that you continue to save enough to pay the average monthly cost of ${monthly_payment_after_dp:.2f}. 
                    * Not including interest rate and taxes.'''
                    )
                st.markdown('This data is for informational purposes only.')
            else:
                st.markdown('### Result:')
                st.markdown(f'### Sorry! You need more time or higher portfolio to buy a house in {num_years} years. :(((')
                st.markdown(f'### You will have from investing and savings ${result: .2f}.')
                st.markdown('This data is for informational purposes only.')
            st.markdown('---')

            # Retrieve mapdata

            url = 'https://zillow-com1.p.rapidapi.com/propertyExtendedSearch'
            query = {f'location': {desired_city}, 'home_type': 'Houses'}
            headers =  {
            'x-rapidapi-host': 'zillow-com1.p.rapidapi.com',
            'x-rapidapi-key': 'c039c94e44msh15c6a851d5e7e68p1ce297jsn3a5904ceb62e'
            }
            response = requests.request('GET', url, headers=headers, params=query)
            response_json = response.json()

            if int(response.status_code) != 200:
                st.markdown(f"### Approximate location of the houses in {desired_city}")
                st.markdown("Sorry! We couldn't get any response from server. Try one more time.")
            else:
                if len(response_json) == 0:
                    st.markdown(f"### Approximate location of the houses in {desired_city}")
                    st.markdown("We did not find any data matching your request...")
                else:
                # pull desired data from json
                    df = pd.DataFrame()
                    count = 0
                    for address in response_json["props"]:
                        big_mac_index_data = {
                        "lon": [response_json["props"][count]['longitude']],
                        "lat": [response_json["props"][count]['latitude']],
                        "address": [response_json["props"][count]['address']],
                        "price": [response_json["props"][count]['price']],
                        }
                        df = df.append(pd.DataFrame.from_dict(big_mac_index_data))
                        if count <= len(response_json["props"]):
                            count = count+1       

                    df_filtred_by_price = df[ (total_price-(total_price*0.1) <= df['price']) & (df['price'] <= total_price+(total_price*0.1))]
                    df_filtred_by_price = df_filtred_by_price.reset_index(drop=True)
                    
                    st.markdown(f"### Approximate location of the houses in {desired_city}")
                    st.map(df_filtred_by_price)
                    st.markdown("### Houses we could find for you based on today's data:")
                    st.markdown("10% range based on desired price.")
                    df_filtred_by_price_drop_lat_lon = df_filtred_by_price.drop(columns=['lon', 'lat'])
                    df_filtred_by_price_drop_lat_lon