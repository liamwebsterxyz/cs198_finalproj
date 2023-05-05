import yfinance as yf
import numpy as np
from scipy import stats


def realized_quadratic_variation(log_prices):
    log_returns = np.diff(log_prices)
    return np.sum(log_returns**2)

def realized_bipower_variation(log_prices, beta=0.5):
    log_returns = np.diff(log_prices)
    return np.sum(np.abs(log_returns[:-1]) ** beta * np.abs(log_returns[1:]) ** beta)

def bns_jump_test(log_prices, significance_level=0.01):
    n = len(log_prices) - 1
    qv = realized_quadratic_variation(log_prices)
    bv = realized_bipower_variation(log_prices)
    
    # Test statistic
    mu = (bv / n) * (1 + (2 ** (-1)) * ((8 / (3 * n)) ** 0.5))
    test_stat = (qv - mu * n) / (bv * (1 - (1 / n)) ** (-1))
    
    # Critical value
    critical_value = stats.norm.ppf(1 - significance_level)
    
    # If test_stat > critical_value, we reject the null hypothesis (no jumps) and conclude that there is a jump.
    jump_detected = test_stat > critical_value
    
    return jump_detected, test_stat, critical_value

def threshold_bipower_variation(log_returns, threshold):
    n = len(log_returns)
    bv = np.sum(np.minimum(np.abs(log_returns[:-1]), threshold) * np.minimum(np.abs(log_returns[1:]), threshold))
    tbv = (n - 1) * (threshold ** 2) - bv
    return tbv

def andersen_jump_identification(log_prices, threshold, significance_level=0.01):
    n = len(log_prices) - 1
    log_returns = np.diff(log_prices)
    
    qv = realized_quadratic_variation(log_prices)
    bv = realized_bipower_variation(log_prices)
    tbv = threshold_bipower_variation(log_returns, threshold)

    # Test statistic
    mu = tbv / n
    test_stat = (qv - mu * n) / (bv * (1 - (1 / n)) ** (-1))
    
    # Critical value
    critical_value = stats.norm.ppf(1 - significance_level)
    
    # If test_stat > critical_value, we reject the null hypothesis (no jumps) and conclude that there is a jump.
    jump_detected = test_stat > critical_value
    
    return jump_detected, test_stat, critical_value

def combined_jump_detection(log_prices, threshold, significance_level=0.01):
    bns_jump, bns_test_stat, bns_critical_value = bns_jump_test(log_prices, significance_level)
    andersen_jump, andersen_test_stat, andersen_critical_value = andersen_jump_identification(log_prices, threshold, significance_level)
    
    # Only consider a jump to be present if both tests indicate a jump.
    jump_detected = bns_jump and andersen_jump
    
    return jump_detected, bns_test_stat, bns_critical_value, andersen_test_stat, andersen_critical_value

def get_price_data(ticker, start_date, end_date, interval):
    stock = yf.Ticker(ticker)
    price_data = stock.history(start=start_date, end=end_date, interval=interval)
    return price_data

def main():


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

        # Calculate log prices
        log_prices = np.log(price_data['Close'].values)

        # Calculate threshold for Andersen et al. (2010) method
        threshold = np.percentile(np.abs(np.diff(log_prices)), 95)

        # Apply combined jump detection strategy
        jump_detected, bns_test_stat, bns_critical_value, andersen_test_stat, andersen_critical_value = combined_jump_detection(log_prices, threshold)

        print("Jump detected:", jump_detected)
        print("BNS test statistic:", bns_test_stat)
        print("BNS critical value:", bns_critical_value)
        print("Andersen test statistic:", andersen_test_stat)
        print("Andersen critical value:", andersen_critical_value)

if __name__ == "__main__":
    main()

