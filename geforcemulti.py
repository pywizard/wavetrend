import warnings
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import platform
import numpy as np
from numpy import NaN, Inf, arange, isscalar, asarray, array
from matplotlib.finance import *
from matplotlib.widgets import MultiCursor
from datetime import timedelta
import sys
import hashlib
import hmac
import time
import datetime
from PyQt4 import QtGui, QtCore, uic
import traceback
import copy
import threading
import pandas as pd
import talib
import math
import gc
from config import *
import platform
import ctypes
import os
import Queue
from playsound import playsound
import ccxt

if exchange == "HITBTC":
  client = ccxt.hitbtc2({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
elif exchange == "BINANCE":
   client = ccxt.binance({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  }) 
elif exchange == "BITSTAMP":
   client = ccxt.bitstamp({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
elif exchange == "GEMINI":
   client = ccxt.gemini({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
elif exchange == "OKEX":
   client = ccxt.okex({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
elif exchange == "BITMEX":
   client = ccxt.bitmex({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
elif exchange == "GDAX":
   client = ccxt.gdax({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
elif exchange == "KRAKEN":
   client = ccxt.kraken({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
elif exchange == "BITTREX":
   client = ccxt.bittrex({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
else:
  print "Please configure a valid Exchange."
  sys.exit(1)

class abstract():
  pass

config = {}

green = "#50B787"
greenish = "#136D6F"
red = "#E0505E"
black = "#131D27"
darkish = "#363C4E"
white = "#C6C7C8"

def _candlestick(ax, quotes, first, last_line1, last_line2, last_rect, candle_width, width=0.2, colorup='white', colordown='black',
                 alpha=1.0):

    """
    Plot the time, open, high, low, close as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of quote sequences
        data to plot.  time must be in float date format - see date2num
        (time, open, high, low, close, ...) vs
        (time, open, close, high, low, ...)
        set by `ochl`
    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level
    ochl: bool
        argument to select between ochl and ohlc ordering of quotes

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """

    width = candle_width
    OFFSET = width / 2.0

    lines = []
    patches = []

    colorup = "#13525E"
    colordown = "#9F2207"
    colorup2 = "#50B787"
    colordown2 = "#E0505E"

    if first == False:
      quotes = [quotes[-1]]
    for q in quotes:
        t, open, high, low, close = q[:5]

        if close >= open:
            color = colorup
            color2 = colorup2
            lower = open
            higher = close
            height = close - open
            vline1 = Line2D(
                xdata=(t, t), ydata=(higher, high),
                color=colorup2,
                linewidth=0.5,
                antialiased=True,
            )

            vline2 = Line2D(
                xdata=(t, t), ydata=(low, lower),
                color=colorup2,
                linewidth=0.5,
                antialiased=True,
            )
            
            rect = Rectangle(
                xy=(t - OFFSET, lower),
                width=width,
                height=height,
                facecolor=color,
                edgecolor=colorup2,
                linewidth=0.5
            )
        else:
            color = colordown
            color2 = colordown2
            lower = close
            higher = open
            height = open - close
            vline1 = Line2D(
                xdata=(t, t), ydata=(higher, high),
                color=colordown2,
                linewidth=0.5,
                antialiased=True,
            )

            vline2 = Line2D(
                xdata=(t, t), ydata=(low, lower),
                color=colordown2,
                linewidth=0.5,
                antialiased=True,
            )            

            rect = Rectangle(
                xy=(t - OFFSET, lower),
                width=width,
                height=height,
                facecolor=color,
                edgecolor=colordown2,
                linewidth=0.5
            )

        if first == True:
          lines.append(vline1)
          lines.append(vline2)
          patches.append(rect)
          ax.add_line(vline1)
          ax.add_line(vline2)
          ax.add_patch(rect)
          last_line1 = vline1
          last_line2 = vline2
          last_rect = rect
        else:
          last_line1.set_ydata((high, higher))
          last_line2.set_ydata((low, lower))
          last_rect.set_y(lower)
          last_rect.set_height(height)
          last_rect.set_facecolor(color)
          last_rect.set_edgecolor(color2)
        
    ax.autoscale_view()

    return last_line1, last_line2, last_rect

def _invalidate_internal(self, value, invalidating_node):
    """
    Called by :meth:`invalidate` and subsequently ascends the transform
    stack calling each TransformNode's _invalidate_internal method.
    """
    # determine if this call will be an extension to the invalidation
    # status. If not, then a shortcut means that we needn't invoke an
    # invalidation up the transform stack as it will already have been
    # invalidated.

    # N.B This makes the invalidation sticky, once a transform has been
    # invalidated as NON_AFFINE, then it will always be invalidated as
    # NON_AFFINE even when triggered with a AFFINE_ONLY invalidation.
    # In most cases this is not a problem (i.e. for interactive panning and
    # zooming) and the only side effect will be on performance.
    status_changed = self._invalid < value

    if self.pass_through or status_changed:
        self._invalid = value

        for parent in self._parents.values():
            parent._invalidate_internal(value=value,
                                        invalidating_node=self)

matplotlib.transforms.TransformNode._invalidate_internal = _invalidate_internal

class abstract():
  pass

def get_symbol_price(symbol):
  sym = client.fetch_ticker(symbol)
  return float(sym["last"])

def get_full_stacktrace():
    import traceback, sys
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

def BBANDS(real, timeperiod=5, nbdevup=2, nbdevdn=2):
    ma = pd.rolling_mean(real, timeperiod, min_periods=timeperiod)
    std = pd.rolling_std(real, timeperiod, min_periods=timeperiod)
    lo = ma - nbdevdn * std
    hi = ma + nbdevup * std
    return hi, ma, lo

def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

def get_asset_from_symbol(symbol):
  return symbol.split("/")[0]

def get_quote_from_symbol(symbol):
  return symbol.split("/")[1]

def translate_buy_amount_percent(index):
  if index == 0:
    return .25
  elif index == 1:
    return .5
  elif index == 2:
    return .75
  elif index == 3:
    return .90

def translate_buy_amount_percent_reversed(index):
  if index == 0:
    return .90
  elif index == 1:
    return .75
  elif index == 2:
    return .5
  elif index == 3:
    return .25
    
qs = {}
aqs = {}
qs_local = Queue.Queue()

FIGURE_ADD_SUBPLOT = 0
FIGURE_TIGHT_LAYOUT = 1
FIGURE_CLEAR = 2
CANVAS_GET_SIZE = 3
CANVAS_DRAW_IDLE = 4
SHOW_STATUSBAR_MESSAGE = 0

days_table = {"1m": 0.17, "5m": .9, "15m": 2.5, "30m": 5 , "1h": 10, "4h": 40, "6h": 60, "12h": 120, "1d": 240}

def ceil_dt(dt, seconds):
    # how many secs have passed this hour
    nsecs = dt.minute*60 + dt.second + dt.microsecond*1e-6  
    # number of seconds to next quarter hour mark
    # Non-analytic (brute force is fun) way:  
    #   delta = next(x for x in xrange(0,3601,900) if x>=nsecs) - nsecs
    # analytic way:
    delta = math.ceil(nsecs / seconds) * seconds - nsecs
    #time + number of seconds to quarter hour mark.
    return dt + datetime.timedelta(seconds=delta)

def run_geforce(symbol, tab_index, timeframe_entered):
    global qs
    global aqs
    global days_table
    
    time.sleep(2)

    days_entered = days_table[timeframe_entered]

    to_sell = 0

    init = True
    prev_trade_time = 0
    counter = 0
    wt_was_rising = False
    first = True
    last_line1 = None
    last_line2 = None
    last_rect = None
    while True:
        try:
          if first == True:
            date, open_, high, low, close, vol, limit, timestamp = getData(timeframe_entered, days_entered, symbol, False)
          else:
            date2, open2_, high2, low2, close2, vol2, limit2, timestamp2 = getData(timeframe_entered, days_entered, symbol, True)
          
          if first == True:
            qs[tab_index].put(FIGURE_ADD_SUBPLOT)
            ax = aqs[tab_index].get()
            ax3 = ax.twinx()
            first_candle_date = timestamp[-1]

            prices = []
            for i in range(0, len(date)):
                prices.append((date2num(date[i]), open_[i], high[i], low[i], close[i], vol[i], date[i]))
          else:
            prices[-1] = (date2num(date2[1]), open2_[1], high2[1], low2[1], close2[1], vol2[1], date2[1])
            prices[-2] = (date2num(date2[0]), open2_[0], high2[0], low2[0], close2[0], vol2[0], date2[0])

          if first == False and first_candle_date != timestamp2[-1]:
            qs[tab_index].put(FIGURE_CLEAR)
            aqs[tab_index].get()
            first = True
            last_line1 = None
            last_line2 = None
            last_rect = None
            continue

          prices2 = [x[4] for x in prices]
          dates2 = [x[0] for x in prices]
          dates3 = [x[6] for x in prices]

          n1, n2, period = 10, 21, 60
          ap = (np.array(high) + np.array(low) + np.array(close)) / 3
          esa = talib.EMA(ap, timeperiod=n1)
          d = talib.EMA(abs(ap - esa), timeperiod=n1)
          ci = (ap - esa) / (0.015 * d)
          wt1 = talib.EMA(ci, timeperiod=n2)
          wt2 = talib.SMA(wt1, timeperiod=4)

          bb_upper, bb_middle, bb_lower = BBANDS(np.array(close), timeperiod=20)

          if first == True:
            wavetrend1 = ax3.plot(dates2, wt1, color=green, lw=.5)
            wavetrend2 = ax3.plot(dates2, wt2, color=red, lw=.5)
          else:
            wavetrend1[0].set_ydata(wt1)
            wavetrend2[0].set_ydata(wt2)

          if first == True:
            bb_upper_, = ax.plot(date, bb_upper, color=greenish, lw=.5, antialiased=True)
            bb_middle_, = ax.plot(date, bb_middle, color=red, lw=.5, antialiased=True)
            bb_lower_, = ax.plot(date, bb_lower, color=greenish, lw=.5, antialiased=True)
          else:
            bb_upper_.set_ydata(bb_upper)
            bb_middle_.set_ydata(bb_middle)
            bb_lower_.set_ydata(bb_lower)

          xvalues1 = wavetrend1[0].get_xdata()
          yvalues1 = wavetrend1[0].get_ydata()
          xvalues2 = wavetrend2[0].get_xdata()
          yvalues2 = wavetrend2[0].get_ydata()

          start_x = 0
          for i in xrange(0, len(wt1)):
              if not np.isnan(wt1[i]):
                start_x = i
                break

          xl = ax.get_xlim()
          ax.set_xlim(date[start_x], xl[1])

          wt_y_current = yvalues1[-1]
          symbol_with_timeframe = symbol + " " + timeframe_entered
          
          if init == True:
            wt_y_before = yvalues1[-1]
            intersect = False
            intersect_type = "NONE"
            sell_intersect = False
            buy_intersect = False
            buy_threshold = config[symbol_with_timeframe].buy_threshold
            sell_threshold = config[symbol_with_timeframe].sell_threshold
            wt_difference = yvalues1[-1] - yvalues2[-1]
            if wt_difference > 0:
              wt_rising = True
              wt_rising_before = True
            else:
              wt_rising = False
              wt_rising_before = False
          
          if wt_y_current > 53:
            wt_y_before = yvalues1[-1]
          elif wt_y_current < -53:
            wt_y_before = yvalues1[-1]  
          
          if wt_y_current < 53:
            if wt_y_before > 53:
              intersect = True
              intersect_threshold = 53 - yvalues1[-1]
              intersect_type = "SELL"
          
          if wt_y_current > -53:
            if wt_y_before < -53:
              intersect = True
              intersect_threshold = yvalues1[-1] + 53
              intersect_type = "BUY"

          if config[symbol_with_timeframe].trade_all_crossings == False:
            if intersect == True:
              if intersect_type == "SELL":
                if intersect_threshold > sell_threshold:
                    sell_intersect = True
                    wt_y_before = yvalues1[-1]
              
              if intersect_type == "BUY":
                if intersect_threshold > buy_threshold:
                    buy_intersect = True
                    wt_y_before = yvalues1[-1]
            
          if config[symbol_with_timeframe].trade_all_crossings == True:
            wt_difference = yvalues1[-1] - yvalues2[-1]
            if wt_difference > 0:
              wt_rising = True
            else:
              wt_rising = False

            if wt_rising != wt_rising_before:
              if wt_rising == True:
                if abs(wt_difference) > buy_threshold:
                  buy_intersect = True
                  wt_rising_before = wt_rising
              
              if wt_rising == False:
                if abs(wt_difference) > sell_threshold:
                  sell_intersect = True
                  wt_rising_before = wt_rising

          if wt_rising == True:          
            if counter % 15 == 0:
              print symbol + " " + timeframe_entered + " Rising Wavetrend, threshold = %.8f" % abs(wt_difference)
          else:
            if counter % 15 == 0:
              print symbol + " " + timeframe_entered + " Falling Wavetrend, threshold = %.8f" % abs(wt_difference)
          
          if counter % 15 == 0 and wt_y_current > 53:
            print symbol + " " + timeframe_entered + " Wavetrend above 53, threshold = %.8f" % (wt_y_current - 53)

          if counter % 15 == 0 and wt_y_current < 53:
            print symbol + " " + timeframe_entered + " Wavetrend below 53, threshold = %.8f" % (53 - wt_y_current)

          if counter % 15 == 0 and wt_y_current < -53:
            print symbol + " " + timeframe_entered + " Wavetrend below -53, threshold = %.8f" % (-53 - wt_y_current)

          if counter % 15 == 0 and wt_y_current > -53:
            print symbol + " " + timeframe_entered + " Wavetrend above -53, threshold = %.8f" % (wt_y_current + 53)
          
          if buy_intersect == True or sell_intersect == True:            
            print symbol + " INTERSECTION!!!"
            if buy_intersect == True:
                buy_intersect = False
                intersect = False
                #buy
                print "BUY"
                asset_balance = 0
                symbol_price = get_symbol_price(symbol)

                amount_per_trade = translate_buy_amount_percent(config[symbol_with_timeframe].buy_amount_percent_index)
                if symbol.endswith("USDT"):
                  asset_balance = float(client.fetch_balance()["USDT"]["free"])
                  buy_amount = truncate((asset_balance / symbol_price) * amount_per_trade, 2)
                elif symbol.endswith("USD"):
                  asset_balance = float(client.fetch_balance()["USD"]["free"])
                  buy_amount = truncate((asset_balance / symbol_price) * amount_per_trade, 2)                  
                else:
                  asset_balance = float(client.fetch_balance()["BTC"]["free"])
                  buy_amount = truncate((asset_balance / symbol_price) * amount_per_trade, 2)
                
                print buy_amount

                if buy_amount != 0:
                  try:
                    order = client.create_market_buy_order(symbol, buy_amount)
                    playsound("beep.wav")
                    main.updateBalances(symbol)
                    prev_trade_time = datetime.datetime.now()
                  except:
                    print get_full_stacktrace()
                  time.sleep(5)
                  f = open("trades.txt", "a")
                  f.write("BUY %s MARKET @ %.8f\n" % (symbol, symbol_price))
                  f.close()
                  item = QtGui.QListWidgetItem("BUY %s MARKET @ %.8f" % (symbol, symbol_price))
                  main.listWidget_4.addItem(item)
              
            if sell_intersect == True:
                #sell
                sell_intersect = False
                intersect = False
                print "SELL"
                
                asset_balance = truncate(float(client.fetch_balance()[get_asset_from_symbol(symbol)]["free"]), 2)
                  
                to_sell = asset_balance
                
                print asset_balance
                
                if asset_balance != 0:
                  symbol_price = get_symbol_price(symbol)
                  print to_sell
                  try:
                    order = client.create_market_sell_order(symbol, to_sell)
                    playsound("beep.wav")
                    main.updateBalances(symbol)
                    prev_trade_time = datetime.datetime.now()
                  except:
                    print get_full_stacktrace()
                  f = open("trades.txt", "a")
                  f.write("SELL %s MARKET @ %.8f\n" % (symbol, symbol_price))
                  f.close()
                  item = QtGui.QListWidgetItem("SELL %s MARKET @ %.8f" % (symbol, symbol_price))
                  main.listWidget_4.addItem(item)

          ticker = prices[-1][4]

          in_time = datetime.datetime.now()
          if timeframe_entered == "1m":
            in_time = ceil_dt(in_time, 60)
          elif timeframe_entered == "5m":
            in_time = ceil_dt(in_time, 5*60)
          elif timeframe_entered == "15m":
            in_time = ceil_dt(in_time, 15*60)
          elif timeframe_entered == "30m":
            in_time = ceil_dt(in_time, 30*60)
          elif timeframe_entered == "1h":
            in_time = ceil_dt(in_time, 60*60)

          duration = in_time - datetime.datetime.now()
          days, seconds = duration.days, duration.seconds
          hours = days * 24 + seconds // 3600
          minutes = (seconds % 3600) // 60
          seconds = seconds % 60
          time_to_hour = "%02d:%02d" % (minutes, seconds)

          if first == True:
            price_line = ax.axhline(ticker, color='gray', linestyle="dotted", lw=.9)
            if symbol.endswith("USDT") or symbol.endswith("USD"):
              annotation = ax.text(date[-1] + (date[-1]-date[-5]), ticker, "%.2f" % ticker, fontsize=7, color=white)
            else:
              annotation = ax.text(date[-1] + (date[-1]-date[-5]), ticker, "%.8f" % ticker, fontsize=7, color=white)
            annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))

            qs[tab_index].put(CANVAS_GET_SIZE)
            qs[tab_index].put(annotation)
            tbox = aqs[tab_index].get()
          
            dbox = tbox.transformed(ax.transData.inverted())
            y0 = dbox.height * 2.4
            if timeframe_entered in ["1m", "5m", "15m", "30m", "1h"]:
              time_annotation = ax.text(date[-1] + (date[-1]-date[-5]), ticker - y0, time_to_hour, fontsize=7, color=white)
              time_annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))
          else:
            price_line.set_ydata(ticker)
            
            if symbol.endswith("USDT") or symbol.endswith("USD"):
              annotation.set_text("%.2f" % ticker)
            else:
              annotation.set_text("%.8f" % ticker)
              
            annotation.set_y(ticker)
            annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))
            qs[tab_index].put(CANVAS_GET_SIZE)
            qs[tab_index].put(annotation)
            tbox = aqs[tab_index].get()
            
            dbox = tbox.transformed(ax.transData.inverted())
            y0 = dbox.height * 2.4
            if timeframe_entered in ["1m", "5m", "15m", "30m", "1h"]:            
              time_annotation.set_text(time_to_hour)
              time_annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))
              time_annotation.set_y(ticker - y0)

          if init == True:
            xl = ax.get_xlim()
            candle_width = ((dbox.x0 - xl[0]) / limit) * 0.8
          
          last_line1, last_line2, last_rect = _candlestick(ax, prices, first, last_line1, last_line2, last_rect, candle_width)
          
          if first == True:
            ax3.axhline(60, color=red, lw=.8)
            ax3.axhline(-60, color=green, lw=.8)
            ax3.axhline(0, color='gray', lw=.5)
            ax3.axhline(53, color=red, linestyle="dotted", lw=.8)
            ax3.axhline(-53, color=green, linestyle="dotted", lw=.8)
            ax.set_axis_bgcolor(black)

            pad = 0.25
            yl = ax.get_ylim()
            ax.set_ylim(yl[0]-(yl[1]-yl[0])*pad,yl[1])
            ax.set_xlabel(timeframe_entered)
            ax.set_ylabel(symbol)

            ax.spines['top'].set_edgecolor(darkish)
            ax.spines['left'].set_edgecolor(darkish)
            ax.spines['right'].set_edgecolor(darkish)
            ax.spines['bottom'].set_edgecolor(darkish)
            ax.set_axis_bgcolor(black)
            ax.xaxis.label.set_color(white)
            ax.yaxis.label.set_color(white)
            ax.tick_params(axis='x', colors=white)
            ax.tick_params(axis='y', colors=white)
            ax3.spines['left'].set_edgecolor(darkish)
            ax3.spines['right'].set_edgecolor(darkish)
            ax3.spines['top'].set_visible(False)
            ax3.spines['bottom'].set_visible(False)
            ax3.xaxis.label.set_color(white)
            ax3.yaxis.label.set_color(white)
            ax3.tick_params(axis='x', colors=white)
            ax3.tick_params(axis='y', colors=white)            
            ax.grid(alpha=.25)
            ax.grid(True)

            if init == True:
              qs[tab_index].put(FIGURE_TIGHT_LAYOUT)
              aqs[tab_index].get()

            bbox = ax.get_position()
            ax3.set_position([bbox.x0, bbox.y0, bbox.width, bbox.height / 4])
            ax.autoscale_view()
            first = False

            
          prices2[:] = []
          dates2[:] = []
          dates3[:] = []
          xvalues1 = None
          yvalues1 = None
          xvalues2 = None
          yvalues2 = None
          gc.collect()

          qs[tab_index].put(CANVAS_DRAW_IDLE)
          aqs[tab_index].get()
        except:
          print get_full_stacktrace()
          
        counter = counter + 1
        
        init = False

def relative_strength(prices, n=14):
    """
    compute the n period relative strength indicator
    http://stockcharts.com/school/doku.php?id=chart_school:glossary_r#relativestrengthindex
    http://www.investopedia.com/terms/r/rsi.asp
    """

    deltas = np.diff(prices)
    seed = deltas[:n+1]
    up = seed[seed >= 0].sum()/n
    down = -seed[seed < 0].sum()/n
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100./(1. + rs)

    for i in range(n, len(prices)):
        delta = deltas[i - 1]  # cause the diff is 1 shorter

        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(n - 1) + upval)/n
        down = (down*(n - 1) + downval)/n

        rs = up/down
        rsi[i] = 100. - 100./(1. + rs)

    return rsi

def ema(x, n, t):
    x = np.asarray(x)
    if t=='simple':
        weights = np.ones(n)
    else:
        weights = np.exp(np.linspace(-1., 0., n))

    weights /= weights.sum()

    a =  np.convolve(x, weights, mode='full')[:len(x)]
    a[:n] = a[n]
    return a

def shiftme(arr, num):
    result = np.empty(len(arr)+num) * np.nan
    for i in xrange(len(arr)):
      result[i+num] = arr[i]

    return result

def ichimoku_clouds(high, low, close, n1=9, n2=26, n3=52):
        """
        Calculate Ichimoku Clouds.
        """
        conversion = (pd.rolling_max(high, n1) + pd.rolling_min(low, n1)) / 2.0
        base = (pd.rolling_max(high, n2) + pd.rolling_min(low, n2)) / 2.0
        leading_a = (conversion + base) / 2.0
        leading_b = (pd.rolling_max(high, n3) + pd.rolling_min(low, n3)) / 2.0
        lagging = close.shift(-n2)
        leading_a = shiftme(leading_a, n2)
        leading_b = shiftme(leading_b, n2)
        return conversion, base, leading_a, leading_b, lagging

def peakdetect(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Returns two arrays

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.

    """
    maxtab = []
    mintab = []

    if x is None:
        x = arange(len(v))

    v = asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        sys.exit('Input argument delta must be positive')

    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]

        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return maxtab, mintab

def getData(timeframe_entered, days_entered, currency_entered, few_candles):
    if few_candles == False:
      limit = 0
      if timeframe_entered == "15m":
          limit = int(days_entered * 4 * 24)

      if timeframe_entered == "1m":
          limit = int(days_entered * 60 * 24)

      if timeframe_entered == "5m":
          limit = int(days_entered * 12 * 24)

      if timeframe_entered == "30m":
          limit = int(days_entered * 2 * 24)

      if timeframe_entered == "1h":
          limit = int(days_entered * 24)

      if timeframe_entered == "4h":
          limit = int(days_entered * (24/4))

      if timeframe_entered == "6h":
          limit = int(days_entered * (24/6))

      if timeframe_entered == "12h":
          limit = int(days_entered * (24/12))

      if timeframe_entered == "1d":
          limit = int(days_entered)

      if timeframe_entered == "3d":
          limit = int(days_entered / 3)

      if timeframe_entered == "1w":
          limit = int(days_entered / 7)

      if timeframe_entered == "1M":
          limit = int(days_entered / 31)
    else:
      limit = 2

    dt = []
    open_ = []
    high = []
    low = []
    close = []
    volume = []
    timestamp = []
    candles = client.fetch_ohlcv(currency_entered, timeframe_entered, limit=limit)

    for candle in candles:
      dt.append(datetime.datetime.fromtimestamp(int(candle[0]) / 1e3))
      open_.append(float(candle[1]))
      high.append(float(candle[2]))
      low.append(float(candle[3]))
      close.append(float(candle[4]))
      volume.append(float(candle[5]))
      timestamp.append(candle[0])

    return dt, open_, high, low, close, volume, limit, timestamp

from operator import itemgetter
DIRPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, symbol=None):
        self.fig = Figure(facecolor=black, edgecolor=white)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
main_shown = False
class Window(QtGui.QMainWindow):
    global tab_widgets
    global config
    def __init__(self, symbol, timeframe_entered):
        QtGui.QDialog.__init__(self)
        resolution = QtGui.QDesktopWidget().screenGeometry()
        uic.loadUi(os.path.join(DIRPATH, 'mainwindowqt.ui'), self)
        self.setWindowTitle("WAVETREND ROBOT - " + exchange)
        self.setGeometry(0, 0, int(resolution.width()/1.1), int(resolution.height()/1.2))
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))         
        self.toolButton.clicked.connect(self.add_coin_clicked)
        self.tab_widgets = []
        self.tab_widgets.append(self.tabWidget.widget(0))
        self.tabWidget.currentChanged.connect(self.tabOnChange)
        self.pushButton_4.clicked.connect(self.configAcceptClicked)
        self.toolButton_2.clicked.connect(self.buy_clicked)
        self.toolButton_3.clicked.connect(self.sell_clicked)
        self.label.setPixmap(QtGui.QPixmap("arrowr.png").scaled(16,16))
        self.expanded = True
        self.label.mousePressEvent = self.expand_collapse
    
        widget = QtGui.QVBoxLayout(self.tabWidget.widget(0))
        dc = MplCanvas(self.tabWidget.widget(0), dpi=100, symbol=symbol)
        widget.addWidget(dc)

        self.horizontalLayout_3.insertWidget(1, OrderBookWidget(), alignment=QtCore.Qt.AlignTop)
        
        self.dcs = {}
        self.dcs[0] = dc
        
        global qs
        global aqs
        qs[0] = Queue.Queue()
        aqs[0] = Queue.Queue()
        
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.queue_handler)
        timer.start(1)
                
        t = threading.Thread(target=run_geforce, args=(symbol, 0, timeframe_entered))
        t.daemon = True
        t.start()
        
        t = threading.Thread(target=self.update_usdt_balance)
        t.daemon = True
        t.start()
    
    def queue_handler(self):
      global qs
      global aqs
      global qs_local
      if QtGui.QApplication.hasPendingEvents():
        return
      
      for i in xrange(0, len(qs)):
        if qs[i].qsize() > 0:
          value = qs[i].get()
          if value == FIGURE_ADD_SUBPLOT:
            aqs[i].put(self.dcs[i].fig.add_subplot(1,1,1,facecolor=black))
          elif value == FIGURE_TIGHT_LAYOUT:
            self.dcs[i].fig.tight_layout()
            aqs[i].put(0)
          elif value == FIGURE_CLEAR:
            self.dcs[i].fig.clf()
            aqs[i].put(0)
          elif value == CANVAS_GET_SIZE:
            annotation = qs[i].get()
            aqs[i].put(annotation.get_window_extent(self.dcs[i].renderer))
          elif value == CANVAS_DRAW_IDLE:
            if self.tabWidget.currentIndex() == i:
              self.dcs[i].draw_idle()
            aqs[i].put(0)
        
      if qs_local.qsize() > 0:
        value = qs_local.get()
        if value == SHOW_STATUSBAR_MESSAGE:
          message = qs_local.get()
          self.statusbar.showMessage(message)
                
    def expand_collapse(self, event):
      if self.expanded == True:
        self.label.setPixmap(QtGui.QPixmap("arrowl.png").scaled(16,16))
        self.groupBox.hide()
        self.expanded = False
      else:
        self.label.setPixmap(QtGui.QPixmap("arrowr.png").scaled(16,16))
        self.groupBox.show()
        self.expanded = True
        
    def buy_clicked(self, event):
      print "BUY"
      
      asset_balance = 0
      symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex())).split(" ")[0]
      symbol_price = get_symbol_price(symbol)

      amount_per_trade = translate_buy_amount_percent_reversed(self.comboBox_5.currentIndex())
      if symbol.endswith("USDT"):
        asset_balance = float(client.fetch_balance()["USDT"]["free"])
        buy_amount = truncate((asset_balance / symbol_price) * amount_per_trade, 2)
      elif symbol.endswith("USD"):
        asset_balance = float(client.fetch_balance()["USD"]["free"])
        buy_amount = truncate((asset_balance / symbol_price) * amount_per_trade, 2)        
      else:
        asset_balance = float(client.fetch_balance()["BTC"]["free"])
        buy_amount = truncate((asset_balance / symbol_price) * amount_per_trade, 2)
      
      if buy_amount == 0:
        return

      msg = "Buy " + str(buy_amount) + " " + symbol + "?"
      reply = QtGui.QMessageBox.question(self, 'WAVETREND ROBOT', 
                       msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

      if reply == QtGui.QMessageBox.Yes:
          symbol_price = get_symbol_price(symbol)
          try:
            client.create_market_buy_order(symbol, buy_amount)
            playsound("beep.wav")
            self.updateBalances(symbol)
          except:
            pass
            
          symbol_price = get_symbol_price(symbol)
          item = QtGui.QListWidgetItem("BUY %s MARKET @ %.8f" % (symbol, symbol_price))
          self.listWidget_4.addItem(item)

          f = open("trades.txt", "a")
          f.write("BUY %s MARKET @ %.8f\n" % (symbol, symbol_price))
          f.close()
    def sell_clicked(self, event):
      print "SELL"
      
      symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex())).split(" ")[0]
      amount_per_trade = translate_buy_amount_percent_reversed(self.comboBox_5.currentIndex())
      
      sell_amount = truncate(float(client.fetch_balance()[get_asset_from_symbol(symbol)]["free"]) * amount_per_trade, 2)

      if sell_amount == 0:
        return
    
      msg = "Sell " + str(sell_amount) + " " + symbol + "?"
      reply = QtGui.QMessageBox.question(self, 'WAVETREND ROBOT', 
                       msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

      if reply == QtGui.QMessageBox.Yes:
          try: 
            client.create_market_sell_order(symbol, sell_amount)
            playsound("beep.wav")
            self.updateBalances(symbol)
          except:
            pass
          
          symbol_price = get_symbol_price(symbol)
          item = QtGui.QListWidgetItem("SELL %s MARKET %.8f" % (symbol, symbol_price))
          self.listWidget_4.addItem(item)
          f = open("trades.txt", "a")
          f.write("SELL %s MARKET @ %.8f\n" % (symbol, symbol_price))
          f.close()    
    
    def configAcceptClicked(self, event):
      try:
        buy_threshold = float(self.lineEdit_7.text())
      except:
        QtGui.QMessageBox.information(self, "WAVETREND ROBOT", "Entered buy theshold is not a number")
        return
        
      try:
        sell_threshold = float(self.lineEdit_8.text())
      except:
        QtGui.QMessageBox.information(self, "WAVETREND ROBOT", "Entered sell theshold is not a number")
        return
        
      selected_symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex()))
      if self.checkBox_4.isChecked() == True:
        config[selected_symbol].trade_auto = True
      else:
        config[selected_symbol].trade_auto = False
        
      if self.radioButton_8.isChecked() == True:
        config[selected_symbol].trade_all_crossings = True
      else:
        config[selected_symbol].trade_all_crossings = False
        
      if self.radioButton_7.isChecked() == True:
        config[selected_symbol].trade_lines_only = True
      else:
        config[selected_symbol].trade_lines_only = False
          
      config[selected_symbol].buy_threshold = float(buy_threshold)
      config[selected_symbol].sell_threshold = float(sell_threshold)
      config[selected_symbol].buy_amount_percent_index = self.comboBox_4.currentIndex()
    
      QtGui.QMessageBox.information(self, "WAVETREND ROBOT", selected_symbol + " Wavetrend configured.")
    
    def updateBalances(self, symbol):
      asset = get_asset_from_symbol(symbol)
      asset_balance = client.fetch_balance()[asset]["free"]
      main.label_14.setText(asset.upper() + " Balance: " + str(asset_balance))
      quote = get_quote_from_symbol(symbol)
      quote_balance = client.fetch_balance()[quote]["free"]
      main.label_15.setText(quote.upper() + " Balance: " + str(quote_balance)) 
    
    def tabOnChange(self, event):
      selected_symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex()))
      symbol = selected_symbol
      main.groupBox.setTitle(selected_symbol)
      self.checkBox_4.setChecked(config[selected_symbol].trade_auto)
      self.radioButton_8.setChecked(config[selected_symbol].trade_all_crossings)
      self.radioButton_7.setChecked(config[selected_symbol].trade_lines_only)
      self.lineEdit_7.setText(str(config[selected_symbol].buy_threshold))
      self.lineEdit_8.setText(str(config[selected_symbol].sell_threshold))
      self.comboBox_4.setCurrentIndex(config[selected_symbol].buy_amount_percent_index)
      self.updateBalances(symbol.split(" ")[0])
      
    def addTab(self, symbol, timeframe_entered):
      self.tab_widgets.append(QtGui.QWidget())
      tab_index = self.tabWidget.addTab(self.tab_widgets[-1], symbol + " " + timeframe_entered)
      self.tabWidget.setCurrentWidget(self.tab_widgets[-1])
      main.tabWidget.setTabIcon(tab_index, QtGui.QIcon("coin.ico"))
      widget = QtGui.QVBoxLayout(self.tabWidget.widget(tab_index))
      dc = MplCanvas(self.tabWidget.widget(tab_index), dpi=100, symbol=symbol)
      widget.addWidget(dc)
      
      global qs
      global aqs
      qs[tab_index] = Queue.Queue()
      aqs[tab_index] = Queue.Queue()
      self.dcs[tab_index] = dc
      
      t = threading.Thread(target=run_geforce, args=(symbol, tab_index, timeframe_entered))
      t.daemon = True
      t.start()
    
    def add_coin_clicked(self, event):
      global dialog
      dialog = Dialog()
      dialog.show()
       
    def update_usdt_balance(self):
      global qslocal
      symbols = client.fetch_tickers()
      self.usdt_symbols = []
      self.btc_symbols = []
      for symbol,value in symbols.iteritems():
        if symbol.endswith("USDT"):
          self.usdt_symbols.append(symbol) 
        if symbol.endswith("USD"):
          self.usdt_symbols.append(symbol)
        if symbol.endswith("BTC"):
          self.btc_symbols.append(symbol)
      
      while True:
        time.sleep(5)
        try:
          ticker = client.fetch_tickers()
          balances = client.fetch_balance()
          usdt_balance = 0
          
          if "BTC/USDT" in ticker:
            btcusd_symbol = "BTC/USDT"
          else:
            btcusd_symbol = "BTC/USD"
          
          btc_price = get_symbol_price(btcusd_symbol)
          for balance_symbol, balance in balances.iteritems():
            if "free" not in balance:
              continue
            if float(balance["free"]) == 0.0:
              continue
            if balance_symbol == "USDT":
              usdt_balance = usdt_balance + float(balance["free"])
            elif balance_symbol + "/USDT" in self.usdt_symbols:
              for symbol_name,symbol in ticker.iteritems():
                if symbol_name == balance_symbol + "/USDT":
                  symbol_price = float(symbol["last"])
                  break
              usdt_balance = usdt_balance + float(balance["free"]) * symbol_price
            elif balance_symbol + "/USD" in self.usdt_symbols:
              for symbol_name,symbol in ticker.iteritems():
                if symbol_name == balance_symbol + "/USD":
                  symbol_price = float(symbol["last"])
                  break
              usdt_balance = usdt_balance + float(balance["free"]) * symbol_price
            elif balance_symbol + "/BTC" in self.btc_symbols:
              for symbol_name,symbol in ticker.iteritems():
                if symbol_name == balance_symbol + "/BTC":
                  symbol_price = float(symbol["last"])
                  break
              usdt_balance = usdt_balance + float(balance["free"]) * symbol_price * btc_price
        
          qs_local.put(SHOW_STATUSBAR_MESSAGE)
          qs_local.put("USD Balance: " + "%.2f" % usdt_balance)
        except:
          print get_full_stacktrace()
          
        time.sleep(35)
    
class Dialog(QtGui.QDialog):
    global config
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(DIRPATH, 'windowqt.ui'), self)
        
        coins = client.fetchTickers()

        if "BTC/USDT" in coins:
          btcusd_symbol = "BTC/USDT"
        else:
          btcusd_symbol = "BTC/USD"
        
        btc_price = get_symbol_price(btcusd_symbol)
        coins_ = []
        for coin, value in coins.iteritems():            
            if coin.endswith("BTC"):
              coins[coin]["volumeFloat"] =int(float(coins[coin]["quoteVolume"]) * btc_price)
              coins_.append(coins[coin])
            if coin.endswith("USDT"):
              coins[coin]["volumeFloat"] = int(float(coins[coin]["quoteVolume"]))
              coins_.append(coins[coin])
            if coin.endswith("USD"):
              coins[coin]["volumeFloat"] = int(float(coins[coin]["quoteVolume"]))
              coins_.append(coins[coin])
        coins = sorted(coins_, key=itemgetter("volumeFloat"), reverse=True)
        
        self.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        
        for coin in coins:
          if coin["symbol"].endswith("BTC") or coin["symbol"].endswith("USDT"):
            rowPosition = self.tableWidget.rowCount() - 1
            self.tableWidget.insertRow(rowPosition)
            self.tableWidget.setItem(rowPosition, 0, QtGui.QTableWidgetItem(coin["symbol"]))
            if "change" in coin and coin["change"]:
              self.tableWidget.setItem(rowPosition, 1, QtGui.QTableWidgetItem(str("%.08f" % coin["change"])))
            if "percentage" in coin and coin["percentage"]:
              self.tableWidget.setItem(rowPosition, 2, QtGui.QTableWidgetItem(str(coin["percentage"])))
            self.tableWidget.setItem(rowPosition, 3, QtGui.QTableWidgetItem(str(coin["volumeFloat"])))
            if "change" in coin and coin["change"]:
              if float(coin["change"]) < 0:
                self.tableWidget.item(rowPosition, 0).setForeground(QtGui.QColor(255,0,0))
                self.tableWidget.item(rowPosition, 1).setForeground(QtGui.QColor(255,0,0))
                self.tableWidget.item(rowPosition, 2).setForeground(QtGui.QColor(255,0,0))
                self.tableWidget.item(rowPosition, 3).setForeground(QtGui.QColor(255,0,0))
              else:
                self.tableWidget.item(rowPosition, 0).setForeground(QtGui.QColor(0,255,0))
                self.tableWidget.item(rowPosition, 1).setForeground(QtGui.QColor(0,255,0))
                self.tableWidget.item(rowPosition, 2).setForeground(QtGui.QColor(0,255,0))
                self.tableWidget.item(rowPosition, 3).setForeground(QtGui.QColor(0,255,0))

    def accept(self):
      selectionModel = self.tableWidget.selectionModel()
      if selectionModel.hasSelection():
        row = self.tableWidget.selectedItems()[0].row()
        timeframe_entered = str(self.comboBox.currentText())
        symbol = str(self.tableWidget.item(row, 0).text())
        symbol_with_timeframe = symbol + " " + timeframe_entered
  
        config[symbol_with_timeframe] = abstract()
        config[symbol_with_timeframe].trade_auto = False
        config[symbol_with_timeframe].trade_all_crossings = True
        config[symbol_with_timeframe].trade_lines_only = False
        config[symbol_with_timeframe].buy_threshold = 1.0
        config[symbol_with_timeframe].sell_threshold = 1.0
        config[symbol_with_timeframe].buy_amount_percent_index = 0
  
        global main
        global main_shown

        if not main_shown:
          main = Window(symbol, timeframe_entered)
          main.updateBalances(symbol)
          main.tabWidget.setTabText(0, symbol + " " + timeframe_entered)
          main.tabWidget.setTabIcon(0, QtGui.QIcon("coin.ico"))
          main.groupBox.setTitle(symbol + " " + timeframe_entered)
          main.show()
          main_shown = True
          f = open("trades.txt")
          lines = f.readlines()
          for line in lines:
            item = QtGui.QListWidgetItem(line)
            main.listWidget_4.addItem(item)
          f.close()
        else:
          main.updateBalances(symbol)
          main.addTab(symbol, timeframe_entered)
          main.groupBox.setTitle(symbol)        
        self.close()

def orderbook(exchange, symbol):
  #print(str(exchange))
  return exchange.fetch_order_book(symbol)

def bid_ask_sum(symbol, bids, precision=10): # can be asks too instead of bids
  bids_summed = []
  whole_1 = 0
  
  highest_sum = 0
    
  for bid in bids:
      price = bid[0]
      qty = bid[1]
      frac, whole_2 = math.modf(price / precision)
      if whole_1 == whole_2:
          continue
      frac, whole_1 = math.modf(price / precision)
      remainder = price % precision
      qty_summed = 0
      
      for bid in bids:
        price = bid[0]
        qty = bid[1]
        frac, whole = math.modf(price / precision)
        if whole_1 == whole:
          qty_summed += qty
      
      usd_summed = qty_summed * (whole_1 * precision + remainder)
#      if symbol.endswith("BTC"):
#        btc_price = self.exchange.fetch_ticker("BTC/USD")["last"]
#        usd_summed = usd_summed * btc_price
      
      if usd_summed > 1000000:
        usd_summed = "%.2f" % float(usd_summed/1000000) + " M"
      elif usd_summed > 1000:
        usd_summed = "%.2f" % float(usd_summed/1000000) + " M"
      else:
        continue
      
      if qty_summed > highest_sum:
          highest_sum = qty_summed

      if not symbol.endswith("BTC"):
        bids_summed.append(["%.2f" % (whole_1 * precision + remainder), float("%.2f" % qty_summed), usd_summed]) 
      else:
        bids_summed.append(["%.8f" % (whole_1 * precision + remainder), float("%.8f" % qty_summed), usd_summed]) 

  bids_score = []
  for bid in bids_summed:
      score = 0
      qty = bid[1]
      if qty > highest_sum / 5:
        score = score + 1
      if qty > highest_sum / 4:
        score = score + 1
      if qty > highest_sum / 3:
        score = score + 1
      if qty > highest_sum / 2:
        score = score + 1
      if qty >= highest_sum:
        score = score + 1
        
      bids_score.append([score,bid])

  return bids_score

def display_market_depth(bids, asks, symbol, precision):
  strs = []
  
  bids_str = bids
  asks_str = asks
  bids_str.reverse()
  asks_str.reverse()

  top_bid = float(bids_str[0][0])

  bids2 = []
  for bid in bids_str:
      bids2.append([float(bid[0]), float(bid[1])])
      if top_bid - float(bid[0]) > 300:
        break
      
  asks2 = []
  for ask in asks_str:
      if float(ask[0]) > top_bid + 300:
        continue
      asks2.append([float(ask[0]), float(ask[1])])
  
  bids_summed = bid_ask_sum(symbol, bids2, precision)
  asks_summed = bid_ask_sum(symbol, asks2, precision)

  for bid in bids_summed:
      try:
        ask = asks_summed.pop()
        if not symbol.endswith("BTC"):
          asks = str(ask[1][0]) + " "  * (9 - len(str(ask[1][0]))) + str(ask[1][2]) + " " + "*" * ask[0]
        else:
          asks = "%.6f" % float(ask[1][0]) + " " + str(ask[1][1]) + " "  * (10 - len(str(ask[1][1]))) + str(ask[1][2]) + " " + "*" * ask[0]
      except:
        asks = ""
      if not symbol.endswith("BTC"):            
        strs.append(" " * (5-bid[0]) + "*" * bid[0] + " " + str(bid[1][0]) + " "  * (9 - len(str(bid[1][0]))) + str(bid[1][2]) + "\t" + asks)
      else:
        strs.append(" " * (5-bid[0]) + "*" * bid[0] + " " + "%.6f" % float(bid[1][0]) + " " + str(bid[1][1]) + " "  * (10 - len(str(bid[1][1]))) + str(bid[1][2]) + "\t" + asks)

  return strs

class Orderbook():
    def __init__(self):        
        self.exchange_gdax = ccxt.gdax({
        'enableRateLimit': True,
        })
        self.exchange_bitfinex = ccxt.bitfinex({
        'enableRateLimit': True,
        })      
        self.exchange_kraken = ccxt.kraken({
        'enableRateLimit': True,
        })
        self.exchange_bittrex = ccxt.bittrex({
        'enableRateLimit': True,
        })
        self.exchange_binance = ccxt.binance({
        'enableRateLimit': True,
        })  
        self.exchange_bitmex = ccxt.bitmex({
        'enableRateLimit': True,
        })
        self.exchange_bitstamp = ccxt.bitstamp({
        'enableRateLimit': True,
        }) 
        self.exchange_gemini = ccxt.gemini({
        'enableRateLimit': True,
        })
        self.exchange_poloniex = ccxt.poloniex({
        'enableRateLimit': True,
        })
        self.exchange_hitbtc = ccxt.hitbtc2({
        'enableRateLimit': True,
        })
        self.exchange_okex = ccxt.okex({
        'enableRateLimit': True,
        })
        
        self.lastupdate = 0
        self.prev_buy = 0
        self.prev_sell = 0
        
        self.ex_queue = Queue.Queue()
        t = threading.Thread(target=self.collect_ex)
        t.start()

    def add_position(self, pos, isbid):
      if isbid:
        if pos[0] not in self.ob["bids"]:
          self.ob["bids"][pos[0]] = pos[1]
        else:
          self.ob["bids"][pos[0]] += pos[1]

      if not isbid:
        if pos[0] not in self.ob["asks"]:
          self.ob["asks"][pos[0]] = pos[1]
        else:
          self.ob["asks"][pos[0]] += pos[1]

    def update_trades(self, trades):
      counter = 0
      for trade in trades:
        if trade["side"] == "buy":
          self.ob["trades"]["buy"] += trade["price"] * trade["amount"]
        elif trade["side"] == "sell":
          self.ob["trades"]["sell"] += trade["price"] * trade["amount"]
        counter = counter + 1
        if counter > 100:
          break
    
    def collect_ex_threadable(self, exchange, symbol, is_bitmex=False):
      while True:
        try:
          if not is_bitmex:
            ob_exchange = orderbook(exchange, symbol)
            for pos in ob_exchange["bids"]:
              self.add_position(pos, True)
            for pos in ob_exchange["asks"]:
              self.add_position(pos, False)
            ob_trades = exchange.fetch_trades(symbol, limit=100)
            self.update_trades(ob_trades)
          else:
            ob_exchange = orderbook(self.exchange_bitmex, "BTC/USD")
            btc_price = self.exchange_bitmex.fetch_ticker("BTC/USD")["last"]
            for bid in ob_exchange["bids"]:
              pos = [bid[0], float(bid[1]) / float(btc_price)]
              self.add_position(pos, True)
            for ask in ob_exchange["asks"]:
              pos = [ask[0], float(ask[1]) / float(btc_price)]
              self.add_position(pos, False)
        except:
          print get_full_stacktrace()
          time.sleep(3)
        break
    
    def collect_ex(self):
      while True:
        if time.time() - self.lastupdate > 5 or self.lastupdate == 0:
          try:
            self.ob={}
            self.ob["bids"] = {}
            self.ob["asks"] = {}
            self.ob["trades"] = {}
            self.ob["trades"]["buy"] = 0
            self.ob["trades"]["sell"] = 0
            
            threads = []
            
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_gdax, "BTC/USD",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_bitfinex, "BTC/USDT",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_kraken, "BTC/USD",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_bittrex, "BTC/USD",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_binance, "BTC/USDT",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_bitstamp, "BTC/USD",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_gemini, "BTC/USD",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_hitbtc, "BTC/USDT",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_okex, "BTC/USDT",))
            threads.append(t)
            t = threading.Thread(target=self.collect_ex_threadable, args=(self.exchange_bitmex, "BTC/USD", True,))
            threads.append(t)            
            
            for t in threads:            
              t.daemon = True
              t.start()
            
            for t in threads:
              t.join()

            ob_bids = sorted((float(x),y) for x,y in self.ob["bids"].items())
            ob_asks = sorted((float(x),y) for x,y in self.ob["asks"].items())

            bookstr = "btcusd (combined)\n\n"
            ob_accum = display_market_depth(ob_bids, ob_asks, "BTC/USD", 7)
            for ob in ob_accum:
              bookstr = bookstr + ob + "\n"
            
            buy_usd = self.ob["trades"]["buy"]
            sell_usd = self.ob["trades"]["sell"]
            
            buy_percent = ""
            sell_percent = ""
            if self.prev_buy != 0:
              if buy_usd > self.prev_buy:
                increase = buy_usd - self.prev_buy
                increase = (increase / self.prev_buy) * 100
                buy_percent = "+%.2f" % increase + "%"
              else:
                decrease = self.prev_buy - buy_usd
                decrease = (decrease / self.prev_buy) * 100
                buy_percent = "-%.2f" % decrease + "%"
                
              sell_percent = 0
              if sell_usd > self.prev_sell:
                increase = sell_usd - self.prev_sell
                increase = (increase / self.prev_sell) * 100
                sell_percent = "+%.2f" % increase + "%"
              else:
                decrease = self.prev_sell - sell_usd
                decrease = (decrease / self.prev_sell) * 100
                sell_percent = "-%.2f" % decrease + "%"
            
            if buy_usd > 1000000:
              buy_usd = "%.2f" % float(buy_usd/1000000) + " M"
            elif buy_usd > 1000:
              buy_usd = "%.2f" % float(buy_usd/1000000) + " M"
            else:
              buy_usd = int(buy_usd)
              
            if sell_usd > 1000000:
              sell_usd = "%.2f" % float(sell_usd/1000000) + " M"
            elif sell_usd > 1000:
              sell_usd = "%.2f" % float(sell_usd/1000000) + " M"
            else:
              sell_usd = int(sell_usd)                         
            
            bookstr = bookstr + "BUY: " + buy_usd + " " + buy_percent
            bookstr = bookstr + "\nSELL: " + sell_usd + " " + sell_percent

            self.prev_buy = self.ob["trades"]["buy"]
            self.prev_sell = self.ob["trades"]["sell"]

            self.ex_queue.put(bookstr)
            
            self.lastupdate = time.time()
          except:
            stacktrace = get_full_stacktrace()
            print stacktrace

    def loop(self, lbl):
        if self.ex_queue.empty() == False:
          bookstr = self.ex_queue.get()
          lbl.setText(bookstr)
          
class OrderBookWidget(QtGui.QLabel):
    def __init__(self,parent=None):
        super(OrderBookWidget,self).__init__(parent)
        self.init_orderbook_widget()
 
    def init_orderbook_widget(self):
        self.setMinimumWidth(337)
        newfont = QtGui.QFont("Courier New", 9, QtGui.QFont.Bold) 
        self.setFont(newfont)
        self.setText("btcusd (combined)\nloading...")
        self.setStyleSheet("QLabel { background-color : #363C4E; color : #C6C7C8; }")
        self.orderbook = Orderbook()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.orderbook_widget_loop)
        self.timer.start(1)

    def orderbook_widget_loop(self):
        self.orderbook.loop(self)

if __name__ == "__main__":
  init_btc_balance = float(client.fetch_balance()["BTC"]["free"])

  app = QtGui.QApplication(sys.argv)
  with open("style.qss","r") as fh:
    app.setStyleSheet(fh.read())
  dialog = Dialog()
  dialog.show()
  os._exit(app.exec_())
