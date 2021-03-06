from ccxt.base.exchange import Exchange
import base64
import hashlib
import math
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import PermissionDenied
from ccxt.base.errors import ArgumentsRequired
from ccxt.base.errors import InsufficientFunds
from ccxt.base.errors import InvalidOrder
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import NotSupported
from ccxt.base.errors import DDoSProtection
from ccxt.base.errors import ExchangeNotAvailable
from ccxt.base.errors import InvalidNonce
from ccxt.base.decimal_to_precision import SIGNIFICANT_DIGITS
from ccxt.base.decimal_to_precision import decimal_to_precision
import json
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.pricing as pricing
import urllib3
import arrow
import warnings
import time
warnings.filterwarnings("ignore")

class oanda (Exchange):
    def __init__(self, account_id, account_token):
        self.account_id = account_id
        self.account_token = account_token
        self.oanda = oandapyV20.API(access_token=account_token)
        self.decimal_to_precision = decimal_to_precision
        self.timeframes = {
            '1m': 'M1',
            '5m': 'M5',
            '15m': 'M15',
            '30m': 'M30',
            '1h': 'H1',
            '2h': 'H2',
            '3h': 'H3',
            '4h': 'H4',
            '6h': 'H6',
            '8h': 'H8',
            '12h': 'H12',
            '1d': 'D',
            '1w': 'W'
        }
        self.elapsed_table = {"1m": 60, "3m": 60*3, "5m": 60*5, "15m": 60*15, "30m": 60*30, \
                 "1h": 60*60, "2h": 60*60*2, "3h": 60*60*3, "4h": 60*60*4, \
                 "6h": 60*60*6, "8h": 60*60*8, "12h": 60*60*12, "1d": 60*60*24, "1D": 60*60*24, \
                 "3d": 60*60*24*3, "3D": 60*60*24*3, "1w": 60*60*24*7}
    def describe(self):
        return self.deep_extend(super(oanda, self).describe(), {
            'id': 'oanda',
            'name': 'Oanda',
            'version': 'v1v2',
            'rateLimit': 1500,
            'certified': True,
            # new metainfo interface
            'has': {
                'CORS': False,
                'cancelAllOrders': False,
                'createDepositAddress': False,
                'deposit': False,
                'fetchClosedOrders': False,
                'fetchDepositAddress': False,
                'fetchTradingFee': False,
                'fetchTradingFees': False,
                'fetchFundingFees': False,
                'fetchMyTrades': False,
                'fetchOHLCV': True,
                'fetchOpenOrders': False,
                'fetchOrder': False,
                'fetchTickers': True,
                'fetchTransactions': False,
                'fetchDeposits': False,
                'fetchWithdrawals': False,
                'withdraw': False,
            },
        })

    def fetch_markets(self):
        sleep_time = 0.2
        while True:
            try:
                request = accounts.AccountInstruments(accountID=self.account_id)
                self.oanda.request(request)
                instruments = request.response["instruments"]
                result = {}
                id = 0
                for instrument in instruments:
                    id = id + 1
                    symbol = instrument["name"]
                    base = symbol.split("_")[0]
                    quote = symbol.split("_")[1]
                    baseId = 0
                    quoteId = 0
                    precision = {}
                    precision["price"] = instrument["displayPrecision"]
                    limits = None
                    market = None
                    name = instrument["displayName"]
                    type = instrument["type"]
                    result[symbol] = {
                        'id': id,
                        'symbol': symbol,
                        'name': name,
                        'type': type,
                        'base': base,
                        'quote': quote,
                        'baseId': baseId,
                        'quoteId': quoteId,
                        'active': True,
                        'precision': precision,
                        'limits': limits,
                        'info': market
                    }
                self.markets = result
                break
            except Exception as e:
                time.sleep(sleep_time)
                sleep_time = sleep_time * 2
                if sleep_time > 30:
                    sleep_time = 0.2

        return self.markets

    def is_instrument_halted(self, symbol):
        sleep_time = 1
        while True:
            try:
                request = pricing.PricingInfo(accountID=self.account_id, params={"instruments": symbol})
                self.oanda.request(request)
                tradeable = request.response["prices"][0]["tradeable"]
                break
            except Exception as e:
                time.sleep(sleep_time)
                sleep_time = sleep_time * 2
                if sleep_time > 60:
                    sleep_time = 1
        return tradeable

    def amount_to_precision(self, symbol, amount):
        return self.number_to_string(amount)

    def parse_ohlcv(self, ohlcv, market=None, timeframe='1m', since=None, limit=None):
        return [
            ohlcv[0],
            ohlcv[1],
            ohlcv[3],
            ohlcv[4],
            ohlcv[2],
            ohlcv[5],
        ]

    def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=None, params={}):
        sleep_time = 1
        while True:
            try:
                url = "https://api-fxtrade.oanda.com/v1/candles?instrument=" + symbol +"&count=" + str(limit) + "&candleFormat=midpoint&granularity=" + self.timeframes[timeframe]
                http = urllib3.PoolManager(cert_reqs='CERT_NONE')
                response = http.request('GET', url)
                json_body = json.loads(response.data.decode('utf-8'))
                if "candles" in json_body:
                    break
            except:
                time.sleep(1)
                sleep_time = sleep_time * 2
                if sleep_time > 30:
                    sleep_time = 1

        candles = []
        real_timestamps = []
        fake_timestamps = 86400
        for candle in json_body["candles"]:
            candle_time = candle["time"][:-8]
            timestamp = arrow.get(candle_time, 'YYYY-MM-DDTHH:mm:ss').datetime
            timestamp_local = arrow.Arrow.fromdatetime(timestamp).to('local').datetime
            real_timestamps.append(timestamp_local)
            candles.append([int(fake_timestamps), candle["openMid"], candle["highMid"], candle["lowMid"], candle["closeMid"], candle["volume"]])
            fake_timestamps = fake_timestamps + self.elapsed_table[timeframe]

        return candles, real_timestamps
