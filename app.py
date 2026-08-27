import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import requests

st.set_page_config(layout="wide")
st.title("Institutional Accumulation Tracker")

# Inputs
col_input1, col_input2 = st.columns(2)
with col_input1:
    ticker_input = st.text_input("Enter Ticker Symbol (e.g., MU, NVDA, BHP.AX)", value="MU").strip().upper()
with col_input2:
    period = st.selectbox("Select Timeframe", ["3m", "6m", "1y", "2y"], index=2)

if st.button("Analyze Stock"):
    if not ticker_input:
        st.warning("Please enter a ticker symbol.")
    else:
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        try:
            df = yf.download(ticker_input, period=period, progress=False, session=session)
            if df.empty:
                df = yf.Ticker(ticker_input, session=session).history(period=period)

            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df['Date_Str'] = df.index.strftime('%Y-%m-%d')
                df['Price_Diff'] = df['Close'].diff()
                df['OBV_Direction'] = np.where(df['Price_Diff'] > 0, 1, np.where(df['Price_Diff'] < 0, -1, 0))
                df['OBV'] = (df['Volume'] * df['OBV_Direction']).fillna(0).cumsum()

                # --- 2-COLUMN LAYOUT ---
                main_col, side_col = st.columns([2.2, 1.2], gap="medium")

                # Left Column: Main Price vs OBV Graph
                with main_col:
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
                    
                    ax1.plot(df.index, df['Close'], label='Price ($)', color='#1f77b4', linewidth=1.5)
                    ax1.set_title(f"{ticker_input} — Price vs. OBV Accumulation", fontsize=12, fontweight='bold')
                    ax1.set_ylabel("Price ($)")
                    ax1.grid(True, alpha=0.3)
                    ax1.legend(loc="upper left")

                    ax2.plot(df.index, df['OBV'] / 1e6, label='On-Balance Volume (M)', color='#2ca02c', linewidth=1.5)
                    ax2.set_ylabel("OBV (Millions)")
                    ax2.grid(True, alpha=0.3)
                    ax2.legend(loc="upper left")

                    st.pyplot(fig)

                # Right Column: Highest Volume Leaderboard (Horizontal Bars)
                with side_col:
                    st.markdown("### Top Volume Days Leaderboard")
                    st.caption(f"Ranked highest to lowest volume across the selected timeframe ({period}).")

                    # Filter top 15 highest volume days to keep display clean
                    top_vol_df = df.sort_values(by='Volume', ascending=True).tail(15).copy()
                    
                    # Create combined label with Date and Price
                    top_vol_df['Label'] = top_vol_df.apply(
                        lambda row: f"{row['Date_Str']}  (${row['Close']:.2f})", axis=1
                    )

                    # Up vs Down day coloring
                    top_vol_df['Color'] = np.where(top_vol_df['Price_Diff'] >= 0, 'Up Day', 'Down Day')

                    # Horizontal Bar Chart
                    fig_vol = px.bar(
                        top_vol_df,
                        x='Volume',
                        y='Label',
                        orientation='h',
                        text_auto='.2s',
                        color='Color',
                        color_discrete_map={'Up Day': '#2ca02c', 'Down Day': '#d62728'}
                    )
                    
                    fig_vol.update_layout(
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=550,
                        xaxis_title="Volume",
                        yaxis_title=None,
                        margin=dict(l=10, r=10, t=30, b=10)
                    )
                    
                    st.plotly_chart(fig_vol, use_container_width=True)

            else:
                st.error(f"No data returned for '{ticker_input}'.")
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
