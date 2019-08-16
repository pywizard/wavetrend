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
import tpqoa
import json
import requests
import arrow
import warnings
warnings.filterwarnings("ignore")

class oanda (Exchange):
    def __init__(self, account_id, account_token):
        f = open("oanda.cfg", "w")
        f.write("[oanda]\naccount_id = " + account_id + "\naccess_token = " + account_token + "\naccount_type = practice\n")
        f.close()
        self.oanda = tpqoa.tpqoa('oanda.cfg')
        self.decimal_to_precision = decimal_to_precision
        self.timeframes = {
            '1m': 'M1',
            '5m': 'M5',
            '15m': 'M15',
            '30m': 'M30',
            '1h': 'H1',
            '3h': 'H3',
            '6h': 'H5',
            '12h': 'H12',
            '1d': 'D',
            '1w': 'W',
            '1M': 'M',
        }
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

    def fetch_markets(self, params={}):
        instruments = self.oanda.get_instruments()
        result = {}
        id = 0
        for instrument in instruments:
            id = id + 1
            symbol = instrument[1]
            base = symbol.split("_")[0]
            quote = symbol.split("_")[1]
            baseId = 0
            quoteId = 0
            precision = {}
            precision["price"] = 4
            limits = None
            market = None
            name = instrument[0]
            result[symbol] = {
                'id': id,
                'symbol': symbol,
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

    def amount_to_precision(self, symbol, amount):
        return self.number_to_string(amount)

    def fetch_balance(self, params={}):
        return 0

    def fetch_order_book(self, symbol, limit=None, params={}):
        return #XXX
        self.load_markets()
        request = {
            'symbol': self.market_id(symbol),
        }
        if limit is not None:
            request['limit_bids'] = limit
            request['limit_asks'] = limit
        response = self.publicGetBookSymbol(self.extend(request, params))
        return self.parse_order_book(response, None, 'bids', 'asks', 'price', 'amount')

    def fetch_tickers(self, symbols=None, params={}):
        instruments = self.oanda.get_instruments()
        instrument_list = instruments[0][1]
        for instrument in instruments:
            if instrument[1] == instruments[0][1]:
                continue
            instrument_list = instrument_list + "," + instrument[1]

        pricing_response = self.oanda.ctx.pricing.get(
            self.oanda.account_id,
            instruments=instrument_list,
            since=None,
            includeUnitsAvailable=False
        )

        json_response = json.loads(pricing_response.raw_body)

        result = {}
        for price in json_response["prices"]:
            ticker = self.parse_ticker(price)
            symbol = ticker['symbol']
            result[symbol] = ticker
            for instrument in instruments:
                if instrument[1] == symbol:
                    ticker["name"] = instrument[0]
                    break
        return result

    def fetch_ticker(self, symbol, params={}):
        pricing_response = self.oanda.ctx.pricing.get(
            self.oanda.account_id,
            instruments=symbol,
            since=None,
            includeUnitsAvailable=False
        )

        result = {}
        for price in pricing_response.get("prices", 200):
            ticker = self.parse_ticker(price)
            symbol = ticker['symbol']
            result[symbol] = ticker

        return result

    def parse_ticker(self, ticker, market=None):
        symbol = ticker["instrument"]
        bid = ticker["bids"][0]["price"]
        ask = ticker["asks"][0]["price"]
        return {
            'symbol': symbol,
            'bid': self.safe_float(ticker, 'bid'),
            'ask': self.safe_float(ticker, 'ask'),
        }

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
        url = "https://api-fxtrade.oanda.com/v1/candles?instrument=" + symbol +"&count=" + str(limit) + "&candleFormat=midpoint&granularity=" + self.timeframes[timeframe] + "&dailyAlignment=0&alignmentTimezone=America%2FNew_York"
        response = requests.get(url)
        json_body = response.json()

        candles = []
        for candle in json_body["candles"]:
            candle_time = candle["time"][:-8]
            timestamp = arrow.get(candle_time, 'YYYY-MM-DDTHH:mm:ss').timestamp
            candles.append([timestamp, candle["openMid"], candle["highMid"], candle["lowMid"], candle["closeMid"],candle["volume"]])

        return candles

    def handle_errors(self, code, reason, url, method, headers, body, response):
        if response is None:
            return
        if code >= 400:
            if body[0] == '{':
                feedback = self.id + ' ' + self.json(response)
                message = None
                if 'message' in response:
                    message = response['message']
                elif 'error' in response:
                    message = response['error']
                else:
                    raise ExchangeError(feedback)  # malformed(to our knowledge) response
                exact = self.exceptions['exact']
                if message in exact:
                    raise exact[message](feedback)
                broad = self.exceptions['broad']
                broadKey = self.findBroadlyMatchedKey(broad, message)
                if broadKey is not None:
                    raise broad[broadKey](feedback)
                raise ExchangeError(feedback)  # unknown message
