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

is_windows = False
if platform.system() == "Windows":
  is_windows = True
  is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
  if not is_admin:
    print "Please run this program as Admin, since it requires to configure the system time."
    sys.exit(1)

from binance.client import Client
client = Client(api_key, api_secret)



class abstract():
  pass

config = {}

def _candlestick(ax, quotes, first, last_line1, last_line2, last_rect, width=0.2, colorup='white', colordown='black',
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

    width = 0.026
    OFFSET = width / 2.0

    lines = []
    patches = []

    colorup = "white"
    colordown = "black"
    
    if first == False:
      quotes = [quotes[-1]]
    for q in quotes:
        t, open, high, low, close = q[:5]

        if close >= open:
            color = colorup
            lower = open
            higher = close
            height = close - open
        else:
            color = colordown
            lower = close
            higher = close
            height = open - close

        vline1 = Line2D(
            xdata=(t, t), ydata=(higher, high),
            color="black",
            linewidth=0.5,
            antialiased=True,
        )

        vline2 = Line2D(
            xdata=(t, t), ydata=(low, lower),
            color="black",
            linewidth=0.5,
            antialiased=True,
        )

        rect = Rectangle(
            xy=(t - OFFSET, lower),
            width=width,
            height=height,
            facecolor=color,
            edgecolor="black",
            linewidth=0.5
        )
        rect.set_alpha(alpha)

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
  prices = client.get_all_tickers()
  for sym in prices:
    if sym["symbol"] == symbol.upper():
      return float(sym["price"])

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
  asset = ""
  if symbol == "BTCUSDT":
    asset = "BTC"
  elif symbol.find("BTC") > -1:
    asset = symbol.split("BTC")[0]
  elif symbol.find("USDT") > -1:
    asset = symbol.split("USDT")[0]

  return asset.lower()

def translate_buy_amount_percent(index):
  if index == 0:
    return .25
  elif index == 1:
    return .5
  elif index == 0:
    return .75
  elif index == 0:
    return .97
    
def run_geforce(symbol, fig, canvas, main):
    global drawing
    global queue
    global status_bar

    timeframe_entered = "1h"
    days_entered = "10"
    bought = False
    sold = False

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
          date, open_, high, low, close, vol = getDataBinance(timeframe_entered, days_entered, symbol)
          
          if first == True:
            ax = fig.add_subplot(1,1,1)
            ax3 = ax.twinx()

          prices = []
          for i in range(0, len(date)):
              prices.append((date2num(date[i]), open_[i], high[i], low[i], close[i], vol[i], date[i]))

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
            wavetrend1 = ax3.plot(dates2, wt1, color="green", lw=.5)
            wavetrend2 = ax3.plot(dates2, wt2, color="red", lw=.5)
          else:
            wavetrend1[0].set_ydata(wt1)
            wavetrend2[0].set_ydata(wt2)

          if first == True:
            bb_upper_, = ax.plot(date, bb_upper, color="blue", lw=.5, antialiased=True, alpha=.5)
            bb_middle_, = ax.plot(date, bb_middle, color="blue", lw=.5, antialiased=True, alpha=.5)
            bb_lower_, = ax.plot(date, bb_lower, color="blue", lw=.5, antialiased=True, alpha=.5)
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

          wt_rising = False
     
          if config[symbol].trade_all_crossings == True:
            diff = yvalues1[-1] - yvalues2[-1]
            if diff > 0:
              if counter % 15 == 0:
                print symbol + " Rising Wavetrend %.8f" % abs(diff)
              wt_rising = True
            else:
              if counter % 15 == 0:
                print symbol + " Falling Wavetrend %.8f" % abs(diff)

          if config[symbol].trade_all_crossings == False:
            if yvalues1[-1] > 53:
              wt_line_above_53 = True
              diff = yvalues1[-1] - 53
            else:
              wt_line_above_53 = False
              diff = 53 - yvalues1[-1]
            
            if yvalues1[-1] > -53:
              wt_line_below_53 = False
              diff = yvalues1[-1] - -53
            else:
              wt_line_below_53 = True
              diff = -53 - yvalues1[-1]
            
            if counter % 15 == 0 and wt_line_above_53 == True:
              print symbol + " Wavetrend above 53"

            if counter % 15 == 0 and wt_line_above_53 == False:
              print symbol + " Wavetrend below 53"

            if counter % 15 == 0 and wt_line_below_53 == True:
              print symbol + " Wavetrend below -53"

            if counter % 15 == 0 and wt_line_below_53 == False:
              print symbol + " Wavetrend above -53"

          if init == True:
            wt_was_rising = wt_rising
            wt_line_was_above_53 = yvalues1[-1] > 53
            wt_line_was_below_53 = yvalues1[-1] < -53
          
          buy_diff = config[symbol].buy_threshold
          sell_diff = config[symbol].sell_threshold * -1
          
          if config[symbol].trade_all_crossings == True:
            cross = wt_rising != wt_was_rising and (abs(diff) > abs(buy_diff) or abs(diff) < abs(sell_diff)) and config[symbol].trade_auto == True
          else:
            cross_buy = False
            if wt_line_was_below_53 == True and wt_line_below_53 == False:
              cross_buy = True
            
            cross_sell = False
            if wt_line_was_above_53 == True and wt_line_above_53 == False:
              cross_sell = True
            
            cross = (cross_buy or cross_sell) and (abs(diff) > abs(buy_diff) or abs(diff) < abs(sell_diff)) and config[symbol].trade_auto == True
            
          if cross == True:
            print symbol + " INTERSECTION!!!"
            
            if config[symbol].trade_all_crossings == True:
              wt_was_rising = wt_rising
              buy = wt_rising == True and not bought
            else:
              if cross_buy:
                wt_line_was_below_53 = wt_line_below_53
              
              buy = cross_buy and not bought
              
            if buy == True:
                #buy
                if is_windows:
                  import win32api
                  gt = client.get_server_time()
                  tt=time.gmtime(int((gt["serverTime"])/1000))
                  win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)

                print "BUY"
                asset_balance = 0
                symbol_price = get_symbol_price(symbol)

                amount_per_trade = translate_buy_amount_percent(config[symbol].buy_amount_percent_index)
                if symbol.endswith("USDT"):
                  asset_balance = float(client.get_asset_balance("usdt")["free"])
                  buy_amount = truncate((asset_balance / symbol_price) * amount_per_trade, 3)
                  if buy_amount < truncate((init_btc_balance / symbol_price) * amount_per_trade, 3):
                      buy_amount = truncate((asset_balance / symbol_price) * 0.97, 3)
                else:
                  asset_balance = float(client.get_asset_balance("btc")["free"])
                  buy_amount = truncate((asset_balance / symbol_price) * amount_per_trade, 2)
                  if buy_amount < truncate((init_btc_balance /symbol_price) * amount_per_trade, 2):
                      buy_amount = truncate((asset_balance / symbol_price) * 0.97, 2)
                
                print buy_amount

                if buy_amount != 0:
                  from playsound import playsound
                  try:
                    order = client.order_market_buy(symbol=symbol, quantity=buy_amount)
                    playsound("beep.wav")
                    prev_trade_time = datetime.datetime.now()
                  except:
                    print get_full_stacktrace()
                  time.sleep(5)
                  if symbol.endswith("USDT"):
                    to_sell = int(truncate(float(client.get_asset_balance("usdt")["free"]), 2))
                  else:
                    to_sell = truncate(float(client.get_asset_balance(get_asset_from_symbol(symbol))["free"]), 2)
                  print "TO SELL: " + str(to_sell)
                  bought = True
                  sold = False
                  f = open("trades.txt", "a")
                  f.write("BUY %s MARKET @ %.8f\n" % (symbol, symbol_price))
                  f.close()
                  item = QtGui.QListWidgetItem("BUY %s MARKET @ %.8f" % (symbol, symbol_price))
                  main.listWidget.addItem(item)

            if config[symbol].trade_all_crossings == True:
              wt_was_rising = wt_rising
              sell = wt_rising == False and not sold
            else:
              if cross_sell:
                wt_line_was_above_53 = wt_line_above_53
              
              sell = cross_sell and not sold
              
            if sell == True:
                #sell
                if is_windows:
                  import win32api
                  gt = client.get_server_time()
                  tt=time.gmtime(int((gt["serverTime"])/1000))
                  win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)
                print "SELL"
                
                if symbol == "BTCUSDT":                  
                  symbol_price = get_symbol_price(symbol)
                  asset_balance = truncate(float(client.get_asset_balance("usdt")["free"]) * 0.97 / symbol_price, 3)
                else:
                  asset_balance = truncate(float(client.get_asset_balance(get_asset_from_symbol(symbol))["free"]), 2)
                
                if to_sell == 0:
                  to_sell = asset_balance
                
                print asset_balance
                
                if asset_balance != 0:
                  from playsound import playsound
                  symbol_price = get_symbol_price(symbol)
                  print to_sell
                  try:
                    order = client.order_market_sell(symbol=symbol, quantity=to_sell)
                    playsound("beep.wav")
                    prev_trade_time = datetime.datetime.now()
                  except:
                    print get_full_stacktrace()
                  bought = False
                  sold = True
                  f = open("trades.txt", "a")
                  f.write("SELL %s MARKET @ %.8f\n" % (symbol, symbol_price))
                  f.close()
                  item = QtGui.QListWidgetItem("SELL %s MARKET @ %.8f" % (symbol, symbol_price))
                  main.listWidget.addItem(item)

          ticker = prices[-1][4]
          in_one_hour = datetime.datetime.now()
          in_one_hour = in_one_hour.replace(minute = 0, second = 0)
          in_one_hour = in_one_hour + timedelta(hours=1)
          duration = in_one_hour - datetime.datetime.now()
          
          days, seconds = duration.days, duration.seconds
          hours = days * 24 + seconds // 3600
          minutes = (seconds % 3600) // 60
          seconds = seconds % 60
          time_to_hour = "%02d:%02d" % (minutes, seconds)

          if first == True:
            price_line = ax.axhline(ticker, color='black', linestyle="dotted", lw=.7)
            annotation = ax.text(date[-1] + timedelta(hours=3), ticker, "%.8f" % ticker, fontsize=7, color='black')
            annotation.set_bbox(dict(facecolor='white', edgecolor='black', lw=.5))
            
            tbox = annotation.get_window_extent(canvas.renderer)
            dbox = tbox.transformed(ax.transData.inverted())
            y0 = dbox.height * 2.4
            time_annotation = ax.text(date[-1] + timedelta(hours=3), ticker - y0, time_to_hour, fontsize=7, color='black')
            time_annotation.set_bbox(dict(facecolor='white', edgecolor='black', lw=.5))
          else:
            price_line.set_ydata(ticker)
            annotation.set_text("%.8f" % ticker)
            annotation.set_y(ticker)
            annotation.set_bbox(dict(facecolor='white', edgecolor='black', lw=.5))
            tbox = annotation.get_window_extent(canvas.renderer)
            dbox = tbox.transformed(ax.transData.inverted())
            y0 = dbox.height * 2.4
            time_annotation.set_text(time_to_hour)
            time_annotation.set_bbox(dict(facecolor='white', edgecolor='black', lw=.5))
            time_annotation.set_y(ticker - y0)

          last_line1, last_line2, last_rect = _candlestick(ax, prices, first, last_line1, last_line2, last_rect)
          if first == True:
            ax3.axhline(60, color='red')
            ax3.axhline(-60, color='green')
            ax3.axhline(0, color='gray', lw=.5)
            ax3.axhline(53, color='red', linestyle="dotted")
            ax3.axhline(-53, color='green', linestyle="dotted")
            ax.set_axis_bgcolor('white')

            pad = 0.25
            yl = ax.get_ylim()
            ax.set_ylim(yl[0]-(yl[1]-yl[0])*pad,yl[1])
            ax.set_xlabel(timeframe_entered)
            ax.set_ylabel(symbol)

            ax.spines['top'].set_edgecolor((18/255.0,27/255.0,33/255.0))
            ax.spines['left'].set_edgecolor((18/255.0,27/255.0,33/255.0))
            ax.spines['right'].set_edgecolor((18/255.0,27/255.0,33/255.0))
            ax.spines['bottom'].set_edgecolor((18/255.0,27/255.0,33/255.0))
            ax.set_axis_bgcolor('white')
            ax3.spines['left'].set_edgecolor('black')
            ax3.spines['right'].set_edgecolor('black')
            ax3.spines['top'].set_visible(False)
            ax3.spines['bottom'].set_visible(False)
            ax.grid(alpha=.25)
            ax.grid(True)

            if init == True:
              fig.tight_layout()

            bbox = ax.get_position()
            ax3.set_position([bbox.x0, bbox.y0, bbox.width, bbox.height / 4])
            ax.autoscale_view()
            first = False
            
          prices[:] = []
          prices2[:] = []
          dates2[:] = []
          dates3[:] = []
          xvalues1 = None
          yvalues1 = None
          xvalues2 = None
          yvalues2 = None
          gc.collect()

          canvas.draw()
          '''
          drawing.put(1)
          while True:
            val = queue.get()
            if val == 1:
              break
          '''
          
        except:
          print get_full_stacktrace()

        if datetime.datetime.now().minute == 0 and datetime.datetime.now().second < 5 and init == False:
          fig.clf()
          first = True
          time.sleep(10)
          
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

def getDataBinance(timeframe_entered, days_entered, currency_entered):
    limit = 0
    if timeframe_entered == "15m":
        limit = int(days_entered) * 4 * 24

    if timeframe_entered == "1m":
        limit = int(days_entered) * 60 * 24

    if timeframe_entered == "5m":
        limit = int(days_entered) * 12 * 24

    if timeframe_entered == "30m":
        limit = int(days_entered) * 2 * 24

    if timeframe_entered == "1h":
        limit = int(days_entered) * 24

    if timeframe_entered == "4h":
        limit = int(days_entered) *(24/4)

    if timeframe_entered == "6h":
        limit = int(days_entered) * (24/6)

    if timeframe_entered == "12h":
        limit = int(days_entered) * (24/12)

    if timeframe_entered == "1d":
        limit = int(days_entered)

    if timeframe_entered == "3d":
        limit = int(days_entered) / 3

    if timeframe_entered == "1w":
        limit = int(days_entered) / 7

    if timeframe_entered == "1M":
        limit = int(days_entered) / 31

    dt = []
    open_ = []
    high = []
    low = []
    close = []
    volume = []
    candles = client.get_klines(symbol=currency_entered, interval=timeframe_entered, limit=limit)

    for candle in candles:
      dt.append(datetime.datetime.fromtimestamp(int(candle[0]) / 1e3))
      open_.append(float(candle[1]))
      high.append(float(candle[2]))
      low.append(float(candle[3]))
      close.append(float(candle[4]))
      volume.append(float(candle[5]))

    return dt, open_, high, low, close, volume

listbox = None
tab_count = 0

from operator import itemgetter
DIRPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, symbol=None):
        self.fig = Figure(facecolor='white')

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
    def __init__(self, symbol):
        QtGui.QDialog.__init__(self)
        resolution = QtGui.QDesktopWidget().screenGeometry()
        uic.loadUi(os.path.join(DIRPATH, 'mainwindowqt.ui'), self)
        self.setGeometry(0, 0, int(resolution.width()/1.1), int(resolution.height()/1.2))
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2)) 
        widget = QtGui.QVBoxLayout(self.tabWidget.widget(0))
        dc = MplCanvas(self.tabWidget.widget(0), dpi=100, symbol=symbol)
        widget.addWidget(dc)
        t = threading.Thread(target=run_geforce, args=(symbol, dc.fig, dc, self))
        t.daemon = True
        t.start()
        
        self.toolButton.clicked.connect(self.add_coin_clicked)
        self.tab_widgets = []
        self.tab_widgets.append(self.tabWidget.widget(0))
        self.tabWidget.currentChanged.connect(self.tabOnChange)
        self.pushButton.clicked.connect(self.configAcceptClicked)
    
    def configAcceptClicked(self, event):
      try:
        buy_threshold = float(self.lineEdit.text())
      except:
        QtGui.QMessageBox.information(self, "WAVETREND ROBOT", "Entered buy theshold is not a number")
        return
        
      try:
        sell_threshold = float(self.lineEdit_2.text())
      except:
        QtGui.QMessageBox.information(self, "WAVETREND ROBOT", "Entered sell theshold is not a number")
        return
        
      selected_symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex()))
      if self.checkBox.isChecked() == True:
        config[selected_symbol].trade_auto = True
      else:
        config[selected_symbol].trade_auto = False
        
      if self.radioButton.isChecked() == True:
        config[selected_symbol].trade_all_crossings = True
      else:
        config[selected_symbol].trade_all_crossings = False
        
      if self.radioButton_2.isChecked() == True:
        config[selected_symbol].trade_lines_only = True
      else:
        config[selected_symbol].trade_lines_only = False
          
      config[selected_symbol].buy_threshold = float(buy_threshold)
      config[selected_symbol].sell_threshold = float(sell_threshold)
      config[selected_symbol].buy_amount_percent_index = self.comboBox.currentIndex()
    
      QtGui.QMessageBox.information(self, "WAVETREND ROBOT", selected_symbol + " Wavetrend configured.")
    
    def tabOnChange(self, event):
      selected_symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex()))
      main.groupBox.setTitle(selected_symbol + " Wavetrend")
      self.checkBox.setChecked(config[selected_symbol].trade_auto)
      self.radioButton.setChecked(config[selected_symbol].trade_all_crossings)
      self.radioButton_2.setChecked(config[selected_symbol].trade_lines_only)
      self.lineEdit.setText(str(config[selected_symbol].buy_threshold))
      self.lineEdit_2.setText(str(config[selected_symbol].sell_threshold))
      self.comboBox.setCurrentIndex(config[selected_symbol].buy_amount_percent_index)
    
    def addTab(self, symbol):
      self.tab_widgets.append(QtGui.QWidget())
      tab_index = self.tabWidget.addTab(self.tab_widgets[-1], symbol)
      self.tabWidget.setCurrentWidget(self.tab_widgets[-1])
      widget = QtGui.QVBoxLayout(self.tabWidget.widget(tab_index))
      dc = MplCanvas(self.tabWidget.widget(tab_index), dpi=100, symbol=symbol)
      widget.addWidget(dc)
      t = threading.Thread(target=run_geforce, args=(symbol, dc.fig, dc, self))
      t.daemon = True
      t.start()
         
    def add_coin_clicked(self, event):
      global dialog
      dialog = Dialog()
      dialog.show()
        
class Dialog(QtGui.QDialog):
    global config
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uic.loadUi(os.path.join(DIRPATH, 'windowqt.ui'), self)
        
        coins = client.get_ticker()
        btc_price = get_symbol_price("BTCUSDT")
        coins_ = []
        for coin in coins:
            if coin["symbol"].endswith("BTC"):
              coin["volumeFloat"] =int(float(coin["quoteVolume"]) * btc_price)
              coins_.append(coin)
            if coin["symbol"].endswith("USDT"):
              coin["volumeFloat"] = int(float(coin["quoteVolume"]))
              coins_.append(coin)
        coins = sorted(coins_, key=itemgetter("volumeFloat"), reverse=True)
        
        self.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        
        for coin in coins:
          if coin["symbol"].endswith("BTC") or coin["symbol"].endswith("USDT"):
            rowPosition = self.tableWidget.rowCount() - 1
            self.tableWidget.insertRow(rowPosition)
            self.tableWidget.setItem(rowPosition, 0, QtGui.QTableWidgetItem(coin["symbol"]))
            self.tableWidget.setItem(rowPosition, 1, QtGui.QTableWidgetItem(coin["priceChange"]))
            self.tableWidget.setItem(rowPosition, 2, QtGui.QTableWidgetItem(coin["priceChangePercent"]))
            self.tableWidget.setItem(rowPosition, 3, QtGui.QTableWidgetItem(str(coin["volumeFloat"])))
            if float(coin["priceChange"]) < 0:
              self.tableWidget.item(rowPosition, 0).setBackground(QtGui.QColor(255,0,0))
              self.tableWidget.item(rowPosition, 1).setBackground(QtGui.QColor(255,0,0))
              self.tableWidget.item(rowPosition, 2).setBackground(QtGui.QColor(255,0,0))
              self.tableWidget.item(rowPosition, 3).setBackground(QtGui.QColor(255,0,0))
            else:
              self.tableWidget.item(rowPosition, 0).setBackground(QtGui.QColor(0,255,0))
              self.tableWidget.item(rowPosition, 1).setBackground(QtGui.QColor(0,255,0))
              self.tableWidget.item(rowPosition, 2).setBackground(QtGui.QColor(0,255,0))
              self.tableWidget.item(rowPosition, 3).setBackground(QtGui.QColor(0,255,0))

    def accept(self):
      selectionModel = self.tableWidget.selectionModel()
      if selectionModel.hasSelection():
        row = self.tableWidget.selectedItems()[0].row()
        symbol = str(self.tableWidget.item(row, 0).text())
  
        config[symbol] = abstract()
        config[symbol].trade_auto = False
        config[symbol].trade_all_crossings = True
        config[symbol].trade_lines_only = False
        config[symbol].buy_threshold = 1.0
        config[symbol].sell_threshold = 1.0
        config[symbol].buy_amount_percent_index = 0
  
        global main
        global main_shown
        if not main_shown:
          main = Window(symbol)
          main.tabWidget.setTabText(main.tabWidget.count()-1, symbol)
          main.groupBox.setTitle(symbol + " Wavetrend")
          main.show()
          main_shown = True
          f = open("trades.txt")
          lines = f.readlines()
          for line in lines:
            item = QtGui.QListWidgetItem(line)
            main.listWidget.addItem(item)
          f.close()
        else:
          main.addTab(symbol)
          main.groupBox.setTitle(symbol + " Wavetrend")
        
        self.close()

if __name__ == "__main__":
  init_btc_balance = float(client.get_asset_balance("btc")["free"])

  app = QtGui.QApplication(sys.argv)
  dialog = Dialog()
  dialog.show()
  os._exit(app.exec_())
