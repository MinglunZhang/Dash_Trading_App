# For utilities (helper functions) to be used in this HW.
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_usdt_rates(YYYY):
    # Requests the USDT's daily yield data for a given year. Results are
    #   returned as a DataFrame object with the 'Date' column formatted as a
    #   pandas datetime type.

    URL = 'https://www.treasury.gov/resource-center/data-chart-center/' + \
          'interest-rates/pages/TextView.aspx?data=yieldYear&year=' + str(YYYY)

    cmt_rates_page = requests.get(URL)

    soup = BeautifulSoup(cmt_rates_page.content, 'html.parser')

    table_html = soup.findAll('table', {'class': 't-chart'})

    df = pd.read_html(str(table_html))[0]
    df.Date = pd.to_datetime(df.Date)

    return df

def Y_m_d_to_unix_str(ymd_str):
    return str(int(time.mktime(pd.to_datetime(ymd_str).date().timetuple())))

def fetch_GSPC_data(start_date, end_date):
    # Requests the USDT's daily yield data for a given year. Results are
    #   returned as a DataFrame object with the 'Date' column formatted as a
    #   pandas datetime type.

    URL = 'https://finance.yahoo.com/quote/%5EGSPC/history?' + \
            'period1=' + Y_m_d_to_unix_str(start_date) + \
            '&period2=' + Y_m_d_to_unix_str(end_date) + \
            '&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true'

    gspc_page = requests.get(URL)

    soup = BeautifulSoup(gspc_page.content, 'html.parser')

    table_html = soup.findAll('table', {'data-test': 'historical-prices'})


    df = pd.read_html(str(table_html))[0]

    df.drop(df.tail(1).index, inplace=True)

    # see formats here: https://www.w3schools.com/python/python_datetime.asp
    df.Date = pd.to_datetime(df.Date)

    return df

