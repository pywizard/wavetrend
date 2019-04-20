from bitfinex import WssClient
from binance.client import Client
from binance.websockets import BinanceSocketManager

class Bitfinex:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.manager_candlestick = WssClient(self.api_key, self.api_secret)
        self.manager_depth = WssClient(self.api_key, self.api_secret)
        self.started_candlestick = False
        self.started_depth = False

    def start_candlestick_websocket(self, symbol, interval, callback):
        self.symbol = symbol.split("/")[0] + symbol.split("/")[1]
        self.manager_candlestick.subscribe_to_candles(symbol=self.symbol,timeframe=interval,callback=callback)
        if self.started_candlestick == False:
            self.manager_candlestick.start()
            self.started_candlestick = True

    def stop_candlestick_websocket(self):
        self.manager_candlestick.close()

    def start_depth_websocket(self, symbol, callback):
        self.symbol = symbol.split("/")[0] + symbol.split("/")[1]
        self.manager_depth.subscribe_to_orderbook(symbol=self.symbol,precision="P1",callback=callback)
        if self.started_depth == False:
            self.manager_depth.start()
            self.started_depth = True

    def stop_depth_websocket(self):
        self.manager_depth.close()


class Binance:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)
        self.manager = BinanceSocketManager(self.client)
        self.started = False

    def start_candlestick_websocket(self, symbol, interval, callback):
        self.symbol = symbol.split("/")[0] + symbol.split("/")[1]
        self.connection_key = self.manager.start_kline_socket(self.symbol, callback, interval=interval)
        if self.started == False:
            self.manager.start()
            self.started = True

    def stop_candlestick_websocket(self):
        self.manager.stop_socket(self.connection_key)

    def start_depth_websocket(self, symbol, callback):
        self.symbol = symbol.split("/")[0] + symbol.split("/")[1]
        self.depth_key = self.manager.start_depth_socket(self.symbol, callback, depth=BinanceSocketManager.WEBSOCKET_DEPTH_20)
        if self.started == False:
            self.manager.start()
            self.started = True

    def stop_depth_websocket(self):
        self.manager.stop_socket(self.depth_key)
