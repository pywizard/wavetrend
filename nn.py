#
# Copyright (c) 2019 Nikolaos Rangos. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
from sklearn.linear_model import LinearRegression
from PyQt5 import QtCore
import psutil
import time
import os
import sys
from exchange_accounts import EXCHANGE_BITFINEX
import traceback
import collections
import queue as Queue

def get_full_stacktrace():
    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
    if not exc is None:  # i.e. if an exception is present
        del stack[-1]       # remove call of full_stack, the printed exception
                            # will contain the caught exception caller instead
    trc = 'Traceback (most recent call last):\n'
    stackstr = trc + ''.join(traceback.format_list(stack))
    if not exc is None:
         stackstr += '  ' + traceback.format_exc().lstrip(trc)
    f = open("debug.log", "a")
    f.write(stackstr + "\n")
    f.close()
    return stackstr

class NeuralNetwork(QtCore.QThread):
    DISPLAY_LINE = QtCore.pyqtSignal(str)
    def __init__(self, parent, accounts):
        super(NeuralNetwork, self).__init__(parent)
        self.parent = parent
        self.train_input = []
        self.train_output = []
        self.train_times = []
        self.bid = []
        self.ask = []
        self.nn_qs = Queue.Queue()
        self.nn_qs_orderbook = collections.deque()
        self.current_order_id = 0
        self.symbol = "BTC/USDT"
        self.asset_balance_usd = 6000
        self.accounts = accounts
        self.current_order_id = 0
        self.exchange = EXCHANGE_BITFINEX
        self.trade_state = "NEUTRAL"
        self.train_time = time.time()
        self.trains_time = time.time()
        self.percent_check_time = time.time()
        self.first = True
        self.market_type_trending = True
        self.ai_trending_market = True
        self.predict_time = time.time() + 60 * 30  # XXX 60 multiplied by 30
        self.display_time = time.time()
        self.exit_thread = False

    def dobuy(self, price):
        try:
            percent = 1
            asset_balance = self.asset_balance_usd
            accounts = self.accounts
            amount = float(
                accounts.client(accounts.EXCHANGE_BITFINEX).amount_to_precision(self.symbol,
                                                                                (asset_balance / price) * percent))
            print(str(amount))
            try:
                if self.current_order_id != 0:
                    params = {'type': 'market'}
                    order = accounts.client_(accounts.EXCHANGE_BITFINEX).create_order(symbol=self.symbol, side="buy",
                                                                                      type="market", amount=amount,
                                                                                      params=params)
            except:
                print(get_full_stacktrace())
            params = {'type': 'market'}
            order = accounts.client_(accounts.EXCHANGE_BITFINEX).create_order(symbol=self.symbol, side="buy",
                                                                              type="market", amount=amount, params=params)
            self.current_order_id = int(order["id"])
        except:
            print(get_full_stacktrace())
            return

    def dosell(self, price):
        try:
            percent = 1
            asset_balance = self.asset_balance_usd
            accounts = self.accounts
            amount = float(accounts.client(accounts.EXCHANGE_BITFINEX).amount_to_precision(self.symbol,
                                                                                           (asset_balance / price) *
                                                                                           percent))
            print(str(amount))
            try:
                if self.current_order_id != 0:
                    params = {'type': 'market'}
                    order = accounts.client_(accounts.EXCHANGE_BITFINEX).create_order(symbol=self.symbol, side="sell",
                                                                                      type="market", amount=amount,
                                                                                      params=params)
            except:
                print(get_full_stacktrace())
            params = {'type': 'market'}
            order = accounts.client_(accounts.EXCHANGE_BITFINEX).create_order(symbol=self.symbol, side="sell",
                                                                              type="market", amount=amount, params=params)
            self.current_order_id = int(order["id"])
        except:
            print(get_full_stacktrace())
            return

    def run(self):
        while True:
            if self.exit_thread == True:
                break

            if self.market_type_trending == False and \
                    self.ai_trending_market == True:
                for ii in reversed(range(0, self.train_times)):
                    if time.time() - self.train_times[ii] > 60 * 60:
                        del self.train_input[:ii]
                        del self.train_output[:ii]
                        del self.train_times[:ii]
                        break

            if self.ai_trending_market == True:
                if time.time() - self.train_time > 60 * 60:
                    self.train_time = time.time()
                    del self.train_input[:int(len(self.train_input) / 2)]
                    del self.train_output[:int(len(self.train_output) / 2)]

            elif self.ai_trending_market == False:
                if time.time() - self.percent_check_time > 60 * 5:
                    total, available, percent, used, free = psutil.virtual_memory()
                    available_megabyte = available / (1024 * 1024)
                    process = psutil.Process(os.getpid())
                    process_rss_megabyte = process.memory_full_info().rss / (1024 * 1024)
                    if (process_rss_megabyte * 100) / available_megabyte > 50:
                        del self.train_input[:int(len(self.train_input) / 2)]
                        del self.train_output[:int(len(self.train_output) / 2)]
                    self.percent_check_time = time.time()

            if self.first == True or time.time() - self.trains_time > 60 * 30:
                market_str = ""
                if self.ai_trending_market == True:
                    market_str = "TREND"
                    self.market_type_trending = True
                else:
                    market_str = "SIDEWAYS"
                    self.market_type_trending = False
                self.DISPLAY_LINE.emit("Market Type: " + market_str)
                self.first = False
                self.trains_time = time.time()

            if time.time() - self.predict_time > 30:
                outcome_buystr = ""
                outcome_sellstr = ""

                predictor = LinearRegression(n_jobs=-1)

                if len(self.train_input) > len(self.train_output):
                    train_input_start_index = len(self.train_input) - len(self.train_output)
                elif len(self.train_output) > len(self.train_input):
                    train_output_start_index = len(self.train_output) - len(self.train_input)
                elif len(self.train_input) == len(self.train_output):
                    train_input_start_index = 0
                    train_output_start_index = 0
                try:
                    predictor.fit(X=self.train_input[train_input_start_index:],
                                  y=self.train_output[train_output_start_index:])
                except:
                    continue

                try:
                    percent = 1
                    asset_balance = self.asset_balance_usd
                    amount = float(
                        self.accounts.client(self.exchange).amount_to_precision(self.symbol,
                                                                                (asset_balance / self.bid[0]) * percent))
                    X_TEST = [[float(self.bid[0]), float(amount)]]
                    outcome = predictor.predict(X=X_TEST)
                    print("AI says buy? " + str(outcome[0]) + " " + str(self.bid[0]))
                    outcome_buystr = "AI says buy? " + str(outcome[0]) + " " + str(self.bid[0])
                    if outcome[0] > 0.7:
                        if self.trade_state == "NEUTRAL" or self.trade_state == "SOLD":
                            self.dobuy(self.bid[0])
                            self.trade_state = "BOUGHT"
                            outcome_buystr = outcome_buystr + " YES"
                except:
                    print(get_full_stacktrace())
                try:
                    percent = 1
                    asset_balance = self.asset_balance_usd
                    amount = float(self.accounts.client(self.exchange).amount_to_precision(self.symbol,
                                                                                            (asset_balance /
                                                                                             self.ask[0]) * percent))
                    X_TEST = [[float(self.ask[0]), float(amount)]]
                    outcome = predictor.predict(X=X_TEST)
                    print("AI says sell? " + str(outcome[0]) + " " + str(self.ask[0]))
                    outcome_sellstr = "AI says sell? " + str(outcome[0]) + " " + str(self.ask[0])
                    if outcome[0] < 0.3:
                        if self.trade_state == "NEUTRAL" or self.trade_state == "BOUGHT":
                            self.dosell(self.ask[0])
                            self.trade_state = "SOLD"
                            outcome_sellstr = outcome_sellstr + " YES"
                except:
                    print(get_full_stacktrace())

                if time.time() - self.display_time > 60 or outcome_buystr.find("YES") > -1 \
                        or outcome_sellstr.find("YES") > -1:
                    self.DISPLAY_LINE.emit(outcome_buystr)
                    self.DISPLAY_LINE.emit(outcome_sellstr)
                    self.display_time = time.time()

                self.predict_time = time.time()
            time.sleep(1)
