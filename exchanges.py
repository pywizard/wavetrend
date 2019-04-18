from binance.client import Client
from binance.websockets import BinanceSocketManager

class Binance:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)
        self.manager = BinanceSocketManager(self.client)

    def start_candlestick_websocket(self, symbol, interval, callback):
        self.symbol = symbol.split("/")[0] + symbol.split("/")[1]
        self.connection_key = self.manager.start_kline_socket(self.symbol, callback, interval=interval)
        self.manager.start()

    def stop_candlestick_websocket(self):
        self.manager.stop_socket(self.connection_key)