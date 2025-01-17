from pandas import (
    DataFrame,
    to_datetime
)

import numpy as np

from tabulate import tabulate

import datetime as dt

import requests
import json
import os


class Coin:
    """
    Description:
    A Class containing the historical data of the prices for a coin, along with
    the profit. It also allows the prediction of the prices through some
    simulation algorithms.


    Parameters:
    token : str
        The corresponding token that will be sent to the Binance database to
        download the historical data of the prices of the coin.

    interval : str
        The length of each entry of the coin historical data. Must be one of the
        followings:
        - Seconds:  1  s
        - Minutes:  1  m / 3  m / 5  m / 15 m / 30 m
        - Hours:    1  h / 2  h / 4  h / 6  h / 8  h / 12 h
        - Days:     1  d / 3  d
        - Weeks:    1  w
        - Months:   1  M

    Notes:
    Please make sure to check the Binance database for available coins!
    """

    def __init__(self, token: str, interval="1h"):
        # First, we validate the token and receive the data

        if not isinstance(token, str):
            raise TypeError("token must be a string")

        self.token = token
        self.data = download_data(token, interval)

        # We adjust the time as the corresponding

        self.data.reset_index(inplace=True)
        self.data.rename(columns={"index": "time"}, inplace=True)
        self.data["time"] = to_datetime(self.data["time"], unit="ms")
        self.data.set_index("time", inplace=True)

        # We adjust the data types of each column as well

        self.data["o"] = self.data["o"].apply(lambda x: float(x))
        self.data["h"] = self.data["h"].apply(lambda x: float(x))
        self.data["l"] = self.data["l"].apply(lambda x: float(x))
        self.data["c"] = self.data["c"].apply(lambda x: float(x))
        self.data["qav"] = self.data["qav"].apply(lambda x: float(x))
        self.data["taker_base_vol"] = self.data["taker_base_vol"].apply(lambda x: float(x))
        self.data["taker_quote_vol"] = self.data["taker_quote_vol"].apply(lambda x: float(x))

        # We add the profit and accumulated profit since data was downloaded

        self.data["profit"] = 100 * (self.data["c"] / self.data["c"].shift(1) - 1)
        self.data["accum_profit"] = (1 + self.data["profit"] / 100).cumprod() - 1
        self.data["accum_profit"] = self.data["accum_profit"] * 100

        # ADDING INDICATORS #
        # Moving Averages

        self.data["short_ma"] = self.data["c"].rolling(window=3, min_periods=1).mean()
        self.data["long_ma"] = self.data["c"].rolling(window=15, min_periods=1).mean()
        self.data["ma_diff"] = self.data["short_ma"] - self.data["long_ma"]

        # Buy / Sell Volume Difference

        self.data["buy_usdt_vol"] = self.data["taker_quote_vol"]
        self.data["sell_usdt_vol"] = self.data["qav"] - self.data["taker_quote_vol"]
        self.data["buy_sell_vol_ratio"] = self.data["buy_usdt_vol"] - self.data["sell_usdt_vol"]

        # Volume Difference Moving Average

        self.data["average_vol"] = self.data["buy_sell_vol_ratio"].rolling(window=3, min_periods=1).mean()

        # On Board Volume

        self.data["obv"] = 0
        self.data["obv"] = self.data["obv"].shift(1) + np.sign(self.data["profit"]) * self.data["qav"]

        # Relative Strength Index

        delta = self.data["c"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=3, min_periods=1, closed="left").mean()
        avg_loss = loss.rolling(window=3, min_periods=1, closed="left").mean()
        rs = avg_gain / avg_loss
        self.data["rsi"] = 100 - (100 / (1 + rs))

    def __str__(self):
        return self.token

    def copy_data(self):
        return self.data.copy(deep=False)

    def print_data(self):
        print(tabulate(self.data, headers="keys"))

    def export_data(self, file_path):
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        filename = f"{file_path}/{self.token}.csv"
        self.data.to_csv(filename)


def download_data(token, interval):
    """
    Description:
    This function sends a request to the Binance API and then returns the data
    as a JSON object. The data is transformed into a DataFrame and sent to the
    Coin object. The parameters are those sent directly to the Coin
    constructor method.


    Parameters:
    token : str
        The corresponding token that will be sent to the Binance database to
        download the historical data of the prices of the coin.

    interval : str
        The length of each entry of the coin historical data. Must be one of the
        followings:
        - Seconds:  1  s
        - Minutes:  1  m / 3  m / 5  m / 15 m / 30 m
        - Hours:    1  h / 2  h / 4  h / 6  h / 8  h / 12 h
        - Days:     1  d / 3  d
        - Weeks:    1  w
        - Months:   1  M


    Taken from:
    https://stackoverflow.com/questions/66295187/how-do-i-get-all-the-prices-history-with-binance-api-for-a-crypto-using-python
    """

    root_url = 'https://api.binance.com/api/v1/klines'
    url = root_url + '?symbol=' + token + '&interval=' + interval

    data = json.loads(requests.get(url).text)
    df = DataFrame(data)
    df.columns = ['open_time',
                  'o', 'h', 'l', 'c', 'v',
                  'close_time', 'qav', 'num_trades',
                  'taker_base_vol', 'taker_quote_vol', 'ignore']
    df.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in df.open_time]

    return df
