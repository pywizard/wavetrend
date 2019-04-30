import os
#macos: run openblas single threaded
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
import warnings
warnings.filterwarnings("ignore")
import matplotlib
import matplotlib.style
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as matplotlib_ticker
from matplotlib.dates import date2num
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import ctypes
from matplotlib.transforms import Bbox
from matplotlib import cbook
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_qt5 import (
    QtCore, QtGui, QtWidgets, _BackendQT5, FigureCanvasQT, FigureManagerQT,
    NavigationToolbar2QT, backend_version)
from matplotlib.backends.qt_compat import QT_API
import sys
import time
import datetime
from PyQt5 import QtGui, QtWidgets, QtCore, uic
import traceback
import copy
import threading
import math
import queue as Queue
import ccxt
from indicators import *
from colors import *
import decimal
import random
import functools
import exchanges
import weakref
import numpy
import platform
import prettydate
import collections

#FIX: squash memory leak for redraws
class MyTransformNode(object):
    def __init__(self, shorthand_name=None):
        self._parents = {}
        self._invalid = 1
        self._shorthand_name = shorthand_name or ''

    def set_children(self, *children):
        """
        Set the children of the transform, to let the invalidation
        system know which transforms can invalidate this transform.
        Should be called from the constructor of any transforms that
        depend on other transforms.
        """
        # Parents are stored as weak references, so that if the
        # parents are destroyed, references from the children won't
        # keep them alive.
        for child in children:
            # Use weak references so this dictionary won't keep obsolete nodes
            # alive; the callback deletes the dictionary entry. This is a
            # performance improvement over using WeakValueDictionary.
            ref = weakref.ref(self, lambda ref, sid=id(self),
                                        target=child._parents: target.pop(sid))
            child._parents[id(self)] = ref

    def __setstate__(self, data_dict):
        self.__dict__ = data_dict
        # turn the normal dictionary back into a dictionary with weak values
        # The extra lambda is to provide a callback to remove dead
        # weakrefs from the dictionary when garbage collection is done.
        self._parents = {k: weakref.ref(v, lambda ref, sid=k,
                                                  target=self._parents:
                                                        target.pop(sid))
                         for k, v in self._parents.items() if v is not None}

matplotlib.transforms.TransformNode.set_children = MyTransformNode.set_children
matplotlib.transforms.TransformNode.__setstate__ = MyTransformNode.__setstate__

class FigureCanvas(FigureCanvasAgg, FigureCanvasQT):

    def __init__(self, figure):
        # Must pass 'figure' as kwarg to Qt base class.
        super().__init__(figure=figure)

    def paintEvent(self, event):
        """Copy the image from the Agg canvas to the qt.drawable.
        In Qt, all drawing should be done inside of here when a widget is
        shown onscreen.
        """
        if self._update_dpi():
            # The dpi update triggered its own paintEvent.
            return
        self._draw_idle()  # Only does something if a draw is pending.

        # If the canvas does not have a renderer, then give up and wait for
        # FigureCanvasAgg.draw(self) to be called.
        if not hasattr(self, 'renderer'):
            return

        painter = QtGui.QPainter(self)

        rect = event.rect()
        left = rect.left()
        top = rect.top()
        width = rect.width()
        height = rect.height()
        # See documentation of QRect: bottom() and right() are off by 1, so use
        # left() + width() and top() + height().
        bbox = Bbox(
            [[left, self.renderer.height - (top + height * self._dpi_ratio)],
             [left + width * self._dpi_ratio, self.renderer.height - top]])
        reg = self.copy_from_bbox(bbox)
        buf = memoryview(reg)

        # clear the widget canvas
        painter.eraseRect(rect)

        # pyqt5 supports Format_RGBA8888, qt4 doesn't, since we are using
        # pyqt5 we don't convert the buf to argb32. this is much faster!
        qimage = QtGui.QImage(buf, buf.shape[1], buf.shape[0],
                              QtGui.QImage.Format_RGBA8888)
        if hasattr(qimage, 'setDevicePixelRatio'):
            # Not available on Qt4 or some older Qt5.
            qimage.setDevicePixelRatio(self._dpi_ratio)
        origin = QtCore.QPoint(left, top)
        painter.drawImage(origin / self._dpi_ratio, qimage)

        ctypes.c_long.from_address(id(buf)).value = 1
        self._draw_rect_callback(painter)

        painter.end()

matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg = FigureCanvas

config = {}
exec(open("config.txt").read(), config)

exchanges_ = config["exchanges"].copy()

active_count = 0
exchange = ""
for exchange_name in exchanges_:
    if exchanges_[exchange_name]["active"] == True:
        exchange = exchange_name
        api_key = config["exchanges"][exchange_name]["api_key"]
        api_secret = config["exchanges"][exchange_name]["api_secret"]
        active_count = active_count + 1

if active_count > 1 or active_count == 0:
    print("Please configure a valid Exchange.")
    print("One exchange must be configured active.")
    sys.exit(1)

if exchange == "BITFINEX":
  client = ccxt.bitfinex2({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True
  })
elif exchange == "BINANCE":
   client = ccxt.binance({
   'apiKey': api_key,
   'secret': api_secret,
   'enableRateLimit': True,
   'options': {'adjustForTimeDifference': True}
  })
else:
  print("Please configure a valid Exchange.")
  sys.exit(1)

markets = client.fetch_markets()
ticker = client.fetch_tickers()
is_usdt = False
if "BTC/USDT" in ticker:
  is_usdt = True

matplotlib.rcParams['font.family'] = 'monospace'

is_darwin = platform.system() == "Darwin"

class abstract():
  pass

def _candlestick(ax, quotes, first, last_line1, last_line2, last_rect, candle_width, \
                 scanner_results, highest_price, width=0.2, colorup='white', colordown='black', alpha=1.0):

    width = candle_width
    line_width = 0.9
    OFFSET = width / 2.0

    lines = []
    patches = []
    annotations = []

    colorup = "#134F5C"
    colordown = "#A61C00"
    colorup2 = "#53B987"
    colordown2 = "#EB4D5C"

    if first == False:
      quotes = [quotes[-1]]

    i = 0
    for q in quotes:
        annotate = False
        for scanner_result in scanner_results:
            if scanner_result[0] == i:
                annotate = True
                break
        i = i + 1

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
                linewidth=line_width,
                antialiased=True
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
                linewidth=line_width,
                antialiased=True,
            )

        if first == True:
          lines.append(vline1)
          lines.append(vline2)
          patches.append(rect)
          ax.add_line(vline1)
          ax.add_line(vline2)
          ax.add_patch(rect)

          if annotate == True:
              rect.set_facecolor(orange)
              rect.set_edgecolor(orange)
              vline1.set_color(orange)
              vline2.set_color(orange)

              rx, ry = rect.get_xy()
              cx = rx + rect.get_width()
              cy = highest_price
              color = green
              if scanner_result[1] > 0:
                  color = green
              elif scanner_result[1] < 0:
                  color = red

              text = ax.annotate(scanner_result[2], (cx, cy), color=color, weight='bold',
                          fontsize=6, ha='center', va='center')

              returns = 0
              for annotation_x in annotations:
                  if rx < annotation_x + rect.get_width()*15:
                     returns = returns + 1
              text.set_text(" " + "\n\n" * returns + scanner_result[2])

              annotations.append(rx)

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

window_ids = {}
def get_window_id():
  return "win-" + ''.join(random.choice('0123456789abcdef') for i in range(10))

window_configs = {}

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
    for market in markets:
        if market["symbol"] == symbol:
            return market["base"]

def get_quote_from_symbol(symbol):
    for market in markets:
        if market["symbol"] == symbol:
            return market["quote"]

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

SHOW_STATUSBAR_MESSAGE = 0
CANDLE_TYPE_CANDLESTICK = 0
CANDLE_TYPE_HEIKIN_ASHI = 1
TRADE_TYPE_TRENDING = 0
TRADE_TYPE_OSC = 1

tab_current_index = None
destroyed_window_ids = {}

DataRunnerTabs = {}

days_table = {"1m": 0.17, "5m": .9, "15m": 2.5, "30m": 5 , "1h": 10, "2h": 20, "3h": 30, "4h": 40, "6h": 60, "12h": 120, "1d": 240, "1D": 240}
elapsed_table = {"1m": 60, "5m": 60*5, "15m": 60*15, "30m": 60*30, "1h": 60*60, "2h": 60*60*2, "3h": 60*60*3, "4h": 60*60*4, "6h": 60*60*6, "12h": 60*60*12, "1d": 60*60*24, "1D": 60*60*24}

from operator import itemgetter

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, dpi=100, symbol=None):
        self.fig = Figure(facecolor=black, edgecolor=white, dpi=dpi,
                          frameon=False, tight_layout=False, constrained_layout=False)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

main_shown = False

class DataRunner:
  def __init__(self, parent, symbol, window_id, tab_index, timeframe_entered):
    global markets
    self.symbol = symbol
    self.window_id = window_id
    self.tab_index = tab_index
    self.parent = parent
    self.timeframe_entered = timeframe_entered
    self.bfx_chanid = -1
    self.bfx_chanid_ticker = -1

    if exchange == "BITFINEX":
        self.exchange_obj = exchanges.Bitfinex(markets, api_key, api_secret)
        self.exchange_obj.start_ticker_websocket(self.symbol, self.process_message_ticker)
        self.websocket_ticker_alive_time = time.time()
        if timeframe_entered == "1d":
            self.timeframe_entered = "1D"
        self.last_result = []
    elif exchange == "BINANCE":
        self.exchange_obj = exchanges.Binance(markets, api_key, api_secret)
    self.exchange_obj.start_candlestick_websocket(self.symbol, self.timeframe_entered, self.process_message)

    self.kill_websocket_watch_thread = False
    self.websocket_alive_time = time.time()
    self.websocket_watch_thread = threading.Thread(target=self.websocket_watch)
    self.websocket_watch_thread.daemon = True
    self.websocket_watch_thread.start()

  def restart_websocket(self):
      self.bfx_chanid = -1
      self.exchange_obj.stop_candlestick_websocket()
      self.exchange_obj.start_candlestick_websocket(self.symbol, self.timeframe_entered, self.process_message)
      self.websocket_alive_time = time.time()

  def restart_ticker_websocket(self):
      self.bfx_chanid_ticker = -1
      self.exchange_obj.stop_ticker_websocket()
      self.exchange_obj.start_ticker_websocket(self.symbol, self.process_message_ticker)
      self.websocket_ticker_alive_time = time.time()

  def websocket_watch(self):
    while True:
        if self.kill_websocket_watch_thread == True:
            break
        if time.time() - self.websocket_alive_time > 60:
           self.restart_websocket()
        if exchange == "BITFINEX":
            if time.time() - self.websocket_ticker_alive_time > 60:
               self.restart_ticker_websocket()
        time.sleep(0.1)

  def process_message_ticker(self, msg):
      if exchange != "BITFINEX":
          return

      if isinstance(msg, dict) and "chanId" in msg:
          self.bfx_chanid_ticker = msg["chanId"]
          return
      elif self.bfx_chanid_ticker != -1  and isinstance(msg, list) and msg[0] == self.bfx_chanid_ticker:
          self.websocket_ticker_alive_time = time.time()
          if not isinstance(msg[1], list):
              return

          if len(self.last_result) != 0:
            result = copy.copy(self.last_result)
            last_price = float(msg[1][6])
            if last_price > result[2]: #high
                result[2] = last_price
            if last_price < result[3]: #low
                result[3] = last_price
            result[4] = last_price # close

            dqs[self.window_id].append(result)

  def process_message(self, msg):
    if exchange == "BITFINEX":
        if isinstance(msg, dict) and "chanId" in msg:
            self.bfx_chanid = msg["chanId"]
            return
        elif  self.bfx_chanid != -1  and isinstance(msg, list) and msg[0] == self.bfx_chanid:
            self.websocket_alive_time = time.time()
            candle_time = time.time() // elapsed_table[self.timeframe_entered] * elapsed_table[self.timeframe_entered]
            candle = None

            if isinstance(msg[1], list) and len(msg[1]) > 0 and isinstance(msg[1][0], list) and len(msg[1][0]) > 0:
                candle = msg[1][0]
            elif isinstance(msg[1], list) and len(msg[1]) > 0:
                candle = msg[1]
            else:
                return

            if int((float(candle[0]) / 1000)) != candle_time:
                return

            dt = datetime.datetime.fromtimestamp(float(candle[0]) / 1000)

            open_ = float(candle[1])
            high = float(candle[3])
            low = float(candle[4])
            close = float(candle[2])
            volume = float(candle[5])

            result = [dt, open_, high, low, close, volume, 1]
            self.last_result = copy.copy(result)

            dqs[self.window_id].append(result)

    elif exchange == "BINANCE":
        if "e" in msg and msg["e"] == "error":
            self.restart_websocket()
            return

        if "e" in msg and msg["e"] == "kline":
            self.websocket_alive_time = time.time()
            open_ = float(msg["k"]["o"])
            high = float(msg["k"]["h"])
            low = float(msg["k"]["l"])
            close = float(msg["k"]["c"])
            volume = float(msg["k"]["v"])
            dt = datetime.datetime.fromtimestamp(msg["k"]["t"] / 1000)

            result = [dt, open_, high, low, close, volume, 1]

            dqs[self.window_id].append(result)

class ChartRunner(QtCore.QThread):
  FIGURE_ADD_SUBPLOT = QtCore.pyqtSignal(str, int, object)
  FIGURE_CLEAR = QtCore.pyqtSignal(str)
  FIGURE_ADD_AXES = QtCore.pyqtSignal(str, list, object)
  CANVAS_GET_SIZE = QtCore.pyqtSignal(str, object)
  FIGURE_TIGHT_LAYOUT = QtCore.pyqtSignal(str)
  CANVAS_DRAW = QtCore.pyqtSignal(str)
  CHART_DESTROY = QtCore.pyqtSignal(str)

  def __init__(self, parent, symbol, tab_index, timeframe_entered):
    super(ChartRunner, self).__init__(parent)
    self.parent = parent
    self.symbol = symbol
    self.tab_index = tab_index
    self.timeframe_entered = timeframe_entered

  def candlescanner(self, open_, high, low, close):
      patterns = [[talib.CDL2CROWS, "Two Crows", "Bearish market reversal signal STRONG"],
                  [talib.CDL3BLACKCROWS, "Three Black Crows", "78% Reversal of the current uptrend STRONG"],
                  [talib.CDL3INSIDE, "Three Inside", "Reversal signal Moderate"],
                  [talib.CDL3LINESTRIKE, "Three Line Strike", "%84 Reversal signal STRONG"],
                  [talib.CDL3OUTSIDE, "Three Outside", "Reversal signal Moderate"],
                  [talib.CDL3STARSINSOUTH, "Three Stars in South", "Bullish Reversal STRONG"],
                  [talib.CDL3WHITESOLDIERS, "Three White Soldiers", "Bullish Reversal STRONG"],
                  [talib.CDLABANDONEDBABY, "Abandonded Baby", "70% Reversal of the current trend STRONG"],
                  [talib.CDLADVANCEBLOCK, "Advance Block", "Advance Block STRONG"],
                  [talib.CDLBREAKAWAY, "Breakaway", "63% Reversal Signal STRONG"],
                  [talib.CDLDARKCLOUDCOVER, "Dark Cloud Cover", "Bearish Reversal STRONG"],
                  [talib.CDLDRAGONFLYDOJI, "Dragonfly Doji", "Reversal Pattern Moderate"],
                  [talib.CDLENGULFING, "Engulfing", "Reversal Pattern Moderate"],
                  [talib.CDLEVENINGDOJISTAR, "Evening Doji", "Bearish Reversal STRONG"],
                  [talib.CDLEVENINGSTAR, "Evening Star", "72% Bearish Reversal STRONG"],
                  [talib.CDLHAMMER, "Hammer", "Bullish Reversal Moderate"],
                  [talib.CDLHANGINGMAN, "Hanging Man", "Bearish Reversal Moderate"],
                  [talib.CDLIDENTICAL3CROWS, "Identical Three Crows", "Bearish"],
                  [talib.CDLINNECK, "In Neck", "Bearish Continuation"],
                  [talib.CDLLADDERBOTTOM, "Ladder Bottom", "Ladder Bottom"],
                  [talib.CDLLONGLINE, "Long Line", ""],
                  [talib.CDLMORNINGDOJISTAR, "Morning Doji Star", "Bullish Reversal STRONG"],
                  [talib.CDLMORNINGSTAR, "Morning Star", "Bullish Reversal Moderate STRONG"],
                  [talib.CDLONNECK, "On Neck", "Bearish Continuation"],
                  [talib.CDLPIERCING, "Piercing Line", "Bullish Reversal Moderate"],
                  [talib.CDLRISEFALL3METHODS, "Rise Fall 3 Methods", "Bullish Continuation"],
                  [talib.CDLSHORTLINE, "Short Line", ""],
                  [talib.CDLTHRUSTING, "Thrusting", "Bearish Continuation"],
                  [talib.CDLTRISTAR, "Tristar", "Reversal Moderate STRING"],
                  [talib.CDLTASUKIGAP, "Tasuki Gap", "Market Continuation"],
                  [talib.CDLCLOSINGMARUBOZU, 'Closing Marubozu', 'Closing Marubozu'],
                  [talib.CDLCONCEALBABYSWALL, 'Concealing Baby Swallow STRONG'],
                  [talib.CDLCOUNTERATTACK, 'Counterattack'],
                  [talib.CDLDOJISTAR, 'Doji Star'],
                  [talib.CDLGAPSIDESIDEWHITE, 'Up/Down-gap side-by-side white lines'],
                  [talib.CDLGRAVESTONEDOJI, 'Gravestone Doji', 'Gravestone Doji'],
                  [talib.CDLHANGINGMAN, 'Hanging Man'],
                  [talib.CDLHARAMI, 'Harami Pattern'],
                  [talib.CDLHARAMICROSS, 'Harami Cross Pattern'],
                  [talib.CDLHIKKAKE, 'Hikkake Pattern'],
                  [talib.CDLHIKKAKEMOD, 'Modified Hikkake Pattern'],
                  [talib.CDLHOMINGPIGEON, 'Homing Pigeon'],
                  [talib.CDLINVERTEDHAMMER, 'Inverted Hammer', 'Inverted Hammer'],
                  [talib.CDLKICKING, 'Kicking'],
                  [talib.CDLKICKINGBYLENGTH, 'Kicking - bull/bear determined by the longer marubozu'],
                  [talib.CDLMARUBOZU, 'Marubozu', 'Marubozu DTRONG'],
                  [talib.CDLMATCHINGLOW, 'Matching Low', 'Matching Low'],
                  [talib.CDLMATHOLD, 'Mat Hold', 'Mat Hold STRONG'],
                  [talib.CDLSEPARATINGLINES, 'Separating Lines'],
                  [talib.CDLSHOOTINGSTAR, 'Shooting Star', 'Shooting Star'],
                  [talib.CDLSTALLEDPATTERN, 'Stalled Pattern'],
                  [talib.CDLSTICKSANDWICH, 'Stick Sandwich', 'Stick Sandwich'],
                  [talib.CDLTAKURI, 'Takuri (Dragonfly Doji with very long lower shadow)'],
                  [talib.CDLUNIQUE3RIVER, 'Unique 3 River'],
                  [talib.CDLUPSIDEGAP2CROWS, 'Upside Gap Two Crows'],
                  [talib.CDLXSIDEGAP3METHODS, 'Upside/Downside Gap Three Methods']]

      results = []
      ndarray_open = numpy.array(open_)
      ndarray_high = numpy.array(high)
      ndarray_low = numpy.array(low)
      ndarray_close = numpy.array(close)
      for pattern in patterns:
          talib_function = pattern[0]
          pattern_name = pattern[1]
          if len(pattern) == 3:
              pattern_description = pattern[2]
          else:
              pattern_description = pattern_name

          if pattern_description.find("STRONG") < 0:
              continue

          result = talib_function(ndarray_open, ndarray_high, ndarray_low, ndarray_close)

          for i in range(0, len(close)):
              if result[i] != 0:
                  # result[i] contains positive value, bullish pattern
                  # or negative value, bearish pattern
                  results.append([i, result[i], pattern_name, pattern_description])
      return results

  def run(self):
    global qs
    global aqs
    global tab_current_index
    global destroyed_window_ids
    global window_configs

    days_entered = days_table[self.timeframe_entered]
    timeframe_entered = self.timeframe_entered
    symbol = self.symbol
    tab_index = self.tab_index

    to_sell = 0

    init = True
    prev_trade_time = 0
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
    current_candle_type = window_configs[self.tab_index].candle_type
    current_trade_type = window_configs[self.tab_index].trade_type
    date = None
    date2 = None
    force_redraw_chart = False # True means switched from tab

    while True:
        try:
          while True:
              if init == True:
                  update_time = time.time()
                  break
              if time.time() - update_time < 1:
                  time.sleep(0.1)
              else:
                  update_time = time.time()
                  break

          candle_type = window_configs[self.tab_index].candle_type
          trade_type = window_configs[self.tab_index].trade_type

          if init == False and first == True and exchange == "BITFINEX" and time.time() > time_close:
              date, open_, high, low, close, vol, limit = self.getData(timeframe_entered, days_entered, symbol, False)
              time_close = (datetime.datetime.timestamp(date[-1]) // elapsed_table[self.timeframe_entered] * \
                            elapsed_table[self.timeframe_entered]) + elapsed_table[self.timeframe_entered]
              date2 = None
              if time.time() > time_close:
                  time.sleep(1)
          elif first == True:
                date, open_, high, low, close, vol, limit = self.getData(timeframe_entered, days_entered,
                                                                         symbol, False)
                time_close = (datetime.datetime.timestamp(date[-1]) // elapsed_table[self.timeframe_entered] * \
                              elapsed_table[self.timeframe_entered]) + elapsed_table[self.timeframe_entered]
                date2 = None
          else:
            try:
                chart_result = dqs[self.tab_index].pop()
                dqs[self.tab_index].clear()
                [date2, open2_, high2, low2, close2, vol2, limit2] = chart_result
            except IndexError:
                pass

          if first == True:
            self.FIGURE_ADD_SUBPLOT.emit(self.tab_index, 111, None)
            ax = aqs[self.tab_index].get()

            prices[:] = []
            for i in range(0, len(date)):
                prices.append((date2num(date[i]), open_[i], high[i], low[i], close[i], vol[i], date[i]))

            ax.xaxis.set_tick_params(labelsize=9)
            ax.yaxis.set_tick_params(labelsize=9)
          else:
            if date2 != None:
                prices[-1] = [date2num(date2), open2_, high2, low2, close2, vol2, date2]

          hotkeys_pressed = current_candle_type != candle_type or current_trade_type != trade_type
          if hotkeys_pressed == True:
              force_redraw_chart = True

          if first == False and (force_redraw_chart == True or time.time() > time_close):
            self.FIGURE_CLEAR.emit(self.tab_index)
            aqs[self.tab_index].get()
            first = True
            last_line1 = None
            last_line2 = None
            last_rect = None
            indicators[:] = []
            indicator_axes[:] = []
            current_candle_type = candle_type
            current_trade_type = trade_type
            force_redraw_chart = False
            continue

          if first == True:
            indicators.append(indicator_BBANDS())
            if current_trade_type == TRADE_TYPE_TRENDING:
              indicators.append(indicator_MACD())
            elif current_trade_type == TRADE_TYPE_OSC:
              indicators.append(indicator_STOCH())
            indicators.append(indicator_DMI())
            indicators.append(indicator_RSI())
            indicators.append(indicator_VOLUME())

          start_x = 0
          indicator_axes_count = 0

          pdate = [x[0] for x in prices]
          popen = [x[1] for x in prices]
          phigh = [x[2] for x in prices]
          plow = [x[3] for x in prices]
          pclose = [x[4] for x in prices]
          pvol = [x[5] for x in prices]

          for indicator in indicators:
            if first == True:
              indicator.generate_values(popen, phigh, plow, pclose, pvol)
              if indicator.overlay_chart:
                indicator.plot_once(ax, pdate)
              else:
                indicator_axes_count += 1
                rows = 0
                if indicator_axes_count == 1:
                    rows = 211
                elif indicator_axes_count == 2:
                    rows = 311
                elif indicator_axes_count == 3:
                    rows = 411
                elif indicator_axes_count == 4:
                    rows = 511
                if indicator.name == "VOLUME":
                    self.FIGURE_ADD_AXES.emit(self.tab_index, [0,0,0.4,0.4], ax)
                    new_ax = aqs[self.tab_index].get()
                    new_ax.patch.set_visible(False)
                    new_ax.spines['top'].set_visible(False)
                    new_ax.grid(False)
                    ax.spines['bottom'].set_visible(False)
                else:
                    self.FIGURE_ADD_SUBPLOT.emit(self.tab_index, rows, ax)
                    new_ax = aqs[self.tab_index].get()
                    new_ax.grid(alpha=.25)
                    new_ax.grid(True)
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
                indicator_axes.append(new_ax)
                indicator_update_time = time.time()
                indicator.plot_once(new_ax, pdate)
            else:
              indicator.generate_values(popen, phigh, plow, pclose, pvol)
              if time.time() - indicator_update_time > 10 or current_candle_type != candle_type or current_trade_type != trade_type:
                indicator.update()              
            
            xaxis_start = indicator.xaxis_get_start()
            if xaxis_start != 0 and xaxis_start > start_x:
              start_x = xaxis_start
                          
          if time.time() - indicator_update_time > 10 or current_candle_type != candle_type or current_trade_type != trade_type:
            indicator_update_time = time.time()     

          if current_candle_type == CANDLE_TYPE_HEIKIN_ASHI:
            ### Heikin Ashi
            if first == True:  
              date_list    = range(0, len(popen))
              open_list    = copy.deepcopy(popen)
              close_list   = copy.deepcopy(pclose)
              high_list    = copy.deepcopy(phigh)
              low_list     = copy.deepcopy(plow)
              volume_list  = copy.deepcopy(pvol)
              elements        = len(popen)

              for i in range(1, elements):
                  close_list[i] = (open_list[i] + close_list[i] + high_list[i] + low_list[i])/4
                  open_list[i]  = (open_list[i-1] + close_list[i-1])/2
                  high_list[i]  = max(high_list[i], open_list[i], close_list[i])
                  low_list[i]   = min(low_list[i], open_list[i], close_list[i])
              
              prices2 = []
              prices2[:] = []
              for i in range(0, len(date)):
                  prices2.append((date2num(date[i]), open_list[i], high_list[i], low_list[i], close_list[i], volume_list[i], date[i]))
            else:
              open_list[-1]    = popen[-1]
              close_list[-1]   = pclose[-1]
              high_list[-1]    = phigh[-1]
              low_list[-1]     = plow[-1]
              volume_list[-1]  = pvol[-1]
              
              close_list[-1] = (open_list[-1] + close_list[-1] + high_list[-1] + low_list[-1])/4
              open_list[-1]  = (open_list[-2] + close_list[-2])/2
              high_list[-1]  = max(high_list[-1], open_list[-1], close_list[-1])
              low_list[-1]   = min(low_list[-1], open_list[-1], close_list[-1])
              prices2[-1] = (date2num(date[-1]), open_list[-1], high_list[-1], low_list[-1], close_list[-1], volume_list[-1], date[-1])
            ###

          if start_x != 0:
            highest_price = 0
            lowest_price = 999999999999

            #candlestick
            if current_candle_type == CANDLE_TYPE_CANDLESTICK:
              for i in range(start_x, len(date)):
                if high[i] > highest_price:
                  highest_price = high[i] #candlestick
                if low[i] < lowest_price:
                  lowest_price = low[i] #candlestick
            elif current_candle_type == CANDLE_TYPE_HEIKIN_ASHI:
              #heikin ashi
              for i in range(start_x, len(date)):
                if high_list[i] > highest_price:
                  highest_price = high_list[i]
                if low_list[i] < lowest_price:
                  lowest_price = low_list[i]            
              ###

            xl = ax.get_xlim()
            ax.set_xlim(date[start_x], xl[1])


          if prices[-1][4] > highest_price:
              highest_price = prices[-1][4]
          if prices[-1][4] < lowest_price:
              lowest_price = prices[-1][4]
          #ax.yaxis.set_major_locator(matplotlib_ticker.MultipleLocator((highest_price-lowest_price)/20))
          ax.set_ylim((lowest_price - lowest_price*0.0015, highest_price + highest_price*0.0015))

          ticker = prices[-1][4]
          ticker_formatted = str(client.price_to_precision(symbol, ticker))
          ticker_for_line = prices[-1][4]
          
          if "e-" in str(ticker) or "e+" in str(ticker):
            d1 = ctx.create_decimal(repr(ticker))
            ticker_formatted = format(d1, 'f')

          next_candle_start_time = time.time() // elapsed_table[timeframe_entered] * \
                                   elapsed_table[timeframe_entered] + elapsed_table[timeframe_entered]

          duration = datetime.datetime.fromtimestamp(next_candle_start_time) - datetime.datetime.now()
          days, seconds = duration.days, duration.seconds
          hours = days * 24 + seconds // 3600
          minutes = (seconds % 3600) // 60
          seconds = seconds % 60
          if hours == 0:
            time_to_next_candle = "%02d:%02d" % (minutes, seconds)
          else:
            time_to_next_candle = "%02d:%02d:%02d" % (hours, minutes, seconds)

          if first == True:
            color = "#2c681d" # green
            line_color = green
            if prices[-1][4] < prices[-1][1]:
                color = "#681d1d" # red
                line_color = red

            tag_title = symbol + " " + ticker_formatted

            if not (exchange == "BITFINEX" and time.time() > time_close): # bitfinex not waiting for new candle data
                tag_title = tag_title + "\n"
                tag_title = tag_title + " " * (len(tag_title)-len(time_to_next_candle)-1) + time_to_next_candle

            price_line = ax.axhline(ticker_for_line, color=line_color, linestyle="dotted", lw=.9)
            annotation = ax.text(date[-1] + (date[-1]-date[-5]), ticker_for_line, tag_title, fontsize=8, weight="bold", color=white, backgroundcolor=color, family="monospace")

            self.CANVAS_GET_SIZE.emit(self.tab_index, annotation)
            tbox = aqs[tab_index].get()

            dbox = tbox.transformed(ax.transData.inverted())
            annotation.set_y(ticker_for_line)
            annotation.set_bbox(dict(facecolor=color, edgecolor=white, lw=.5))
          else:
            color = "#2c681d" # green
            line_color = green
            if prices[-1][4] < prices[-1][1]:
                color = "#681d1d" # red
                line_color = red

            tag_title = symbol + " " + ticker_formatted
            if not (exchange == "BITFINEX" and time.time() > time_close):
                tag_title = tag_title + "\n"
                tag_title = tag_title + " " * (len(tag_title)-len(time_to_next_candle)-1) + time_to_next_candle

            price_line.set_ydata(ticker_for_line)
            price_line.set_color(line_color)
            annotation.set_text(tag_title)
            annotation.set_y(ticker_for_line)
            annotation.set_backgroundcolor(color)
            annotation.set_bbox(dict(facecolor=color, edgecolor=white, lw=.5))

          if init == True:
            xl = ax.get_xlim()
            candle_width = ((dbox.x0 - xl[0]) / limit) * 0.8
          if first == True:
            for i in range(0, len(indicators)):
              if indicators[i].name == "MACD" or indicators[i].name == "VOLUME":
                indicators[i].candle_width = candle_width
                indicators[i].update()


          if first == True:
            scanner_results = self.candlescanner(popen, phigh, plow, pclose)
          if current_candle_type == CANDLE_TYPE_CANDLESTICK:
            last_line1, last_line2, last_rect = _candlestick(ax, prices, first, last_line1, last_line2, last_rect, candle_width, scanner_results, highest_price)
          elif current_candle_type == CANDLE_TYPE_HEIKIN_ASHI:        
            last_line1, last_line2, last_rect = _candlestick(ax, prices2, first, last_line1, last_line2, last_rect, candle_width, scanner_results, highest_price)
          
          if first == True:
            ax.autoscale_view()
            ax.set_facecolor(black)
            ax.yaxis.tick_right()
            ax.yaxis.set_label_position("right")
            ax.spines['top'].set_edgecolor(grayscale_dark)
            ax.spines['left'].set_edgecolor(grayscale_dark)
            ax.spines['right'].set_edgecolor(grayscale_light)
            ax.spines['bottom'].set_edgecolor(grayscale_light)
            ax.spines['left'].set_linewidth(3)
            ax.spines['top'].set_linewidth(3)
            ax.set_facecolor(black)
            ax.xaxis.label.set_color(white)
            ax.yaxis.label.set_color(white)
            ax.tick_params(axis='x', colors=white)
            ax.tick_params(axis='y', colors=white)
            ax.grid(alpha=.25)
            ax.grid(True)

          if init == True:
            ax.set_position([0.04,0.04,0.9,0.93])
            self.FIGURE_TIGHT_LAYOUT.emit(self.tab_index)
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
                if axis != indicator_axes[len(indicator_axes)-1]:
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

          pdate[:] = []
          popen[:] = []
          phigh[:] = []
          plow[:] = []
          pclose[:] = []
          pvol[:] = []

          do_break = False
          while True:
              if tab_index in destroyed_window_ids:
                  do_break = True
                  break

              self.CANVAS_DRAW.emit(self.tab_index)
              return_value = aqs[tab_index].get()
              if return_value == 0:
                  break
              else:
                  if time.time() > time_close:
                    force_redraw_chart = True
                  time.sleep(0.1)
                  update_time = time.time() - 1

          if do_break == True:
            break

          first = False
          init = False
        except:
          print(get_full_stacktrace())
          

    self.CHART_DESTROY.emit(self.tab_index)
    
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

        if timeframe_entered == "2h":
            limit = int(days_entered * (24/2))

        if timeframe_entered == "3h":
            limit = int(days_entered * (24/3))

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
          print(get_full_stacktrace())
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

    time.sleep(5)
    while True:
      try:
        ticker = client.fetch_tickers()

        self.usdt_symbols = []
        self.btc_symbols = []
        for symbol,value in ticker.items():
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
        for balance_symbol, balance in balances.items():
          if "total" not in balance:
            continue
          if float(balance["total"]) == 0.0:
            continue
          if balance_symbol == "USDT":
            usdt_balance = usdt_balance + float(balance["total"])
          elif balance_symbol + "/USDT" in self.usdt_symbols:
            for symbol_name,symbol in ticker.items():
              if symbol_name == balance_symbol + "/USDT":
                symbol_price = float(symbol["last"])
                break
            usdt_balance = usdt_balance + float(balance["total"]) * symbol_price
          elif balance_symbol + "/USD" in self.usdt_symbols:
            for symbol_name,symbol in ticker.items():
              if symbol_name == balance_symbol + "/USD":
                symbol_price = float(symbol["last"])
                break
            usdt_balance = usdt_balance + float(balance["total"]) * symbol_price
          elif balance_symbol + "/BTC" in self.btc_symbols:
            for symbol_name,symbol in ticker.items():
              if symbol_name == balance_symbol + "/BTC":
                symbol_price = float(symbol["last"])
                break
            usdt_balance = usdt_balance + float(balance["total"]) * symbol_price * btc_price
        
        btc_balance = usdt_balance / btc_price
        
        qs_local.put(SHOW_STATUSBAR_MESSAGE)
        qs_local.put("USD Balance: " + "%.2f - BTC Balance: %.8f" % (usdt_balance, btc_balance))
        self.data_ready.emit()
      except:
        print(get_full_stacktrace())
        
      time.sleep(35)

class Window(QtWidgets.QMainWindow):
    global tab_widgets
    global config
    global window_ids
    def __init__(self, symbol, timeframe_entered):
        global selected_symbol
        global DataRunnerTabs
        QtWidgets.QMainWindow.__init__(self)
        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        uic.loadUi('mainwindowqt.ui', self)
        self.setWindowTitle("WAVETREND - " + exchange)
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
        
        window_id = get_window_id()
        window_ids[0] = window_id        
        window_configs[window_id] = abstract()
        window_configs[window_id].candle_type = CANDLE_TYPE_CANDLESTICK
        window_configs[window_id].trade_type = TRADE_TYPE_TRENDING
        
        self.tabBar = self.tabWidget.tabBar()
        tabBarMenu = QtWidgets.QMenu()
        closeAction = QtWidgets.QAction("close", self)
        tabBarMenu.addAction(closeAction)
        closeAction.triggered.connect(functools.partial(self.removeTab, window_ids[0]))
        menuButton = QtWidgets.QToolButton(self)
        menuButton.setStyleSheet('border: 0px; padding: 0px;')
        menuButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menuButton.setMenu(tabBarMenu)
        self.tabBar.setTabButton(0, QtWidgets.QTabBar.RightSide, menuButton)

        widget = QtWidgets.QHBoxLayout(self.tabWidget.widget(0))
        self.OrderbookWidget = []
        OrderBookWidget_ = OrderBookWidget(self, symbol, window_id)
        OrderBookWidget_.DISPLAY_ORDERBOOK.connect(OrderBookWidget_.on_DISPLAY_ORDERBOOK, QtCore.Qt.BlockingQueuedConnection)
        OrderBookWidget_.DISPLAY_TRADES.connect(OrderBookWidget_.on_DISPLAY_TRADES, QtCore.Qt.BlockingQueuedConnection)
        self.OrderbookWidget.append(OrderBookWidget_)
        dc = MplCanvas(self.tabWidget.widget(0), symbol=symbol)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(4)
        sizePolicy.setVerticalStretch(1)
        dc.setSizePolicy(sizePolicy)
        widget.addWidget(dc)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        OrderBookWidget_.setSizePolicy(sizePolicy)
        widget.addWidget(OrderBookWidget_, alignment=QtCore.Qt.AlignRight)

        self.dcs = {}
        self.dcs[window_id] = dc
        
        global qsb
        global aqs
        global dqs
        qs[window_id] = Queue.Queue()
        aqs[window_id] = Queue.Queue()
        dqs[window_id] = collections.deque()

        DataRunnerTabs[window_id] = DataRunner(self, symbol, window_id, 0, timeframe_entered)

        self.chart_runner_thread = ChartRunner(self, symbol, window_id, timeframe_entered)
        self.chart_runner_thread.FIGURE_ADD_SUBPLOT.connect(self.on_FIGURE_ADD_SUBPLOT)
        self.chart_runner_thread.FIGURE_CLEAR.connect(self.on_FIGURE_CLEAR)
        self.chart_runner_thread.FIGURE_ADD_AXES.connect(self.on_FIGURE_ADD_AXES)
        self.chart_runner_thread.CANVAS_GET_SIZE.connect(self.on_CANVAS_GET_SIZE)
        self.chart_runner_thread.FIGURE_TIGHT_LAYOUT.connect(self.on_FIGURE_TIGHT_LAYOUT)
        self.chart_runner_thread.CANVAS_DRAW.connect(self.on_CANVAS_DRAW)
        self.chart_runner_thread.CHART_DESTROY.connect(self.on_CHART_DESTROY)
        self.chart_runner_thread.start()
        
        self.updateusdbalance_runner_thread = UpdateUsdBalanceRunner(self)
        self.updateusdbalance_runner_thread.data_ready.connect(self.queue_handle)
        self.updateusdbalance_runner_thread.start()

    def keyPressEvent(self, event):
     global window_configs
      
     key = event.key()
       
     self.symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex())).split(" ")[0]
     if str(key) == "66": # B pressed
      try:
        percent = .25
        price = get_symbol_price(self.symbol)
        quote = get_quote_from_symbol(self.symbol)
        asset_balance = float(client.fetch_balance()[quote]["free"])
        amount = float(client.amount_to_precision(self.symbol, (asset_balance / price) * percent))

        book = orderbook(client, self.symbol)
        asks_added = 0
        for ask in book["asks"]:
          asks_added = asks_added + ask[1]
          if asks_added > amount:
            price = ask[0]
            print(str(amount) + " " + str(price))
            client.create_limit_buy_order(self.symbol, amount, price)
            return
      except:
        print(get_full_stacktrace())
        return
      
     if str(key) == "83": # S pressed
      try:
        asset_balance = float(client.fetch_balance()[get_asset_from_symbol(self.symbol)]["free"])
        amount = float(client.amount_to_precision(self.symbol, asset_balance * .5))
        book = orderbook(client, self.symbol)
        bids_added = 0
        for bid in book["bids"]:
          bids_added = bids_added + bid[1]
          if bids_added > amount:
            price = bid[0]
            print(str(amount) + " " + str(price))
            client.create_limit_sell_order(self.symbol, amount, price)
            return       
      except:
        print(get_full_stacktrace())
        return

     if str(key) == "67": # C pressed
      tab_index = self.tabWidget.currentIndex()
      window_configs[window_ids[tab_index]].candle_type = CANDLE_TYPE_CANDLESTICK
      return

     if str(key) == "72": # H pressed
      tab_index = self.tabWidget.currentIndex()
      window_configs[window_ids[tab_index]].candle_type = CANDLE_TYPE_HEIKIN_ASHI
      return

     if str(key) == "84": # T pressed
      tab_index = self.tabWidget.currentIndex()
      window_configs[window_ids[tab_index]].trade_type = TRADE_TYPE_TRENDING
      return

     if str(key) == "79": # O pressed
      tab_index = self.tabWidget.currentIndex()
      window_configs[window_ids[tab_index]].trade_type = TRADE_TYPE_OSC
      return

     if str(key) == "16777264": # F1 pressed
      self.tabWidget.setCurrentIndex(0)
      return
     if str(key) == "16777265": # F2 pressed
      self.tabWidget.setCurrentIndex(1)
      return
     if str(key) == "16777266": # F3 pressed
      self.tabWidget.setCurrentIndex(2)
      return
     if str(key) == "16777267": # F4 pressed
      self.tabWidget.setCurrentIndex(3)
      return
     if str(key) == "16777268": # F5 pressed
      self.tabWidget.setCurrentIndex(4)
      return
     if str(key) == "16777269": # F6 pressed
      self.tabWidget.setCurrentIndex(5)
      return
     if str(key) == "16777270": # F7 pressed
      self.tabWidget.setCurrentIndex(6)
      return
     if str(key) == "16777271": # F8 pressed
      self.tabWidget.setCurrentIndex(7)
      return
     if str(key) == "16777272": # F9 pressed
      self.tabWidget.setCurrentIndex(8)
      return

    @QtCore.pyqtSlot(str, int, matplotlib.axes.Axes)
    def on_FIGURE_ADD_SUBPLOT(self, winid, rows, sharex):
        global aqs
        axis = self.dcs[winid].fig.add_subplot(rows, facecolor=black, sharex=sharex)
        aqs[winid].put(axis)

    @QtCore.pyqtSlot(str)
    def on_FIGURE_CLEAR(self, winid):
        global aqs
        self.dcs[winid].fig.clf()
        aqs[winid].put(0)

    @QtCore.pyqtSlot(str, list, matplotlib.axes.Axes)
    def on_FIGURE_ADD_AXES(self, winid, position, sharex):
        global aqs
        axis = self.dcs[winid].fig.add_axes(position, facecolor=black, sharex=sharex)
        aqs[winid].put(axis)

    @QtCore.pyqtSlot(str, matplotlib.text.Text)
    def on_CANVAS_GET_SIZE(self, winid, annotation):
        global aqs
        aqs[winid].put(annotation.get_window_extent(self.dcs[winid].renderer))

    @QtCore.pyqtSlot(str)
    def on_FIGURE_TIGHT_LAYOUT(self, winid):
        global aqs
        self.dcs[winid].fig.tight_layout()
        aqs[winid].put(0)

    @QtCore.pyqtSlot(str)
    def on_CANVAS_DRAW(self, winid):
        global aqs

        for tab_index in window_ids:
            if winid == window_ids[tab_index]:
                break

        if self.tabWidget.currentIndex() == tab_index:
            self.dcs[winid].draw_idle()
            aqs[winid].put(0)
        else:
            aqs[winid].put(1)

    @QtCore.pyqtSlot(str)
    def on_CHART_DESTROY(self, winid):
        global aqs
        global window_ids

        for tab_index in window_ids:
            if winid == window_ids[tab_index]:
                break

        del qs[winid]
        del aqs[winid]
        del dqs[winid]
        self.dcs[winid].fig.clf()
        del self.dcs[winid]

        global DataRunnerTabs

        DataRunnerTabs[winid].kill_websocket_watch_thread = True
        DataRunnerTabs[winid].websocket_watch_thread.join()
        DataRunnerTabs[winid].exchange_obj.stop_candlestick_websocket()
        if exchange == "BITFINEX":
            DataRunnerTabs[winid].exchange_obj.stop_ticker_websocket()
        del DataRunnerTabs[winid].exchange_obj
        del DataRunnerTabs[winid]

        self.OrderbookWidget[tab_index].exchange_obj.stop_depth_websocket()
        self.OrderbookWidget[tab_index].exchange_obj.stop_trades_websocket()
        self.OrderbookWidget[tab_index].kill_websocket_watch_thread = True
        self.OrderbookWidget[tab_index].websocket_watch_thread.join()
        del self.OrderbookWidget[tab_index].exchange_obj
        del self.OrderbookWidget[tab_index]

        self.tabWidget.removeTab(tab_index)
        self.tabWidget.setCurrentIndex(tab_index)

        window_ids_copy = {}
        for j in window_ids.keys():
            if j == tab_index:
                del window_ids[j]
                break

        counter = 0
        for j in window_ids.keys():
            window_ids_copy[counter] = window_ids[j]
            counter = counter + 1

        window_ids = copy.deepcopy(window_ids_copy)

    def queue_handle(self):
      global qs_local

      if qs_local.qsize() > 0:
        value = qs_local.get()
        if value == SHOW_STATUSBAR_MESSAGE:
          message = qs_local.get()
          self.statusbar.showMessage(message)
    
    def tabOnChange(self, event):
      global tab_current_index
      if self.tabWidget.currentIndex() in window_ids:
        tab_current_index = window_ids[self.tabWidget.currentIndex()]
        self.OrderbookWidget[self.tabWidget.currentIndex()].update_trades_display()

    def removeTab(self, window_id):
      global destroyed_window_ids
      destroyed_window_ids[window_id] = "DESTROYED"

    def addTab(self, symbol, timeframe_entered):
      global tab_current_index
      global DataRunnerTabs

      self.tab_widgets.append(QtWidgets.QWidget())
      tab_index = self.tabWidget.addTab(self.tab_widgets[-1], symbol + " " + timeframe_entered)
      self.tabWidget.setCurrentWidget(self.tab_widgets[-1])
      main.tabWidget.setTabIcon(tab_index, QtGui.QIcon("coin.ico"))
      widget = QtWidgets.QHBoxLayout(self.tabWidget.widget(tab_index))

      window_id = get_window_id()
      window_ids[tab_index] = window_id
      window_configs[window_id] = abstract()
      window_configs[window_id].candle_type = CANDLE_TYPE_CANDLESTICK
      window_configs[window_id].trade_type = TRADE_TYPE_TRENDING
      
      tabBarMenu = QtWidgets.QMenu()
      closeAction = QtWidgets.QAction("close", self)
      tabBarMenu.addAction(closeAction)
      closeAction.triggered.connect(functools.partial(self.removeTab, window_ids[tab_index]))      
      menuButton = QtWidgets.QToolButton(self)
      menuButton.setStyleSheet('border: 0px; padding: 0px;')
      menuButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
      menuButton.setMenu(tabBarMenu)      
      self.tabBar.setTabButton(tab_index, QtWidgets.QTabBar.RightSide, menuButton)

      OrderBookWidget_ = OrderBookWidget(self, symbol, window_id)
      OrderBookWidget_.DISPLAY_ORDERBOOK.connect(OrderBookWidget_.on_DISPLAY_ORDERBOOK)
      OrderBookWidget_.DISPLAY_TRADES.connect(OrderBookWidget_.on_DISPLAY_TRADES, QtCore.Qt.BlockingQueuedConnection)
      self.OrderbookWidget.append(OrderBookWidget_)
      dc = MplCanvas(self.tabWidget.widget(0), symbol=symbol)
      sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
      sizePolicy.setHorizontalStretch(4)
      sizePolicy.setVerticalStretch(1)
      dc.setSizePolicy(sizePolicy)
      widget.addWidget(dc)
      sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
      sizePolicy.setHorizontalStretch(1)
      sizePolicy.setVerticalStretch(1)
      OrderBookWidget_.setSizePolicy(sizePolicy)
      widget.addWidget(OrderBookWidget_, alignment=QtCore.Qt.AlignRight)

      global qs
      global aqs
      global dqs
      
      qs[window_id] = Queue.Queue()
      aqs[window_id] = Queue.Queue()
      dqs[window_id] = collections.deque()
      self.dcs[window_id] = dc

      DataRunnerTabs[window_id] = DataRunner(self, symbol, window_id, tab_index, timeframe_entered)

      tab_current_index = window_id

      self.chart_runner_thread = ChartRunner(self, symbol, window_id, timeframe_entered)
      self.chart_runner_thread.FIGURE_ADD_SUBPLOT.connect(self.on_FIGURE_ADD_SUBPLOT)
      self.chart_runner_thread.FIGURE_CLEAR.connect(self.on_FIGURE_CLEAR)
      self.chart_runner_thread.FIGURE_ADD_AXES.connect(self.on_FIGURE_ADD_AXES)
      self.chart_runner_thread.CANVAS_GET_SIZE.connect(self.on_CANVAS_GET_SIZE)
      self.chart_runner_thread.FIGURE_TIGHT_LAYOUT.connect(self.on_FIGURE_TIGHT_LAYOUT)
      self.chart_runner_thread.CANVAS_DRAW.connect(self.on_CANVAS_DRAW)
      self.chart_runner_thread.CHART_DESTROY.connect(self.on_CHART_DESTROY)
      self.chart_runner_thread.start()

    def add_coin_clicked(self, event):
      global dialog
      dialog = Dialog()
      dialog.show()

    def trade_coin_clicked(self, event):
      self.trade_dialog = TradeDialog(self)
      self.trade_dialog.show()
      
class TradeDialog(QtWidgets.QDialog):
  def __init__(self, parent):
    self.parent = parent
    QtWidgets.QDialog.__init__(self)
    uic.loadUi('trade.ui', self)
    self.setFixedSize(713, 385)
    self.symbol = str(self.parent.tabWidget.tabText(self.parent.tabWidget.currentIndex())).split(" ")[0]
    symbol = self.symbol
    self.trade_coin_price = get_symbol_price(symbol)
    trade_coin_price_str = "%.06f" % self.trade_coin_price
    self.setWindowTitle("Trade " + symbol)
    asset = get_asset_from_symbol(symbol)
    quote = get_quote_from_symbol(symbol)
    balance = client.fetch_balance()
    if quote not in balance:
        balance[quote] = {}
        balance[quote]["free"] = 0
    if asset not in balance:
        balance[asset] = {}
        balance[asset]["free"] = 0
    self.quote_free_balance = balance[quote]["free"]
    self.asset_free_balance = balance[asset]["free"]
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
    amount = float(client.amount_to_precision(self.symbol, float(self.editAmount.text())))
    price = float(self.editPrice.text())
    
    symbol_price = get_symbol_price(self.symbol)
    if price > symbol_price:
      return
    
    try:
      client.create_limit_buy_order(self.symbol, amount, price)
    except:
      print(get_full_stacktrace())
      return
    
    self.close()
    
  def selllimit_clicked(self, event):
    amount = float(client.amount_to_precision(self.symbol, float(self.editAmount2.text())))
    price = float(self.editPrice2.text())

    symbol_price = get_symbol_price(self.symbol)
    if price < symbol_price:
      return    
    
    try:
      client.create_limit_sell_order(self.symbol, amount, price)
    except:
      print(get_full_stacktrace())
      return

    self.close()
    
  def buymarket_clicked(self, event):
    amount = truncate(float(self.editAmount_4.text()), 2)

    try:
      client.create_market_buy_order(self.symbol, amount)
    except:
      print(get_full_stacktrace())
      return
    
    self.close()
    
  def sellmarket_clicked(self, event):
    amount = truncate(float(self.editAmount2_3.text()), 2)
    
    try:
      client.create_market_sell_order(self.symbol, amount)
    except:
      print(get_full_stacktrace())
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

class Dialog(QtWidgets.QDialog):
    global config
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        uic.loadUi('windowqt.ui', self)
        self.setFixedSize(555, 575)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.comboBox.addItem("1h")
        for key, value in client.timeframes.items():
          if key == "1h" or key == "1w" or key == "1M" or key not in days_table.keys():
            continue
          self.comboBox.addItem(key)
        
        coins = client.fetchTickers()

        if "BTC/USDT" in coins:
          btcusd_symbol = "BTC/USDT"
        else:
          btcusd_symbol = "BTC/USD"
        
        btc_price = get_symbol_price(btcusd_symbol)
        coins_ = []
        for coin, value in coins.items():
            if coin.endswith("BTC"):
              coins[coin]["volumeFloat"] = int(float(coins[coin]["baseVolume"]) * float(coins[coin]["last"]) * btc_price)
              coins_.append(coins[coin])
            if coin.endswith("USDT"):
              coins[coin]["volumeFloat"] = int(float(coins[coin]["baseVolume"]) * float(coins[coin]["last"]))
              coins_.append(coins[coin])
            if coin.endswith("USD"):
              coins[coin]["volumeFloat"] = int(float(coins[coin]["baseVolume"]) * float(coins[coin]["last"]))
              coins_.append(coins[coin])
        coins = sorted(coins_, key=itemgetter("volumeFloat"), reverse=True)
        
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        
        for coin in coins:
          if coin["symbol"].endswith("BTC") or coin["symbol"].endswith("USDT") or coin["symbol"].endswith("USD"):
            rowPosition = self.tableWidget.rowCount() - 1
            self.tableWidget.insertRow(rowPosition)
            self.tableWidget.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem(coin["symbol"]))
            if "change" in coin and coin["change"]:
              self.tableWidget.setItem(rowPosition, 1, QtWidgets.QTableWidgetItem(str("%.08f" % coin["change"])))
            if "percentage" in coin and coin["percentage"]:
              self.tableWidget.setItem(rowPosition, 2, QtWidgets.QTableWidgetItem(str("%.02f" % coin["percentage"])))
            else:
              self.tableWidget.setItem(rowPosition, 2, QtWidgets.QTableWidgetItem(""))
            self.tableWidget.setItem(rowPosition, 3, QtWidgets.QTableWidgetItem(str(coin["volumeFloat"])))
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
        self.close()

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

def orderbook(exchange, symbol):
  return exchange.fetch_order_book(symbol)

class OrderBookWidget(QtWidgets.QWidget):
    DISPLAY_ORDERBOOK = QtCore.pyqtSignal(list, list)
    DISPLAY_TRADES = QtCore.pyqtSignal(list)

    def __init__(self, parent, symbol, winid):
        super(OrderBookWidget,self).__init__(parent)
        self.parent = parent
        self.winid = winid
        self.symbol = symbol

        self.kill_websocket_watch_thread = False
        self.websocket_alive_time = time.time()
        self.websocket_alive_time_trades = time.time()
        self.websocket_watch_thread = threading.Thread(target=self.websocket_watch)
        self.websocket_watch_thread.daemon = True
        self.websocket_watch_thread.start()
        self.bfx_chanid = -1
        self.bfx_orderbook = {}
        self.bfx_orderbook["bids"] = {}
        self.bfx_orderbook["asks"] = {}
        self.orderbook_time_shown = 0
        self.trades_list = []
        self.bfx_chanid_trades = -1

        widget = QtWidgets.QHBoxLayout()
        self.tableWidgetBids = QtWidgets.QTableWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(2)
        self.tableWidgetBids.setSizePolicy(sizePolicy)
        self.tableWidgetBids.setColumnCount(3)
        self.tableWidgetBids.verticalHeader().setVisible(False)
        self.tableWidgetBids.horizontalHeader().setStyleSheet("QHeaderView::section{border: 0px; border-bottom: 0px;}")
        self.tableWidgetBids.setShowGrid(False)
        self.tableWidgetBids.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidgetBids.setHorizontalHeaderLabels(["Price", "Qty", "Sum"])
        self.tableWidgetBids.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        header = self.tableWidgetBids.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        widget.addWidget(self.tableWidgetBids, 1)
        self.tableWidgetAsks = QtWidgets.QTableWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(2)
        self.tableWidgetAsks.setSizePolicy(sizePolicy)
        self.tableWidgetAsks.setColumnCount(3)
        self.tableWidgetAsks.verticalHeader().setVisible(False)
        self.tableWidgetAsks.horizontalHeader().setStyleSheet("QHeaderView::section{border: 0px; border-bottom: 0px}")
        self.tableWidgetAsks.setShowGrid(False)
        self.tableWidgetAsks.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidgetAsks.setHorizontalHeaderLabels(["Price", "Qty", "Sum"])
        self.tableWidgetAsks.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        header = self.tableWidgetAsks.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        widget.addWidget(self.tableWidgetAsks, 1)

        widget_verticalLayout = QtWidgets.QVBoxLayout(self)
        widget_verticalLayout.addLayout(widget, 1)
        self.tableWidgetTrades = QtWidgets.QTableWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        self.tableWidgetTrades.setSizePolicy(sizePolicy)
        self.tableWidgetTrades.setColumnCount(3)
        self.tableWidgetTrades.verticalHeader().setVisible(False)
        self.tableWidgetTrades.horizontalHeader().setStyleSheet("QHeaderView::section{border: 0px; border-bottom: 0px;}")
        self.tableWidgetTrades.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidgetTrades.setHorizontalHeaderLabels(["Time", "Price", "Quantity"])
        self.tableWidgetTrades.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        header = self.tableWidgetTrades.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        widget_verticalLayout.addWidget(self.tableWidgetTrades)
        self.tableWidgetTrades.setMinimumHeight(self.height()*0.4)

        self.init_orderbook_widget()

    def resizeEvent(self, event):
        self.tableWidgetTrades.setMinimumHeight(self.height()*0.4)

    @QtCore.pyqtSlot(list, list)
    def on_DISPLAY_ORDERBOOK(self, bids_, asks_):
        font = QtGui.QFont()
        font.setPointSize(9)
        if is_darwin == True:
            font.setPointSize(10)

        self.tableWidgetBids.setRowCount(len(bids_))
        highest_amount = 0
        for bid in bids_:
            if bid[1] > highest_amount:
                highest_amount = bid[1]
        second_highest_amount = 0
        for bid in bids_:
            if bid[1] > second_highest_amount and bid[1] != highest_amount:
                second_highest_amount = bid[1]
        third_highest_amount = 0
        for bid in bids_:
            if bid[1] > third_highest_amount and bid[1] != highest_amount and bid[1] != second_highest_amount:
                third_highest_amount = bid[1]

        highest_amount_ask = 0
        for ask in asks_:
            if ask[1] > highest_amount_ask:
                highest_amount_ask = ask[1]
        second_highest_amount_ask = 0
        for ask in asks_:
            if ask[1] > second_highest_amount_ask and ask[1] != highest_amount_ask:
                second_highest_amount_ask = ask[1]
        third_highest_amount_ask = 0
        for ask in asks_:
            if ask[1] > third_highest_amount_ask and ask[1] != highest_amount_ask and ask[1] != second_highest_amount_ask:
                third_highest_amount_ask = ask[1]
        i = 0
        sum = 0
        for bid in bids_:
            self.tableWidgetBids.setRowHeight(i, 23)
            price = str(client.price_to_precision(self.symbol, bid[0]))
            amount = str(client.amount_to_precision(self.symbol, bid[1]))
            sum = sum + bid[1]
            sum_str = str(client.amount_to_precision(self.symbol, sum))

            columnItem = QtWidgets.QTableWidgetItem(price)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

            if bid[1] == highest_amount:
                columnItem.setBackground(QtGui.QColor(11, 83, 69))
            elif bid[1] == second_highest_amount:
                columnItem.setBackground(QtGui.QColor(14, 102, 85))
            elif bid[1] == third_highest_amount:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(33, 47, 60))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetBids.setItem(i, 0, columnItem)
            columnItem = QtWidgets.QTableWidgetItem(amount)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if bid[1] == highest_amount:
                columnItem.setBackground(QtGui.QColor(11, 83, 69))
            elif bid[1] == second_highest_amount:
                columnItem.setBackground(QtGui.QColor(14, 102, 85))
            elif bid[1] == third_highest_amount:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(33, 47, 60))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetBids.setItem(i, 1, columnItem)
            columnItem = QtWidgets.QTableWidgetItem(sum_str)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if bid[1] == highest_amount:
                columnItem.setBackground(QtGui.QColor(11, 83, 69))
            elif bid[1] == second_highest_amount:
                columnItem.setBackground(QtGui.QColor(14, 102, 85))
            elif bid[1] == third_highest_amount:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(33, 47, 60))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetBids.setItem(i, 2, columnItem)
            i = i + 1

        i = 0
        sum = 0
        self.tableWidgetAsks.setRowCount(len(asks_))
        for ask in asks_:
            self.tableWidgetAsks.setRowHeight(i, 23)
            price = str(client.price_to_precision(self.symbol, ask[0]))
            amount = str(client.amount_to_precision(self.symbol, ask[1]))
            sum = sum + ask[1]
            sum_str = str(client.amount_to_precision(self.symbol, sum))

            columnItem = QtWidgets.QTableWidgetItem(price)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if ask[1] == highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(100, 30, 22))
            elif ask[1] == second_highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(123, 36, 28))
            elif ask[1] == third_highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            else:
                columnItem.setBackground(QtGui.QColor(33, 47, 60))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetAsks.setItem(i, 0, columnItem)
            columnItem = QtWidgets.QTableWidgetItem(amount)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if ask[1] == highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(100, 30, 22))
            elif ask[1] == second_highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(123, 36, 28))
            elif ask[1] == third_highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            else:
                columnItem.setBackground(QtGui.QColor(33, 47, 60))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetAsks.setItem(i, 1, columnItem)
            columnItem = QtWidgets.QTableWidgetItem(sum_str)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if ask[1] == highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(100, 30, 22))
            elif ask[1] == second_highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(123, 36, 28))
            elif ask[1] == third_highest_amount_ask:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            else:
                columnItem.setBackground(QtGui.QColor(33, 47, 60))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetAsks.setItem(i, 2, columnItem)
            i = i + 1

        if len(bids_) > len(asks_):
            multiplier = len(bids_)
        else:
            multiplier = len(asks_)

    @QtCore.pyqtSlot(list)
    def on_DISPLAY_TRADES(self, trades_list):
        self.tableWidgetTrades.setRowCount(len(self.trades_list))
        font = QtGui.QFont()
        font.setPointSize(9)
        if is_darwin == True:
            font.setPointSize(10)

        i = 0
        for trade in reversed(trades_list):
            trade_time = trade[0]
            trade_price = trade[1]
            trade_quantity = trade[2]
            trade_buy_maker = not trade[3]
            trade_time_pretty = prettydate.date(datetime.datetime.fromtimestamp(trade_time))

            self.tableWidgetTrades.setRowHeight(i, 23)
            trade_price = str(client.price_to_precision(self.symbol, trade_price))
            trade_quantity = str(client.amount_to_precision(self.symbol, trade_quantity))

            columnItem = QtWidgets.QTableWidgetItem(str(trade_time_pretty))
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if trade_buy_maker == True:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetTrades.setItem(i, 0, columnItem)

            columnItem = QtWidgets.QTableWidgetItem(trade_price)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if trade_buy_maker == True:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetTrades.setItem(i, 1, columnItem)

            columnItem = QtWidgets.QTableWidgetItem(trade_quantity)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if trade_buy_maker == True:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetTrades.setItem(i, 2, columnItem)
            i = i + 1

    def restart_websocket(self):
        self.exchange_obj.stop_depth_websocket()
        self.exchange_obj.start_depth_websocket(self.symbol, self.process_message)

    def restart_websocket_trades(self):
        self.exchange_obj.stop_trades_websocket()
        self.exchange_obj.start_trades_websocket(self.symbol, self.process_message_trades)
        self.websocket_alive_time_trades = time.time()

    def websocket_watch(self):
        while True:
            if self.kill_websocket_watch_thread == True:
                break
            if time.time() - self.websocket_alive_time > 60:
                self.restart_websocket()
            if time.time() - self.websocket_alive_time_trades > 60:
                self.restart_websocket_trades()
            time.sleep(0.1)

    def process_message(self, msg):
        if exchange == "BITFINEX":
            if isinstance(msg, dict) and "chanId" in msg:
                self.websocket_alive_time = time.time()
                self.bfx_orderbook = {}
                self.bfx_orderbook["bids"] = {}
                self.bfx_orderbook["asks"] = {}
                self.bfx_chanid = msg["chanId"]
                return
            elif self.bfx_chanid != -1 and isinstance(msg, list) and msg[0] == self.bfx_chanid:
                self.websocket_alive_time = time.time()

                if isinstance(msg[1], list) and len(msg[1]) > 0 and isinstance(msg[1][0], list) and len(msg[1][0]) > 0:
                    #create in memory orderbook
                    for order in msg[1]:
                        price = float(order[0])
                        count = int(order[1])
                        amount = float(order[2])
                        if amount > 0:
                            self.bfx_orderbook["bids"][price] = [count, amount]
                        else:
                            self.bfx_orderbook["asks"][price] = [count, amount * -1]
                elif isinstance(msg[1], list) and len(msg[1]) > 0:
                    #update in memory orderbook
                    order = msg[1]
                    price = float(order[0])
                    count = int(order[1])
                    amount = float(order[2])

                    if count == 0:
                        if amount == 1:
                            del self.bfx_orderbook["bids"][price]
                        elif amount == -1:
                            del self.bfx_orderbook["asks"][price]
                    elif count > 0:
                        if amount > 0:
                            self.bfx_orderbook["bids"][price] = [count, amount]
                        elif amount < 0:
                            self.bfx_orderbook["asks"][price] = [count, amount * -1]
                else:
                    return

            for tab_index in window_ids:
                if self.winid == window_ids[tab_index]:
                    break

            if self.parent.tabWidget.currentIndex() != tab_index:
                return

            if self.orderbook_time_shown != 0 and time.time() - self.orderbook_time_shown < 1:
                return

            bids = []
            asks = []
            for order in sorted(self.bfx_orderbook["bids"], reverse=True):
                bids.append([order, self.bfx_orderbook["bids"][order][1]])
            for order in sorted(self.bfx_orderbook["asks"]):
                asks.append([order, self.bfx_orderbook["asks"][order][1]])

            self.DISPLAY_ORDERBOOK.emit(bids, asks)
            self.orderbook_time_shown = time.time()
            return

        elif exchange == "BINANCE":
            #msg is a python-binance depth cache instance
            if msg is not None:
                self.websocket_alive_time = time.time()
                for tab_index in window_ids:
                    if self.winid == window_ids[tab_index]:
                        break
                if self.parent.tabWidget.currentIndex() != tab_index:
                    return
                if self.orderbook_time_shown != 0 and time.time() - self.orderbook_time_shown < 1:
                    return

                bids_ = msg.get_bids()[:25]
                asks_ = msg.get_asks()[:25]
                #bids_ = [[float(bid[0]), float(bid[1])] for bid in msg["bids"]]
                #asks_ = [[float(ask[0]), float(ask[1])] for ask in msg["asks"]]
                self.DISPLAY_ORDERBOOK.emit(bids_, asks_)
                self.orderbook_time_shown = time.time()
                return
            else:
                self.restart_websocket()
                return

    def process_message_trades(self, msg):
        if exchange == "BITFINEX":
            if isinstance(msg, dict) and "chanId" in msg:
                self.websocket_alive_time = time.time()
                self.bfx_chanid_trades = msg["chanId"]
                return
            elif self.bfx_chanid_trades != -1 and isinstance(msg, list) and msg[0] == self.bfx_chanid_trades:
                self.websocket_alive_time_trades = time.time()

                if isinstance(msg[1], list) and len(msg[1]) > 0 and isinstance(msg[1][0], list) and len(msg[1][0]) > 0:
                    for trade in reversed(msg[1]):
                        trade_time = trade[1] / 1000
                        trade_price = float(trade[3])
                        trade_quantity = float(trade[2])
                        trade_buy_maker = trade_quantity < 0
                        if trade_quantity < 0:
                            trade_quantity = trade_quantity * -1
                        self.trades_list.append([trade_time, trade_price, trade_quantity, trade_buy_maker])

                    for tab_index in window_ids:
                        if self.winid == window_ids[tab_index]:
                            break
                    if self.parent.tabWidget.currentIndex() != tab_index:
                        return

                    self.DISPLAY_TRADES.emit(self.trades_list)
                elif isinstance(msg[1], str) and msg[1] == "te" and isinstance(msg[2], list) and len(msg[2]) > 0:
                    trade = msg[2]
                    trade_time = trade[1] / 1000
                    trade_price = float(trade[3])
                    trade_quantity = float(trade[2])
                    trade_buy_maker = trade_quantity < 0
                    if trade_quantity < 0:
                        trade_quantity = trade_quantity * -1
                    self.trades_list.append([trade_time, trade_price, trade_quantity, trade_buy_maker])
                    if len(self.trades_list) > 100:
                        self.trades_list.pop(0)

                    for tab_index in window_ids:
                        if self.winid == window_ids[tab_index]:
                            break
                    if self.parent.tabWidget.currentIndex() != tab_index:
                        return

                    self.DISPLAY_TRADES.emit(self.trades_list)
                    return

        elif exchange == "BINANCE":
            if isinstance(msg, dict) and "T" in msg:
                self.websocket_alive_time_trades = time.time()
                trade_time = msg["T"] / 1000
                trade_price = float(msg["p"])
                trade_quantity = float(msg["q"])
                trade_buy_maker = msg["m"]
                self.trades_list.append([trade_time, trade_price, trade_quantity, trade_buy_maker])

                if len(self.trades_list) > 100:
                    self.trades_list.pop(0)

                for tab_index in window_ids:
                    if self.winid == window_ids[tab_index]:
                        break
                if self.parent.tabWidget.currentIndex() != tab_index:
                    return

                self.DISPLAY_TRADES.emit(self.trades_list)
                return

    def update_trades_display(self):
        self.on_DISPLAY_TRADES(self.trades_list)

    def init_orderbook_widget(self):
        global markets
        newfont = QtGui.QFont("Courier New")
        self.setFont(newfont)
        self.setStyleSheet("QLabel { background-color : #131D27; color : #C6C7C8; }")
        if exchange == "BITFINEX":
            self.exchange_obj = exchanges.Bitfinex(markets, api_key, api_secret)
        elif exchange == "BINANCE":
            self.exchange_obj = exchanges.Binance(markets, api_key, api_secret)
        self.exchange_obj.start_depth_websocket(self.symbol, self.process_message)
        self.exchange_obj.start_trades_websocket(self.symbol, self.process_message_trades)

if __name__ == "__main__":
  app = QtWidgets.QApplication(sys.argv)
  with open("style.qss","r") as fh:
    app.setStyleSheet(fh.read())
  dialog = Dialog()
  dialog.show()
  os._exit(app.exec_())
