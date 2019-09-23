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
    def __init__(self, parent, accounts, symbol):
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
        self.symbol = symbol
        self.asset_balance_usd = 6000
        self.accounts = accounts
        self.current_order_id = 0
        self.exchange = EXCHANGE_BITFINEX
        self.trade_state = "NEUTRAL"
        self.percent_check_time = time.time()
        self.first = True
        self.ai_trending_market = True
        self.predict_time = time.time()
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

            self.train_input = []
            self.train_output = []
            self.train_times = []

            all_trades = {}

            for ii in reversed(range(0, 25)):
                trades_since_1day = self.accounts.client(EXCHANGE_BITFINEX).fetchTrades(self.symbol, time.time() * 1000 - 86400000 * ii,
                                                                               5000)
                for trade in trades_since_1day:
                    trade_outcome = 1
                    if trade["side"] == "sell":
                        trade_outcome = 0
                    elif trade["side"] == "buy":
                        trade_outcome = 1

                    trade_existing = False
                    if trade["price"] in all_trades and all_trades[trade["price"]] == trade["timestamp"]:
                        trade_existing = True

                    if trade_existing == False:
                        self.train_input.append([trade["price"], trade["amount"]])
                        self.train_output.append(trade_outcome)
                        self.train_times.append(trade["timestamp"] / 1000)
                        all_trades[trade["price"]] = trade["timestamp"]

            predictor = LinearRegression(n_jobs=-1)

            outcome_above_sum = 0
            outcome_below_sum = 0
            outcome_above = 0
            outcome_below = 0
            counter = 0
            while True:
                print(str(counter) + "/" + str(len(self.train_times)))

                counter_neg = counter * -1
                counter = counter + 125
                if counter >= len(self.train_times):
                    break

                predictor.fit(X=self.train_input[counter_neg:],
                              y=self.train_output[counter_neg:])

                current_bid = self.train_input[counter_neg:][1]
                percent = 1
                amount = float(
                    self.accounts.client(self.exchange).amount_to_precision(self.symbol,
                                                                            (self.asset_balance_usd / current_bid[
                                                                                0]) * percent))
                X_TEST = [[current_bid[0], amount]]
                outcome = predictor.predict(X=X_TEST)[0]
                if outcome > 0.5:
                    outcome_above_sum = outcome_above_sum + outcome
                    outcome_above = outcome_above + 1
                elif outcome < 0.5:
                    outcome_below_sum = outcome_below_sum + outcome
                    outcome_below = outcome_below + 1

            limit_above = outcome_above_sum / outcome_above
            limit_below = outcome_below_sum / outcome_below
            self.DISPLAY_LINE.emit("limit above 0.5 = " + str(limit_above))
            self.DISPLAY_LINE.emit("limit below 0.5 = " + str(limit_below))

            time_start = time.time()
            while True:
                if time.time() - time_start > 60*60:
                    break

                if self.exit_thread == True:
                    break

                if time.time() - self.predict_time > 60:
                    outcome_buystr = ""
                    outcome_sellstr = ""

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
                        if self.trade_state == "SOLD" and outcome[0] > 0.5:
                            self.dobuy(self.bid[0])
                            self.trade_state = "NEUTRAL"
                            outcome_buystr = outcome_buystr + " YES"
                        elif outcome[0] > limit_above:
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
                        if self.trade_state == "BOUGHT" and outcome[0] < 0.5:
                            self.dosell(self.ask[0])
                            self.trade_state = "NEUTRAL"
                            outcome_sellstr = outcome_sellstr + " YES"
                        elif outcome[0] < limit_below:
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
