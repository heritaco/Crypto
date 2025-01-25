from pandas import (
    DataFrame,
    to_datetime,
    read_csv,
    concat
)

import numpy as np

from tabulate import tabulate

import datetime as dt

import requests
import json
import os


class Coin:
    """
    A Class containing the historical data of the prices for a coin, along
    with the profit. It also allows the prediction of the prices through
    some simulation algorithms.


    :parameter:
        token : str
        The corresponding token that will be sent to the Binance database
        to download the historical data of the prices of the coin.
        It is formed as Forex nicknames, e.g.: BTCUSDT, ETHUSDT.

        interval : str
        The length of each entry of the coin historical data. Must be one
        the followings:
        - Seconds:    1s
        - Minutes:    1m /   3m /   5m /  15m /  30m
        - Hours:      1h /   2h /   4h /   6h /   8h /  12h
        - Days:       1d /   3d
        - Weeks:      1w
        - Months:     1M

    Notes:
    Please make sure to check the Binance database for available coins!
    """

    def __init__(self, token: str, interval="1h"):
        # First, we validate the token and receive the data

        if not isinstance(token, str):
            raise TypeError("token must be a string")

        self.token = token
        self.data = download_data(token, interval)
        self.interval = interval

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

        # We add the net profit and max profit

        self.data["net_profit"] = 100 * (self.data["c"] / self.data["c"].shift(1) - 1)
        self.data["max_profit"] = 100 * (self.data["h"] / self.data["o"] - 1)

        # ADDING INDICATORS #

        # Buy / Sell Volume Difference

        self.data["buy_usdt_vol"] = self.data["taker_quote_vol"]
        self.data["sell_usdt_vol"] = self.data["qav"] - self.data["taker_quote_vol"]
        self.data["buy_sell_vol_diff"] = self.data["buy_usdt_vol"] - self.data["sell_usdt_vol"]

        # Volume Difference Moving Average

        self.data["average_vol"] = self.data["buy_sell_vol_diff"].rolling(window=3, min_periods=1).mean()

        # On Board Volume

        self.data["obv"] = 0
        self.data["obv"] = self.data["obv"].shift(1) + np.sign(self.data["net_profit"]) * self.data["qav"]

        # On Board Volume Moving Average

        self.data["obv_av"] = self.data["obv"].rolling(window=3).mean()

    def __str__(self):
        return self.token

    def copy_data(self):
        """
        This method returns a shallow copy of the historical data that can be modified
        without affecting the data atribute of the object.

        :parameter:
            none

        :returns:
            data_copy : pandas.DataFrame
            A shallow copy of the coin historical data. Changes done to the copy will
            not affect the data attribute of the object.
        """

        return self.data.copy(deep=False)

    def print_data(self):
        """
        This method prints the historical data of the coin directly into the console
        as a table.

        :parameter:
            none

        :returns:
            none
        """

        print(tabulate(self.data, headers="keys"))

    def export_data(self, file_path):
        """
        This method saves the historical data of the coin into a csv file. If the
        corresponding file already exists into the path, the new data that is not
        already in the file will be added.

        :parameter:
            file_path : str
            The path to the file where the data will be saved.

        :returns:
            none
        """

        file_name = f"{file_path}/{self.token}_{self.interval}.csv"

        # Remove the last tuple of the database, as it has incomplete data

        data_copy = self.data.iloc[:-1, :]

        # If the path does not exist, it is created

        if not os.path.exists(file_path):
            os.makedirs(file_path)

        # If the file already exists, it is update, otherwise, it is created

        if os.path.exists(file_name):
            data_copy = self.update_data(file_path)

        data_copy.to_csv(file_name)

    def update_data(self, file_path):
        """
        This method takes the historical data of the coin that is already saved
        in the path and updates it with the new data.

        :parameter:
            file_path : str
            The path to the file where the data is already saved.

        :returns:
            final_data : pandas.DataFrame
            The updated DataFrame.
        """

        saved_data = read_csv(f"{file_path}/{self.token}_{self.interval}.csv", index_col=0)
        new_data = self.copy_data()

        saved_data.index = to_datetime(saved_data.index)
        saved_index = set(saved_data.index)
        new_data = new_data.loc[~new_data.index.isin(saved_index)]
        new_data = new_data.dropna(inplace=True)
        final_data = concat([saved_data, new_data])

        return final_data


def download_data(token, interval):
    """
    This function sends a request to the Binance API and then returns the data
    as a JSON object. The data is transformed into a DataFrame and sent to the
    Coin object. The parameters are those sent directly to the Coin
    constructor method.


    :parameter:
        token : str
        The corresponding token that will be sent to the Binance database to
        download the historical data of the prices of the coin.

        interval : str
        The length of each entry of the coin historical data. Must be one of the
        followings:
        - Seconds:    1s
        - Minutes:    1m /   3m /   5m /  15m /  30m
        - Hours:      1h /   2h /   4h /   6h /   8h /  12h
        - Days:       1d /   3d
        - Weeks:      1w
        - Months:     1M


    :returns:
        historical_data : pandas.DataFrame
        The basic historical data of the prices of the coin, along with the
        corresponding volume.

    Taken from:
    https://stackoverflow.com/questions/66295187/how-do-i-get-all-the-prices-history-with-binance-api-for-a-crypto-using-python
    """

    root_url = 'https://api.binance.com/api/v1/klines'
    url = root_url + '?symbol=' + token + '&interval=' + interval

    data = json.loads(requests.get(url).text)
    historical_data = DataFrame(data)
    historical_data.columns = ['open_time',
                  'o', 'h', 'l', 'c', 'v',
                  'close_time', 'qav', 'num_trades',
                  'taker_base_vol', 'taker_quote_vol', 'ignore']
    historical_data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in historical_data.open_time]

    return historical_data
