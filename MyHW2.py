from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Seconds/Day
sec_per_day = 86400
# The start date of the data fetch
data_start_date = '1.1.2015'
# The end date of the data fetch
data_end_date = '1.1.2020'
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
    close = table['Close*'].iloc[trade_date - num_days:trade_date]
    total = 0.0
    for c in close:
        total += float(c)
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
    return "HOLD"


# To trade on the day
def trade(current_cash, current_share, current_trade_date, table, short_term, long_term):
    signal = get_signal(current_trade_date, short_term, long_term, table)
    # Spend all to buy, sell all for cash or stay on hold
    if signal == "BUY":
        current_share += current_cash / float(table['Open'].iloc[current_trade_date])
        current_cash = 0
    elif signal == "SELL":
        current_cash += current_share * float(table['Open'].iloc[current_trade_date])
        current_share = 0
    return current_cash, current_share


# Test on historical data
def back_test(table, short_term, long_term):
    current_cash = 10000.0
    current_share = 0.0
    # Start from day with full long average
    trade_start_date = long_term
    # End at the last row in the table
    trade_end_date = len(table) - 1
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
    # for shortP in range(1, 40):
    #     for longP in range(shortP + 1, 100):
    #         rtn = back_test(table, shortP, longP)
    #         if (rtn > mostrtn):
    #             mostrtn = rtn
    #             s = shortP
    #             l = longP
    # print(mostrtn)
    # print(s)
    # print(l)
    back_test(table, 2, 10)

if __name__ == "__main__":
    main()
