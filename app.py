import os
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from datetime import datetime
from dateutil.relativedelta import relativedelta
from MCForecastTools import MCSimulation
from PIL import Image
from alpaca_trade_api.rest import TimeFrame

# Web page name
st.set_page_config(page_title="Real Estate Purchase Planner in California", page_icon=":house:")
st.image(Image.open('pics/picture.jpg'))

st.markdown('---')

# Fist part of sidebar
st.sidebar.markdown("# Portfolio")

# Define the inputs
# portfolio
savings = int(st.sidebar.text_input('Current savings, $', '10000')) # savings
cont_monthly = int(st.sidebar.slider('Monthly contribution to the current savings, $', 0, 10000, 1000, step=100)) # min, max, default
pf_risk_type = st.sidebar.radio('Portfolio Type?', ['Low risk', 'Medium risk', 'High risk']) # portfolio type
curr_btc = float(st.sidebar.text_input('Number of BTC in your portfolio', '0')) # number of BTC in the portfolio
curr_eth = float(st.sidebar.text_input('Number of ETH in your portfolio', '0')) # number of ETH in the portfolio
curr_spy = float(st.sidebar.text_input('Number of SPY in your portfolio', '1')) # number of SPY in the portfolio
curr_agg = float(st.sidebar.text_input('Number of AGG in your portfolio', '1')) # number of AGG in the portfolio

# desired house
st.sidebar.markdown("# Desired house")
total_price = int(st.sidebar.text_input('Desired house price $', '1500000')) # desired house price
pct_down = float(st.sidebar.slider('Percent down on the house?', 0, 100, 20)) # min, max, default # divide by 100 later
desired_city = st.sidebar.text_input('Desired city, state "Example: San Francisco, CA"', 'San Francisco, CA') # desired city
st.sidebar.markdown("# Time period")
num_years = int(st.sidebar.slider('How many years?', 0, 50, 15, step=1)) # min, max, default

# Checking if portfolio type is Low risk and (BTC or ETH = 0). Low risk doesn't contain the crypto
if (pf_risk_type == "Low risk") and (curr_btc !=0 or curr_eth !=0):
    st.markdown('### BTC and ETH should be ZERO!! (low risk only includes stocks and bonds)')
else:
    if savings >= total_price: # checking if user has enougth money
        st.markdown(f'### You have enough money in savings alone to buy the house at ${total_price:,.2f}!')
    else:
        # Load .env environment variables
        load_dotenv()

        # Alpaca API
        # set API keys
        alpaca_api_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        rapidapi_key = os.getenv("RAPIDAPI_KEY")

        # create the Alpaca API object
        alpaca = tradeapi.REST(
            alpaca_api_key,
            alpaca_secret_key,
            api_version="v2")

        # Altrnative API
        # the Free Crypto API Call endpoint URLs for the held cryptocurrency assets
        btc_url = "https://api.alternative.me/v2/ticker/Bitcoin/?convert=USD"
        eth_url = "https://api.alternative.me/v2/ticker/Ethereum/?convert=USD"

        # RapidAPI - Zillow
        # set query parameters for pulling map data (addresses from Zillow)
        url = 'https://zillow-com1.p.rapidapi.com/propertyExtendedSearch' # url for search
        query = {f'location': {desired_city}, 'home_type': 'Houses'}

        # set type of data resource and security key
        headers =  {
        'x-rapidapi-host': 'zillow-com1.p.rapidapi.com',
        'x-rapidapi-key': rapidapi_key
        }

        # If no errors, run the main part of app
        with st.spinner('### Please wait...'):

            # Set the tickers (Alpaca's API standart)
            tickers_stocks = ["SPY", "AGG"]
            tickers_crypto = ["BTCUSD", "ETHUSD"]

            # Portfolio types and portions of assets for each type
            # Low risk = 100% stocks (SPY, AGG)
            # Medium risk = 80% stocks (SPY, AGG), 20% crypto (ETH, BTC)
            # High risk = 40% stocks (SPY, AGG), 60% crypto (ETH, BTC)

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

            # Calculate dates
            now = datetime.now() # end date
            now_to_string = now.strftime("%Y-%m-%d") # convert end date to string
            # dates for historical information
            years_ago = now - relativedelta(years=num_years) # calculate start date
            years_ago_to_string = years_ago.strftime("%Y-%m-%d") # convert end date to string

            # date for stock and bonds (we are taking yesterday's close price)
            stocks_day = now - relativedelta(days=1)

            # check if today is not a weekend or not a Monday. We are taking close prices from previous trading day
            if now.weekday() == 5: # 5 is Satuday, Week [0 - Monday, ..., 6 - Sunday]
                stocks_day = now - relativedelta(days=1) # if today is Saturday => close prices from Friday
            elif now.weekday() == 6:
                stocks_day = now - relativedelta(days=2) # if today if Sunday => close prices from Friday
            elif now.weekday() == 0:
                stocks_day = now - relativedelta(days=3) # if today is Monday => close prices from Friday

            stocks_day_to_string = stocks_day.strftime("%Y-%m-%d") # convert to string
            
            # format current date as ISO format for getting historical information
            start_date = pd.Timestamp(years_ago_to_string, tz="America/New_York").isoformat()
            end_date = pd.Timestamp(now_to_string, tz="America/New_York").isoformat()

            # Using the Python requests library, make an API call to access the current price of BTC and Eth
            btc_response = requests.get(btc_url).json()
            eth_response = requests.get(eth_url).json()

            # navigate the BTC response object to access the current price of BTC and Eth
            btc_price = btc_response["data"]["1"]["quotes"]["USD"]["price"]
            eth_price = eth_response["data"]["1027"]["quotes"]["USD"]["price"]

            # compute the current value of the BTC holding 
            btc_value = curr_btc * btc_price
            eth_value = curr_eth * eth_price

            # Calculating stocks and bonds values (last close prices)
            # Run Alpaca's call
            stocks_before = alpaca.get_bars(
                tickers_stocks,
                TimeFrame.Day,
                start = pd.Timestamp(stocks_day_to_string, tz="America/New_York").isoformat(),
                end = pd.Timestamp(stocks_day_to_string, tz="America/New_York").isoformat()
            ).df
            
            # parsing stocks_today df
            agg_close_price = stocks_before.iloc[0,3]
            spy_close_price = stocks_before.iloc[1,3]

            # calculating value of AGG and SPY
            spy_value = curr_spy * spy_close_price
            agg_value = curr_agg * agg_close_price
            total_stocks_bonds = agg_value + spy_value

            # Collecting data for MC simulation
            # get closing prices for SPY and AGG
            stocks_spy = alpaca.get_bars(
                tickers_stocks[0],
                TimeFrame.Day,
                start = start_date,
                end = end_date,
                limit = 1000
            ).df
            
            stocks_agg = alpaca.get_bars(
                tickers_stocks[1],
                TimeFrame.Day,
                start = start_date,
                end = end_date,
                limit = 1000
            ).df

            # get closing prices for BTC and ETH
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

            # formatting and concat all dataframes: crypto
            btc = btc.drop(columns=['trade_count','exchange', 'vwap'])
            eth = eth.drop(columns=['trade_count','exchange', 'vwap'])

            btc = pd.concat([btc], keys=['BTC'], axis=1) # add layer
            eth = pd.concat([eth], keys=['ETH'], axis=1)
            
            btc = btc.reset_index(drop=True)
            eth = eth.reset_index(drop=True)
            
            # formatting and concat all dataframes: stocks and bonds
            stocks_agg = stocks_agg.drop(columns=['trade_count', 'vwap'])
            stocks_spy = stocks_spy.drop(columns=['trade_count', 'vwap'])
            stocks_agg = pd.concat([stocks_agg], keys=['AGG'], axis=1) # add layer
            stocks_spy = pd.concat([stocks_spy], keys=['SPY'], axis=1)
            
            stocks_agg = stocks_agg.reset_index(drop=True)
            stocks_spy = stocks_spy.reset_index(drop=True)
            
            # concatinate crypto, stocks and bonds
            concat_df = pd.concat([btc, eth, stocks_spy, stocks_agg], verify_integrity=True, axis=1) # concatinate all dfs
            concat_df = concat_df.dropna() # drop N/A

            # Run Monte Carlo simulation for concat_df
            # set parameters fir simulation
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

            monthly_payment_after_dp = (total_price - amount_needed)/(360) # 30 year mortgage is 360 months

            # check if user will able to buy the house in desired time period
            if result >= total_price:
                st.markdown('### Result:')
                st.markdown(f'### Congratulations! You will be able to buy a house with desired price ${total_price:,} in {num_years} years. :)))')
                st.markdown(f'### You will have ${result:,.2f} from your investments and savings.')
                st.markdown('This data is for informational purposes only.')
            elif result >= amount_needed:
                st.markdown('### Result:')
                st.markdown(f'### Congratulations! You can afford the {pct_down}% down payment on a house with desired price of ${total_price:,} in {num_years} years. :)))')
                st.markdown(f'### You will have ${result:,.2f} from your investments and savings.')
                st.markdown(
                    f'''### Make sure that you continue to save enough to pay the average monthly cost of ${monthly_payment_after_dp:,.2f}. 
                    * Calculated for a 30 year mortgage period - not including interest rate and taxes.'''
                    )
                st.markdown('This data is for informational purposes only.')
            else:
                st.markdown('### Result:')
                st.markdown(f'### Sorry! You need more time or higher portfolio to buy a house in {num_years} years. :(((')
                st.markdown(f'### You will have ${result:,.2f} from your investments and savings.')
                st.markdown('This data is for informational purposes only.')
            st.markdown('---')

            # Retrieve mapdata - addresses with RapidAPI - Zillow ---
            # perform the GET request
            response = requests.request('GET', url, headers=headers, params=query)
            response_json = response.json() # convert response to json

            # check if app recieved error code
            if int(response.status_code) != 200:
                st.markdown(f"### Approximate location of the houses in {desired_city}")
                st.markdown("Sorry! We couldn't get any response from the server. Try one more time.")
            else:
                if len(response_json) == 0: # check if json doesn't contain requested data
                    st.markdown(f"### Approximate location of the houses in {desired_city}")
                    st.markdown("We did not find any data that matches your request...")
                else:
                # pull desired data from json
                    df = pd.DataFrame()
                    count = 0
                    for address in response_json["props"]:
                        big_mac_index_data = {
                        "lon": [response_json["props"][count]['longitude']],
                        "lat": [response_json["props"][count]['latitude']],
                        "Address": [response_json["props"][count]['address']],
                        "Current price": [response_json["props"][count]['price']],
                        }
                        df = df.append(pd.DataFrame.from_dict(big_mac_index_data))
                        if count <= len(response_json["props"]):
                            count = count+1       
                    # filter results by current price
                    df_filtred_by_price = df[ (total_price-(total_price*0.2) <= df['Current price']) & (df['Current price'] <= total_price+(total_price*0.2))]
                    df_filtred_by_price = df_filtred_by_price.reset_index(drop=True)
                    
                    st.markdown(f"### Approximate locations of the houses in {desired_city}")
                    st.map(df_filtred_by_price) # generate map
                    st.markdown("### Houses we could find for you based on today's data:")
                    st.markdown("The current price results are within a 20% range of your desired price. The future price is calculated with an interest rate of 3.8%.") # 3.8% is the current reported average increase
                    st.write("Please refer to [Zillow](https://www.zillow.com) for more information.")
                    df_filtred_by_price_drop_lat_lon = df_filtred_by_price.drop(columns=['lon', 'lat']) # drop extra columns

                    # calculate future price
                    interest_rate = 0.038
                    df_filtred_by_price_drop_lat_lon["Future price"]=df_filtred_by_price_drop_lat_lon['Current price']*((1+interest_rate)**num_years)

                    # output table with addresses
                    df_filtred_by_price_drop_lat_lon
