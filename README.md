**📈 Cumulative Average Research Tool**

A web-based dashboard designed to identify stock trends using the Cumulative Average Strategy, popularized by Sri Mahesh Chander Kaushik. This tool helps investors decide whether to "Buy/Average" a position or "Avoid" it based on price momentum since the yearly high.

**🎥 Strategy Reference:** Watch the Strategy on YouTube: https://www.youtube.com/watch?v=hLYGIhMYO7M&t=1492s

**🚀 Features**

Automated Data Fetching: Pulls real-time NSE data via Yahoo Finance.

Smart Signal Logic: Calculates 10-day cumulative averages to generate BUY or AVOID signals.

Excel-Style UI: Clean, grid-based dashboard for easy data visualization.

Custom Watchlist: Monitors your personal holdings via an external Excel file.

**🛠️ Installation & Setup**
1. Prerequisites
Ensure you have Python installed. You will need to install the following dependencies. Note that curl_cffi is required to prevent Yahoo Finance from blocking your requests.

Bash
pip install streamlit yfinance pandas curl_cffi openpyxl
2. Configuration
Clone or download this repository to your local machine.

Open the stocks.xlsx file.

Add the stock symbols you wish to monitor (use the .NS suffix for NSE stocks, e.g., BAJFINANCE.NS).

3. Running the App
Navigate to the project folder in your terminal and run:

Bash
streamlit run app.py
The app will automatically launch in your default web browser (usually at http://localhost:8501).

**📊 How it Works**
Identify the Peak: The tool finds the highest price of the stock in the last 365 days.

Track the Recovery: It analyzes all data points from that high-date to the current date.

**Signal Generation:**

BUY / HOLD: If the current price is above the 10-day cumulative average.

AVOID / HOLD: If the current price is below the 10-day cumulative average.

**⚖️ Disclaimer**
This tool is for educational purposes only. Trading in the stock market involves risk. Please consult with a financial advisor before making any investment decisions based on this strategy.
