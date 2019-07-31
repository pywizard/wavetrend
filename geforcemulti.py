import os
import sys
import platform
#macos: run openblas single threaded
is_darwin = platform.system() == "Darwin"
if is_darwin == True:
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
import warnings
warnings.filterwarnings("ignore")
import matplotlib
import matplotlib.style
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import date2num
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import ctypes
from matplotlib.transforms import Bbox
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_qt5 import FigureCanvasQT
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
import prettydate
import collections
from exchange_accounts import ExchangeAccounts
from sklearn.linear_model import LinearRegression
import psutil

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
matplotlib.rcParams['font.family'] = 'monospace'

class abstract():
  pass

def _bars(ax, quotes, first, last_line1, last_line2, last_rect, candle_width, \
                 scanner_results, highest_price, trendbars_enabled, last_trendbar_color, trendbars_display_counter):
    width = candle_width
    line_width = 0.9
    OFFSET = width / 2.0

    lines = []
    patches = []
    annotations = []
    trendbar_colors = [""] * len(quotes)

    colorup = "#134F5C"
    colordown = "#A61C00"
    colorup2 = "#53B987"
    colordown2 = "#EB4D5C"

    trendbars_refresh = trendbars_display_counter % 60 == 0
    if trendbars_enabled == True and (first == True or trendbars_refresh == True):
        indicator_color1 = "#134F5C"
        indicator_color1_2 = "#53B987"
        indicator_color2 = "#7F7F28" # yellowish
        indicator_color2_2 = "#FF7F28"
        indicator_color3 = "#A61C00"
        indicator_color3_2 = "#EB4D5C"

        trendbars_period_1 = 8
        trendbars_period_2 = 34

        high = []
        low = []
        close = []

        for q in quotes:
            t, open, high_, low_, close_ = q[:5]
            high.append(high_)
            low.append(low_)
            close.append(close_)

        cci1 = talib.CCI(np.array(high), np.array(low), np.array(close), timeperiod=trendbars_period_1)
        cci2 = talib.CCI(np.array(high), np.array(low), np.array(close), timeperiod=trendbars_period_2)

        cci1_ = []
        cci2_ = []
        for cci_value in cci1:
            if np.isnan(cci_value) == True:
                cci1_.append(0)
            else:
                cci1_.append(cci_value)
        for cci_value in cci2:
            if np.isnan(cci_value) == True:
                cci2_.append(0)
            else:
                cci2_.append(cci_value)

        for i in range(0, len(cci1_)):
            if cci1_[i] >= 0 and cci2_[i] >= 0:
                trendbar_colors[i] = [indicator_color1, indicator_color1_2]
            elif cci1_[i] >= 0 and cci2_[i] < 0:
                trendbar_colors[i] = [indicator_color2, indicator_color2_2]
            else:
                trendbar_colors[i] = [indicator_color3, indicator_color3_2]

    if first == False:
      quotes = [quotes[-1]]

    i = 0
    for q in quotes:
        if first == True:
            annotate = False
            scanner_result = []
            for scanner_result in scanner_results:
                if scanner_result[0] == i:
                    annotate = True
                    break
        i = i + 1

        t, open, high, low, close = q[:5]
        
        if close >= open:
            if trendbars_enabled == True and first == True:
                colorup = trendbar_colors[i-1][0]
                colorup2 = trendbar_colors[i-1][1]

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
            if trendbars_enabled == True and first == True:
                colordown = trendbar_colors[i-1][0]
                colordown2 = trendbar_colors[i-1][1]

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

          if annotate == True and len(scanner_result) != 0:
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
          last_trendbar_color = trendbar_colors[-1]
        else:
          if trendbars_enabled == True and trendbars_refresh == True:
              color = trendbar_colors[-1][0]
              color2 = trendbar_colors[-1][1]
              last_trendbar_color = trendbar_colors[-1]
          elif trendbars_enabled == True:
              color = last_trendbar_color[0]
              color2 = last_trendbar_color[1]

          last_line1.set_ydata((high, higher))
          last_line2.set_ydata((low, lower))
          last_line1.set_color(color2)
          last_line2.set_color(color2)          
          last_rect.set_y(lower)
          last_rect.set_height(height)
          last_rect.set_facecolor(color)
          last_rect.set_edgecolor(color2)

    trendbars_display_counter = trendbars_display_counter + 1
    ax.autoscale_view()

    return last_line1, last_line2, last_rect, last_trendbar_color, trendbars_display_counter

window_ids = {}
def get_window_id():
  return "win-" + ''.join(random.choice('0123456789abcdef') for i in range(10))

window_configs = {}
asset_balance_usd = 6000

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

def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

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
qs_local = {}
exchange_balances = {}

CANDLE_TYPE_CANDLESTICK = 0
CANDLE_TYPE_HEIKIN_ASHI = 1
BBAND_TYPE_DEFAULT = 0
BBAND_TYPE_TRENDBARS = 1
TRADE_TYPE_TRENDING = 0
TRADE_TYPE_OSC = 1
INTERNAL_TAB_INDEX_NOTFOUND = "NOTFOUND"

tab_current_index = None
destroyed_window_ids = {}

ChartRunnerTabs = {}
DataRunnerTabs = {}
stop_buying = True
stop_selling = True

train_input = []
train_output = []
current_order_id = 0

days_table = {"1m": 0.17, "3m": .5, "5m": .9, "15m": 2.5, "30m": 5 , "1h": 10, \
              "2h": 20, "3h": 30, "4h": 40, "6h": 60, "8h": 80, "12h": 120, \
              "1d": 240, "1D": 240, "3d": 3*240, "3D": 3*240}
elapsed_table = {"1m": 60, "3m": 60*3, "5m": 60*5, "15m": 60*15, "30m": 60*30, \
                 "1h": 60*60, "2h": 60*60*2, "3h": 60*60*3, "4h": 60*60*4, \
                 "6h": 60*60*6, "8h": 60*60*8, "12h": 60*60*12, "1d": 60*60*24, "1D": 60*60*24, \
                 "3d": 60*60*24*3, "3D": 60*60*24*3}

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
  def __init__(self, parent, exchange, symbol, window_id, tab_index, timeframe_entered):
    self.symbol = symbol
    self.window_id = window_id
    self.tab_index = tab_index
    self.parent = parent
    self.exchange = exchange
    self.timeframe_entered = timeframe_entered
    self.chanid = -1
    self.chanid_ticker = -1

    if self.exchange == accounts.EXCHANGE_BITFINEX:
        self.last_result = []
        self.exchange_obj = exchanges.Bitfinex(accounts.exchanges[accounts.EXCHANGE_BITFINEX]["markets"], \
                                               accounts.exchanges[accounts.EXCHANGE_BITFINEX]["api_key"], \
                                               accounts.exchanges[accounts.EXCHANGE_BITFINEX]["api_secret"])
        self.exchange_obj.start_ticker_websocket(self.symbol, self.process_message_ticker)
        self.websocket_ticker_alive_time = time.time()
        if timeframe_entered == "1d":
            self.timeframe_entered = "1D"
    elif self.exchange == accounts.EXCHANGE_BINANCE:
        self.exchange_obj = exchanges.Binance(accounts.exchanges[accounts.EXCHANGE_BINANCE]["markets"], \
                                              accounts.exchanges[accounts.EXCHANGE_BITFINEX]["api_key"], \
                                              accounts.exchanges[accounts.EXCHANGE_BITFINEX]["api_secret"])
    elif self.exchange == accounts.EXCHANGE_KRAKEN:
        self.last_result = []
        self.exchange_obj = exchanges.Kraken(accounts.exchanges[accounts.EXCHANGE_KRAKEN]["markets"])
        self.exchange_obj.start_ticker_websocket(self.symbol, self.process_message_ticker)
        self.websocket_ticker_alive_time = time.time()
    self.exchange_obj.start_candlestick_websocket(self.symbol, self.timeframe_entered, self.process_message)

    self.kill_websocket_watch_thread = False
    self.websocket_alive_time = time.time()
    self.websocket_watch_thread = threading.Thread(target=self.websocket_watch)
    self.websocket_watch_thread.daemon = True
    self.websocket_watch_thread.start()

  def restart_websocket(self):
      self.chanid = -1
      self.exchange_obj.stop_candlestick_websocket()
      self.exchange_obj.start_candlestick_websocket(self.symbol, self.timeframe_entered, self.process_message)
      self.websocket_alive_time = time.time()

  def restart_ticker_websocket(self):
      self.chanid_ticker = -1
      self.exchange_obj.stop_ticker_websocket()
      self.exchange_obj.start_ticker_websocket(self.symbol, self.process_message_ticker)
      self.websocket_ticker_alive_time = time.time()

  def websocket_watch(self):
    while True:
        if self.kill_websocket_watch_thread == True:
            break
        if time.time() - self.websocket_alive_time > 60:
           self.restart_websocket()
        if self.exchange == accounts.EXCHANGE_BITFINEX or self.exchange == accounts.EXCHANGE_KRAKEN:
            if time.time() - self.websocket_ticker_alive_time > 60:
               self.restart_ticker_websocket()
        time.sleep(0.1)

  def process_message_ticker(self, msg):
      if self.exchange == accounts.EXCHANGE_KRAKEN:
          if isinstance(msg, dict) and "channelID" in msg:
              self.chanid_ticker = msg["channelID"]
              return
          elif self.chanid_ticker != -1  and isinstance(msg, list) and msg[0] == self.chanid_ticker:
              self.websocket_ticker_alive_time = time.time()
              if not isinstance(msg[1], dict):
                  return
              if 'c' not in msg[1].keys():
                  return

              if len(self.last_result) != 0:
                result = copy.copy(self.last_result)
                close_price = float(msg[1]['c'][0])

                last_price = close_price
                if last_price > result[2]: #high
                    result[2] = last_price
                if last_price < result[3]: #low
                    result[3] = last_price
                result[4] = last_price # close

                dqs[self.window_id].append(result)
                return

      elif self.exchange == accounts.EXCHANGE_BITFINEX:
          if isinstance(msg, dict) and "chanId" in msg:
              self.chanid_ticker = msg["chanId"]
              return
          elif self.chanid_ticker != -1  and isinstance(msg, list) and msg[0] == self.chanid_ticker:
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
                return

  def process_message(self, msg):
    if self.exchange == accounts.EXCHANGE_KRAKEN:
        if isinstance(msg, dict) and "channelID" in msg:
            self.chanid = msg["channelID"]
            return
        elif self.chanid != -1 and isinstance(msg, list) and msg[0] == self.chanid:
            self.websocket_alive_time = time.time()
            candle_time = time.time() // elapsed_table[self.timeframe_entered] * elapsed_table[self.timeframe_entered]
            candle = None

            if isinstance(msg[1], list) and len(msg[1]) > 0 and isinstance(msg[1][0], list) and len(msg[1][0]) > 0:
                candle = msg[1][0]
            elif isinstance(msg[1], list) and len(msg[1]) > 0:
                candle = msg[1]
            else:
                return

            if int(float(candle[1]) - elapsed_table[self.timeframe_entered]) != candle_time:
                return

            dt = datetime.datetime.fromtimestamp(float(candle[1]) - elapsed_table[self.timeframe_entered])
            open_ = float(candle[2])
            high = float(candle[3])
            low = float(candle[4])
            close = float(candle[5])
            volume = float(candle[7])

            result = [dt, open_, high, low, close, volume, 1]
            self.last_result = copy.copy(result)

            dqs[self.window_id].append(result)
            return
    elif self.exchange == accounts.EXCHANGE_BITFINEX:
        if isinstance(msg, dict) and "chanId" in msg:
            self.chanid = msg["chanId"]
            return
        elif  self.chanid != -1  and isinstance(msg, list) and msg[0] == self.chanid:
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

    elif self.exchange == accounts.EXCHANGE_BINANCE:
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
  CANVAS_DRAW = QtCore.pyqtSignal(str)
  CHART_DESTROY = QtCore.pyqtSignal(str, str)

  def __init__(self, parent, exchange, symbol, tab_index, timeframe_entered, OrderbookWidget):
    super(ChartRunner, self).__init__(parent)
    self.parent = parent
    self.exchange = exchange
    self.symbol = symbol
    self.tab_index = tab_index
    self.timeframe_entered = timeframe_entered
    self.OrderbookWidget = OrderbookWidget
    self.widthAdjusted = False

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

    init = True
    first = True
    last_line1 = None
    last_line2 = None
    last_rect = None
    last_trendbar_color = None
    trendbars_display_counter = 0
    prices = []
    indicators = []
    indicator_axes = []
    ctx = decimal.Context()
    ctx.prec = 20
    indicator_update_time = 0
    current_candle_type = window_configs[self.tab_index].candle_type
    current_trade_type = window_configs[self.tab_index].trade_type
    current_bband_type = window_configs[self.tab_index].bband_type
    date = None
    date2 = None
    force_redraw_chart = False # True means switched from tab
    bband_index = -1
    keltner_index = -1
    squeeze_now_shown = False

    while True:
        try:
          while True:
              if init == True:
                  self.FIGURE_CLEAR.emit(self.tab_index)
                  aqs[self.tab_index].get()
                  while True:
                      if self.OrderbookWidget.orderbookWidthAdjusted == False:
                          time.sleep(0.05)
                          continue
                      else:
                          break
                  update_time = time.time()
                  break
              if force_redraw_chart == True:
                  update_time = time.time()
                  break
              elif time.time() - update_time < 1:
                  time.sleep(0.1)
              else:
                  update_time = time.time()
                  break

          candle_type = window_configs[self.tab_index].candle_type
          trade_type = window_configs[self.tab_index].trade_type
          bband_type = window_configs[self.tab_index].bband_type
          hotkeys_pressed = current_candle_type != candle_type or current_trade_type != trade_type or current_bband_type != bband_type
          if hotkeys_pressed == True:
              trendbars_display_counter = 0
              force_redraw_chart = True

          if first == True and force_redraw_chart == False:
                date, open_, high, low, close, vol, limit = self.getData(timeframe_entered, days_entered, symbol)
                time_close = (datetime.datetime.timestamp(date[-1]) // elapsed_table[self.timeframe_entered] * \
                              elapsed_table[self.timeframe_entered]) + elapsed_table[self.timeframe_entered]
                date2 = None
          elif first == False and force_redraw_chart == False:
            try:
                chart_result = dqs[self.tab_index].pop()
                dqs[self.tab_index].clear()
                [date2, open2_, high2, low2, close2, vol2, limit2] = chart_result
            except IndexError:
                pass
          else:
              if first == False and force_redraw_chart == True:
                self.FIGURE_CLEAR.emit(self.tab_index)
                aqs[self.tab_index].get()
                first = True
                force_redraw_chart = False
                last_line1 = None
                last_line2 = None
                last_rect = None
                indicators.clear()
                indicator_axes.clear()
                current_candle_type = candle_type
                current_trade_type = trade_type
                current_bband_type = bband_type
                continue

          if first == True:
            self.FIGURE_ADD_SUBPLOT.emit(self.tab_index, 111, None)
            ax = aqs[self.tab_index].get()

            prices.clear()
            for i in range(0, len(date)):
                prices.append([date2num(date[i]), open_[i], high[i], low[i], close[i], vol[i], date[i]])

            ax.xaxis.set_tick_params(labelsize=7)
            ax.yaxis.set_tick_params(labelsize=7)
          else:
            if date2 != None:
                prices[-1] = [date2num(date2), open2_, high2, low2, close2, vol2, date2]

          if first == True:
            indicators.append(indicator_BBANDS(current_bband_type == BBAND_TYPE_TRENDBARS))
            bband_index = 0
            indicators.append(indicator_KELTNER_CHANNEL())
            keltner_index = 1
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
                new_ax.xaxis.set_tick_params(labelsize=7)
                new_ax.yaxis.set_tick_params(labelsize=7)
                new_ax.spines['left'].set_edgecolor(grayscale_dark)
                new_ax.spines['right'].set_edgecolor(grayscale_light)
                new_ax.spines['top'].set_edgecolor(grayscale_light)
                new_ax.spines['bottom'].set_edgecolor(grayscale_light)
                new_ax.spines['bottom'].set_linewidth(1.05)
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
              if time.time() - indicator_update_time > 10 or current_candle_type != candle_type or current_trade_type != trade_type or current_bband_type != bband_type:
                indicator.update()              
            
            xaxis_start = indicator.xaxis_get_start()
            if xaxis_start != 0 and xaxis_start > start_x:
              start_x = xaxis_start
                          
          if time.time() - indicator_update_time > 10 or current_candle_type != candle_type or current_trade_type != trade_type or current_bband_type != bband_type:
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
              prices2.clear()
              for i in range(0, len(date)):
                  prices2.append([date2num(date[i]), open_list[i], high_list[i], low_list[i], close_list[i], volume_list[i], date[i]])
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
              prices2[-1] = [date2num(date[-1]), open_list[-1], high_list[-1], low_list[-1], close_list[-1], volume_list[-1], date[-1]]
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

          if prices[-1][2] > highest_price:
              highest_price = prices[-1][2]
          if prices[-1][3] < lowest_price:
              lowest_price = prices[-1][3]

          tick_values = ax.yaxis.get_major_locator().tick_values(lowest_price, highest_price)
          ylim_offset = (tick_values[1] - tick_values[0]) / 6
          ax.set_ylim((lowest_price - ylim_offset, highest_price + ylim_offset))

          ticker = prices[-1][4]
          ticker_formatted = str(accounts.client(self.exchange).price_to_precision(symbol, ticker))
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
            color = "#2c681d"  # green
            line_color = green
            text_color = white

            if prices[-1][4] < prices[-1][1]:
                color = "#681d1d"  # red
                line_color = red
                text_color = white

            tag_title = symbol + " " + ticker_formatted

            if time.time() <= time_close and not (hours == 0 and minutes == 0 and seconds == 0):
                tag_title = tag_title + "\n"
                tag_title = tag_title + " " * (len(tag_title)-len(time_to_next_candle)-1) + time_to_next_candle

            price_line = ax.axhline(ticker_for_line, color=line_color, linestyle="dotted", lw=.9)
            annotation = ax.text(date[-1] + (date[-1]-date[-5]), ticker_for_line, tag_title, fontsize=7, weight="bold", color=text_color, backgroundcolor=color, family="monospace")

            self.CANVAS_GET_SIZE.emit(self.tab_index, annotation)
            tbox = aqs[tab_index].get()

            dbox = tbox.transformed(ax.transData.inverted())
            annotation.set_y(ticker_for_line)
            annotation.set_bbox(dict(facecolor=color, edgecolor=white, lw=.5))
          else:
            color = "#2c681d"  # green
            line_color = green
            text_color = white
            if prices[-1][4] < prices[-1][1]:
                color = "#681d1d"  # red
                line_color = red
                text = white

            tag_title = symbol + " " + ticker_formatted
            if time.time() <= time_close and not (hours == 0 and minutes == 0 and seconds == 0):
                tag_title = tag_title + "\n"
                tag_title = tag_title + " " * (len(tag_title)-len(time_to_next_candle)-1) + time_to_next_candle

            price_line.set_ydata(ticker_for_line)
            price_line.set_color(line_color)
            annotation.set_text(tag_title)
            annotation.set_y(ticker_for_line)
            annotation.set_backgroundcolor(color)
            annotation.set_bbox(dict(facecolor=color, edgecolor=text_color, lw=.5))

          if init == True:
            xl = ax.get_xlim()
            candle_width = ((dbox.x0 - xl[0]) / limit) * 0.8

          if first == True:
            for i in range(0, len(indicators)):
              if indicators[i].name == "MACD" or indicators[i].name == "VOLUME":
                indicators[i].candle_width = candle_width
                indicators[i].update()
            indicators[bband_index].in_keltner(ax, pdate, indicators[keltner_index].keltner_hband, \
                                               indicators[keltner_index].keltner_lband, lowest_price)
            squeeze_now_shown = False
          else:
            if squeeze_now_shown == False:
                index = len(pdate) - 1
                indicators[bband_index].in_keltner_now(ax, pdate[-1], indicators[keltner_index].keltner_hband[index], \
                                                       indicators[keltner_index].keltner_lband[index], lowest_price)
                squeeze_now_shown = True

          if first == True and self.timeframe_entered in ["12h","1d","1D","3d","3D"]:
            scanner_results = self.candlescanner(popen, phigh, plow, pclose)
          elif self.timeframe_entered not in ["12h","1d","1D","3d","3D"]:
            scanner_results = []
          if current_candle_type == CANDLE_TYPE_CANDLESTICK:
            last_line1, last_line2, last_rect, last_trendbar_color, trendbars_display_counter = \
                _bars(ax, prices, first, last_line1, last_line2, last_rect, candle_width, scanner_results, highest_price, \
                      current_bband_type == BBAND_TYPE_TRENDBARS, last_trendbar_color, trendbars_display_counter)
          elif current_candle_type == CANDLE_TYPE_HEIKIN_ASHI:        
            last_line1, last_line2, last_rect, last_trendbar_color, trendbars_display_counter = \
                _bars(ax, prices2, first, last_line1, last_line2, last_rect, candle_width, scanner_results, highest_price, \
                      current_bband_type == BBAND_TYPE_TRENDBARS, last_trendbar_color, trendbars_display_counter)
          
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

          adjustView = False
          if self.widthAdjusted == False:
            dpi_scale_trans = self.parent.dcs[self.tab_index].fig.dpi_scale_trans
            position_width = 0.8
            dc_width = self.parent.dcs[self.tab_index].width()
            while True:
                ax.set_position([0.04, 0.04, position_width, 0.93])
                bbox = annotation.get_window_extent().transformed(dpi_scale_trans.inverted())
                width = bbox.x1 + bbox.width / 3
                width *= 100
                if width < dc_width:
                    position_width += 0.005
                else:
                    break
            self.widthAdjusted = True
            adjustView = True
            ax_bbox = ax.get_position()

          if first == True or adjustView == True:
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

            if first == True:
                better_bband_str = ""
                if current_bband_type == BBAND_TYPE_TRENDBARS:
                    better_bband_str = ", Better Bollinger Band, MACD Confirm"
                ax.plot(1,1, label=symbol + ", " + timeframe_entered + better_bband_str, marker = '',ls ='')
                legend = ax.legend(frameon=False,loc="upper left", fontsize=9)
                for text in legend.get_texts():
                  text.set_color(grayscale_lighter)

          pdate.clear()
          popen.clear()
          phigh.clear()
          plow.clear()
          pclose.clear()
          pvol.clear()

          if init == False and time.time() > time_close:
            do_break = False
            while True:
              if tab_index in destroyed_window_ids:
                  do_break = True
                  break
              self.CANVAS_DRAW.emit(self.tab_index)
              return_value = aqs[tab_index].get()
              if return_value == 0:
                  try:
                      dqs[self.tab_index].pop()
                      dqs[self.tab_index].clear()
                      force_redraw_chart = True
                      break
                  except IndexError:
                      time.sleep(0.1)
                      continue
              else:
                  force_redraw_chart = True
                  time.sleep(0.1)

          else:
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
          

    self.CHART_DESTROY.emit(self.tab_index, self.exchange)
    
  def getData(self, timeframe_entered, days_entered, currency_entered):
    limit = 0
    if timeframe_entered == "15m":
        limit = int(days_entered * 4 * 24)

    if timeframe_entered == "1m":
        limit = int(days_entered * 60 * 24)

    if timeframe_entered == "3m":
        limit = int(days_entered * 20 * 24)

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

    if timeframe_entered == "8h":
        limit = int(days_entered * (24/8))

    if timeframe_entered == "12h":
        limit = int(days_entered * (24/12))

    if timeframe_entered == "1d":
        limit = int(days_entered)

    if timeframe_entered == "3d":
        limit = int(days_entered / 3)

    dt = []
    open_ = []
    high = []
    low = []
    close = []
    volume = []

    while True:
        try:
          if self.exchange == accounts.EXCHANGE_KRAKEN:
            candles = accounts.client(self.exchange).fetch_ohlcv(currency_entered, timeframe_entered)
          else:
            candles = accounts.client(self.exchange).fetch_ohlcv(currency_entered, timeframe_entered, limit=limit)
          break
        except:
          print(get_full_stacktrace())
          time.sleep(3)
          continue

    if self.exchange == accounts.EXCHANGE_KRAKEN:
        candles = candles[len(candles)-limit:]

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
  
  def __init__(self, parent, exchange, winid):
    super(UpdateUsdBalanceRunner, self).__init__(parent)
    self.parent = parent
    self.exchange = exchange
    self.winid = winid

  def run(self):
    global qs_local
    global destroyed_window_ids

    time.sleep(5)
    while True:
      try:
        ticker = accounts.fetch_tickers(self.exchange)

        self.usdt_symbols = []
        self.btc_symbols = []
        for symbol,value in ticker.items():
          if symbol.endswith("USDT"):
            self.usdt_symbols.append(symbol) 
          if symbol.endswith("USD"):
            self.usdt_symbols.append(symbol)
          if symbol.endswith("BTC"):
            self.btc_symbols.append(symbol)

        balances = accounts.client(self.exchange).fetch_balance()
        usdt_balance = 0
        
        if "BTC/USD" in ticker:
          btcusd_symbol = "BTC/USD"
        else:
          btcusd_symbol = "BTC/USDT"
        
        btc_price = float(ticker[btcusd_symbol]["last"])
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

        qs_local[self.winid].append([self.exchange, self.exchange + " USD Balance: " + "%.2f - BTC Balance: %.8f" % (usdt_balance, btc_balance)])
      except:
        print(get_full_stacktrace())

      do_break = False
      for i in range(0, 35*60*10):
        if self.winid in destroyed_window_ids:
            del qs_local[self.winid]
            do_break = True
            break
        time.sleep(0.1)

      if do_break == True:
          break

class Window(QtWidgets.QMainWindow):
    global tab_widgets
    global config
    global window_ids
    def __init__(self, exchange, symbol, timeframe_entered):
        global selected_symbol
        global ChartRunnerTabs
        global DataRunnerTabs
        QtWidgets.QMainWindow.__init__(self)
        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        uic.loadUi('mainwindowqt.ui', self)
        self.setWindowTitle("WAVETREND " + exchange)
        self.toolButton.clicked.connect(self.add_coin_clicked)
        self.toolButton_2.clicked.connect(self.trade_coin_clicked)
        self.exchange = exchange
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
        window_configs[window_id].bband_type = BBAND_TYPE_DEFAULT

        self.tabBar = self.tabWidget.tabBar()
        tabBarMenu = QtWidgets.QMenu()
        trendingMarketAction = QtWidgets.QAction("trending", self)
        oscillatingMarketAction = QtWidgets.QAction("oscillating", self)
        candlestickChartAction = QtWidgets.QAction("candlestick", self)
        heikinashiChartAction = QtWidgets.QAction("heikin ashi", self)
        trendbarsChartActionEnable = QtWidgets.QAction("+better bband", self)
        trendbarsChartActionDisable = QtWidgets.QAction("-better bband", self)
        closeAction = QtWidgets.QAction("close", self)
        tabBarMenu.addAction(trendingMarketAction)
        tabBarMenu.addAction(oscillatingMarketAction)
        tabBarMenu.addAction(candlestickChartAction)
        tabBarMenu.addAction(heikinashiChartAction)
        tabBarMenu.addAction(trendbarsChartActionEnable)
        tabBarMenu.addAction(trendbarsChartActionDisable)
        tabBarMenu.addAction(closeAction)
        trendingMarketAction.triggered.connect(functools.partial(self.trendingEnabled, window_ids[0]))
        oscillatingMarketAction.triggered.connect(functools.partial(self.oscillatingEnabled, window_ids[0]))
        candlestickChartAction.triggered.connect(functools.partial(self.candlestickEnabled, window_ids[0]))
        heikinashiChartAction.triggered.connect(functools.partial(self.heikinashiEnabled, window_ids[0]))
        trendbarsChartActionEnable.triggered.connect(functools.partial(self.trendbarsEnabled, window_ids[0]))
        trendbarsChartActionDisable.triggered.connect(functools.partial(self.trendbarsDisabled, window_ids[0]))
        closeAction.triggered.connect(functools.partial(self.removeTab, window_ids[0]))
        menuButton = QtWidgets.QToolButton(self)
        menuButton.setStyleSheet('border: 0px; padding: 0px;')
        menuButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menuButton.setMenu(tabBarMenu)
        self.tabBar.setTabButton(0, QtWidgets.QTabBar.RightSide, menuButton)

        widget = QtWidgets.QHBoxLayout(self.tabWidget.widget(0))
        self.OrderbookWidget = []
        OrderBookWidget_ = OrderBookWidget(self, self.exchange, symbol, window_id)
        OrderBookWidget_.DISPLAY_ORDERBOOK.connect(OrderBookWidget_.on_DISPLAY_ORDERBOOK, QtCore.Qt.BlockingQueuedConnection)
        OrderBookWidget_.DISPLAY_TRADES.connect(OrderBookWidget_.on_DISPLAY_TRADES, QtCore.Qt.BlockingQueuedConnection)
        self.OrderbookWidget.append(OrderBookWidget_)
        dc = MplCanvas(self.tabWidget.widget(0), symbol=symbol)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        dc.setSizePolicy(sizePolicy)
        widget.addWidget(dc)
        widget.addWidget(OrderBookWidget_, alignment=QtCore.Qt.AlignRight)
        widget.setSpacing(0)

        self.dcs = {}
        self.dcs[window_id] = dc
        
        global qs
        global aqs
        global dqs
        global qs_local
        global exchange_balances
        qs[window_id] = Queue.Queue()
        aqs[window_id] = Queue.Queue()
        dqs[window_id] = collections.deque()
        qs_local[window_id] = collections.deque()

        exchange_balances[self.exchange] = {}
        exchange_balances[self.exchange][window_id] = ""

        DataRunnerTabs[window_id] = DataRunner(self, self.exchange, symbol, window_id, 0, timeframe_entered)

        ChartRunnerTabs[window_id] = ChartRunner(self, self.exchange, symbol, window_id, timeframe_entered, OrderBookWidget_)
        ChartRunnerTabs[window_id].FIGURE_ADD_SUBPLOT.connect(self.on_FIGURE_ADD_SUBPLOT)
        ChartRunnerTabs[window_id].FIGURE_CLEAR.connect(self.on_FIGURE_CLEAR)
        ChartRunnerTabs[window_id].FIGURE_ADD_AXES.connect(self.on_FIGURE_ADD_AXES)
        ChartRunnerTabs[window_id].CANVAS_GET_SIZE.connect(self.on_CANVAS_GET_SIZE)
        ChartRunnerTabs[window_id].CANVAS_DRAW.connect(self.on_CANVAS_DRAW)
        ChartRunnerTabs[window_id].CHART_DESTROY.connect(self.on_CHART_DESTROY)
        ChartRunnerTabs[window_id].start()

        self.updateusdbalance_runner_thread = UpdateUsdBalanceRunner(self, self.exchange, window_id)
        self.updateusdbalance_runner_thread.start()

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_usd_balance)
        timer.start(5000)

    def keyPressEvent(self, event):
     global window_configs
     global stop_buying
     global stop_selling

     key = event.key()

     self.symbol = str(self.tabWidget.tabText(self.tabWidget.currentIndex())).split(" ")[0]
     if str(key) == "66": # B pressed
        print("BUYING")
        stop_buying = False
        stop_selling = True
     '''
      try:
        percent = .25
        price = accounts.get_symbol_price(self.exchange, self.symbol)
        quote = accounts.get_quote_from_symbol(self.exchange, self.symbol)
        asset_balance = float(accounts.client(self.exchange).fetch_balance()[quote]["free"])
        amount = float(accounts.client(self.exchange).amount_to_precision(self.symbol, (asset_balance / price) * percent))

        book = accounts.get_orderbook(self.exchange, self.symbol)
        asks_added = 0
        for ask in book["asks"]:
          asks_added = asks_added + ask[1]
          if asks_added > amount:
            price = ask[0]
            print(str(amount) + " " + str(price))
            accounts.client(self.exchange).create_limit_buy_order(self.symbol, amount, price)
            return
      except:
        print(get_full_stacktrace())
        return
     '''

     if str(key) == "83": # S pressed
      print("NOT BUYING")
      stop_buying = True
      stop_selling = False
      '''
      try:
        asset_balance = float(accounts.client(self.exchange).fetch_balance()[accounts.get_asset_from_symbol(self.exchange, self.symbol)]["free"])
        amount = float(accounts.client(self.exchange).amount_to_precision(self.symbol, asset_balance * .5))
        book = accounts.get_orderbook(self.exchange, self.symbol)
        bids_added = 0
        for bid in book["bids"]:
          bids_added = bids_added + bid[1]
          if bids_added > amount:
            price = bid[0]
            print(str(amount) + " " + str(price))
            accounts.client(self.exchange).create_limit_sell_order(self.symbol, amount, price)
            return       
      except:
        print(get_full_stacktrace())
        return
      '''

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
    def on_CANVAS_DRAW(self, winid):
        global aqs

        tab_index = get_tab_index(winid)
        if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
            aqs[winid].put(1)
            return

        if self.tabWidget.currentIndex() == tab_index:
            self.dcs[winid].draw_idle()
            aqs[winid].put(0)
        else:
            aqs[winid].put(1)

    @QtCore.pyqtSlot(str, str)
    def on_CHART_DESTROY(self, winid, exchange):
        global aqs
        global window_ids

        tab_index = get_tab_index(winid)
        if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
            return

        del qs[winid]
        del aqs[winid]
        del dqs[winid]
        self.dcs[winid].fig.clf()
        del self.dcs[winid]

        global DataRunnerTabs

        DataRunnerTabs[winid].kill_websocket_watch_thread = True
        DataRunnerTabs[winid].websocket_watch_thread.join()
        DataRunnerTabs[winid].exchange_obj.stop_candlestick_websocket()
        if exchange == accounts.EXCHANGE_BITFINEX or exchange == accounts.EXCHANGE_KRAKEN:
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

    def update_usd_balance(self):
      global qs_local
      global exchange_balances

      index = self.tabWidget.currentIndex()
      if index == -1:
          return
      tab_index = window_ids[index]
      if tab_index in qs_local and len(qs_local[tab_index]) > 0:
        [exchange, message] = qs_local[tab_index].pop()
        qs_local[tab_index].clear()
        #populate through all windows for the same exchange
        if exchange in exchange_balances:
            for winid in exchange_balances[exchange]:
                exchange_balances[exchange][winid] = message
            self.statusbar.showMessage(message)
      else:
        winid_found = False
        for exchange in exchange_balances.keys():
            for winid in exchange_balances[exchange].keys():
                if winid == tab_index:
                    message = exchange_balances[exchange][winid]
                    if message == "":
                        for winid_ in exchange_balances[exchange]:
                            message = exchange_balances[exchange][winid_]
                            if message != "":
                                self.statusbar.showMessage(message)
                                exchange_balances[exchange][winid] = \
                                    exchange_balances[exchange][winid_]
                                winid_found = True
                                break
                    else:
                        self.statusbar.showMessage(message)
                        winid_found = True
                    break
                if winid_found == True:
                    break
            if winid_found == True:
                break

    def tabOnChange(self, event):
      global tab_current_index
      if self.tabWidget.currentIndex() in window_ids:
        self.exchange = str(self.tabWidget.tabText(self.tabWidget.currentIndex())).split(" ")[2]
        self.setWindowTitle("WAVETREND " + self.exchange)
        tab_current_index = window_ids[self.tabWidget.currentIndex()]
        self.OrderbookWidget[self.tabWidget.currentIndex()].update_trades_display()
        self.update_usd_balance()
      else:
        self.statusbar.showMessage("")

    def trendingEnabled(self, window_id):
        global window_configs
        window_configs[window_id].trade_type = TRADE_TYPE_TRENDING

    def oscillatingEnabled(self, window_id):
        global window_configs
        window_configs[window_id].trade_type = TRADE_TYPE_OSC

    def candlestickEnabled(self, window_id):
        global window_configs
        window_configs[window_id].candle_type = CANDLE_TYPE_CANDLESTICK

    def heikinashiEnabled(self, window_id):
        global window_configs
        window_configs[window_id].candle_type = CANDLE_TYPE_HEIKIN_ASHI

    def trendbarsEnabled(self, window_id):
        global window_configs
        window_configs[window_id].bband_type = BBAND_TYPE_TRENDBARS

    def trendbarsDisabled(self, window_id):
        global window_configs
        window_configs[window_id].bband_type = BBAND_TYPE_DEFAULT

    def removeTab(self, window_id, selected_exchange):
      global destroyed_window_ids
      global exchange_balances
      self.exchange = selected_exchange
      destroyed_window_ids[window_id] = "DESTROYED"

      #remove specific window_id from exchange_balances list
      exchange_ = ""
      exchange_balances_copy = copy.deepcopy(exchange_balances)
      for exchange in exchange_balances_copy:
          for winid in exchange_balances_copy[exchange]:
              if winid == window_id:
                  del exchange_balances[exchange][winid]
                  exchange_ = exchange
                  break
      #remove exchange from exchange_balances list if there
      #isn't another tab open with the same exchange
      found = False
      if exchange_ != "" and len(exchange_balances[exchange_]) == 0:
          del exchange_balances[exchange_]

      self.update_usd_balance()

    def addTab(self, symbol, timeframe_entered, selected_exchange):
      global tab_current_index
      global ChartRunnerTabs
      global DataRunnerTabs

      self.exchange = selected_exchange
      self.setWindowTitle("WAVETREND " + self.exchange)
      self.tab_widgets.append(QtWidgets.QWidget())
      tab_index = self.tabWidget.addTab(self.tab_widgets[-1], symbol + " " + timeframe_entered + " " + self.exchange)
      self.tabWidget.setCurrentWidget(self.tab_widgets[-1])
      main.tabWidget.setTabIcon(tab_index, QtGui.QIcon("coin.ico"))
      widget = QtWidgets.QHBoxLayout(self.tabWidget.widget(tab_index))

      window_id = get_window_id()
      window_ids[tab_index] = window_id
      window_configs[window_id] = abstract()
      window_configs[window_id].candle_type = CANDLE_TYPE_CANDLESTICK
      window_configs[window_id].trade_type = TRADE_TYPE_TRENDING
      window_configs[window_id].bband_type = BBAND_TYPE_DEFAULT

      tabBarMenu = QtWidgets.QMenu()
      trendingMarketAction = QtWidgets.QAction("trending", self)
      oscillatingMarketAction = QtWidgets.QAction("oscillating", self)
      candlestickChartAction = QtWidgets.QAction("candlestick", self)
      heikinashiChartAction = QtWidgets.QAction("heikin ashi", self)
      trendbarsChartActionEnable = QtWidgets.QAction("+better bband", self)
      trendbarsChartActionDisable = QtWidgets.QAction("-better bband", self)
      closeAction = QtWidgets.QAction("close", self)
      tabBarMenu.addAction(trendingMarketAction)
      tabBarMenu.addAction(oscillatingMarketAction)
      tabBarMenu.addAction(candlestickChartAction)
      tabBarMenu.addAction(heikinashiChartAction)
      tabBarMenu.addAction(trendbarsChartActionEnable)
      tabBarMenu.addAction(trendbarsChartActionDisable)
      tabBarMenu.addAction(closeAction)
      trendingMarketAction.triggered.connect(functools.partial(self.trendingEnabled, window_ids[tab_index]))
      oscillatingMarketAction.triggered.connect(functools.partial(self.oscillatingEnabled, window_ids[tab_index]))
      candlestickChartAction.triggered.connect(functools.partial(self.candlestickEnabled, window_ids[tab_index]))
      heikinashiChartAction.triggered.connect(functools.partial(self.heikinashiEnabled, window_ids[tab_index]))
      trendbarsChartActionEnable.triggered.connect(functools.partial(self.trendbarsEnabled, window_ids[tab_index]))
      trendbarsChartActionDisable.triggered.connect(functools.partial(self.trendbarsDisabled, window_ids[tab_index]))
      closeAction.triggered.connect(functools.partial(self.removeTab, window_ids[tab_index], selected_exchange))

      menuButton = QtWidgets.QToolButton(self)
      menuButton.setStyleSheet('border: 0px; padding: 0px;')
      menuButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
      menuButton.setMenu(tabBarMenu)      
      self.tabBar.setTabButton(tab_index, QtWidgets.QTabBar.RightSide, menuButton)

      OrderBookWidget_ = OrderBookWidget(self, self.exchange, symbol, window_id)
      OrderBookWidget_.DISPLAY_ORDERBOOK.connect(OrderBookWidget_.on_DISPLAY_ORDERBOOK)
      OrderBookWidget_.DISPLAY_TRADES.connect(OrderBookWidget_.on_DISPLAY_TRADES, QtCore.Qt.BlockingQueuedConnection)
      self.OrderbookWidget.append(OrderBookWidget_)
      dc = MplCanvas(self.tabWidget.widget(0), symbol=symbol)
      sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
      sizePolicy.setHorizontalStretch(1)
      sizePolicy.setVerticalStretch(1)
      dc.setSizePolicy(sizePolicy)
      widget.addWidget(dc)
      widget.addWidget(OrderBookWidget_, alignment=QtCore.Qt.AlignRight)

      global qs
      global aqs
      global dqs
      global qs_local
      global exchange_balances

      qs[window_id] = Queue.Queue()
      aqs[window_id] = Queue.Queue()
      dqs[window_id] = collections.deque()
      qs_local[window_id] = collections.deque()
      self.dcs[window_id] = dc

      DataRunnerTabs[window_id] = DataRunner(self, self.exchange, symbol, window_id, tab_index, timeframe_entered)

      tab_current_index = window_id

      ChartRunnerTabs[window_id] = ChartRunner(self, self.exchange, symbol, window_id, timeframe_entered, OrderBookWidget_)
      ChartRunnerTabs[window_id].FIGURE_ADD_SUBPLOT.connect(self.on_FIGURE_ADD_SUBPLOT)
      ChartRunnerTabs[window_id].FIGURE_CLEAR.connect(self.on_FIGURE_CLEAR)
      ChartRunnerTabs[window_id].FIGURE_ADD_AXES.connect(self.on_FIGURE_ADD_AXES)
      ChartRunnerTabs[window_id].CANVAS_GET_SIZE.connect(self.on_CANVAS_GET_SIZE)
      ChartRunnerTabs[window_id].CANVAS_DRAW.connect(self.on_CANVAS_DRAW)
      ChartRunnerTabs[window_id].CHART_DESTROY.connect(self.on_CHART_DESTROY)
      ChartRunnerTabs[window_id].start()

      if self.exchange not in exchange_balances:
          exchange_balances[self.exchange] = {}
          self.updateusdbalance_runner_thread = UpdateUsdBalanceRunner(self, self.exchange, window_id)
          self.updateusdbalance_runner_thread.start()
      exchange_balances[self.exchange][window_id] = ""

      self.update_usd_balance()

    def add_coin_clicked(self, event):
      global dialog
      dialog = Dialog()
      dialog.show()

    def trade_coin_clicked(self, event):
      self.trade_dialog = TradeDialog(self, self.exchange)
      self.trade_dialog.show()

    def resizeEvent(self, event):
        global ChartRunnerTabs
        for tab_number in range(0, self.tabWidget.count()):
            ChartRunnerTabs[window_ids[tab_number]].widthAdjusted = False
        return super(Window, self).resizeEvent(event)

class TradeDialog(QtWidgets.QDialog):
  def __init__(self, parent, exchange):
    self.parent = parent
    self.exchange = exchange
    QtWidgets.QDialog.__init__(self)
    uic.loadUi('trade.ui', self)
    self.setFixedSize(713, 385)
    self.symbol = str(self.parent.tabWidget.tabText(self.parent.tabWidget.currentIndex())).split(" ")[0]
    symbol = self.symbol
    self.trade_coin_price = accounts.fetch_tickers(self.exchange)[symbol]["last"]
    trade_coin_price_str = "%.06f" % self.trade_coin_price
    self.setWindowTitle("Trade " + symbol)
    asset = accounts.get_asset_from_symbol(self.exchange, symbol)
    quote = accounts.get_quote_from_symbol(self.exchange, symbol)
    balance = accounts.client(self.exchange).fetch_balance()
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
    amount = float(accounts.client(self.exchange).amount_to_precision(self.symbol, float(self.editAmount.text())))
    price = float(self.editPrice.text())
    
    symbol_price = accounts.get_symbol_price(self.exchange, self.symbol)
    if price > symbol_price:
      return
    
    try:
      accounts.client(self.exchange).create_limit_buy_order(self.symbol, amount, price)
    except:
      print(get_full_stacktrace())
      return
    
    self.close()
    
  def selllimit_clicked(self, event):
    amount = float(accounts.client(self.exchange).amount_to_precision(self.symbol, float(self.editAmount2.text())))
    price = float(self.editPrice2.text())

    symbol_price = accounts.get_symbol_price(self.exchange, self.symbol)
    if price < symbol_price:
      return    
    
    try:
      accounts.client(self.exchange).create_limit_sell_order(self.symbol, amount, price)
    except:
      print(get_full_stacktrace())
      return

    self.close()
    
  def buymarket_clicked(self, event):
    amount = truncate(float(self.editAmount_4.text()), 2)

    try:
      accounts.client(self.exchange).create_market_buy_order(self.symbol, amount)
    except:
      print(get_full_stacktrace())
      return
    
    self.close()
    
  def sellmarket_clicked(self, event):
    amount = truncate(float(self.editAmount2_3.text()), 2)
    
    try:
      accounts.client(self.exchange).create_market_sell_order(self.symbol, amount)
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
    price = accounts.get_symbol_price(self.exchange, self.symbol)
    self.editAmount_4.setText("%.02f" % (self.quote_free_balance / self.trade_coin_price))
    total = (self.quote_free_balance / self.trade_coin_price) * price
    if truncate(self.quote_free_balance / self.trade_coin_price, 2) == 0:
      self.editTotal_3.setText("")
    else:
      self.editTotal_3.setText("%.04f" % (total))
  
  def sellMarketLabelClicked(self, event):
    price = accounts.get_symbol_price(self.exchange, self.symbol)
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

        self.selected_exchange = ""
        for exchange_name in accounts.exchanges.keys():
            if self.selected_exchange == "":
                self.selected_exchange = exchange_name
            self.exchangeCombobox.addItem(exchange_name)
        self.exchangeCombobox.currentIndexChanged.connect(self.on_exchange_selected)

        self.updateWidget()

        #close opened splash screen
        if platform.system() == "Windows":
            import win32gui
            window_handle = win32gui.FindWindow("WavetrendSplash", None)
            if window_handle != 0:
                win32gui.EndDialog(window_handle, 0)

    def updateWidget(self):
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["Symbol", "Price Change", "Price Change %", "Volume"])
        self.comboBox.clear()
        self.tableWidget.setRowCount(0)
        self.comboBox.addItem("1d")
        for key, value in accounts.client(self.selected_exchange).timeframes.items():
            if key == "1d" or key not in days_table.keys():
                continue
            self.comboBox.addItem(key)

        coins = accounts.fetch_tickers(self.selected_exchange)

        if "BTC/USD" in coins:
            btcusd_symbol = "BTC/USD"
        else:
            btcusd_symbol = "BTC/USDT"

        btc_price = coins[btcusd_symbol]["last"]
        coins_ = []
        for coin, value in coins.items():
            if coin.endswith("BTC"):
                coins[coin]["volumeFloat"] = int(
                    float(coins[coin]["baseVolume"]) * float(coins[coin]["last"]) * btc_price)
                coins_.append(coins[coin])
            if coin.endswith("USDT"):
                coins[coin]["volumeFloat"] = int(float(coins[coin]["baseVolume"]) * float(coins[coin]["last"]))
                coins_.append(coins[coin])
            if coin.endswith("USD"):
                coins[coin]["volumeFloat"] = int(float(coins[coin]["baseVolume"]) * float(coins[coin]["last"]))
                coins_.append(coins[coin])
        coins = sorted(coins_, key=itemgetter("volumeFloat"), reverse=True)

        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        hasChange = False
        hasPercentage = False
        for coin in coins:
            if coin["symbol"].endswith("BTC") or coin["symbol"].endswith("USDT") or coin["symbol"].endswith("USD"):
                rowPosition = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowPosition)
                self.tableWidget.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem(coin["symbol"]))
                if "change" in coin and coin["change"] is not None:
                    self.tableWidget.setItem(rowPosition, 1, QtWidgets.QTableWidgetItem(str("%.08f" % coin["change"])))
                    hasChange = True
                if "percentage" in coin and coin["percentage"] is not None:
                    self.tableWidget.setItem(rowPosition, 2,
                                             QtWidgets.QTableWidgetItem(str("%.02f" % coin["percentage"])))
                    hasPercentage = True
                else:
                    self.tableWidget.setItem(rowPosition, 2, QtWidgets.QTableWidgetItem(""))
                self.tableWidget.setItem(rowPosition, 3, QtWidgets.QTableWidgetItem(str(coin["volumeFloat"])))
                if "change" in coin and coin["change"]:
                    if float(coin["change"]) < 0:
                        self.tableWidget.item(rowPosition, 0).setForeground(QtGui.QColor(255, 0, 0))
                        self.tableWidget.item(rowPosition, 1).setForeground(QtGui.QColor(255, 0, 0))
                        self.tableWidget.item(rowPosition, 2).setForeground(QtGui.QColor(255, 0, 0))
                        self.tableWidget.item(rowPosition, 3).setForeground(QtGui.QColor(255, 0, 0))
                    else:
                        self.tableWidget.item(rowPosition, 0).setForeground(QtGui.QColor(0, 255, 0))
                        self.tableWidget.item(rowPosition, 1).setForeground(QtGui.QColor(0, 255, 0))
                        self.tableWidget.item(rowPosition, 2).setForeground(QtGui.QColor(0, 255, 0))
                        self.tableWidget.item(rowPosition, 3).setForeground(QtGui.QColor(0, 255, 0))

        if hasChange == False and hasPercentage == False:
            self.tableWidget.removeColumn(1)
            self.tableWidget.removeColumn(1)
        elif hasChange == False:
            self.tableWidget.removeColumn(1)
        elif hasPercentage == False:
            self.tableWidget.removeColumn(2)

        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def on_exchange_selected(self):
        if self.exchangeCombobox.currentText() != self.selected_exchange:
            self.selected_exchange = self.exchangeCombobox.currentText()
            self.updateWidget()

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
          main = Window(self.selected_exchange, symbol, timeframe_entered)
          main.tabWidget.setTabText(0, symbol + " " + timeframe_entered + " " + self.selected_exchange)
          main.tabWidget.setTabIcon(0, QtGui.QIcon("coin.ico"))
          main.showMaximized()
          main_shown = True
        else:
          main.addTab(symbol, timeframe_entered, self.selected_exchange)

class OrderBookWidget(QtWidgets.QWidget):
    DISPLAY_ORDERBOOK = QtCore.pyqtSignal(list, list)
    DISPLAY_TRADES = QtCore.pyqtSignal(list)

    def __init__(self, parent, exchange, symbol, winid):
        super(OrderBookWidget,self).__init__(parent)
        self.parent = parent
        self.exchange = exchange
        self.winid = winid
        self.symbol = symbol

        self.kill_websocket_watch_thread = False
        self.websocket_alive_time = time.time()
        self.websocket_alive_time_trades = time.time()
        self.websocket_watch_thread = threading.Thread(target=self.websocket_watch)
        self.websocket_watch_thread.daemon = True
        self.websocket_watch_thread.start()
        self.wss_chanid = -1
        self.wss_orderbook = {}
        self.wss_orderbook["bids"] = {}
        self.wss_orderbook["asks"] = {}
        self.orderbook_time_shown = 0
        self.trades_list = []
        self.wss_chanid_trades = -1

        self.font = QtGui.QFont()
        self.font.setPointSize(10)

        self.predict_time = time.time() + 60*30 #XXX 60 multiplied by 30
        self.percent_check_time = time.time()
        self.trade_state = "NEUTRAL"
        self.train_time = time.time()

        if is_darwin == True:
            self.font.setPointSize(11)

        widget = QtWidgets.QHBoxLayout()
        self.tableWidgetBids = QtWidgets.QTableWidget()
        self.tableWidgetBids.setColumnCount(3)
        self.tableWidgetBids.verticalHeader().setVisible(False)
        self.tableWidgetBids.horizontalHeader().setStyleSheet("QHeaderView::section{border: 0px; border-bottom: 0px;}")
        self.tableWidgetBids.setShowGrid(False)
        self.tableWidgetBids.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidgetBids.setHorizontalHeaderLabels(["Price", "Qty", "Sum"])
        self.tableWidgetBids.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidgetBids.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidgetBids.horizontalHeader().setFont(self.font)
        self.tableWidgetBids.setStyleSheet("QTableWidget::item { margin-left: 5px; margin-right: 5px; }")
        header = self.tableWidgetBids.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        widget.addWidget(self.tableWidgetBids)
        self.tableWidgetAsks = QtWidgets.QTableWidget()
        self.tableWidgetAsks.setColumnCount(3)
        self.tableWidgetAsks.verticalHeader().setVisible(False)
        self.tableWidgetAsks.horizontalHeader().setStyleSheet("QHeaderView::section{border: 0px; border-bottom: 0px}")
        self.tableWidgetAsks.setShowGrid(False)
        self.tableWidgetAsks.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidgetAsks.setHorizontalHeaderLabels(["Price", "Qty", "Sum"])
        self.tableWidgetAsks.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidgetAsks.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidgetAsks.horizontalHeader().setFont(self.font)
        self.tableWidgetAsks.setStyleSheet("QTableWidget::item { margin-left: 5px; margin-right: 5px; }")
        header = self.tableWidgetAsks.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        widget.addWidget(self.tableWidgetAsks)

        widget_verticalLayout = QtWidgets.QVBoxLayout(self)
        widget_verticalLayout.addLayout(widget)
        self.tableWidgetTrades = QtWidgets.QTableWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.tableWidgetTrades.setSizePolicy(sizePolicy)
        self.tableWidgetTrades.setColumnCount(3)
        self.tableWidgetTrades.verticalHeader().setVisible(False)
        self.tableWidgetTrades.horizontalHeader().setStyleSheet("QHeaderView::section{border: 0px; border-bottom: 0px;}")
        self.tableWidgetTrades.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidgetTrades.setHorizontalHeaderLabels(["Time", "Price", "Quantity"])
        self.tableWidgetTrades.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidgetTrades.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidgetTrades.horizontalHeader().setFont(self.font)
        header = self.tableWidgetTrades.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        widget_verticalLayout.addWidget(self.tableWidgetTrades)
        self.tableWidgetTrades.setMinimumHeight(self.height()*0.4)
        self.orderbookWidthAdjusted = False
        self.tableWidgetBids.hide()
        self.tableWidgetAsks.hide()
        self.tableWidgetTrades.hide()
        self.init_orderbook_widget()

    def kraken_prettify_value(self, value):
        if value.find(".") > -1 and len(value.split(".")[1]) > 3:
            value = "%.3f" % float(value)
        return value

    def resizeEvent(self, event):
        self.tableWidgetTrades.setMinimumHeight(self.height()*0.4)

    def dobuy(self, price):
        global current_order_id
        try:
            percent = 1
            asset_balance = asset_balance_usd
            amount = float(
                accounts.client(accounts.EXCHANGE_BITFINEX).amount_to_precision(self.symbol, (asset_balance / price) * percent))
            print(str(amount))
            try:
                if current_order_id != 0:
                    params = {'type': 'market'}
                    order = accounts.client_(accounts.EXCHANGE_BITFINEX).create_order(symbol=self.symbol, side="buy",
                                                                                      type="market", amount=amount,
                                                                                      params=params)
            except:
                print(get_full_stacktrace())
            params = {'type': 'limit'}
            order = accounts.client_(accounts.EXCHANGE_BITFINEX).create_order(symbol=self.symbol, side="buy", type="limit", price=price, amount=amount, params=params)
            current_order_id = int(order["id"])
        except:
            print(get_full_stacktrace())
            return

    def dosell(self, price):
        global current_order_id
        try:
            percent = 1
            asset_balance = asset_balance_usd
            amount = float(accounts.client(accounts.EXCHANGE_BITFINEX).amount_to_precision(self.symbol, (asset_balance / price) * percent))
            print(str(amount))
            try:
                if current_order_id != 0:
                    params = {'type': 'market'}
                    order = accounts.client_(accounts.EXCHANGE_BITFINEX).create_order(symbol=self.symbol, side="sell",
                                                                                      type="market", amount=amount,
                                                                                      params=params)
            except:
                print(get_full_stacktrace())
            params = {'type': 'limit'}
            order = accounts.client_(accounts.EXCHANGE_BITFINEX).create_order(symbol=self.symbol, side="sell", type="limit", price=price, amount=amount, params=params)
            current_order_id = int(order["id"])
        except:
            print(get_full_stacktrace())
            return

    @QtCore.pyqtSlot(list, list)
    def on_DISPLAY_ORDERBOOK(self, bids_, asks_):
        global stop_buying
        global stop_selling
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

        orderbook_intact = False
        if len(bids_) > 0 and len(asks_) > 0:
            if asks_[0][0] - bids_[0][0] < 50 and asks_[0][0] - bids_[0][0] > -50:
                orderbook_intact = True

        if orderbook_intact and time.time() - self.predict_time > 60 and len(bids_) > 0:
            # AI
            try:
                bid = bids_[0]
                predictor = LinearRegression(n_jobs=-1)
                predictor.fit(X=train_input, y=train_output)
                percent = 1
                asset_balance = asset_balance_usd
                amount = float(
                    accounts.client(self.exchange).amount_to_precision(self.symbol, (asset_balance / bid[0]) * percent))
                X_TEST = [[float(bid[0]), float(amount)]]
                outcome = predictor.predict(X=X_TEST)
                print("AI says buy? " + str(outcome) + " " + str(bid[0]))
                if outcome[0] > 0.7:
                    if self.trade_state == "NEUTRAL" or self.trade_state == "SOLD":
                        self.dobuy(bid[0])
                        self.trade_state = "BOUGHT"
            except:
                print(get_full_stacktrace())

        for bid in bids_:
            self.tableWidgetBids.setRowHeight(i, 23)
            price = str(accounts.client(self.exchange).price_to_precision(self.symbol, bid[0]))
            amount = str(accounts.client(self.exchange).amount_to_precision(self.symbol, bid[1]))
            sum = sum + bid[1]
            sum_str = str(accounts.client(self.exchange).amount_to_precision(self.symbol, sum))
            if self.exchange == accounts.EXCHANGE_KRAKEN:
                amount = self.kraken_prettify_value(amount)
                sum_str = self.kraken_prettify_value(sum_str)

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
            columnItem.setFont(self.font)
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
            columnItem.setFont(self.font)
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
            columnItem.setFont(self.font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetBids.setItem(i, 2, columnItem)
            i = i + 1

        i = 0
        sum = 0
        self.tableWidgetAsks.setRowCount(len(asks_))

        if orderbook_intact and time.time() - self.predict_time > 60 and len(asks_) > 0:
            # AI
            try:
                ask = asks_[0]
                percent = 1
                predictor = LinearRegression(n_jobs=-1)
                predictor.fit(X=train_input, y=train_output)
                asset_balance = asset_balance_usd
                amount = float(accounts.client(self.exchange).amount_to_precision(self.symbol, (asset_balance / ask[0]) * percent))
                X_TEST = [[float(ask[0]), float(amount)]]
                outcome = predictor.predict(X=X_TEST)
                print("AI says sell? " + str(outcome) + " " + str(ask[0]))
                if outcome[0] < 0.3:
                    if self.trade_state == "NEUTRAL" or self.trade_state == "BOUGHT":
                        self.dosell(ask[0])
                        self.trade_state = "SOLD"
                self.predict_time = time.time()
            except:
                print(get_full_stacktrace())

        for ask in asks_:
            self.tableWidgetAsks.setRowHeight(i, 23)
            self.tableWidgetBids.setRowHeight(i, 23)
            price = str(accounts.client(self.exchange).price_to_precision(self.symbol, ask[0]))
            amount = str(accounts.client(self.exchange).amount_to_precision(self.symbol, ask[1]))
            sum = sum + ask[1]
            sum_str = str(accounts.client(self.exchange).amount_to_precision(self.symbol, sum))
            if self.exchange == accounts.EXCHANGE_KRAKEN:
                amount = self.kraken_prettify_value(amount)
                sum_str = self.kraken_prettify_value(sum_str)

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
            columnItem.setFont(self.font)
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
            columnItem.setFont(self.font)
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
            columnItem.setFont(self.font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetAsks.setItem(i, 2, columnItem)
            i = i + 1

        if self.orderbookWidthAdjusted == False and len(bids_) > 0 and len(bids_[0]) > 0:
            self.tableWidgetBids.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
            self.tableWidgetAsks.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
            self.tableWidgetBids.show()
            self.tableWidgetAsks.show()
            self.tableWidgetTrades.show()
            self.setMinimumWidth(self.width())
            self.setMaximumWidth(self.width())
            header = self.tableWidgetBids.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
            header = self.tableWidgetAsks.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
            self.orderbookWidthAdjusted = True

    @QtCore.pyqtSlot(list)
    def on_DISPLAY_TRADES(self, trades_list):
        global train_input
        global train_output
        self.tableWidgetTrades.setRowCount(len(self.trades_list))

        i = 0
        for trade in reversed(trades_list):
            trade_time = trade[0]
            trade_price = trade[1]
            trade_quantity = trade[2]
            trade_buy_maker = not trade[3]
            trade_time_pretty = prettydate.date(datetime.datetime.fromtimestamp(trade_time))

            if trade_buy_maker == True:
                trade = 1
            else:
                trade = 0
            train_input.append([trade_price, trade_quantity])
            train_output.append(trade)


            if time.time() - self.percent_check_time > 60:
                total, available, percent, used, free = psutil.virtual_memory()
                available_megabyte = available / (1024*1024)
                process = psutil.Process(os.getpid())
                process_rss_megabyte = process.memory_full_info().rss / (1024*1024)
                if (process_rss_megabyte * 100) / available_megabyte > 80:
                    del train_input[:int(len(train_input)*0.25)]
                    del train_output[:int(len(train_output)*0.25)]
                self.percent_check_time = time.time()

            '''
            if time.time() - self.train_time > 60*60*12:
                self.train_time = time.time()
                del train_input[:int(len(train_input)/2)]
                del train_output[:int(len(train_output)/2)]
            '''

            self.tableWidgetTrades.setRowHeight(i, 23)
            trade_price = str(accounts.client(self.exchange).price_to_precision(self.symbol, trade_price))
            trade_quantity = str(accounts.client(self.exchange).amount_to_precision(self.symbol, trade_quantity))

            columnItem = QtWidgets.QTableWidgetItem(str(trade_time_pretty))
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if trade_buy_maker == True:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(self.font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetTrades.setItem(i, 0, columnItem)

            columnItem = QtWidgets.QTableWidgetItem(trade_price)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if trade_buy_maker == True:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(self.font)
            columnItem.setFlags(QtCore.Qt.NoItemFlags)
            self.tableWidgetTrades.setItem(i, 1, columnItem)

            columnItem = QtWidgets.QTableWidgetItem(trade_quantity)
            columnItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            if trade_buy_maker == True:
                columnItem.setBackground(QtGui.QColor(17, 122, 101))
            else:
                columnItem.setBackground(QtGui.QColor(146, 43, 33))
            columnItem.setForeground(QtGui.QColor(208, 211, 212))
            columnItem.setFont(self.font)
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
        if self.exchange == accounts.EXCHANGE_KRAKEN:
            if isinstance(msg, dict) and "channelID" in msg:
                self.websocket_alive_time = time.time()
                self.wss_orderbook = {}
                self.wss_orderbook["bids"] = {}
                self.wss_orderbook["asks"] = {}
                self.wss_chanid = msg["channelID"]
                return
            elif self.wss_chanid != -1 and isinstance(msg, list) and msg[0] == self.wss_chanid:
                self.websocket_alive_time = time.time()

                if isinstance(msg, list) and isinstance(msg[1], dict) and "as" in msg[1].keys() and "a" not in msg[1].keys() \
                        and isinstance(msg[1]["as"], list) and len(msg[1]["as"]) > 0:
                    # create in memory orderbook
                    for order in msg[1]["bs"]:
                        price = float(order[0])
                        volume = float(order[1])
                        self.wss_orderbook["bids"][price] = volume
                    for order in msg[1]["as"]:
                        price = float(order[0])
                        volume = float(order[1])
                        self.wss_orderbook["asks"][price] = volume

                elif isinstance(msg, list) and isinstance(msg[1], dict) and "a" in msg[1] or "b" in msg[1]:
                    # update in memory orderbook
                    bids = []
                    asks = []

                    if "a" in msg[1].keys():
                        asks = msg[1]["a"]
                    elif "b" in msg[1].keys():
                        bids = msg[1]["b"]

                    if len(msg) > 2 and isinstance(msg[2], dict) and ("a" in msg[2].keys() or "b" in msg[2].keys()):
                        if "a" in msg[2].keys():
                            asks = msg[2]["a"]
                        elif "b" in msg[2].keys():
                            bids = msg[2]["b"]

                    for order in bids:
                        price = float(order[0])
                        volume = float(order[1])
                        if volume != 0:
                            self.wss_orderbook["bids"][price] = volume
                        else:
                            del self.wss_orderbook["bids"][price]
                    for order in asks:
                        price = float(order[0])
                        volume = float(order[1])
                        if volume != 0:
                            self.wss_orderbook["asks"][price] = volume
                        else:
                            del self.wss_orderbook["asks"][price]

                else:
                    return

            tab_index = get_tab_index(self.winid)
            if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
                return

            if self.parent.tabWidget.currentIndex() != tab_index:
                return

            if self.orderbook_time_shown != 0 and time.time() - self.orderbook_time_shown < 1:
                return

            bids = []
            asks = []
            for order in sorted(self.wss_orderbook["bids"], reverse=True):
                bids.append([order, self.wss_orderbook["bids"][order]])
            for order in sorted(self.wss_orderbook["asks"]):
                asks.append([order, self.wss_orderbook["asks"][order]])

            self.DISPLAY_ORDERBOOK.emit(bids[:25], asks[:25])
            self.orderbook_time_shown = time.time()
            return

        elif self.exchange == accounts.EXCHANGE_BITFINEX:
            if isinstance(msg, dict) and "chanId" in msg:
                self.websocket_alive_time = time.time()
                self.wss_orderbook = {}
                self.wss_orderbook["bids"] = {}
                self.wss_orderbook["asks"] = {}
                self.wss_chanid = msg["chanId"]
                return
            elif self.wss_chanid != -1 and isinstance(msg, list) and msg[0] == self.wss_chanid:
                self.websocket_alive_time = time.time()

                if isinstance(msg[1], list) and len(msg[1]) > 0 and isinstance(msg[1][0], list) and len(msg[1][0]) > 0:
                    #create in memory orderbook
                    for order in msg[1]:
                        price = float(order[0])
                        count = int(order[1])
                        amount = float(order[2])
                        if amount > 0:
                            self.wss_orderbook["bids"][price] = [count, amount]
                        else:
                            self.wss_orderbook["asks"][price] = [count, amount * -1]
                elif isinstance(msg[1], list) and len(msg[1]) > 0:
                    #update in memory orderbook
                    order = msg[1]
                    price = float(order[0])
                    count = int(order[1])
                    amount = float(order[2])

                    if count == 0:
                        if amount == 1:
                            del self.wss_orderbook["bids"][price]
                        elif amount == -1:
                            del self.wss_orderbook["asks"][price]
                    elif count > 0:
                        if amount > 0:
                            self.wss_orderbook["bids"][price] = [count, amount]
                        elif amount < 0:
                            self.wss_orderbook["asks"][price] = [count, amount * -1]
                else:
                    return

            tab_index = get_tab_index(self.winid)
            if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
                return

            if self.parent.tabWidget.currentIndex() != tab_index:
                return

            if self.orderbook_time_shown != 0 and time.time() - self.orderbook_time_shown < 1:
                return

            bids = []
            asks = []

            for order in sorted(self.wss_orderbook["bids"], reverse=True):
                bids.append([order, self.wss_orderbook["bids"][order][1]])
            for order in sorted(self.wss_orderbook["asks"]):
                asks.append([order, self.wss_orderbook["asks"][order][1]])

            self.DISPLAY_ORDERBOOK.emit(bids, asks)
            self.orderbook_time_shown = time.time()
            return

        elif self.exchange == accounts.EXCHANGE_BINANCE:
            #msg is a python-binance depth cache instance
            if msg is not None:
                self.websocket_alive_time = time.time()

                tab_index = get_tab_index(self.winid)
                if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
                    return

                if self.parent.tabWidget.currentIndex() != tab_index:
                    return
                if self.orderbook_time_shown != 0 and time.time() - self.orderbook_time_shown < 1:
                    return

                bids_ = msg.get_bids()[:25]
                asks_ = msg.get_asks()[:25]
                self.DISPLAY_ORDERBOOK.emit(bids_, asks_)
                self.orderbook_time_shown = time.time()
                return
            else:
                self.restart_websocket()
                return

    def process_message_trades(self, msg):
        if self.exchange == accounts.EXCHANGE_KRAKEN:
            if isinstance(msg, dict) and "channelID" in msg:
                self.websocket_alive_time = time.time()
                self.wss_chanid_trades = msg["channelID"]
                return
            elif self.wss_chanid_trades != -1 and isinstance(msg, list) and msg[0] == self.wss_chanid_trades:
                self.websocket_alive_time_trades = time.time()

                if isinstance(msg[1], list) and len(msg[1]) > 0 and isinstance(msg[1][0], list) and len(msg[1][0]) > 0:
                    for trade in msg[1]:
                        trade_time = int(float(trade[2]))
                        trade_price = float(trade[0])
                        trade_quantity = float(trade[1])
                        trade_buy_maker = trade[3] == "s"
                        self.trades_list.append([trade_time, trade_price, trade_quantity, trade_buy_maker])

                    tab_index = get_tab_index(self.winid)
                    if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
                        return

                    if self.parent.tabWidget.currentIndex() != tab_index:
                        return

                    self.DISPLAY_TRADES.emit(self.trades_list)
                    return
        elif self.exchange == accounts.EXCHANGE_BITFINEX:
            if isinstance(msg, dict) and "chanId" in msg:
                self.websocket_alive_time = time.time()
                self.wss_chanid_trades = msg["chanId"]
                return
            elif self.wss_chanid_trades != -1 and isinstance(msg, list) and msg[0] == self.wss_chanid_trades:
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

                    tab_index = get_tab_index(self.winid)
                    if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
                        return

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

                    tab_index = get_tab_index(self.winid)
                    if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
                        return

                    if self.parent.tabWidget.currentIndex() != tab_index:
                        return

                    self.DISPLAY_TRADES.emit(self.trades_list)
                    return

        elif self.exchange == accounts.EXCHANGE_BINANCE:
            if isinstance(msg, dict) and "T" in msg:
                self.websocket_alive_time_trades = time.time()
                trade_time = msg["T"] / 1000
                trade_price = float(msg["p"])
                trade_quantity = float(msg["q"])
                trade_buy_maker = msg["m"]
                self.trades_list.append([trade_time, trade_price, trade_quantity, trade_buy_maker])

                if len(self.trades_list) > 100:
                    self.trades_list.pop(0)

                tab_index = get_tab_index(self.winid)
                if tab_index == INTERNAL_TAB_INDEX_NOTFOUND:
                    return

                if self.parent.tabWidget.currentIndex() != tab_index:
                    return

                self.DISPLAY_TRADES.emit(self.trades_list)
                return

    def update_trades_display(self):
        self.on_DISPLAY_TRADES(self.trades_list)

    def init_orderbook_widget(self):
        newfont = QtGui.QFont("Courier New")
        self.setFont(newfont)
        self.setStyleSheet("QLabel { background-color : #131D27; color : #C6C7C8; }")
        if self.exchange == accounts.EXCHANGE_BITFINEX:
            self.exchange_obj = exchanges.Bitfinex(accounts.exchanges[accounts.EXCHANGE_BITFINEX]["markets"], \
                                                   accounts.exchanges[accounts.EXCHANGE_BITFINEX]["api_key"], \
                                                   accounts.exchanges[accounts.EXCHANGE_BITFINEX]["api_secret"])
        elif self.exchange == accounts.EXCHANGE_BINANCE:
            self.exchange_obj = exchanges.Binance(accounts.exchanges[accounts.EXCHANGE_BINANCE]["markets"], \
                                                  accounts.exchanges[accounts.EXCHANGE_BINANCE]["api_key"], \
                                                  accounts.exchanges[accounts.EXCHANGE_BINANCE]["api_secret"])
        elif self.exchange == accounts.EXCHANGE_KRAKEN:
            self.exchange_obj = exchanges.Kraken(accounts.exchanges[accounts.EXCHANGE_KRAKEN]["markets"])
        self.exchange_obj.start_depth_websocket(self.symbol, self.process_message)
        self.exchange_obj.start_trades_websocket(self.symbol, self.process_message_trades)

def closeSplashScreen():
    # close opened splash screen
    if platform.system() == "Windows":
        import win32gui

        window_handle = win32gui.FindWindow("WavetrendSplash", None)
        if window_handle != 0:
            win32gui.EndDialog(window_handle, 0)

def showQtMessageMissingExchanges():
    closeSplashScreen()
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText("Please configure valid exchanges.")
    msg.setInformativeText("Edit the config.txt file and add your exchanges api keys.")
    msg.setWindowTitle("Missing exchanges")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

def showQtMessageMissingExchangesConfig():
    closeSplashScreen()
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText("Please configure valid exchanges.")
    msg.setInformativeText("Edit the config.txt file and add your exchanges api keys.\n" + \
            "The configuration file config.txt might be corrupted or does not exist.")
    msg.setWindowTitle("Missing configuration")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

def get_tab_index(winid):
    found = False
    for tab_index in window_ids:
        if winid == window_ids[tab_index]:
            found = True
            break
    if found == True:
        return tab_index
    else:
        return "NOTFOUND"

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    config = {}
    try:
        exec (open("config.txt").read(), config)
    except:
        showQtMessageMissingExchangesConfig()
        sys.exit(1)

    exchanges_ = config["exchanges"].copy()

    active_count = 0
    exchange = ""
    for exchange_name in exchanges_:
        if "api_key" in config["exchanges"][exchange_name] and \
                "api_secret" in config["exchanges"][exchange_name] \
                and len(config["exchanges"][exchange_name]["api_key"]) > 5 \
                and len(config["exchanges"][exchange_name]["api_secret"]) > 5:
            active_count = active_count + 1

    if active_count == 0:
        showQtMessageMissingExchanges()
        sys.exit(1)

    exchanges_list = []

    for exchange_name in exchanges_:
        if "api_key" in config["exchanges"][exchange_name] and "api_secret" in \
                config["exchanges"][exchange_name]:
            api_key = config["exchanges"][exchange_name]["api_key"]
            api_secret = config["exchanges"][exchange_name]["api_secret"]
            if len(api_key) > 5 and len(api_secret) > 5:
                exchanges_list.append([exchange_name, api_key, api_secret])

    accounts = ExchangeAccounts(exchanges_list)
    accounts.initialize()

    with open("style.qss","r") as fh:
        app.setStyleSheet(fh.read())

    if platform.system() == "Linux":
        new_font = QtGui.QFont()
        new_font.setPointSize(10)
        app.setFont(new_font)

    dialog = Dialog()
    dialog.show()
    os._exit(app.exec_())
