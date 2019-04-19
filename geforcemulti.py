import warnings
warnings.filterwarnings("ignore")
import matplotlib
import matplotlib.style
matplotlib.use("QT4Agg")
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import ctypes
from matplotlib.transforms import Bbox
from matplotlib import cbook
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_qt5 import (
    QtCore, QtGui, QtWidgets, _BackendQT5, FigureCanvasQT, FigureManagerQT,
    NavigationToolbar2QT, backend_version)
from matplotlib.backends.qt_compat import QT_API
from matplotlib.figure import Figure
import matplotlib.ticker as matplotlib_ticker
from matplotlib.dates import date2num
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import sys
import time
import datetime
from PyQt4 import QtGui, QtCore, uic
import traceback
import copy
import threading
import math
import os
import queue as Queue
import ccxt
from indicators import *
from colors import *
import decimal
import random
import functools
import exchanges

class FigureCanvas(FigureCanvasAgg, FigureCanvasQT):

    def __init__(self, figure):
        # Must pass 'figure' as kwarg to Qt base class.
        super().__init__(figure=figure)

    def _unmultiplied_rgba8888_to_premultiplied_argb32(self, rgba8888):
        """
        Convert an unmultiplied RGBA8888 buffer to a premultiplied ARGB32 buffer.
        """
        if sys.byteorder == "little":
            argb32 = np.take(rgba8888, [2, 1, 0, 3], axis=2)
            rgb24 = argb32[..., :-1]
            alpha8 = argb32[..., -1:]
        else:
            argb32 = np.take(rgba8888, [3, 0, 1, 2], axis=2)
            alpha8 = argb32[..., :1]
            rgb24 = argb32[..., 1:]
        # Only bother premultiplying when the alpha channel is not fully opaque,
        # as the cost is not negligible.  The unsafe cast is needed to do the
        # multiplication in-place in an integer buffer.
        #if alpha8.min() != 0xff: # XXX performance lagging
        #    np.multiply(rgb24, alpha8 / 0xff, out=rgb24, casting="unsafe")
        return argb32

    def paintEvent(self, event):
        """Copy the image from the Agg canvas to the qt.drawable.
        In Qt, all drawing should be done inside of here when a widget is
        shown onscreen.
        """
        if self._update_dpi():
            # The dpi update triggered its own paintEvent.
            return

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
        buf = self._unmultiplied_rgba8888_to_premultiplied_argb32(memoryview(reg))

        painter.eraseRect(rect)

        qimage = QtGui.QImage(buf, buf.shape[1], buf.shape[0],
                              QtGui.QImage.Format_ARGB32_Premultiplied)
        if hasattr(qimage, 'setDevicePixelRatio'):
            # Not available on Qt4 or some older Qt5.
            qimage.setDevicePixelRatio(self._dpi_ratio)
        origin = QtCore.QPoint(left, top)
        painter.drawImage(origin / self._dpi_ratio, qimage)

        painter.end()

matplotlib.backends.backend_qt4agg.FigureCanvasQTAgg = FigureCanvas

conf = {}
exec(open("config.txt").read(), conf)

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
   'enableRateLimit': True,
   'options': {'adjustForTimeDifference': True}
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
  print("Please configure a valid Exchange.")
  sys.exit(1)

ticker = client.fetch_tickers()
is_usdt = False
if "BTC/USDT" in ticker:
  is_usdt = True

markets = client.fetch_markets()

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

CHART_DATA_READY = 1
SHOW_STATUSBAR_MESSAGE = 0
CANDLE_TYPE_CANDLESTICK = 0
CANDLE_TYPE_HEIKIN_ASHI = 1
TRADE_TYPE_TRENDING = 0
TRADE_TYPE_OSC = 1

tab_current_index = None
destroyed_window_ids = {}

DataRunnerTabs = {}

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
    def __init__(self, parent=None, dpi=100, symbol=None):
        self.fig = Figure(facecolor=black, edgecolor=white, dpi=dpi,
                          frameon=False, tight_layout=False, constrained_layout=False)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

main_shown = False

class DataRunner:
  def __init__(self, parent, symbol, tab_index, timeframe_entered):
    self.symbol = symbol
    self.tab_index = tab_index
    self.parent = parent
    self.timeframe_entered = timeframe_entered
    self.exchange_obj = exchanges.Binance(api_key, api_secret)
    self.exchange_obj.start_candlestick_websocket(symbol, timeframe_entered, self.process_message)

  def process_message(self, msg):
    if self.parent.tabWidget.currentIndex() != self.tab_index:
        return

    if msg["e"] == "kline":
        open_ = float(msg["k"]["o"])
        high = float(msg["k"]["h"])
        low = float(msg["k"]["l"])
        close = float(msg["k"]["c"])
        volume = float(msg["k"]["v"])
        dt = datetime.datetime.fromtimestamp(msg["k"]["t"] / 1000)
        time_close = msg["k"]["T"] / 1000

        result = [dt, time_close, open_, high, low, close, volume, 1]

        if dqs[self.tab_index].empty() == True:
            dqs[self.tab_index].put(CHART_DATA_READY)
            dqs[self.tab_index].put(result)

class ChartRunner(QtCore.QThread):
  RETRIEVE_CHART_DATA = QtCore.pyqtSignal(str)
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
    time_close = 0

    while True:
        try:
          candle_type = window_configs[self.tab_index].candle_type
          trade_type = window_configs[self.tab_index].trade_type

          if first == True:
            date, open_, high, low, close, vol, limit = self.getData(timeframe_entered, days_entered, symbol, False)
          else:
            self.RETRIEVE_CHART_DATA.emit(self.tab_index)
            chart_result = aqs[self.tab_index].get()
            if chart_result != 0:
              [date2, time_close2, open2_, high2, low2, close2, vol2, limit2] = chart_result
              [date3, time_close3, open3_, high3, low3, close3, vol3, limit3] = chart_result
              if time_close == 0:
                  time_close = time_close2
            else:
              try:
                date2
              except (NameError, UnboundLocalError) as e:
                try:
                 date3
                 [date2, time_close2, open2_, high2, low2, close2, vol2, limit2] = [date3, time_close3, open3_,
                                                                                    high3, low3, close3,
                                                                                    vol3, limit3]
                except (NameError, UnboundLocalError) as e:
                    [date2, time_close2, open2_, high2, low2, close2, vol2, limit2] = \
                        [date[-1], time_close, open_[-1], high[-1], low[-1], close[-1], vol[-1], limit]

          if first == True:
            self.FIGURE_ADD_SUBPLOT.emit(self.tab_index, 111, None)
            ax = aqs[self.tab_index].get()
            len_candles = len(date)
            
            prices[:] = []
            for i in range(0, len(date)):
                prices.append((date2num(date[i]), open_[i], high[i], low[i], close[i], vol[i], date[i]))

            dates2 = [x[0] for x in prices]
                        
            ax.xaxis.set_tick_params(labelsize=9)
            ax.yaxis.set_tick_params(labelsize=9)
          else:
            prices[-1] = (date2num(date2), open2_, high2, low2, close2, vol2, date2)

          if (first == False and time_close != 0 and time.time() >= time_close)  \
            or current_candle_type != candle_type or current_trade_type != trade_type:
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
            time_close = 0
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
          for indicator in indicators:
            if first == True:
              indicator.generate_values(open_, high, low, close, vol)
              if indicator.overlay_chart:
                indicator.plot_once(ax, dates2)
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
                indicator.plot_once(new_ax, dates2)
            else:
              open_[-1] = open2_
              high[-1] = high2
              low[-1] = low2
              close[-1] = close2
              vol[-1] = vol2
              indicator.generate_values(open_, high, low, close, vol)
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
              date_list    = range(0, len(open_))
              open_list    = copy.deepcopy(open_)
              close_list   = copy.deepcopy(close)
              high_list    = copy.deepcopy(high)
              low_list     = copy.deepcopy(low)
              volume_list  = copy.deepcopy(vol)
              elements        = len(open_)

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
              open_list[-1]    = open_[-1]
              close_list[-1]   = close[-1]
              high_list[-1]    = high[-1]
              low_list[-1]     = low[-1]
              volume_list[-1]  = vol[-1]
              
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
            
            ax.yaxis.set_major_locator(matplotlib_ticker.MultipleLocator((highest_price-lowest_price)/20))
            ax.set_ylim((lowest_price - lowest_price * 0.015, highest_price + highest_price * 0.015))
            
            xl = ax.get_xlim()
            ax.set_xlim(date[start_x], xl[1])

          ticker = prices[-1][4]
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

            self.CANVAS_GET_SIZE.emit(self.tab_index, annotation)
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
            if timeframe_entered in ["1m", "5m", "15m", "30m", "1h"]:            
              time_annotation.set_text(time_to_hour)
              time_annotation.set_bbox(dict(facecolor=black, edgecolor=white, lw=.5))
              time_annotation.set_y(ticker_for_line - y0)

          if init == True:
            xl = ax.get_xlim()
            candle_width = ((dbox.x0 - xl[0]) / limit) * 0.8
          if first == True:
            for i in range(0, len(indicators)):
              if indicators[i].name == "MACD" or indicators[i].name == "VOLUME":
                indicators[i].candle_width = candle_width
                indicators[i].update()
          
          if current_candle_type == CANDLE_TYPE_CANDLESTICK:
            last_line1, last_line2, last_rect = _candlestick(ax, prices, first, last_line1, last_line2, last_rect, candle_width)
          elif current_candle_type == CANDLE_TYPE_HEIKIN_ASHI:        
            last_line1, last_line2, last_rect = _candlestick(ax, prices2, first, last_line1, last_line2, last_rect, candle_width)
          
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

          first = False

          do_break = False
          while True:
              if tab_index in destroyed_window_ids:
                  do_break = True
                  break

              self.CANVAS_DRAW.emit(self.tab_index)
              return_value = aqs[tab_index].get()
              if return_value == 0:
                  break

          if do_break == True:
            break

        except:
          print(get_full_stacktrace())
          
        init = False

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

class Window(QtGui.QMainWindow):
    global tab_widgets
    global config
    global window_ids
    def __init__(self, symbol, timeframe_entered):
        global selected_symbol
        global DataRunnerTabs
        QtGui.QMainWindow.__init__(self)
        resolution = QtGui.QDesktopWidget().screenGeometry()
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
        tabBarMenu = QtGui.QMenu()
        closeAction = QtGui.QAction("close", self)
        tabBarMenu.addAction(closeAction)
        closeAction.triggered.connect(functools.partial(self.removeTab, window_ids[0]))
        menuButton = QtGui.QToolButton(self)
        menuButton.setStyleSheet('border: 0px; padding: 0px;')
        menuButton.setPopupMode(QtGui.QToolButton.InstantPopup)
        menuButton.setMenu(tabBarMenu)
        self.tabBar.setTabButton(0, QtGui.QTabBar.RightSide, menuButton)

        widget = QtGui.QHBoxLayout(self.tabWidget.widget(0))
        self.OrderbookWidget = []
        OrderBookWidget_ = OrderBookWidget(self, symbol, 0)
        self.OrderbookWidget.append(OrderBookWidget_)
        dc = MplCanvas(self.tabWidget.widget(0), symbol=symbol)
        widget.addWidget(dc)
        widget.addWidget(OrderBookWidget_, alignment=QtCore.Qt.AlignTop)
        widget.setContentsMargins(0,0,0,0)

        self.dcs = {}
        self.dcs[window_id] = dc
        
        global qsb
        global aqs
        global dqs
        qs[window_id] = Queue.Queue()
        aqs[window_id] = Queue.Queue()
        dqs[window_id] = Queue.Queue()

        DataRunnerTabs[window_id] = DataRunner(self, symbol, window_id, timeframe_entered)

        self.chart_runner_thread = ChartRunner(self, symbol, window_id, timeframe_entered)
        self.chart_runner_thread.RETRIEVE_CHART_DATA.connect(self.on_RETRIEVE_CHART_DATA)
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
            print(str(amount) + " " + str(price))
            client.create_limit_buy_order(self.symbol, amount, price)
            return
      except:
        print(get_full_stacktrace())
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

    @QtCore.pyqtSlot(str)
    def on_RETRIEVE_CHART_DATA(self, winid):
        global aqs
        if winid in dqs:
            if dqs[winid].qsize() > 0:
                value = dqs[winid].get(block=False)
                if value == CHART_DATA_READY:
                    chart_result = dqs[winid].get()
                    aqs[winid].put(chart_result)
            else:
                aqs[winid].put(0)

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

    @QtCore.pyqtSlot(str, dict, matplotlib.axes.Axes)
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

        if QtGui.QApplication.activeWindow() == self.window() and self.tabWidget.currentIndex() == tab_index:
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
        self.tabWidget.removeTab(tab_index)

        global DataRunnerTabs
        DataRunnerTabs[winid].exchange_obj.stop_candlestick_websocket()
        del DataRunnerTabs[winid].exchange_obj
        del DataRunnerTabs[winid]

        self.OrderbookWidget[tab_index].exchange_obj.stop_depth_websocket()
        del self.OrderbookWidget[tab_index].exchange_obj
        del self.OrderbookWidget[tab_index]

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
      
    def removeTab(self, window_id):
      global destroyed_window_ids
      destroyed_window_ids[window_id] = "DESTROYED"

    def addTab(self, symbol, timeframe_entered):
      global tab_current_index
      global DataRunnerTabs

      self.tab_widgets.append(QtGui.QWidget())
      tab_index = self.tabWidget.addTab(self.tab_widgets[-1], symbol + " " + timeframe_entered)
      self.tabWidget.setCurrentWidget(self.tab_widgets[-1])
      main.tabWidget.setTabIcon(tab_index, QtGui.QIcon("coin.ico"))
      widget = QtGui.QHBoxLayout(self.tabWidget.widget(tab_index))

      window_id = get_window_id()
      window_ids[tab_index] = window_id
      window_configs[window_id] = abstract()
      window_configs[window_id].candle_type = CANDLE_TYPE_CANDLESTICK
      window_configs[window_id].trade_type = TRADE_TYPE_TRENDING
      
      tabBarMenu = QtGui.QMenu()
      closeAction = QtGui.QAction("close", self)
      tabBarMenu.addAction(closeAction)
      closeAction.triggered.connect(functools.partial(self.removeTab, window_ids[tab_index]))      
      menuButton = QtGui.QToolButton(self)
      menuButton.setStyleSheet('border: 0px; padding: 0px;')
      menuButton.setPopupMode(QtGui.QToolButton.InstantPopup)
      menuButton.setMenu(tabBarMenu)      
      self.tabBar.setTabButton(tab_index, QtGui.QTabBar.RightSide, menuButton)

      OrderBookWidget_ = OrderBookWidget(self, symbol, tab_index)
      self.OrderbookWidget.append(OrderBookWidget_)
      dc = MplCanvas(self.tabWidget.widget(0), symbol=symbol)
      widget.addWidget(dc)
      widget.addWidget(OrderBookWidget_, alignment=QtCore.Qt.AlignTop)
      widget.setContentsMargins(0, 0, 0, 0)

      global qs
      global aqs
      global dqs
      
      qs[window_id] = Queue.Queue()
      aqs[window_id] = Queue.Queue()
      dqs[window_id] = Queue.Queue()
      self.dcs[window_id] = dc

      DataRunnerTabs[window_id] = DataRunner(self, symbol, window_id, timeframe_entered)

      tab_current_index = window_id

      self.chart_runner_thread = ChartRunner(self, symbol, window_id, timeframe_entered)
      self.chart_runner_thread.RETRIEVE_CHART_DATA.connect(self.on_RETRIEVE_CHART_DATA)
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
      
class TradeDialog(QtGui.QDialog):
  def __init__(self, parent):
    self.parent = parent
    QtGui.QDialog.__init__(self)
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
    amount = truncate(float(self.editAmount.text()), 2)
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
    amount = truncate(float(self.editAmount2.text()), 2)
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

class Dialog(QtGui.QDialog):
    global config
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uic.loadUi('windowqt.ui', self)
        self.setFixedSize(555, 575)
        self.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
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

class OrderBookWidget(QtGui.QLabel):
    def __init__(self, parent, symbol, tab_index):
        super(OrderBookWidget,self).__init__(parent)
        self.parent = parent
        self.tab_index = tab_index
        self.symbol = symbol
        self.init_orderbook_widget()

    def process_message(self, msg):
        if self.parent.tabWidget.currentIndex() != self.tab_index:
            return

        if "bids" in msg:
            bids_ = msg["bids"]
            asks_ = msg["asks"]

            strs = []
            for bid in bids_:
                try:
                    ask = asks_.pop()
                    if not self.symbol.endswith("BTC"):
                        if self.symbol == "BTC/USDT":
                            ask[0] = "%.2f" % float(ask[0])
                        else:
                            ask[0] = "%.4f" % float(ask[0])
                        asks = str(ask[0]) + " " * (9 - len(str(ask[0]))) + str(ask[1])
                    else:
                        ask[1] = "%.2f" % float(ask[1])
                        asks = "%.8f" % float(ask[0]) + " " * (10 - len(str(ask[1]))) + str(ask[1])
                except:
                    asks = ""
                if not self.symbol.endswith("BTC"):
                    if self.symbol == "BTC/USDT":
                        bid[0] = "%.2f" % float(bid[0])
                    else:
                        bid[0] = "%.4f" % float(bid[0])
                    strs.append(str(bid[0]) + " " * (9 - len(str(bid[0]))) + str(bid[1]) + "\t" + asks)
                else:
                    bid[1] = "%.2f" % float(bid[1])
                    strs.append("%.8f" % float(bid[0]) + " " + " " * (
                                10 - len(str(bid[1]))) + str(bid[1]) + "\t" + asks)

            bookstr = ""
            for s in strs:
                bookstr = bookstr + s + "\n"

            self.setText(bookstr)

    def init_orderbook_widget(self):
        self.setMinimumWidth(337)
        newfont = QtGui.QFont("Courier New", 9, QtGui.QFont.Bold) 
        self.setFont(newfont)
        self.setText("Orderbook Loading...")
        self.setStyleSheet("QLabel { background-color : #131D27; color : #C6C7C8; }")
        self.exchange_obj = exchanges.Binance(api_key, api_secret)
        self.exchange_obj.start_depth_websocket(self.symbol, self.process_message)

if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  with open("style.qss","r") as fh:
    app.setStyleSheet(fh.read())
  dialog = Dialog()
  dialog.show()
  os._exit(app.exec_())

