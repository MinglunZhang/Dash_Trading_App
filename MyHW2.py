from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Seconds/Day
sec_per_day = 86400
# The start date of the data fetch
data_start_date = '1.12.2015'
# The end date of the data fetch
data_end_date = '31.12.2020'
# The stock chosen to analyze
target_stock = "IVV"


# Helper method to fetch data table from the yahoo finance
def fetch_helper(stock, start_string, end_string):
    url = 'https://finance.yahoo.com/quote/' + \
          stock + \
          '/history?period1=' + \
          start_string + \
          '&period2=' + \
          end_string + \
          '&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true'
    gspc_page = requests.get(url)
    soup = BeautifulSoup(gspc_page.content, 'html.parser')
    table_html = soup.findAll('table', {'data-test': 'historical-prices'})
    df = pd.read_html(str(table_html))[0]
    df.drop(df.tail(1).index, inplace=True)
    df.Date = pd.to_datetime(df.Date)
    return df


# Method to generate data table with ascending order from day 1
def fetch_historical_data(stock, start, end):
    table = None
    # Due to the html design of yahoo finance, cannot retrieve large data at once
    data_size = 100
    while end - start > data_size * sec_per_day:
        new_table = fetch_helper(stock, str(start), str(start + data_size * sec_per_day))
        table = pd.concat([new_table, table], ignore_index=True)
        start += data_size * sec_per_day
    new_table = fetch_helper(stock, str(start), str(end))
    table = pd.concat([new_table, table], ignore_index=True)
    # remove unuseful rows
    table = table[~table.Open.str.contains("Dividend")]
    table = table[~table.Open.str.contains("Stock Split")]
    # stupid method for resetting the index
    table = table.iloc[::-1]
    table = pd.concat([None, table], ignore_index=True)
    return table


# Use close price of each day to calculate average price
def get_average_price(trade_date, num_days, table):
    high = table['High'].iloc[trade_date - num_days:trade_date]
    low = table['Low'].iloc[trade_date - num_days:trade_date]
    open = table['Open'].iloc[trade_date - num_days:trade_date]
    close = table['Close*'].iloc[trade_date - num_days:trade_date]
    ad_close = table['Adj Close**'].iloc[trade_date - num_days:trade_date]
    total = 0.0
    for idx in range(0, num_days):
        current_high = float(high.iloc[idx])
        current_low = float(low.iloc[idx])
        current_open = float(open.iloc[idx])
        current_close = float(close.iloc[idx])
        current_adjust_close = float(ad_close.iloc[idx])
        total += (current_close + current_open + current_high + current_low + current_adjust_close) / 5
    return total / num_days


# Find the joint price and determine to buy, sell or hold
def get_signal(current_trade_date, short_term, long_term, table):
    # To determine if there is a joint point of two average lines
    short_avg = get_average_price(current_trade_date, short_term, table)
    long_avg = get_average_price(current_trade_date, long_term, table)
    pre_short_avg = get_average_price(current_trade_date - 1, short_term, table)
    pre_long_avg = get_average_price(current_trade_date - 1, long_term, table)
    if short_avg >= long_avg and pre_short_avg < pre_long_avg:
        return "BUY"
    elif short_avg <= long_avg and pre_short_avg > pre_long_avg:
        return "SELL"
    # todo: add more signal
    return "HOLD"


# To trade on the day
def trade(current_cash, current_share, current_trade_date, table, short_term, long_term):
    signal = get_signal(current_trade_date, short_term, long_term, table)
    # Spend all to buy, sell all for cash or stay on hold
    # todo: adjust the purchase and sell rate
    if signal == "BUY":
        cost = current_cash / 2
        current_share += cost / float(table['Open'].iloc[current_trade_date])
        current_cash -= cost
    elif signal == "SELL":
        amount = current_share / 5
        current_cash += amount * float(table['Open'].iloc[current_trade_date])
        current_share -= amount
    return current_cash, current_share


# Test on historical data
def back_test(table, short_term, long_term):
    current_cash = 10000.0
    current_share = 0.0
    # Start from day with full long average
    trade_start_date = 30 + 1
    # End at the last row in the table
    trade_end_date = len(table) - 1
    print("Start Trading Date: " + str(table['Date'].iloc[trade_start_date]))
    print("End Trading Date: " + str(table['Date'].iloc[trade_end_date]))
    print("Initial Cash: " + str(current_cash))
    # Open price on the first day and the close price on the last day
    sell_price = float(table['Close*'].iloc[trade_end_date])
    buy_price = float(table['Open'].iloc[trade_start_date])
    print("Regular Return: " + str(round((sell_price / buy_price * current_cash), 2)))
    current_trade_date = trade_start_date
    while current_trade_date <= trade_end_date:
        current_cash, current_share = trade(current_cash, current_share, current_trade_date, table, short_term,
                                            long_term)
        current_trade_date += 1
    final_property = round(current_cash + current_share * sell_price, 2)
    print("Model Return: " + str(final_property))
    return final_property


# Main method
def main():
    start = datetime.strptime(data_start_date, '%d.%m.%Y').timestamp()
    end = datetime.strptime(data_end_date, '%d.%m.%Y').timestamp()
    table = fetch_historical_data(target_stock, int(start), int(end))
    # mostrtn = 0
    # s = 0
    # l = 0
    # for shortP in range(5, 10):
    #     print(shortP)
    #     for longP in range(20, 30):
    #         rtn = back_test(table, shortP, longP)
    #         if (rtn > mostrtn):
    #             mostrtn = rtn
    #             s = shortP
    #             l = longP
    # print(mostrtn)
    # print(s)
    # print(l)
    back_test(table, 7, 20)






if __name__ == "__main__":
    main()
