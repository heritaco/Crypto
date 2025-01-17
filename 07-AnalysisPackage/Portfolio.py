from pandas import DataFrame

from StockDataAnalysis.Coin import Coin


class Portfolio:
    """
    Description:
    A Data Structure that encompasses a set of coins, along with methods for
    the optimization of the weights set on each coin and predictions for
    their conjoined prices.

    Parameters:
    tokens : list
        These are the corresponding tokens for the Coin instances in the portfolio.
        Each element of the list must be a String, more specifically, it must be a
        valid token in the CoinGecko database of coins. Each of these tokens will
        be transformed into a Coin.

    interval : str
        The length of each entry of the coin historical data. Must be one of the
        followings:
        - daily
        - hourly
        - minutely

        WARNINGS:
        Only the "daily" interval is currently supported.

    days : int
        The length of the period that the historical data will be taken from.
        Must be a positive integer matching the interval:
        - daily:        91 - 365
        - hourly:        2 - 90
        - minutely:      1

        NOTES:
        For recently launched coins, the number of days selected could be
        greater than the number of available days.
    """

    def __init__(self, tokens: list, interval="daily", days=365):
        # tokens parameter is expected to be a non-empty list of strings
        # Before constructing the Coin List, we must also check that every token is a String

        if not isinstance(tokens, list):
            raise TypeError('tokens must be a list')

        if len(tokens) == 0:
            raise ValueError('tokens must contain at least one element')

        self.coins_data = []

        for token in tokens:
            if not isinstance(token, str):
                raise TypeError(f"Elements of tokens must be strings")

            self.coins_data.append(Coin(token, interval, days))

        self.profit_matrix = None
        self.covariance_matrix = None
        self.correlation_matrix = None

    def __len__(self):
        return len(self.coins_data)

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i < len(self):
            current_stock = self.coins_data[self.i]
            self.i += 1
            return current_stock

        raise StopIteration

    def get_profit_matrix(self):
        if self.profit_matrix is None:
            self.profit_matrix = DataFrame()

            # Create a list to store all DataFrames
            coin_data_frames = []

            # Collect historical prices for each coin
            for coin in self.coins_data:
                coin_data = coin.copy_data().loc[:, ["Periodic Profit"]]
                coin_data_frames.append(coin_data)

            # Align all stocks by dates using an intersection of the indices
            common_dates = set.intersection(*(set(df.index) for df in coin_data_frames))
            common_dates = sorted(common_dates)  # Ensure the dates are sorted

            # Reindex each DataFrame to the common dates
            for coin, coin_data in zip(self.coins_data, coin_data_frames):
                aligned_data = coin_data.loc[common_dates]
                self.profit_matrix[coin] = aligned_data["Periodic Profit"]

        return self.profit_matrix

    # Construction of the Correlation and Covariance Matrix

    def get_correlation_matrix(self):
        if self.profit_matrix is None:
            self.get_profit_matrix()

        if self.correlation_matrix is None:
            self.correlation_matrix = self.profit_matrix.corr()

        return self.correlation_matrix

    def get_covariance_matrix(self):
        if self.profit_matrix is None:
            self.get_profit_matrix()

        if self.covariance_matrix is None:
            self.covariance_matrix = self.profit_matrix.cov()

        return self.covariance_matrix
