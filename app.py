import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import requests

# Page layout configuration
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
        # Bypassing cloud rate limits
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        try:
            df = yf.download(ticker_input, period=period, progress=False, session=session)
            if df.empty:
                df = yf.Ticker(ticker_input, session=session).history(period=period)

            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # Calculate Accumulation Metrics
                df['Price_Diff'] = df['Close'].diff()
                df['OBV_Direction'] = np.where(df['Price_Diff'] > 0, 1, np.where(df['Price_Diff'] < 0, -1, 0))
                df['OBV'] = (df['Volume'] * df['OBV_Direction']).fillna(0).cumsum()

                # --- 2-COLUMN LAYOUT ---
                main_col, side_col = st.columns([2.2, 1], gap="medium")

                # Left Column: Main Price vs. OBV Graph
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

                # Right Column: Side-by-Side Volume Comparison Widget
                with side_col:
                    st.markdown("### Date Volume Comparison")
                    st.caption("Select two dates from the chart to compare institutional volume absorption.")

                    # Default to recent trading dates
                    available_dates = df.index.date
                    default_date_b = available_dates[-1]
                    default_date_a = available_dates[-6] if len(available_dates) >= 6 else available_dates[0]

                    date_a = st.date_input("Date A", value=default_date_a, min_value=available_dates[0], max_value=available_dates[-1])
                    date_b = st.date_input("Date B", value=default_date_b, min_value=available_dates[0], max_value=available_dates[-1])

                    # Filter for target dates
                    df_filtered = df[df.index.date.isin([date_a, date_b])].copy()

                    if not df_filtered.empty:
                        df_filtered['Date_Str'] = df_filtered.index.strftime('%Y-%m-%d')
                        df_filtered['Label'] = df_filtered.apply(
                            lambda row: f"{row['Date_Str']}<br><b>${row['Close']:.2f}</b>", axis=1
                        )

                        # Render Volume Bar Chart
                        fig_vol = px.bar(
                            df_filtered,
                            x='Label',
                            y='Volume',
                            text_auto='.2s',
                            color='Label',
                            color_discrete_sequence=['#1f77b4', '#2ca02c']
                        )
                        
                        fig_vol.update_layout(
                            showlegend=False,
                            height=350,
                            xaxis_title=None,
                            yaxis_title="Volume",
                            margin=dict(l=10, r=10, t=20, b=10)
                        )
                        st.plotly_chart(fig_vol, use_container_width=True)

                        # Context summary metrics
                        if len(df_filtered) == 2:
                            vol_diff = df_filtered['Volume'].iloc[-1] - df_filtered['Volume'].iloc[0]
                            pct_change = (vol_diff / df_filtered['Volume'].iloc[0]) * 100
                            st.metric(
                                label=f"Volume Shift ({df_filtered['Date_Str'].iloc[-1]} vs {df_filtered['Date_Str'].iloc[0]})",
                                value=f"{df_filtered['Volume'].iloc[-1]:,.0f}",
                                delta=f"{pct_change:+.1f}% Volume Change"
                            )
                    else:
                        st.warning("Selected dates fall on non-trading days (weekends/holidays). Choose valid market dates.")

            else:
                st.error(f"No data returned for '{ticker_input}'.")
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
