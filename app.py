import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests

st.title("Institutional Accumulation Tracker")

# Ticker input
ticker_input = st.text_input("Enter Ticker Symbol (e.g., NVDA, BHP.AX)", value="NVDA").strip().upper()
period = st.selectbox("Select Timeframe", ["3m", "6m", "1y"], index=1)

if st.button("Analyze Stock"):
    if not ticker_input:
        st.warning("Please enter a ticker symbol.")
    else:
        # Override default user-agent to bypass cloud IP blocking
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        try:
            # 1. Primary Download Attempt
            df = yf.download(ticker_input, period=period, progress=False, session=session)
            
            # 2. Fallback Attempt via Ticker object if download returns empty
            if df.empty:
                ticker = yf.Ticker(ticker_input, session=session)
                df = ticker.history(period=period)

            if not df.empty:
                # Handle MultiIndex column formatting in newer yfinance versions
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # Calculate Accumulation Metrics
                df['Price_Diff'] = df['Close'].diff()
                df['OBV_Direction'] = np.where(df['Price_Diff'] > 0, 1, np.where(df['Price_Diff'] < 0, -1, 0))
                df['OBV'] = (df['Volume'] * df['OBV_Direction']).fillna(0).cumsum()

                # Render Plots
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
                
                ax1.plot(df.index, df['Close'], label='Price ($)', color='#1f77b4')
                ax1.set_title(f"{ticker_input} — Price vs. OBV Accumulation")
                ax1.grid(True, alpha=0.3)
                ax1.legend(loc="upper left")

                ax2.plot(df.index, df['OBV'] / 1e6, label='On-Balance Volume (M)', color='#2ca02c')
                ax2.grid(True, alpha=0.3)
                ax2.legend(loc="upper left")

                st.pyplot(fig)
            else:
                st.error(f"Unable to fetch data for '{ticker_input}'. If searching non-US markets, ensure you add the suffix (e.g., BHP.AX for ASX or RELIANCE.NS for NSE).")
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
