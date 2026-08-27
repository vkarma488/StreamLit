import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Institutional Accumulation Tracker")

# User inputs
ticker_symbol = st.text_input("Enter Ticker Symbol", value="NVDA").upper()
period = st.selectbox("Select Timeframe", ["3m", "6m", "1y"], index=1)

if st.button("Analyze Stock"):
    df = yf.Ticker(ticker_symbol).history(period=period)
    
    if not df.empty:
        # Technical Calculations
        df['Price_Diff'] = df['Close'].diff()
        df['OBV_Direction'] = np.where(df['Price_Diff'] > 0, 1, np.where(df['Price_Diff'] < 0, -1, 0))
        df['OBV'] = (df['Volume'] * df['OBV_Direction']).fillna(0).cumsum()

        # Plotting
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        ax1.plot(df.index, df['Close'], label='Price ($)', color='#1f77b4')
        ax1.set_title(f"{ticker_symbol} Price vs. OBV Accumulation")
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        ax2.plot(df.index, df['OBV'] / 1e6, label='On-Balance Volume (M)', color='#2ca02c')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        st.pyplot(fig)
    else:
        st.error("Invalid Ticker or No Data Found")
