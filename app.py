import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Configure page to wide mode
st.set_page_config(layout="wide")

# Custom CSS for headers
st.markdown("""
    <style>
    .metric-header {
        background-color: #f2f2f2;
        padding: 8px;
        border: 1px solid #d4d4d4;
        font-weight: bold;
        text-align: center;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("NSE Stock Analysis Dashboard")

# 1. Fetch Data from yfinance
def get_data(ticker):
    """Fetch 365 days of OHLCV data for a single ticker"""
    df = yf.download(ticker, start=(datetime.now() - timedelta(days=365)), progress=False)
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        if df.columns.nlevels == 2:
            df.columns = df.columns.get_level_values(0)
        else:
            df.columns = ["_".join(map(str, c)) for c in df.columns]
    return df

# Load stock list from Excel file
def load_stock_list():
    try:
        excel_file = 'stocks.xlsx'
        stock_df = pd.read_excel(excel_file, sheet_name='nifty-500')  # Stock list sheet
        if stock_df.shape[1] > 0 and stock_df.shape[0] > 0:
            # Get the first column as stock list
            stocks = stock_df.iloc[:, 0].dropna().tolist()
            # Convert to NSE tickers (append .NS if not present)
            stocks = [f"{s}.NS" if not s.endswith(".NS") else s for s in stocks]
            return stocks
    except Exception as e:
        st.warning(f"Could not load stock list from Excel: {e}")
    # Fallback to hardcoded list
    return ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"]

# 2. Stock Selection - Load from Excel
stocks = load_stock_list()

# Create tabs for different views
tab1, tab2 = st.tabs(["Single Stock Analysis", "BUY Eligible Stocks"])

# ==================== TAB 1: Single Stock Analysis ====================
with tab1:
    stock_name = st.selectbox("Select Stock", stocks)

    if stock_name:
        try:
            df = get_data(stock_name)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            df = pd.DataFrame()

        if not df.empty:
            # Step 2: Find all-time high price and date in last 365 days
            df_reset = df.reset_index()
            if 'Date' not in df_reset.columns:
                df_reset.rename(columns={df_reset.columns[0]: 'Date'}, inplace=True)

            # Find row with maximum High value
            max_high_idx = df_reset['High'].idxmax()
            max_high_row = df_reset.loc[max_high_idx]

            yearly_high = max_high_row['High']
            high_date = max_high_row['Date']

            if pd.isna(yearly_high) or pd.isna(high_date):
                st.error("Unable to determine high date – no valid data.")
            else:
                # Step 3: Filter from high date onwards and calculate cumulative average
                df_analysis = df.loc[high_date:].copy()
                df_analysis = df_analysis.reset_index()
                # Cumulative average from day 1 (average of all days from high date onwards)
                df_analysis['Cumulative Average'] = df_analysis['Close'].expanding().mean()

                # Display top metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="metric-header">Stock Name</div>', unsafe_allow_html=True)
                    st.subheader(stock_name.replace('.NS', ''))
                with col2:
                    st.markdown('<div class="metric-header">All Time High Date (Last 365 Days)</div>', unsafe_allow_html=True)
                    st.subheader(high_date.strftime('%d-%b-%Y'))

                # Calculate signal for Last 10 Days trend
                last_10_for_signal = df_analysis[['Cumulative Average']].tail(10).reset_index(drop=True)
                last_10_values_signal = last_10_for_signal['Cumulative Average'].values.astype(float)

                # Compare latest price (index -1, newest) with oldest price (index 0, oldest)
                latest_price = last_10_values_signal[-1]  # Newest date (last index)
                oldest_price = last_10_values_signal[0]  # Oldest date (first index)

                # Determine signal: BUY if latest > oldest (price increasing), AVOID if latest < oldest (price decreasing)
                signal = "BUY" if latest_price > oldest_price else "AVOID / HOLD"
                signal_color = "green" if latest_price > oldest_price else "red"

                col_signal = st.columns(1)[0]
                with col_signal:
                    st.markdown('<div class="metric-header">Signal (Last 10 Days Trend)</div>', unsafe_allow_html=True)
                    if signal_color == "green":
                        st.success(signal)
                    else:
                        st.error(signal)

                # Candlestick Chart
                st.write("### Candlestick Chart (From High Date)")
                if PLOTLY_AVAILABLE:
                    fig = go.Figure(data=[go.Candlestick(
                        x=df_analysis['Date'],
                        open=df_analysis['Open'],
                        high=df_analysis['High'],
                        low=df_analysis['Low'],
                        close=df_analysis['Close']
                    )])
                    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("Install plotly: pip install plotly")

                # Step 5: Display last 10 days in descending order
                st.write("### Last 10 Days (Descending Order)")
                last_10 = df_analysis[['Date', 'Cumulative Average']].tail(10).iloc[::-1].reset_index(drop=True)
                last_10['Date'] = last_10['Date'].dt.strftime('%d-%b-%Y')
                last_10_values = last_10['Cumulative Average'].values.astype(float)

                # Determine colors based on trend
                color_list = []
                for i in range(len(last_10_values)):
                    if i < len(last_10_values) - 1:
                        if last_10_values[i] >= last_10_values[i + 1]:
                            color_list.append('green')
                        else:
                            color_list.append('red')
                    else:
                        color_list.append('lightgray')

                # Format the cumulative average column
                last_10['Cumulative Average'] = last_10['Cumulative Average'].apply(lambda x: f"{x:.2f}")
                last_10.columns = ['Date', 'Cumulative Average']

                try:
                    # Apply color styling by row
                    def color_row(row):
                        idx = row.name
                        color = color_list[idx] if idx < len(color_list) else 'white'
                        return [f'background-color: {color}; color: white' if col == 'Cumulative Average' else '' for col in row.index]

                    styled_last_10 = last_10.style.apply(color_row, axis=1)
                    st.dataframe(styled_last_10, width='stretch')
                except Exception:
                    st.dataframe(last_10, width='stretch')

                # Step 3 & 4: Full analysis data - all days from high date with cumulative average
                st.write("### Full Analysis (All Days from High Date)")
                analysis_table = df_analysis[['Date', 'Close', 'Cumulative Average']].copy()
                analysis_table['Date'] = analysis_table['Date'].dt.strftime('%d-%b-%Y')
                analysis_table['Close'] = analysis_table['Close'].apply(lambda x: f"{x:.2f}")
                analysis_table['Cumulative Average'] = analysis_table['Cumulative Average'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
                analysis_table.columns = ['Date', 'Closing Price', 'Cumulative Average']

                st.write(f"**Total days from high date: {len(analysis_table)}**")
                st.dataframe(analysis_table, width='stretch')

                # Summary metrics
                st.write("### Summary")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("All Time High Price", f"₹{yearly_high:.2f}")
                with col_b:
                    current_price = df_analysis['Close'].iloc[-1]
                    st.metric("Current Price", f"₹{current_price:.2f}")
                with col_c:
                    latest_avg = df_analysis['Cumulative Average'].iloc[-1]
                    if pd.notna(latest_avg):
                        st.metric("Latest Cumulative Avg", f"₹{latest_avg:.2f}")
                    else:
                        st.metric("Latest Cumulative Avg", "N/A")

# ==================== TAB 2: BUY Eligible Stocks ====================
with tab2:
    st.write("### Stocks with BUY Signal")
    st.write("Analyzing stocks based on last 10 days cumulative average trend...")

    if st.button("Scan All Stocks"):
        buy_stocks = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, stock in enumerate(stocks):
            status_text.text(f"Analyzing {stock}... ({idx+1}/{len(stocks)})")
            progress_bar.progress((idx + 1) / len(stocks))

            try:
                df = get_data(stock)
                if df.empty:
                    continue

                df_reset = df.reset_index()
                if 'Date' not in df_reset.columns:
                    df_reset.rename(columns={df_reset.columns[0]: 'Date'}, inplace=True)

                max_high_idx = df_reset['High'].idxmax()
                max_high_row = df_reset.loc[max_high_idx]
                high_date = max_high_row['Date']

                if pd.isna(high_date):
                    continue

                df_analysis = df.loc[high_date:].copy()
                df_analysis = df_analysis.reset_index()
                df_analysis['Cumulative Average'] = df_analysis['Close'].expanding().mean()

                if len(df_analysis) < 10:
                    continue

                last_10_values = df_analysis['Cumulative Average'].tail(10).values.astype(float)
                latest_price = last_10_values[-1]
                oldest_price = last_10_values[0]

                if latest_price > oldest_price:
                    current_price = df_analysis['Close'].iloc[-1]
                    buy_stocks.append({
                        'Stock': stock.replace('.NS', ''),
                        'Current Price': f"₹{current_price:.2f}",
                        'Latest Avg': f"₹{latest_price:.2f}",
                        'Trend': '📈 Increasing'
                    })
            except Exception:
                continue

        status_text.empty()
        progress_bar.empty()

        if buy_stocks:
            st.success(f"Found {len(buy_stocks)} stocks with BUY signal")
            buy_df = pd.DataFrame(buy_stocks)
            st.dataframe(buy_df, width='stretch')
        else:
            st.warning("No stocks found with BUY signal")