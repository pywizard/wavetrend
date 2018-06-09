import warnings
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
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
import Tkinter as tk
import pygubu
import traceback, tkMessageBox
import FileDialog
import copy
import ttk
from Tkinter import *
import threading
import pytz
from tzlocal import get_localzone
import pandas as pd
import copy
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

last_line1 = {}
last_line2 = {}
last_rect = {}

def _candlestick(ax, quotes, tabindex, width=0.2, colorup='white', colordown='black',
                 alpha=1.0):

    global last_line1
    global last_line2
    global last_rect
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
    
    if first[tabindex] == False:
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

        if first[tabindex] == True:
          lines.append(vline1)
          lines.append(vline2)
          patches.append(rect)
          ax.add_line(vline1)
          ax.add_line(vline2)
          ax.add_patch(rect)
          last_line1[tabindex] = vline1
          last_line2[tabindex] = vline2
          last_rect[tabindex] = rect
        else:
          last_line1[tabindex].set_ydata((high, higher))
          last_line2[tabindex].set_ydata((low, lower))
          last_rect[tabindex].set_y(lower)
          last_rect[tabindex].set_height(height)
          last_rect[tabindex].set_facecolor(color)
        
    ax.autoscale_view()

    return lines, patches

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

class Application:
    def __init__(self, master):
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_from_file('window.ui')
        self.mainwindow = builder.get_object('mainframe', master)
        builder.connect_callbacks(self)
        master.report_callback_exception = self.report_callback_exception

    def ok_callback(self):
        global currency_entered2
        global root

        currency_entered2 = self.builder.get_object('boxCurrency').get().upper()

        if currency_entered2 != "":
	    root.quit()
	    root.withdraw()

    def cause_exception(self):
        a = []
        a.a = 0

    def report_callback_exception(self, *args):
        err = traceback.format_exception(*args)
        tkMessageBox.showerror('Exception', err)

class abstract():
  pass

geforce_vars = []

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

queue = {}
queue[1] = Queue.Queue()
queue[2] = Queue.Queue()
drawing = {}
drawing[1] = Queue.Queue()
drawing[2] = Queue.Queue()

canvas = {}
canvas[1] = None
canvas[2] = None

first =  {}
first[1] = True
first[2] = True

def run_geforce(fig, tabindex, tabnum, listbox):
    global currency_entered2
    global drawing
    global queue
    global status_bar
    global geforce_vars
    global first

    currency_entered = currency_entered2
    timeframe_entered = "1h"
    days_entered = "13"
    bought = False
    sold = False

    symbol = currency_entered
    to_sell = 0

    init = True
    switch_hour = False
    prev_trade_time = 0
    counter = 0
    wt_was_rising = False
    while True:
        try:
          date, open_, high, low, close, vol = getDataBinance(timeframe_entered, days_entered, currency_entered)
          
          if first[tabindex] == True:
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

          if first[tabindex] == True:
            wavetrend1 = ax3.plot(dates2, wt1, color="green", lw=.5)
            wavetrend2 = ax3.plot(dates2, wt2, color="red", lw=.5)
          else:
            wavetrend1[0].set_ydata(wt1)
            wavetrend2[0].set_ydata(wt2)

          if first[tabindex] == True:
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

          symbol = currency_entered
          
          wt_rising = False
     
          if yvalues1[-1] - yvalues2[-1] > 0:
            if counter % 15 == 0:
              print "Rising Wavetrend"
            wt_rising = True
          else:
            if counter % 15 == 0:
              print "Falling Wavetrend"
          
          if init == True:
            wt_was_rising = wt_rising
          
          if wt_rising != wt_was_rising:
            print symbol + " INTERSECTION!!!"
            wt_was_rising = wt_rising

            if wt_rising == True and not bought:
                #buy
                if is_windows:
                  import win32api
                  gt = client.get_server_time()
                  tt=time.gmtime(int((gt["serverTime"])/1000))
                  win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)

                print "BUY"
                asset_balance = 0
                symbol = currency_entered
                symbol_price = get_symbol_price(symbol)

                if symbol == "BTCUSDT":
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
                  if symbol == "BTCUSDT":
                    to_sell = int(truncate(float(client.get_asset_balance("usdt")["free"]), 2))
                  else:
                    to_sell = truncate(float(client.get_asset_balance(get_asset_from_symbol(symbol))["free"]), 2)
                  print "TO SELL: " + str(to_sell)
                  bought = True
                  sold = False
                  f = open("trades.txt", "a")
                  f.write("BUY %s MARKET @ %.8f\n" % (symbol, symbol_price))
                  f.close()
                  listbox.insert(END, "BUY %s MARKET @ %.8f" % (symbol, symbol_price))

            if wt_rising == False and not sold:
                #sell
                if is_windows:
                  import win32api
                  gt = client.get_server_time()
                  tt=time.gmtime(int((gt["serverTime"])/1000))
                  win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)
                print "SELL"
                symbol = currency_entered
                
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
                  symbol = currency_entered
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
                  listbox.insert(END, "SELL %s MARKET @ %.8f" % (symbol, symbol_price))

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

          if first[tabindex] == True:
            price_line = ax.axhline(ticker, color='black', linestyle="dotted", lw=.7)
            annotation = ax.text(date[-1] + timedelta(hours=3), ticker, "%.8f" % ticker, fontsize=7, color='black')
            annotation.set_bbox(dict(facecolor='white', edgecolor='black', lw=.5))
            
            tbox = annotation.get_window_extent(canvas[tabindex].renderer)
            dbox = tbox.transformed(ax.transData.inverted())
            y0 = dbox.height * 2.4
            time_annotation = ax.text(date[-1] + timedelta(hours=3), ticker - y0, time_to_hour, fontsize=7, color='black')
            time_annotation.set_bbox(dict(facecolor='white', edgecolor='black', lw=.5))
          else:
            price_line.set_ydata(ticker)
            annotation.set_text("%.8f" % ticker)
            annotation.set_y(ticker)
            annotation.set_bbox(dict(facecolor='white', edgecolor='black', lw=.5))
            tbox = annotation.get_window_extent(canvas[tabindex].renderer)
            dbox = tbox.transformed(ax.transData.inverted())
            y0 = dbox.height * 2.4
            time_annotation.set_text(time_to_hour)
            time_annotation.set_bbox(dict(facecolor='white', edgecolor='black', lw=.5))
            time_annotation.set_y(ticker - y0)

          _candlestick(ax, prices, tabindex)
          if first[tabindex] == True:
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
            ax.set_ylabel(currency_entered)

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
              listbox.insert(END, "=== TRADES === ")
              f = open("trades.txt")
              lines = f.readlines()
              for line in lines:
                listbox.insert(END, line)
              f.close()

            bbox = ax.get_position()
            ax3.set_position([bbox.x0, bbox.y0, bbox.width, bbox.height / 4])
            ax.autoscale_view()
            first[tabindex] = False
            
          prices[:] = []
          prices2[:] = []
          dates2[:] = []
          dates3[:] = []
          xvalues1 = None
          yvalues1 = None
          xvalues2 = None
          yvalues2 = None
          gc.collect()

          drawing[tabindex].put(1)
          while True:
            val = queue[tabindex].get()
            if val == 1:
              break
            time.sleep(0.00000001)

        except:
          print get_full_stacktrace()

        if datetime.datetime.now().minute == 0 and init == False and switch_hour == False:
          fig.clf()
          first[tabindex] = True
          switch_hour = True
        
        if datetime.datetime.now().minute == 1:
          switch_hour = False
          
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

class StatusBar(tk.Frame):
   def __init__(self, master):
      tk.Frame.__init__(self, master)
      self.label = tk.Label(self, bd = 1, relief = tk.SUNKEN, anchor = "center")
      self.label.pack(fill=tk.X)
   def set(self, format0, *args):
      self.label.config(text = format0 % args, font=("Courier",14))
      self.label.update_idletasks()
   def clear(self):
      self.label.config(text="")
      self.label.update_idletasks()

def quit():
    global tkTop
    tkTop.destroy()

listbox = None
tab_count = 0

def on_closing():
   mainroot.destroy()
   os._exit(0)

def add_notebook(event):
  global drawing
  global geforce_vars
  global tab_count
  global root
  global queue
  global canvas

  clicked_tab = notebook.tk.call(notebook._w, "identify", "tab", event.x, event.y)
  if clicked_tab != 0:
    return

  if tab_count == 2:
    tkMessageBox.showinfo('', "Only two coins allowed.")
    return

  root = tk.Tk()
  app = Application(root)
  root.mainloop()

  frame1 = ttk.Frame(notebook)
  listbox = Listbox(frame1)
  listbox.pack(side="bottom", fill=tk.BOTH)
  listbox.config(width=0, height=7, font=('Arial', '12', 'bold'))

  frame1.pack(fill=tk.BOTH, expand=tk.YES)

  notebook.master.title("WAVETREND ROBOT")
  if is_windows:
    notebook.master.state('zoomed')
  else:
    notebook.master.attributes('-zoomed', True)
  notebook.pack(fill=tk.BOTH, expand=tk.YES)

  var = abstract()
  var.show_ema = False
  var.show_wavetrend = True
  var.show_ichimoku_clouds = True
  var.redraw = False

  geforce_vars.append(var)

  fig = Figure(facecolor='white')
  canvas[tab_count + 1] = FigureCanvasTkAgg(fig, master=frame1)
  canvas[tab_count + 1].show()
  canvas[tab_count + 1].get_tk_widget().pack(fill=tk.BOTH, expand=tk.YES)

  tab = notebook.add(frame1, text=str(currency_entered2) + "  ")
  tab_count = tab_count + 1
  notebook.select(tab_count)

  t = threading.Thread(target=run_geforce, args=(fig, tab_count, len(geforce_vars)-1, listbox,))
  t.daemon = True
  t.start()

  listbox.insert(END, "WAVETREND ROBOT 1.0 started.")

  tabindex = tab_count
  while True:
    for i in [1,2]:
      if drawing[i].qsize() != 0 and drawing[i].get() == 1:
        canvas[i].draw()
        queue[i].put(1)
      else:
        notebook.update()
        notebook.update_idletasks()
      time.sleep(0.00000001)

if __name__ == "__main__":
  init_btc_balance = float(client.get_asset_balance("btc")["free"])

  os.environ['TZ'] = str(get_localzone())
  mainroot = tk.Tk()

  imgicon = os.path.join(os.path.dirname(os.path.realpath(__file__)),'joker.gif')
  img = tk.PhotoImage(file=imgicon)
  mainroot.tk.call('wm', 'iconphoto', mainroot._w, img)

  status_bar = StatusBar(mainroot)
  status_bar.pack(side = tk.BOTTOM, fill = tk.X)

  notebook = ttk.Notebook(mainroot)
  notebook.bind("<ButtonRelease-1>", add_notebook)

  frame1 = ttk.Frame(notebook)
  frame1.pack(fill=tk.BOTH, expand=tk.YES)
  notebook.add(frame1, text="+")
  notebook.pack(fill=tk.BOTH, expand=tk.YES)

  mainroot.protocol("WM_DELETE_WINDOW", on_closing)
  mainroot.mainloop()
  os._exit(0)
