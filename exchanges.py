from binance.client import Client
from binance.websockets import BinanceSocketManager

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
