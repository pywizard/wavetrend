import ccxt
import sys

EXCHANGE_BITFINEX = "BITFINEX"
EXCHANGE_BINANCE = "BINANCE"
EXCHANGE_KRAKEN = "KRAKEN"

class ExchangeAccounts:
    def __init__(self, exchanges):
        self.exchanges = {}
        self.EXCHANGE_BITFINEX = "BITFINEX"
        self.EXCHANGE_BINANCE = "BINANCE"
        self.EXCHANGE_KRAKEN = "KRAKEN"

        for exchange in exchanges:
            exchange_name = exchange[0]
            exchange_api_key = exchange[1]
            exchange_api_secret = exchange[2]
            if exchange_name == EXCHANGE_BITFINEX:
                self.exchanges[EXCHANGE_BITFINEX] = {}
                self.exchanges[EXCHANGE_BITFINEX]["api_key"] = exchange_api_key
                self.exchanges[EXCHANGE_BITFINEX]["api_secret"] = exchange_api_secret
            elif exchange_name == EXCHANGE_BINANCE:
                self.exchanges[EXCHANGE_BINANCE] = {}
                self.exchanges[EXCHANGE_BINANCE]["api_key"] = exchange_api_key
                self.exchanges[EXCHANGE_BINANCE]["api_secret"] = exchange_api_secret
            elif exchange_name == EXCHANGE_KRAKEN:
                self.exchanges[EXCHANGE_KRAKEN] = {}
                self.exchanges[EXCHANGE_KRAKEN]["api_key"] = exchange_api_key
                self.exchanges[EXCHANGE_KRAKEN]["api_secret"] = exchange_api_secret
            else:
                print("Please configure a valid Exchange.")
                sys.exit(1)

    def initialize(self):
        for exchange_name in self.exchanges.keys():
            if exchange_name == EXCHANGE_BITFINEX:
                self.exchanges[exchange_name]["client"] = ccxt.bitfinex2({
                    'apiKey': self.exchanges[EXCHANGE_BITFINEX]["api_key"],
                    'secret': self.exchanges[EXCHANGE_BITFINEX]["api_secret"],
                    'enableRateLimit': True
                })
            elif exchange_name == EXCHANGE_BINANCE:
                self.exchanges[exchange_name]["client"] = ccxt.binance({
                    'apiKey': self.exchanges[EXCHANGE_BINANCE]["api_key"],
                    'secret': self.exchanges[EXCHANGE_BINANCE]["api_secret"],
                    'enableRateLimit': True,
                    'options': {'adjustForTimeDifference': True}
                })
            elif exchange_name == EXCHANGE_KRAKEN:
                self.exchanges[exchange_name]["client"] = ccxt.kraken({
                    'apiKey': self.exchanges[EXCHANGE_KRAKEN]["api_key"],
                    'secret': self.exchanges[EXCHANGE_KRAKEN]["api_secret"],
                    'enableRateLimit': True
                })
            else:
                print("Please configure a valid Exchange.")
                sys.exit(1)
            self.exchanges[exchange_name]["markets"] = self.exchanges[exchange_name]["client"].fetch_markets()
            self.exchanges[exchange_name]["tickers"] = self.exchanges[exchange_name]["client"].fetch_tickers()

    def fetch_tickers(self, exchange):
        return self.exchanges[exchange]["client"].fetch_tickers()

    def get_symbol_price(self, exchange, symbol):
        return self.fetch_tickers(exchange)[symbol]["last"]

    def get_asset_from_symbol(self, exchange, symbol):
        for market in self.exchanges[exchange]["markets"]:
            if market["symbol"] == symbol:
                return market["base"]

    def get_quote_from_symbol(self, exchange, symbol):
        for market in self.exchanges[exchange]["markets"]:
            if market["symbol"] == symbol:
                return market["quote"]

    def client(self, exchange):
        return self.exchanges[exchange]["client"]

    def get_orderbook(self, exchange, symbol):
        return self.exchanges[exchange]["client"].fetch_order_book(symbol)
