import yfinance as yf
import numpy as np
from scipy.stats import norm

import pandas_market_calendars as mcal


# Define function for BNS jump test
def bns_jump_test(prices, alpha=0.05):

    n = len(prices)
    diff = np.diff(prices)
    s1 = np.sum(diff > 0)
    s2 = np.sum(diff < 0)
    if s1 == 0 or s2 == 0 or n <= 2:
        return False, 0, np.nan
    numerator = s1 * s2 * (n - s1) * (n - s2)
    if numerator == 0:
        return False, 0, 0
    denominator = (n - 1) * (n - 2)
    if denominator == 0:
        return False, 0, np.inf
    v = 2 * n * numerator / denominator
    se = np.sqrt(v) / np.sqrt(n)
    if np.isnan(se) or np.isinf(se):
        return False, 0, np.nan
    b = s1 - s2
    z = b / se
    p_value = 2 * (1 - norm.cdf(abs(z)))
    return p_value < alpha, b, se

# Define function for Andersen et al. jump detection scheme
def andersen_jump_detection(prices, jump_threshold=None):
    n = len(prices)
    if jump_threshold is None:
        _, _, se = bns_jump_test(prices)
        jump_threshold = 2 * se
    jump_flags = np.zeros(n)
    jump_flags[0] = 1
    for i in range(1, n):
        p_values = []
        for j in range(i):
            if jump_flags[j]:
                continue
            p_value, b, _ = bns_jump_test(prices[j:i])
            if p_value:
                p_values.append((j, b))
        if len(p_values) > 0:
            j, b = max(p_values, key=lambda x: abs(x[1]))
            if abs(b) >= jump_threshold:
                jump_flags[i] = 1
    return jump_flags, jump_threshold

def get_price_data(ticker, start_date, end_date, interval):
    stock = yf.Ticker(ticker)
    price_data = stock.history(start=start_date, end=end_date, interval=interval)
    return price_data

# Create a calendar
nyse = mcal.get_calendar('NYSE')

early = nyse.schedule(start_date='2022-01-01', end_date='2022-12-31', tz='America/New_York')

ticker = "AAPL"

for i in range(1, len(early)-1):
    


    yesterday_date = early.iloc[i-1]['market_close'].date()
    today_date = early.iloc[i]['market_close'].date()
    tomorrow_date = early.iloc[i+1]['market_close'].date()
    interval = "1h"  # daily intervals

    # Get Apple's price data
    yesterday_data = get_price_data(ticker, yesterday_date, today_date, interval)
    today_data = get_price_data(ticker, today_date, tomorrow_date, interval)

    # Combine yesterday's and today open price
    price_data = yesterday_data
    price_data.loc[len(price_data)] = today_data.iloc[0]
    
    jump_flags, jump_threshold = andersen_jump_detection(price_data["Close"].values)

    # Print results
    if np.sum(jump_flags) > 0:
        jump_indices = np.where(jump_flags == 1)[0]
        jump_dates = price_data.iloc[jump_indices].index
        print(f"Jump detected in {ticker} closing prices at the following dates:\n{jump_dates}")
        print(f"Jump threshold: {jump_threshold}")
    else:
        print(f"No jump detected in {ticker} closing prices between {yesterday_data} and {today_data}.")

    # overnight_jump = andersen_jump_detection_last(price_data["Close"].values)

    # # Print results
    # if overnight_jump:
    #     # jump_indices = np.where(jump_flags == 1)[0]
    #     jump_dates = price_data.iloc[len(price_data)].index
    #     print(f"Jump detected in {ticker} closing prices at the following dates:\n{jump_dates}")
    # else:
    #     print(f"No jump detected in {ticker} closing prices between {yesterday_date} and {today_date}.")
