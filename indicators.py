import talib
import numpy as np
from colors import *
import copy
import pandas as pd

class indicator_DMI:
  def __init__(self):
    self.name = "DMI"
    self.overlay_chart = False
    self.first = True
  
  def generate_values(self, open_, high, low, close, volume):
    self.plus_di_values = talib.PLUS_DI(np.array(high), np.array(low), np.array(close))
    self.minus_di_values = talib.MINUS_DI(np.array(high), np.array(low), np.array(close))
    self.adx_values = talib.ADX(np.array(high), np.array(low), np.array(close))

  def get_adx_trend_str(self, adx_value):
    adx_str = ""
    if adx_value <= 25:
      adx_str = "Absent or Weak Trend"
    elif adx_value > 25 and adx_value <= 50:
      adx_str = "Strong Trend"
    elif adx_value > 50 and adx_value <= 75:
      adx_str = "Very Strong Trend"
    elif adx_value > 75:
      adx_str = "Extremely Strong Trend"
    return adx_str

  def plot_once(self, axis, dates):
    self.axis = axis
    self.dates = dates
    self.plus_di = axis.plot(self.dates, self.plus_di_values, color=blue, lw=.7, label="+DI=" + str(int(self.plus_di_values[-1])))
    self.minus_di = axis.plot(self.dates, self.minus_di_values, color=orange, lw=.7, label="-DI=" + str(int(self.minus_di_values[-1])))

    self.adx = axis.plot(self.dates, self.adx_values, color=red, lw=.7, label="ADX=" + str(int(self.adx_values[-1])) + "\n" + self.get_adx_trend_str(int(self.adx_values[-1])))
    self.legend = axis.legend(loc="upper left", facecolor=darkish, edgecolor=darkish, fontsize=8)
    for text in self.legend.get_texts():
      text.set_color("white")
  
  def update(self):
    self.plus_di[0].set_ydata(self.plus_di_values)
    self.minus_di[0].set_ydata(self.minus_di_values)
    self.adx[0].set_ydata(self.adx_values)
    for text in self.legend.get_texts():
      if "+DI" in text.get_text():
        text.set_text("+DI=" + str(int(self.plus_di_values[-1])))
      if "-DI" in text.get_text():
        text.set_text("-DI=" + str(int(self.minus_di_values[-1])))
      if "ADX" in text.get_text():
        text.set_text("ADX=" + str(int(self.adx_values[-1])) + "\n" + self.get_adx_trend_str(int(self.adx_values[-1])))
  
  def xaxis_get_start(self):
    if self.first == True:
      start_x = 0
      self.first = False
      for i in range(0, len(self.adx_values)):
          if not np.isnan(self.adx_values[i]):
            start_x = i
            break
      return start_x
    else:
      return 0

class indicator_BBANDS():
  def __init__(self, better_bbands):
    self.name="BBANDS"
    self.overlay_chart = True
    self.better_bbands = better_bbands
    self.first = True

  def generate_values(self, open_, high, low, close, volume):
    if self.better_bbands == False:
      self.bb_upper, self.bb_middle, self.bb_lower = talib.BBANDS(np.array(close) * 10000, timeperiod=20)
    else:
      self.bb_upper, self.bb_middle, self.bb_lower = talib.BBANDS(np.array(close) * 10000, timeperiod=15, nbdevup=2.0, nbdevdn=2.0)
    self.bb_upper = self.bb_upper / 10000
    self.bb_middle = self.bb_middle / 10000
    self.bb_lower = self.bb_lower / 10000
    
  def plot_once(self, axis, dates):
    self.bb_upper_ = axis.plot(dates, self.bb_upper, color=greenish, lw=.5, antialiased=True)
    self.bb_middle_ = axis.plot(dates, self.bb_middle, color=red, lw=.5, antialiased=True)
    self.bb_lower_ = axis.plot(dates, self.bb_lower, color=greenish, lw=.5, antialiased=True)
    axis.fill_between(dates, self.bb_lower, self.bb_upper, where=self.bb_upper >= self.bb_lower, facecolor=greenish, interpolate=True, alpha=.05)
  
  def update(self):
    self.bb_upper_[0].set_ydata(self.bb_upper)
    self.bb_middle_[0].set_ydata(self.bb_middle)
    self.bb_lower_[0].set_ydata(self.bb_lower)

  def xaxis_get_start(self):
    if self.first == True:
      start_x = 0
      self.first = False
      for i in range(0, len(self.bb_upper)):
          if not np.isnan(self.bb_upper[i]):
            start_x = i
            break
      return start_x
    else:
      return 0

  def in_keltner(self, axis, dates, keltner_upper, keltner_lower, lowest_price):
    in_keltner_channel = False
    in_keltner_channel_index = -1
    for i in range(0, len(self.bb_upper)):
      if i != len(dates)-1 and self.bb_upper[i] - keltner_upper[i] < 0 and keltner_lower[i] - self.bb_lower[i] < 0:
        axis.annotate("*", xy=(dates[i], keltner_upper[i]), xycoords="data", fontsize=6, color=white, weight="bold")
        axis.annotate("*", xy=(dates[i], keltner_lower[i]), xycoords="data", fontsize=6, color=white, weight="bold")
        if in_keltner_channel == False and i - in_keltner_channel_index > 5:
          axis.annotate("Squeeze", (dates[i], lowest_price), fontsize=6, color=white, weight="bold", ha='center', va='center')
          in_keltner_channel = True
          in_keltner_channel_index = i
      else:
        in_keltner_channel = False

  def in_keltner_now(self, axis, dates, keltner_upper, keltner_lower, lowest_price):
    if self.bb_upper[-1] - keltner_upper < 0 and keltner_lower - self.bb_lower[-1] < 0:
      axis.annotate("*", xy=(dates, keltner_upper), xycoords="data", fontsize=6, color=white, weight="bold")
      axis.annotate("*", xy=(dates, keltner_lower), xycoords="data", fontsize=6, color=white, weight="bold")
      axis.annotate("Squeeze", (dates, lowest_price), fontsize=6, color=white, weight="bold", ha='center', va='center')

class indicator_KELTNER_CHANNEL():
  def __init__(self):
    self.name = "KELTNER"
    self.overlay_chart = True

  def keltner_channel_hband(self, high, low, close, n):
    """Keltner channel (KC)
    Showing a simple moving average line (high) of typical price.
    """
    tp = ((4 * high) - (2 * low) + close) / 3.0
    tp = pd.Series(tp).rolling(n).mean()
    return tp

  def keltner_channel_lband(self, high, low, close, n):
    """Keltner channel (KC)
    Showing a simple moving average line (low) of typical price.
    """
    tp = ((-2 * high) + (4 * low) + close) / 3.0
    tp = pd.Series(tp).rolling(n).mean()
    return tp

  def generate_values(self, open_, high, low, close, volume):
    self.keltner_hband = self.keltner_channel_hband(np.array(high), np.array(low), np.array(close), 20)
    self.keltner_lband = self.keltner_channel_lband(np.array(high), np.array(low), np.array(close), 20)

  def plot_once(self, axis, dates):
    pass
    #self.keltner_hband_ = axis.plot(dates, self.keltner_hband, color=blue, lw=.5, antialiased=True)
    #self.keltner_lband_ = axis.plot(dates, self.keltner_lband, color=blue, lw=.5, antialiased=True)

  def update(self):
    pass
    #self.keltner_hband_[0].set_ydata(self.keltner_hband)
    #self.keltner_lband_[0].set_ydata(self.keltner_lband)

  def xaxis_get_start(self):
    return 0

class indicator_RSI():
  def __init__(self):
    self.name = "RSI"
    self.overlay_chart = False
  
  def generate_values(self, open_, high, low, close, volume):
    self.rsi = talib.RSI(np.array(close), timeperiod=14)
    
  def plot_once(self, axis, dates):
    self.rsi_ = axis.plot(dates, self.rsi, color=white, lw=.7, antialiased=True, label=self.name)
    axis.axhline(70, color=white, lw=.5, linestyle="--")
    axis.axhline(30, color=white, lw=.5, linestyle="--")
    self.legend = axis.legend(loc="upper left", facecolor=darkish, edgecolor=darkish, fontsize=8)
    for text in self.legend.get_texts():
      text.set_color("white")
      text.set_text("RSI=" + str(int(self.rsi[-1])))
  
  def update(self):
    self.rsi_[0].set_ydata(self.rsi)
    for text in self.legend.get_texts():
      text.set_text("RSI=" + str(int(self.rsi[-1])))
  
  def xaxis_get_start(self):
    return 0

class indicator_MACD():
  def __init__(self):
    self.name = "MACD"
    self.overlay_chart = False
    self.candle_width = 0
    self.first = True
  
  def generate_values(self, open_, high, low, close, volume):
    self.macd_values, self.signal_values, self.hist_values = talib.MACD(np.array(close))

  def plot_once(self, axis, dates):
    self.axis = axis
    self.dates = copy.deepcopy(dates)
    self.macd = axis.plot(dates, self.macd_values, color=blue, lw=.7, antialiased=True, label="MACD")
    self.signal = axis.plot(dates, self.signal_values, color=red, lw=.7, antialiased=True, label="Signal")
    self.legend = axis.legend(loc="upper left", facecolor=darkish, edgecolor=darkish, fontsize=8)
    for text in self.legend.get_texts():
      text.set_color("white")
  
  def update(self):
    self.macd[0].set_ydata(self.macd_values)
    self.signal[0].set_ydata(self.signal_values)
    
    if self.first == True:
      self.bar = self.axis.bar(self.dates, self.hist_values, self.candle_width, color=green, antialiased=True, label="Histogram")
      for i in range(0, len(self.bar)):
        if self.hist_values[i] > 0:
          self.bar[i].set_facecolor(green)
        elif self.hist_values[i] < 0:
          self.bar[i].set_facecolor(red)
      self.first = False
    else:
      self.bar[-1].set_height(self.hist_values[-1])
      if self.hist_values[-1] > 0:
        self.bar[-1].set_facecolor(green)
      elif self.hist_values[-1] < 0:
        self.bar[-1].set_facecolor(red)
   
  def xaxis_get_start(self):
    return 0

class indicator_STOCH():
  def __init__(self):
    self.name = "MACD"
    self.overlay_chart = False
  
  def generate_values(self, open_, high, low, close, volume):
    self.slowk_values, self.slowd_values = talib.STOCH(np.array(high), np.array(low), np.array(close), slowd_period=3, slowk_period=3, fastk_period=14)

  def plot_once(self, axis, dates):
    self.axis = axis
    self.dates = copy.deepcopy(dates)
    axis.axhline(80, color=white, lw=.5, linestyle="--")
    axis.axhline(20, color=white, lw=.5, linestyle="--")    
    self.slowk = axis.plot(dates, self.slowk_values, color=blue, lw=.7, antialiased=True, label="SLOW K")
    self.slowd = axis.plot(dates, self.slowd_values, color=red, lw=.7, antialiased=True, label="SLOW D")
    self.legend = axis.legend(loc="upper left", facecolor=darkish, edgecolor=darkish, fontsize=8)
    for text in self.legend.get_texts():
      text.set_color("white")
  
  def update(self):
    self.slowk[0].set_ydata(self.slowk_values)
    self.slowd[0].set_ydata(self.slowd_values)
    for text in self.legend.get_texts():
      if "SLOW K" in text.get_text():
        text.set_text("SLOW K=" + str(int(self.slowk_values[-1])))
      if "SLOW D" in text.get_text():
        text.set_text("SLOW D=" + str(int(self.slowd_values[-1])))
    
  def xaxis_get_start(self):
    return 0


class indicator_VOLUME():
  def __init__(self):
    self.name="VOLUME"
    self.overlay_chart = False
    self.first = True
    self.candle_width = 0
  
  def generate_values(self, open_, high, low, close, volume):
    self.open = open_
    self.close = close
    self.volume = volume
    
  def plot_once(self, axis, dates):
    self.axis = axis
    self.dates = copy.deepcopy(dates)
  
  def update(self):
    if self.first == True:
      self.bar = self.axis.bar(self.dates, self.volume, self.candle_width, color=green, antialiased=True, alpha=.5)
      for i in range(0, len(self.bar)):
        if self.close[i] > self.open[i]:
          self.bar[i].set_facecolor(green)
        elif self.close[i] < self.open[i]:
          self.bar[i].set_facecolor(red)
      self.first = False
    else:
      self.bar[-1].set_height(self.volume[-1])
      if self.close[-1] > self.open[-1]:
        self.bar[-1].set_facecolor(green)
      elif self.close[-1] < self.open[-1]:
        self.bar[-1].set_facecolor(red)
  
  def xaxis_get_start(self):
    return 0
