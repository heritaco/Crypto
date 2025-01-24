from pandas import DataFrame

from StockDataAnalysis.Coin import Coin


class Portfolio:
    """
    WARNING: This class has not been tested and I can't guarantee it will work as intended!

    A Data Structure that encompasses a set of coins, along with methods for
    the optimization of the weights set on each coin and predictions for
    their conjoined prices.

    :parameter:
        tokens : list
        These are the corresponding tokens for the Coin instances in the portfolio.
        Each element of the list must be a String, more specifically, it must be a
        valid token in the Binance database of coins. Each of these tokens will
        be transformed into a Coin.
        Each token is formed as Forex nicknames, e.g.: BTCUSDT, ETHUSDT.

        interval : str
        The length of each entry of the coin historical data. Must be one
        the followings:
        - Seconds:    1s
        - Minutes:    1m /   3m /   5m /  15m /  30m
        - Hours:      1h /   2h /   4h /   6h /   8h /  12h
        - Days:       1d /   3d
        - Weeks:      1w
        - Months:     1M
    """

    def __init__(self, tokens: list, interval="1h"):
        # tokens parameter is expected to be a non-empty list of strings
        # Before constructing the Coin List, we must also check that every token is a String

        if not isinstance(tokens, list):
            raise TypeError('tokens must be a list')

        if len(tokens) == 0:
            raise ValueError('tokens must contain at least one element')

        self.coins_list = []

        for token in tokens:
            if not isinstance(token, str):
                raise TypeError(f"Elements of tokens must be strings")

            self.coins_list.append(Coin(token, interval))

        self.profit_matrix = None
        self.covariance_matrix = None
        self.correlation_matrix = None

    def __len__(self):
        return len(self.coins_list)

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i < len(self):
            current_stock = self.coins_list[self.i]
            self.i += 1
            return current_stock

        raise StopIteration

    def get_profit_matrix(self, date_match=False):
        """
        This method returns the DataFrame for comparing the profit of the different
        coins in the Portfolio.

        :parameter:
            date_match : bool
            If date_match is set as True, only the dates that are available for all
            the coins in the Portfolio will be taken.

        :returns:
            profit_matrix : pandas.DataFrame
            The corresponding matrix that contains the profit of each Coin.
        """

        if self.profit_matrix is None:
            self.profit_matrix = DataFrame()

            # Create a list to store all DataFrames
            coin_data_frames = []

            # Collect historical prices for each coin
            for coin in self.coins_list:
                coin_data = coin.copy_data().loc[:, ["net_profit"]]
                coin_data_frames.append(coin_data)

            # Align all stocks by dates using an intersection of the indices
            common_dates = set.intersection(*(set(df.index) for df in coin_data_frames))
            common_dates = sorted(common_dates)  # Ensure the dates are sorted

            # Reindex each DataFrame to the common dates
            for coin, coin_data in zip(self.coins_list, coin_data_frames):
                aligned_data = coin_data.loc[common_dates]
                self.profit_matrix[coin] = aligned_data["net_profit"]

        return self.profit_matrix

    def get_correlation_matrix(self, date_match=False):
        """
        This method returns the DataFrame for comparing the profit of the different
        coins in the Portfolio through the correlation matrix.

        :parameter:
            date_match : bool
            If date_match is set as True, only the dates that are available for all
            the coins in the Portfolio will be taken.

        :returns:
            correlation_matrix : pandas.DataFrame
            The corresponding correlation matrix.
        """

        if self.profit_matrix is None:
            self.get_profit_matrix(date_match)

        if self.correlation_matrix is None:
            self.correlation_matrix = self.profit_matrix.corr()

        return self.correlation_matrix

    def get_covariance_matrix(self, date_match=False):
        """
        This method returns the DataFrame for comparing the profit of the different
        coins in the Portfolio through the covariance matrix.

        :parameter:
            date_match : bool
            If date_match is set as True, only the dates that are available for all
            the coins in the Portfolio will be taken.

        :returns:
            covariance_matrix : pandas.DataFrame
            The corresponding covariance matrix.
        """

        if self.profit_matrix is None:
            self.get_profit_matrix(date_match)

        if self.covariance_matrix is None:
            self.covariance_matrix = self.profit_matrix.cov()

        return self.covariance_matrix
