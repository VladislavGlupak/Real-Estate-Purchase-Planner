import streamlit as st
import pandas as pd
import numpy as np

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
years = st.sidebar.slider('How many yesrs?', 0, 50, 25) # min, max, default

st.markdown('### Your entered data:')
st.write('Monthly Contribution to Investments, $ - ', cont_monthly)
st.write('Portfolio Type for Contributions - ', pf_type_cont)
st.write('Current Holdings of Portfolio, $ - ', curr_holdings)
st.write('Portfolio Type for Current Holdings - ', pf_type_cont)
st.write('You entered the desired price $: - ', total_price)
st.write('Down Payment % - ', down_payment)
st.write('Nuber of years - ', years)