from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

file_path = '../data/IVV.csv'
init_cash = 10000.0
sec_per_day = 86400


def get_average(idx, n, table):
    high = table['High']
    low = table['Low']
    openp = table['Open']
    close = table['Close']
    total = 0.0
    for i in range(idx - n, idx):
        total += (float(high.iloc[i]) + float(low.iloc[i]) + float(openp.iloc[i]) + float(close.iloc[i])) / 4
    return total / n


def get_signal(idx, table):
    short = get_average(idx, 5, table)
    long = get_average(idx, 10, table)
    pshort = get_average(idx - 1, 5, table)
    plong = get_average(idx - 1, 10, table)
    if short >= long and pshort <= plong:
        return "BUY"
    elif short <= long and pshort >= plong:
        return "SELL"
    return ""


def trade(idx, table, blotter, ledger):
    cash = init_cash
    position = 0.0
    if not ledger.empty:
        cash = float(ledger["cash"].iloc[-1])
        position = float(ledger["ivv_position"].iloc[-1])
    the_date = table["Date"].iloc[idx]
    action = get_signal(idx, table)
    size = 0.0
    price = float(table["Open"].iloc[idx])
    if action == "BUY":
        cost = cash / 2
        size = cost / price
        cash -= cost
        position += size
    elif action == "SELL":
        size = position / 2
        gain = size * price
        cash += gain
        position -= size
    p_value = position * price + cash
    p_return = p_value / init_cash - 1
    the_id = len(blotter.index) + 1
    blotter.loc[len(blotter.index)] = [the_date, the_id, action, "IVV", size, price, "MARKET", "FILLED"]
    ledger.loc[len(ledger.index)] = [the_date, position, price, cash, p_value, p_return]
    return blotter, ledger


def backtest(start_date, end_date):
    table = fetch_his_data()
    real_start = date_to_time(start_date)
    real_end = date_to_time(end_date)
    # find actual start date
    temp = table[table['Time'] == real_start]
    while temp.empty:
        real_start += sec_per_day
        temp = table[table['Time'] == real_start]
    start_idx = temp.index.tolist()[0]
    # find actual end date
    temp = table[table['Time'] == real_end]
    while temp.empty:
        real_end -= sec_per_day
        temp = table[table['Time'] == real_end]
    end_idx = temp.index.tolist()[0]

    # start trading
    blotter = pd.DataFrame(None, columns=['date', 'id', 'action', 'symbol', 'size', 'price', 'type', 'status'])
    ledger = pd.DataFrame(None,
                          columns=['date', 'ivv_position', 'ivv_price', 'cash', 'portfolio_value', 'portfolio_returns'])
    while start_idx <= end_idx:
        blotter, ledger = trade(start_idx, table, blotter, ledger)
        start_idx += 1
    return blotter, ledger


def date_to_time(date):
    return int(datetime.strptime(date, "%Y-%m-%d").timestamp())


def fetch_his_data():
    table = pd.read_csv(file_path)
    date = table["Date"].tolist()
    timelist = []
    for each in date:
        timelist.append(date_to_time(each))
    table.insert(1, "Time", timelist, True)
    return table


def main():
    start_date = '2015-04-03'
    end_date = '2016-04-10'
    blotter, ledger = backtest(start_date, end_date)
    print(blotter)
    print(ledger)


if __name__ == "__main__":
    main()
