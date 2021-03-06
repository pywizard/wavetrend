import time
#fix for autobahn on python 3.8 where time.clock() was removed
if not hasattr(time, "clock"):
    import timeit
    time.clock = timeit.default_timer

#fix for kraken
import os
from certifi import where
os.environ['SSL_CERT_FILE'] = where()

from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.depthcache import DepthCacheManager
from kraken_wsclient_py import kraken_wsclient_py as KrakenClient
import bitfinex
import threading
import json
from autobahn.twisted.websocket import  WebSocketClientProtocol

from bitfinex import WssClient

class BitfinexClientProtocol(WebSocketClientProtocol):

    def __init__(self, factory, payload=None):
        super().__init__()
        self.factory = factory
        self.payload = payload

    def onOpen(self):
        self.factory.protocol_instance = self

    def onConnect(self, response):
        if self.payload:
            self.sendMessage(self.payload, isBinary=False)
        # reset the delay after reconnecting
        self.factory.resetDelay()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            try:
                payload_obj = json.loads(payload.decode('utf8'))
            except ValueError:
                pass
            else:
                self.factory.callback(payload_obj)

    def connectionFailed(self, reason):
        super().connectionFailed(reason)

    def connectionLost(self, reason):
        super().connectionLost(reason)

    def connectionMade(self):
        super().connectionMade()

bitfinex.websockets.client.BitfinexClientProtocol = BitfinexClientProtocol

class Bitfinex:
    def __init__(self, account, api_key, api_secret):
        self.account = account
        self.api_key = api_key
        self.api_secret = api_secret
        self.manager_candlestick = WssClient(self.api_key, self.api_secret)
        self.manager_depth = WssClient(self.api_key, self.api_secret)
        self.manager_ticker = WssClient(self.api_key, self.api_secret)
        self.manager_trades = WssClient(self.api_key, self.api_secret)
        self.started_candlestick = False
        self.started_depth = False
        self.started_ticker = False
        self.started_trades = False
        self.markets = None

    def get_exchange_symbol(self, symbol):
        if self.markets is None:
            self.markets = self.account.fetch_markets(self.account.EXCHANGE_BITFINEX)
        for market in self.markets:
            if market["symbol"] == symbol:
                symbol = market["id"]
        return symbol

    def start_candlestick_websocket(self, symbol, interval, callback):
        self.symbol = self.get_exchange_symbol(symbol)
        self.manager_candlestick.subscribe_to_candles(symbol=self.symbol,timeframe=interval,callback=callback)
        if self.started_candlestick == False:
            self.manager_candlestick.start()
            self.started_candlestick = True

    def stop_candlestick_websocket(self):
        self.manager_candlestick.close()

    def start_ticker_websocket(self, symbol, callback):
        self.symbol = self.get_exchange_symbol(symbol)
        self.manager_ticker.subscribe_to_ticker(symbol=self.symbol,callback=callback)
        if self.started_ticker == False:
            self.manager_ticker.start()
            self.started_ticker = True

    def stop_ticker_websocket(self):
        self.manager_ticker.close()

    def start_depth_websocket(self, symbol, callback):
        self.symbol = self.get_exchange_symbol(symbol)
        self.manager_depth.subscribe_to_orderbook(symbol=self.symbol,precision="P1",callback=callback)
        if self.started_depth == False:
            self.manager_depth.start()
            self.started_depth = True

    def stop_depth_websocket(self):
        self.manager_depth.close()

    def start_trades_websocket(self, symbol, callback):
        self.symbol = self.get_exchange_symbol(symbol)
        self.manager_trades.subscribe_to_trades(symbol=self.symbol,callback=callback)
        if self.started_trades == False:
            self.manager_trades.start()
            self.started_trades = True

    def stop_trades_websocket(self):
        self.manager_trades.close()


class Binance:
    def __init__(self, account, api_key, api_secret):
        self.account = account
        sleep_time = 0.2
        while True:
            try:
                self.client = Client(api_key, api_secret)
                break
            except Exception:
                time.sleep(sleep_time)
                sleep_time = sleep_time * 2
                if sleep_time > 10:
                    sleep_time = 0.2

        self.manager = BinanceSocketManager(self.client)
        self.started = False
        self.markets = None

    def get_exchange_symbol(self, symbol):
        if self.markets is None:
            self.markets = self.account.fetch_markets(self.account.EXCHANGE_BINANCE)
        for market in self.markets:
            if market["symbol"] == symbol:
                symbol = market["id"]
        return symbol

    def start_candlestick_websocket(self, symbol, interval, callback):
        self.symbol = self.get_exchange_symbol(symbol)

        sleep_time = 0.2
        while True:
            try:
                self.connection_key = self.manager.start_kline_socket(self.symbol, callback, interval=interval)
                if self.started == False:
                    self.manager.start()
                    self.started = True
                break
            except Exception as e:
                time.sleep(sleep_time)
                sleep_time = sleep_time * 2
                if sleep_time > 30:
                    sleep_time = 0.2

    def stop_candlestick_websocket(self):
        try:
            self.manager.stop_socket(self.connection_key)
        except Exception as e:
            pass

    def start_depth_websocket_internal(self, symbol, callback):
        time.sleep(0.1)
        sleep_time = 0.2
        while True:
            try:
                self.depth_cache_manager = DepthCacheManager(self.client, self.symbol, callback=callback, limit=50, refresh_interval=0)
                self.started = True
                break
            except Exception as e:
                time.sleep(sleep_time)
                sleep_time = sleep_time * 2
                if sleep_time > 30:
                    sleep_time = 0.2

    def start_depth_websocket(self, symbol, callback):
        self.symbol = self.get_exchange_symbol(symbol)
        #Binance Depth Cache Websocket inititally fetches orderbook data from Binance,
        #which would block the main thread, put the start call into a thread
        thread = threading.Thread(target=self.start_depth_websocket_internal, args=(symbol, callback))
        thread.start()

    def stop_depth_websocket(self):
        try:
            self.depth_cache_manager.close(close_socket=True)
        except Exception as e:
            pass

    def start_trades_websocket(self, symbol, callback):
        self.symbol = self.get_exchange_symbol(symbol)
        sleep_time = 0.2
        while True:
            try:
                self.connection_key_trades = self.manager.start_trade_socket(self.symbol, callback)
                if self.started == False:
                    self.manager.start()
                    self.started = True
                break
            except Exception as e:
                time.sleep(sleep_time)
                sleep_time = sleep_time * 2
                if sleep_time > 30:
                    sleep_time = 0.2

    def stop_trades_websocket(self):
        try:
            self.manager.stop_socket(self.connection_key_trades)
        except Exception as e:
            pass

class Kraken:
    def __init__(self, account):
        self.account = account
        self.markets = None
        self.manager_candlestick = KrakenClient.WssClient()
        self.manager_depth = KrakenClient.WssClient()
        self.manager_ticker = KrakenClient.WssClient()
        self.manager_trades = KrakenClient.WssClient()
        self.started_candlestick = False
        self.started_depth = False
        self.started_ticker = False
        self.started_trades = False

    def get_exchange_symbol(self, symbol):
        if self.markets is None:
            self.markets = self.account.fetch_markets(self.account.EXCHANGE_KRAKEN)
        for market in self.markets:
            if market["symbol"] == symbol:
                symbol = market["id"]
        return symbol

    def start_candlestick_websocket(self, symbol, interval, callback):
        interval_table = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "2h": 2 * 60,
                         "3h": 3 * 60, "4h": 4 * 60, "6h": 6 * 60, "12h": 12 * 60,
                         "1d": 24 * 60, "1D": 24 * 60, "1w": 24 * 60 * 30}
        subscription = {'name': 'ohlc', 'interval': interval_table[interval]}
        self.manager_candlestick.subscribe_public(subscription=subscription, pair=[symbol], callback=callback)
        if self.started_candlestick == False:
            self.manager_candlestick.start()
            self.started_candlestick = True

    def stop_candlestick_websocket(self):
        self.manager_candlestick.close()

    def start_ticker_websocket(self, symbol, callback):
        subscription = {'name': 'ticker'}
        self.manager_ticker.subscribe_public(subscription=subscription, pair=[symbol], callback=callback)
        if self.started_ticker == False:
            self.manager_ticker.start()
            self.started_ticker = True

    def stop_ticker_websocket(self):
        self.manager_ticker.close()

    def start_depth_websocket(self, symbol, callback):
        subscription = {'name': 'book', 'depth': 25}
        self.manager_depth.subscribe_public(subscription=subscription, pair=[symbol], callback=callback)
        if self.started_depth == False:
            self.manager_depth.start()
            self.started_depth = True

    def stop_depth_websocket(self):
        try:
            self.manager_depth.close()
        except Exception as e:
            pass

    def start_trades_websocket(self, symbol, callback):
        subscription = {'name': 'trade'}
        self.manager_trades.subscribe_public(subscription=subscription, pair=[symbol], callback=callback)
        if self.started_trades == False:
            self.manager_trades.start()
            self.started_trades = True

    def stop_trades_websocket(self):
        self.manager_trades.close()
