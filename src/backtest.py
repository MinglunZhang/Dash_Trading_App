from datetime import datetime
import pandas as pd
import numpy as np
from numpy.linalg import LinAlgError

file_path = '../data/IVV.csv'
init_cash = 10000.0
sec_per_day = 86400
min_short = 5
max_short = 7
min_long = 10
max_long = 13

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
    buy = 0
    sell = 0
    vwap = float(table['VWAP'].iloc[idx - 1])
    for short_n in range(min_short, max_short):
        for long_n in range(min_long, max_long):
            short = get_average(idx, short_n, table)
            long = get_average(idx, long_n, table)
            pshort = get_average(idx - 1, short_n, table)
            plong = get_average(idx - 1, long_n, table)
            x = np.array([[plong - long, 1], [pshort - short, 1]])
            y = np.array([plong, pshort])
            try:
                joint = np.linalg.solve(x, y)[1]
                if joint < vwap:
                    sell += 1
                else:
                    buy += 1
            except LinAlgError:
                pass
    if buy > sell:
        return 'BUY'
    elif buy < sell:
        return 'SELL'
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
    end_date = '2015-05-10'
    blotter, ledger = backtest(start_date, end_date)
    print(blotter)
    print(ledger)


if __name__ == "__main__":
    main()
