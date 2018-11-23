import warnings
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from numpy import NaN, Inf, arange, isscalar, asarray, array
import matplotlib.ticker as matplotlib_ticker
from matplotlib.dates import date2num
from matplotlib.finance import *
from datetime import timedelta
import sys
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
import os
import Queue
import ccxt
from indicators import *
from colors import *
import decimal
import random
import functools

conf = {}
execfile("config.txt", conf) 

exchange = conf["exchange"]
api_key = conf["api_key"]
api_secret = conf["api_secret"]

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

ticker = client.fetch_tickers()
is_usdt = False
if "BTC/USDT" in ticker:
  is_usdt = True

class abstract():
  pass

config = {}

def _candlestick(ax, quotes, first, last_line1, last_line2, last_rect, candle_width, width=0.2, colorup='white', colordown='black',
                 alpha=1.0):

    width = candle_width
    line_width = 0.9
    OFFSET = width / 2.0

    lines = []
    patches = []

    colorup = "#134F5C"
    colordown = "#A61C00"
    colorup2 = "#53B987"
    colordown2 = "#EB4D5C"

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
                linewidth=line_width,
                antialiased=True,
            )

            vline2 = Line2D(
                xdata=(t, t), ydata=(low, lower),
                color=colorup2,
                linewidth=line_width,
                antialiased=True,
            )
            
            rect = Rectangle(
                xy=(t - OFFSET, lower),
                width=width,
                height=height,
                facecolor=color,
                edgecolor=colorup2,
                linewidth=line_width
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
                linewidth=line_width,
                antialiased=True,
            )

            vline2 = Line2D(
                xdata=(t, t), ydata=(low, lower),
                color=colordown2,
                linewidth=line_width,
                antialiased=True,
            )            

            rect = Rectangle(
                xy=(t - OFFSET, lower),
                width=width,
                height=height,
                facecolor=color,
                edgecolor=colordown2,
                linewidth=line_width
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
          last_line1.set_color(color2)
          last_line2.set_color(color2)          
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

window_ids = {}
def get_window_id():
  return "win-" + ''.join(random.choice('0123456789abcdef') for i in range(10))

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
dqs = {}
qs_local = Queue.Queue()

FIGURE_ADD_SUBPLOT = 0
FIGURE_TIGHT_LAYOUT = 1
FIGURE_CLEAR = 2
CANVAS_GET_SIZE = 3
CANVAS_DRAW = 4
RETRIEVE_CURRENT_INDEX = 5
RETRIEVE_CHART_DATA = 6
CHART_DESTROY = 7
CHART_DATA_READY = 1
SHOW_STATUSBAR_MESSAGE = 0

chartrunner_remove_tab = None
datarunner_remove_tab = None

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

from operator import itemgetter

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

class DataRunner(QtCore.QThread):
  def __init__(self, parent, symbol, tab_index, timeframe_entered):
    super(DataRunner, self).__init__(parent)
    self.symbol = symbol
    self.tab_index = tab_index
    self.timeframe_entered = timeframe_entered
  
  def run(self):
    global dqs
    global datarunner_remove_tab
    
    while True:
      if datarunner_remove_tab != None:
        if self.tab_index == datarunner_remove_tab:
          break
          
      limit = 10

      dt = []
      open_ = []
      high = []
      low = []
      close = []
      volume = []
      
      while True:
        try:
          candles = client.fetch_ohlcv(self.symbol, self.timeframe_entered, limit=limit)
          break
        except:
          print get_full_stacktrace()
          time.sleep(1)
          continue

      for candle in candles:
        dt.append(datetime.datetime.fromtimestamp(int(candle[0]) / 1000))
        open_.append(float(candle[1]))
        high.append(float(candle[2]))
        low.append(float(candle[3]))
        close.append(float(candle[4]))
        volume.append(float(candle[5]))

      result = [dt, open_, high, low, close, volume, limit]
      
      if not dqs[self.tab_index].full():      
        dqs[self.tab_index].put(CHART_DATA_READY)
        dqs[self.tab_index].put(result)
        
    del dqs[self.tab_index]
    datarunner_remove_tab = None

class ChartRunner(QtCore.QThread):
  data_ready = QtCore.pyqtSignal()
  
  def __init__(self, parent, symbol, tab_index, timeframe_entered):
    super(ChartRunner, self).__init__(parent)
    self.parent = parent
    self.symbol = symbol
    self.tab_index = tab_index
    self.timeframe_entered = timeframe_entered

  def run(self):
    global qs
    global aqs
    global chartrunner_remove_tab

    days_entered = days_table[self.timeframe_entered]
    timeframe_entered = self.timeframe_entered
    symbol = self.symbol
    tab_index = self.tab_index

    to_sell = 0

    init = True
    prev_trade_time = 0
    counter = 0
    wt_was_rising = False
    first = True
    last_line1 = None
    last_line2 = None
    last_rect = None    
    prices = []
    indicators = []
    indicator_axes = []
    ctx = decimal.Context()
    ctx.prec = 20
    indicator_update_time = 0
    
    while True:
        try:
          if chartrunner_remove_tab != None:
            if tab_index == chartrunner_remove_tab:
              break
              
          qs[tab_index].put(RETRIEVE_CURRENT_INDEX)
          self.data_ready.emit()
          current_tab_index = aqs[self.tab_index].get()
          
          if tab_index != current_tab_index:
            time.sleep(0.1)
            continue

          if first == True:
            date, open_, high, low, close, vol, limit = self.getData(timeframe_entered, days_entered, symbol, False)
          else:
            qs[self.tab_index].put(RETRIEVE_CHART_DATA)
            self.data_ready.emit()
            chart_result = aqs[self.tab_index].get()
            if chart_result != 0:
              [date2, open2_, high2, low2, close2, vol2, limit2] = chart_result
          
          if first == True:
            qs[tab_index].put(FIGURE_ADD_SUBPLOT)
            self.data_ready.emit()
            ax = aqs[self.tab_index].get()
            previous_candle = [date[-2], open_[-2], high[-2], low[-2], close[-2], vol[-2]]
            len_candles = len(date)
            
            prices[:] = []
            for i in range(0, len(date)):
                prices.append((date2num(date[i]), open_[i], high[i], low[i], close[i], vol[i], date[i]))

            dates2 = [x[0] for x in prices]
                        
            ax.xaxis.set_tick_params(labelsize=9)
            ax.yaxis.set_tick_params(labelsize=9)
          else:
            prices[-1] = (date2num(date2[-1]), open2_[-1], high2[-1], low2[-1], close2[-1], vol2[-1], date2[-1])
            prices[-2] = (date2num(date2[-2]), open2_[-2], high2[-2], low2[-2], close2[-2], vol2[-2], date2[-2])
  
          if first == False and previous_candle != [date2[-2], open2_[-2], high2[-2], low2[-2], close2[-2], vol2[-2]] and len(date2) == 10:
            qs[self.tab_index].put(FIGURE_CLEAR)
            self.data_ready.emit()
            aqs[self.tab_index].get()
            first = True
            last_line1 = None
            last_line2 = None
            last_rect = None
            indicators[:] = []
            indicator_axes[:] = []
            continue

          if first == True:
            indicators.append(indicator_BBANDS())
            indicators.append(indicator_MACD())
            indicators.append(indicator_DMI())
            indicators.append(indicator_RSI())

          '''
          n1, n2, period = 10, 21, 60
          ap = (np.array(high) + np.array(low) + np.array(close)) / 3
          esa = talib.EMA(ap, timeperiod=n1)
          d = talib.EMA(abs(ap - esa), timeperiod=n1)
          ci = (ap - esa) / (0.015 * d)
          wt1 = talib.EMA(ci, timeperiod=n2)
          wt2 = talib.SMA(wt1, timeperiod=4)
          '''
          
          start_x = 0
          for indicator in indicators:
            indicator.generate_values(open, high, low, close)
            if first == True:
              if indicator.overlay_chart:
                indicator.plot_once(ax, dates2)
              else:
                new_ax = ax.twinx()
                new_ax.yaxis.tick_left()
                new_ax.yaxis.set_label_position("left")
                new_ax.xaxis.set_tick_params(labelsize=9)
                new_ax.yaxis.set_tick_params(labelsize=9)                
                new_ax.spines['left'].set_edgecolor(grayscale_dark)
                new_ax.spines['right'].set_edgecolor(grayscale_light)
                new_ax.spines['top'].set_edgecolor(grayscale_light)
                new_ax.spines['bottom'].set_edgecolor(grayscale_light)
                new_ax.spines['left'].set_linewidth(3)
                new_ax.xaxis.label.set_color(white)
                new_ax.yaxis.label.set_color(white)
                new_ax.tick_params(axis='x', colors=white)
                new_ax.tick_params(axis='y', colors=white)            
                new_ax.grid(alpha=.25)
                new_ax.grid(True)
                
                indicator_axes.append(new_ax)
                indicator.plot_once(new_ax, dates2)
                indiactor_update_time = time.time()
            else:
              if time.time() - indicator_update_time > 30:
                indicator.update()              
            
            xaxis_start = indicator.xaxis_get_start()
            if xaxis_start > start_x:
              start_x = xaxis_start
                          
          if time.time() - indicator_update_time > 30:
            indicator_update_time = time.time()     

          highest_price = 0
          lowest_price = 999999999999

          for i in range(start_x, len(date)):
            if high[i] > highest_price:
              highest_price = high[i]
            if low[i] < lowest_price:
              lowest_price = low[i]
              
          ax.yaxis.set_major_locator(matplotlib_ticker.MultipleLocator((highest_price-lowest_price)/20))
          ax.set_ylim((lowest_price - lowest_price * 0.015, highest_price + highest_price * 0.015))
          
          xl = ax.get_xlim()
          ax.set_xlim(date[start_x], xl[1])

          ticker = get_symbol_price(symbol)
          ticker_formatted = str(ticker)
          ticker_for_line = prices[-1][4]
          
          if "e-" in str(ticker) or "e+" in str(ticker):
            d1 = ctx.create_decimal(repr(ticker))
            ticker_formatted = format(d1, 'f')

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
            price_line = ax.axhline(ticker_for_line, color='gray', linestyle="dotted", lw=.9)
            decimal_places = str(ticker_formatted[::-1].find('.'))
            annotation = ax.text(date[-1] + (date[-1]-date[-5]), ticker_for_line, ("%." + decimal_places + "f") % ticker, fontsize=7, color=white)
            annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))

            qs[tab_index].put(CANVAS_GET_SIZE)
            qs[tab_index].put(annotation)
            self.data_ready.emit()
            tbox = aqs[tab_index].get()
          
            dbox = tbox.transformed(ax.transData.inverted())
            y0 = dbox.height * 2.4
            if timeframe_entered in ["1m", "5m", "15m", "30m", "1h"]:
              time_annotation = ax.text(date[-1] + (date[-1]-date[-5]), ticker_for_line - y0, time_to_hour, fontsize=7, color=white)
              time_annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))
          else:
            price_line.set_ydata(ticker_for_line)
            
            decimal_places = str(ticker_formatted[::-1].find('.'))
            annotation.set_text(("%." + decimal_places + "f") % ticker)
              
            annotation.set_y(ticker_for_line)
            annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))
            qs[tab_index].put(CANVAS_GET_SIZE)
            qs[tab_index].put(annotation)
            self.data_ready.emit()
            tbox = aqs[tab_index].get()
            
            dbox = tbox.transformed(ax.transData.inverted())
            y0 = dbox.height * 2.4
            if timeframe_entered in ["1m", "5m", "15m", "30m", "1h"]:            
              time_annotation.set_text(time_to_hour)
              time_annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))
              time_annotation.set_y(ticker_for_line - y0)

          if init == True:
            xl = ax.get_xlim()
            candle_width = ((dbox.x0 - xl[0]) / limit) * 0.8
          if first == True:
            for i in xrange(0, len(indicators)):
              if indicators[i].name == "MACD":
                indicators[i].candle_width = candle_width
                indicators[i].update()
          
          last_line1, last_line2, last_rect = _candlestick(ax, prices, first, last_line1, last_line2, last_rect, candle_width)
          
          if first == True:
            ax.autoscale_view()
            ax.set_axis_bgcolor(black)
            ax.yaxis.tick_right()
            ax.yaxis.set_label_position("right")
            ax.spines['top'].set_edgecolor(grayscale_dark)
            ax.spines['left'].set_edgecolor(grayscale_dark)
            ax.spines['right'].set_edgecolor(grayscale_light)
            ax.spines['bottom'].set_edgecolor(grayscale_light)
            ax.spines['left'].set_linewidth(3)
            ax.spines['top'].set_linewidth(3)
            ax.set_axis_bgcolor(black)
            ax.xaxis.label.set_color(white)
            ax.yaxis.label.set_color(white)
            ax.tick_params(axis='x', colors=white)
            ax.tick_params(axis='y', colors=white)
            ax.grid(alpha=.25)
            ax.grid(True)

          if init == True:
            qs[tab_index].put(FIGURE_TIGHT_LAYOUT)
            self.data_ready.emit()
            aqs[tab_index].get()            
            ax_bbox = ax.get_position()

          if first == True:
            axis_num = 0
            axis_height = None
            for axis in indicator_axes:
              axis_num = axis_num + 1
              bbox = ax_bbox
              if axis_num == 1:
                axis.set_position([bbox.x0, bbox.y0, bbox.width, bbox.height / 7])
                bbox = axis.get_position()
                axis_height = bbox.height 
              else:
                axis.set_position([bbox.x0, bbox.y0 + axis_height, bbox.width, bbox.height / 7])
                bbox = axis.get_position()
                axis_height = axis_height + bbox.height
                              
            ax.set_position([ax_bbox.x0, ax_bbox.y0 + axis_height, ax_bbox.width, ax_bbox.height - axis_height])
            
            first_axis = True
            for axis in indicator_axes:
              axis.get_xaxis().set_visible(True)
              if first_axis:
                first_axis = False
                continue
              for t in axis.xaxis.get_major_ticks():
                t.tick1On = t.tick2On = False
                t.label1On = t.label2On = False            
            
            for t in ax.xaxis.get_major_ticks():
              t.tick1On = t.tick2On = False
              t.label1On = t.label2On = False
            
            ax.plot(1,1, label=symbol + ", " + timeframe_entered + ", " + exchange, marker = '',ls ='')
            legend = ax.legend(frameon=False,loc="upper left", fontsize="medium")
            for text in legend.get_texts():
              text.set_color(grayscale_lighter)
            
          first = False
          #gc.collect()
          
          qs[tab_index].put(CANVAS_DRAW)
          self.data_ready.emit()
          aqs[tab_index].get()
        except:
          print get_full_stacktrace()
          
        counter = counter + 1
        
        init = False
    
    chartrunner_remove_tab = None
    qs[tab_index].put(CHART_DESTROY)
    self.data_ready.emit()
        
  def getData(self, timeframe_entered, days_entered, currency_entered, few_candles):
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
        limit = 10

      dt = []
      open_ = []
      high = []
      low = []
      close = []
      volume = []
      
      while True:
        try:
          candles = client.fetch_ohlcv(currency_entered, timeframe_entered, limit=limit)
          break
        except:
          print get_full_stacktrace()
          time.sleep(1)
          continue

      for candle in candles:
        dt.append(datetime.datetime.fromtimestamp(int(candle[0]) / 1000))
        open_.append(float(candle[1]))
        high.append(float(candle[2]))
        low.append(float(candle[3]))
        close.append(float(candle[4]))
        volume.append(float(candle[5]))

      return dt, open_, high, low, close, volume, limit

class UpdateUsdBalanceRunner(QtCore.QThread):
  data_ready = QtCore.pyqtSignal()
  
  def __init__(self, parent):
    super(UpdateUsdBalanceRunner, self).__init__(parent)
    
  def run(self):
    global qslocal
    
    while True:
      time.sleep(5)
      try:
        ticker = client.fetch_tickers()

        self.usdt_symbols = []
        self.btc_symbols = []
        for symbol,value in ticker.iteritems():
          if symbol.endswith("USDT"):
            self.usdt_symbols.append(symbol) 
          if symbol.endswith("USD"):
            self.usdt_symbols.append(symbol)
          if symbol.endswith("BTC"):
            self.btc_symbols.append(symbol)

        balances = client.fetch_balance()
        usdt_balance = 0
        
        if "BTC/USDT" in ticker:
          btcusd_symbol = "BTC/USDT"
        else:
          btcusd_symbol = "BTC/USD"
        
        btc_price = get_symbol_price(btcusd_symbol)
        for balance_symbol, balance in balances.iteritems():
          if "total" not in balance:
            continue
          if float(balance["total"]) == 0.0:
            continue
          if balance_symbol == "USDT":
            usdt_balance = usdt_balance + float(balance["total"])
          elif balance_symbol + "/USDT" in self.usdt_symbols:
            for symbol_name,symbol in ticker.iteritems():
              if symbol_name == balance_symbol + "/USDT":
                symbol_price = float(symbol["last"])
                break
            usdt_balance = usdt_balance + float(balance["total"]) * symbol_price
          elif balance_symbol + "/USD" in self.usdt_symbols:
            for symbol_name,symbol in ticker.iteritems():
              if symbol_name == balance_symbol + "/USD":
                symbol_price = float(symbol["last"])
                break
            usdt_balance = usdt_balance + float(balance["total"]) * symbol_price
          elif balance_symbol + "/BTC" in self.btc_symbols:
            for symbol_name,symbol in ticker.iteritems():
              if symbol_name == balance_symbol + "/BTC":
                symbol_price = float(symbol["last"])
                break
            usdt_balance = usdt_balance + float(balance["total"]) * symbol_price * btc_price
        
        btc_balance = usdt_balance / btc_price
        
        qs_local.put(SHOW_STATUSBAR_MESSAGE)
        qs_local.put("USD Balance: " + "%.2f - BTC Balance: %.8f" % (usdt_balance, btc_balance))
        self.data_ready.emit()
      except:
        print get_full_stacktrace()
        
      time.sleep(35)

class Window(QtGui.QMainWindow):
    global tab_widgets
    global config
    global window_ids
    def __init__(self, symbol, timeframe_entered):
        QtGui.QMainWindow.__init__(self)
        resolution = QtGui.QDesktopWidget().screenGeometry()
        uic.loadUi('mainwindowqt.ui', self)
        self.setWindowTitle("WAVETREND ROBOT - " + exchange)
        self.setGeometry(0, 0, int(resolution.width()/1.1), int(resolution.height()/1.2))
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))         
        self.toolButton.clicked.connect(self.add_coin_clicked)
        self.toolButton_2.clicked.connect(self.trade_coin_clicked)
        self.tab_widgets = []
        self.tab_widgets.append(self.tabWidget.widget(0))
        self.tabWidget.currentChanged.connect(self.tabOnChange)
        self.setStyleSheet("border: 0;");
        self.tabWidget.setStyleSheet("QTabWidget::pane { border: 0;}");
        
        self.tabBar = self.tabWidget.tabBar()
        tabBarMenu = QtGui.QMenu()
        closeAction = QtGui.QAction("close", self)
        tabBarMenu.addAction(closeAction)
        closeAction.triggered.connect(functools.partial(self.removeTab, 0))
        menuButton = QtGui.QToolButton(self)
        menuButton.setStyleSheet('border: 0px; padding: 0px;')
        menuButton.setPopupMode(QtGui.QToolButton.InstantPopup)
        menuButton.setMenu(tabBarMenu)
        self.tabBar.setTabButton(0, QtGui.QTabBar.RightSide, menuButton)        
 
        widget = QtGui.QVBoxLayout(self.tabWidget.widget(0))
        dc = MplCanvas(self.tabWidget.widget(0), dpi=100, symbol=symbol)
        widget.addWidget(dc)
        widget.setContentsMargins(0,0,0,0)

        self.horizontalLayout_3.insertWidget(1, OrderBookWidget(self), alignment=QtCore.Qt.AlignTop)
        self.horizontalLayout_3.setContentsMargins(0,0,0,0)
        
        window_id = get_window_id()
        window_ids[0] = window_id
        
        self.dcs = {}
        self.dcs[window_id] = dc
        
        global qs
        global aqs
        qs[window_id] = Queue.Queue()
        aqs[window_id] = Queue.Queue()
        dqs[window_id] = Queue.Queue(maxsize=1)

        self.data_runner_thread = DataRunner(self, symbol, window_id, timeframe_entered)
        self.data_runner_thread.start()
        
        self.chart_runner_thread = ChartRunner(self, symbol, window_id, timeframe_entered)
        self.chart_runner_thread.data_ready.connect(self.queue_handle)
        self.chart_runner_thread.start()
        
        self.updateusdbalance_runner_thread = UpdateUsdBalanceRunner(self)
        self.updateusdbalance_runner_thread.data_ready.connect(self.queue_handle)
        self.updateusdbalance_runner_thread.start()
    
    def keyPressEvent(self, event):
     key = event.key()
     self.symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex())).split(" ")[0]
     if str(key) == "66": # B pressed
      try:
        percent = .25
        price = get_symbol_price(self.symbol)
        if self.symbol.endswith("USDT"):
          asset_balance = float(client.fetch_balance()["USDT"]["free"])
          amount = truncate((asset_balance / price) * percent, 2)
        elif self.symbol.endswith("USD"):
          asset_balance = float(client.fetch_balance()["USD"]["free"])
          amount = truncate((asset_balance / price) * percent, 2)                  
        else:
          asset_balance = float(client.fetch_balance()["BTC"]["free"])
          amount = truncate((asset_balance / price) * percent, 2)
        
        book = orderbook(client, self.symbol)
        asks_added = 0
        for ask in book["asks"]:
          asks_added = asks_added + ask[1]
          if asks_added > amount:
            price = ask[0]
            print str(amount) + " " + str(price)
            client.create_limit_buy_order(self.symbol, amount, price)
            return
      except:
        print get_full_stacktrace()
        return
      
     if str(key) == "83": # S pressed
      try:
        asset_balance = truncate(float(client.fetch_balance()[get_asset_from_symbol(self.symbol)]["free"]), 2)
        amount = truncate(asset_balance * .5, 2)
        book = orderbook(client, self.symbol)
        bids_added = 0
        for bid in book["bids"]:
          bids_added = bids_added + bid[1]
          if bids_added > amount:
            price = bid[0]
            print str(amount) + " " + str(price)
            client.create_limit_sell_order(self.symbol, amount, price)
            return       
      except:
        print get_full_stacktrace()
        return
    
    def queue_handle(self):
      global qs
      global aqs
      global qs_local
      global window_ids

      for i in xrange(0, len(window_ids)):
        winid = window_ids[i]
        if hasattr(self.dcs[winid], "renderer") and qs[winid].qsize() > 0:
          value = qs[winid].get()
          if value == FIGURE_ADD_SUBPLOT:
            aqs[winid].put(self.dcs[winid].fig.add_subplot(1,1,1,facecolor=black))
          elif value == FIGURE_TIGHT_LAYOUT:
            self.dcs[winid].fig.tight_layout()
            aqs[winid].put(0)
          elif value == FIGURE_CLEAR:
            self.dcs[winid].fig.clf()
            aqs[winid].put(0)
          elif value == CANVAS_GET_SIZE:
            annotation = qs[winid].get()
            aqs[winid].put(annotation.get_window_extent(self.dcs[winid].renderer))
          elif value == CANVAS_DRAW:         
            QtGui.QApplication.processEvents()
            if self.tabWidget.currentIndex() == i:
              self.dcs[winid].draw()
              self.dcs[winid].flush_events()
            aqs[winid].put(0)
          elif value == RETRIEVE_CURRENT_INDEX:
            aqs[winid].put(window_ids[self.tabWidget.currentIndex()])
          elif value == RETRIEVE_CHART_DATA:
            if winid in dqs:
              if dqs[winid].qsize() > 0:
                value = dqs[winid].get()
                if value == CHART_DATA_READY:
                  chart_result = dqs[winid].get()
                  aqs[winid].put(chart_result)
              else:
                aqs[winid].put(0)
          elif value == CHART_DESTROY:
            del qs[winid]
            del aqs[winid]
            self.dcs[winid].fig.clf()
            del self.dcs[winid]
            self.tabWidget.removeTab(i)
            
            import pprint
            pprint.pprint(window_ids)
            
            window_ids_copy = {}
            for j in window_ids.keys():
              if j == i:
                del window_ids[j]
                break

            counter = 0
            for j in window_ids.keys():
              window_ids_copy[counter] = window_ids[j]
              counter = counter + 1

            window_ids = copy.deepcopy(window_ids_copy)

            print "************************"
            pprint.pprint(window_ids)
            break

      if qs_local.qsize() > 0:
        value = qs_local.get()
        if value == SHOW_STATUSBAR_MESSAGE:
          message = qs_local.get()
          self.statusbar.showMessage(message)
    
    def tabOnChange(self, event):
      selected_symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex()))
      symbol = selected_symbol
      
    def removeTab(self, tab_index):
      global chartrunner_remove_tab
      global datarunner_remove_tab
      
      chartrunner_remove_tab = window_ids[tab_index]
      datarunner_remove_tab = window_ids[tab_index]
    
    def addTab(self, symbol, timeframe_entered):
      self.tab_widgets.append(QtGui.QWidget())
      tab_index = self.tabWidget.addTab(self.tab_widgets[-1], symbol + " " + timeframe_entered)
      self.tabWidget.setCurrentWidget(self.tab_widgets[-1])
      main.tabWidget.setTabIcon(tab_index, QtGui.QIcon("coin.ico"))
      widget = QtGui.QVBoxLayout(self.tabWidget.widget(tab_index))
      
      tabBarMenu = QtGui.QMenu()
      closeAction = QtGui.QAction("close", self)
      tabBarMenu.addAction(closeAction)
      closeAction.triggered.connect(functools.partial(self.removeTab, tab_index))      
      menuButton = QtGui.QToolButton(self)
      menuButton.setStyleSheet('border: 0px; padding: 0px;')
      menuButton.setPopupMode(QtGui.QToolButton.InstantPopup)
      menuButton.setMenu(tabBarMenu)      
      self.tabBar.setTabButton(tab_index, QtGui.QTabBar.RightSide, menuButton)
      
      dc = MplCanvas(self.tabWidget.widget(tab_index), dpi=100, symbol=symbol)
      widget.addWidget(dc)
      
      global qs
      global aqs
      global dqs
      
      window_id = get_window_id()
      window_ids[tab_index] = window_id

      qs[window_id] = Queue.Queue()
      aqs[window_id] = Queue.Queue()
      dqs[window_id] = Queue.Queue(maxsize=1)
      self.dcs[window_id] = dc
      
      self.data_runner_thread = DataRunner(self, symbol, window_id, timeframe_entered)
      self.data_runner_thread.start()      
      
      self.chart_runner_thread = ChartRunner(self, symbol, window_id, timeframe_entered)
      self.chart_runner_thread.data_ready.connect(self.queue_handle)
      self.chart_runner_thread.start()
    
    def add_coin_clicked(self, event):
      global dialog
      dialog = Dialog()
      dialog.show()

    def trade_coin_clicked(self, event):
      self.trade_dialog = TradeDialog(self)
      self.trade_dialog.show()
      
class TradeDialog(QtGui.QDialog):
  def __init__(self, parent):
    QtGui.QDialog.__init__(self)
    uic.loadUi('trade.ui', self)
    self.setFixedSize(713, 385)
    self.symbol = str(parent.tabWidget.tabText(parent.tabWidget.currentIndex())).split(" ")[0]
    symbol = self.symbol
    self.trade_coin_price = get_symbol_price(symbol)
    trade_coin_price_str = "%.06f" % self.trade_coin_price
    self.setWindowTitle("Trade " + symbol)
    asset = get_asset_from_symbol(symbol)
    quote = get_quote_from_symbol(symbol)
    self.quote_free_balance = client.fetch_balance()[quote]["free"]
    self.asset_free_balance = client.fetch_balance()[asset]["free"]
    self.labelFreebalance.setText("%.06f" % self.quote_free_balance + " " + quote)
    self.labelFreebalance2.setText("%.06f" % self.asset_free_balance + " " + asset)
    
    self.labelFreebalance_4.setText("%.06f" % self.quote_free_balance + " " + quote)
    self.labelFreebalance2_3.setText("%.06f" % self.asset_free_balance + " " + asset)    
    
    self.editAmount.textChanged.connect(self.editamount_textChanged)
    self.editAmount2.textChanged.connect(self.editamount2_textChanged)
    self.editAmount_4.textChanged.connect(self.editamount_4_textChanged)
    self.editAmount2_3.textChanged.connect(self.editamount2_3_textChanged)
    
    self.editPrice.textChanged.connect(self.editamount_textChanged)
    self.editPrice2.textChanged.connect(self.editamount2_textChanged)
    self.editPrice.setText(trade_coin_price_str)
    self.editPrice2.setText(trade_coin_price_str)
    
    self.label_29.setText(asset)
    self.label_30.setText(quote)
    self.label_41.setText(asset)
    self.label_47.setText(quote)
    
    self.label_3.setText(asset)
    self.label_5.setText(quote)
    self.label_7.setText(quote)
    self.label_22.setText(asset)
    self.label_24.setText(quote)
    self.label_23.setText(quote)
    
    self.labelFreebalance.mousePressEvent = self.buyLimitLabelClicked
    self.labelFreebalance2.mousePressEvent = self.sellLimitLabelClicked
    self.labelFreebalance_4.mousePressEvent = self.buyMarketLabelClicked
    self.labelFreebalance2_3.mousePressEvent = self.sellMarketLabelClicked
    
    self.toolButton.clicked.connect(self.buylimit_clicked)
    self.toolButton_3.clicked.connect(self.selllimit_clicked)
    
    self.toolButton_4.clicked.connect(self.buymarket_clicked)
    self.toolButton_6.clicked.connect(self.sellmarket_clicked)    

  def buylimit_clicked(self, event):
    amount = truncate(float(self.editAmount.text()), 2)
    price = float(self.editPrice.text())
    
    symbol_price = get_symbol_price(self.symbol)
    if price > symbol_price:
      return
    
    try:
      client.create_limit_buy_order(self.symbol, amount, price)
    except:
      print get_full_stacktrace()
      return
    
    self.close()
    
  def selllimit_clicked(self, event):
    amount = truncate(float(self.editAmount2.text()), 2)
    price = float(self.editPrice2.text())

    symbol_price = get_symbol_price(self.symbol)
    if price < symbol_price:
      return    
    
    try:
      client.create_limit_sell_order(self.symbol, amount, price)
    except:
      print get_full_stacktrace()
      return

    self.close()
    
  def buymarket_clicked(self, event):
    amount = truncate(float(self.editAmount_4.text()), 2)

    try:
      client.create_market_buy_order(self.symbol, amount)
    except:
      print get_full_stacktrace()
      return
    
    self.close()
    
  def sellmarket_clicked(self, event):
    amount = truncate(float(self.editAmount2_3.text()), 2)
    
    try:
      client.create_market_sell_order(self.symbol, amount)
    except:
      print get_full_stacktrace()
      return

    self.close()    

  def buyLimitLabelClicked(self, event):
    if self.editPrice.text() == "":
      return
    price = float(self.editPrice.text())
    self.editAmount.setText("%.02f" % (self.quote_free_balance / self.trade_coin_price))
    total = (self.quote_free_balance / self.trade_coin_price) * price
    if truncate(self.quote_free_balance / self.trade_coin_price, 2) == 0:
      self.editTotal.setText("")
    else:
      self.editTotal.setText("%.04f" % (total))
  
  def sellLimitLabelClicked(self, event):
    if self.editPrice.text() == "":
      return    
    price = float(self.editPrice2.text())
    asset_free_balance = truncate(self.asset_free_balance, 2)
    self.editAmount2.setText("%.02f" % asset_free_balance)
    self.editTotal2.setText("%.04f" % (asset_free_balance * price))
  
  def editamount_textChanged(self, event):
    try:
      if self.editPrice.text() == "":
        return
      price = float(self.editPrice.text())
      amount = truncate(float(self.editAmount.text()), 2)
      self.editTotal.setText("%.04f" % (amount * price))
    except:
      pass
    
  def editamount2_textChanged(self, event):
    try:
      price = float(self.editPrice2.text())
      amount = truncate(float(self.editAmount2.text()), 2)
      self.editTotal2.setText("%.04f" % (amount * price))
    except:
      pass
  
  def buyMarketLabelClicked(self, event):
    price = get_symbol_price(self.symbol)
    self.editAmount_4.setText("%.02f" % (self.quote_free_balance / self.trade_coin_price))
    total = (self.quote_free_balance / self.trade_coin_price) * price
    if truncate(self.quote_free_balance / self.trade_coin_price, 2) == 0:
      self.editTotal_3.setText("")
    else:
      self.editTotal_3.setText("%.04f" % (total))
  
  def sellMarketLabelClicked(self, event):
    price = get_symbol_price(self.symbol)
    asset_free_balance = truncate(self.asset_free_balance, 2)
    self.editAmount2_3.setText("%.02f" % asset_free_balance)
    self.editTotal2_3.setText("%.04f" % (asset_free_balance * price))
    
  def editamount_4_textChanged(self, event):
    price = self.trade_coin_price
    amount = truncate(float(self.editAmount_4.text()), 2)
    self.editTotal_3.setText("%.04f" % (amount * price))

  def editamount2_3_textChanged(self, event):
    price = self.trade_coin_price
    amount = truncate(float(self.editAmount2_3.text()), 2)
    self.editTotal2_3.setText("%.04f" % (amount * price))

class Dialog(QtGui.QDialog):
    global config
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uic.loadUi('windowqt.ui', self)
        self.setFixedSize(555, 575)
        self.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
        self.comboBox.addItem("1h")
        for key, value in client.timeframes.iteritems():
          if key == "1h" or key == "1w" or key == "1M":
            continue
          self.comboBox.addItem(key)
        
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
  
        global main
        global main_shown

        if not main_shown:
          main = Window(symbol, timeframe_entered)
          main.tabWidget.setTabText(0, symbol + " " + timeframe_entered)
          main.tabWidget.setTabIcon(0, QtGui.QIcon("coin.ico"))
          main.show()
          main_shown = True
        else:
          main.addTab(symbol, timeframe_entered)
        self.close()

def orderbook(exchange, symbol):
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
  global auto_last_trade
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

  bids_summed2 = copy.deepcopy(bids_summed)
  asks_summed2 = copy.deepcopy(asks_summed)
  
  unibox = unichr(int('2022', 16))
  
  for bid in bids_summed:
      try:
        ask = asks_summed.pop()
        if not symbol.endswith("BTC"):
          asks = str(ask[1][0]) + " "  * (9 - len(str(ask[1][0]))) + str(ask[1][2]) + " " + unibox * ask[0]
        else:
          asks = "%.6f" % float(ask[1][0]) + " " + str(ask[1][1]) + " "  * (10 - len(str(ask[1][1]))) + str(ask[1][2]) + " " + unibox * ask[0]
      except:
        asks = ""
      if not symbol.endswith("BTC"):            
        strs.append(" " * (5-bid[0]) + unibox * bid[0] + " " + str(bid[1][0]) + " "  * (9 - len(str(bid[1][0]))) + str(bid[1][2]) + "\t" + asks)
      else:
        strs.append(" " * (5-bid[0]) + unibox * bid[0] + " " + "%.6f" % float(bid[1][0]) + " " + str(bid[1][1]) + " "  * (10 - len(str(bid[1][1]))) + str(bid[1][2]) + "\t" + asks)

  return strs

class Orderbook(QtCore.QThread):
    data_ready = QtCore.pyqtSignal()
  
    def __init__(self, parent):
        super(Orderbook, self).__init__(parent)

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
          continue
        break
    
    def collect_ex(self):
      while True:
        if time.time() - self.lastupdate > 10 or self.lastupdate == 0:
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
            if is_usdt:
              btcusd_symbol = "BTC/USDT"
            else:
              btcusd_symbol = "BTC/USD" 
            ob_accum = display_market_depth(ob_bids, ob_asks, btcusd_symbol, 7)
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
            self.data_ready.emit()
            
            self.lastupdate = time.time()
          except:
            stacktrace = get_full_stacktrace()
            print stacktrace
          
class OrderBookWidget(QtGui.QLabel):
    def __init__(self,parent=None):
        super(OrderBookWidget,self).__init__(parent)
        self.init_orderbook_widget()
        self.parent = parent
 
    def init_orderbook_widget(self):
        self.setMinimumWidth(337)
        newfont = QtGui.QFont("Courier New", 9, QtGui.QFont.Bold) 
        self.setFont(newfont)
        self.setText("btcusd (combined)\nloading...")
        self.setStyleSheet("QLabel { background-color : #131D27; color : #C6C7C8; }")
        self.orderbook = Orderbook(self)
        self.orderbook.data_ready.connect(self.orderbook_widget_update)

    def orderbook_widget_update(self):
        if self.orderbook.ex_queue.empty() == False:
          bookstr = self.orderbook.ex_queue.get()
          self.setText(bookstr)

if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  with open("style.qss","r") as fh:
    app.setStyleSheet(fh.read())
  dialog = Dialog()
  dialog.show()
  os._exit(app.exec_())
  