import talib
import numpy as np
from colors import *
import copy

class indicator_DMI:
  def __init__(self):
    self.name = "DMI"
    self.overlay_chart = False
  
  def generate_values(self, open, high, low, close):
    self.plus_di_values = talib.PLUS_DI(np.array(high), np.array(low), np.array(close))
    self.minus_di_values = talib.MINUS_DI(np.array(high), np.array(low), np.array(close))
    self.adx_values = talib.ADX(np.array(high), np.array(low), np.array(close))
    
  def plot_once(self, axis, dates):
    self.axis = axis
    self.dates = dates
    self.plus_di = axis.plot(self.dates, self.plus_di_values, color=blue, lw=.7, label="+DI=" + str(int(self.plus_di_values[-1])))
    self.minus_di = axis.plot(self.dates, self.minus_di_values, color=orange, lw=.7, label="-DI=" + str(int(self.minus_di_values[-1])))
    self.adx = axis.plot(self.dates, self.adx_values, color=red, lw=.7, label="ADX=" + str(int(self.adx_values[-1])))
    self.legend = axis.legend(loc="upper left", facecolor=darkish, edgecolor=darkish, fontsize="small")
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
        text.set_text("ADX=" + str(int(self.adx_values[-1])))
  
  def xaxis_get_start(self):
    start_x = 0
    for i in xrange(0, len(self.adx_values)):
        if not np.isnan(self.adx_values[i]):
          start_x = i
          break
    return start_x

class indicator_BBANDS():
  def __init__(self):
    self.name="BBANDS"
    self.overlay_chart = True
  
  def generate_values(self, open, high, low, close):
    self.bb_upper, self.bb_middle, self.bb_lower = talib.BBANDS(np.array(close), timeperiod=20)    
    
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
    return 0

class indicator_RSI():
  def __init__(self):
    self.name = "RSI"
    self.overlay_chart = False
  
  def generate_values(self, open, high, low, close):
    self.rsi = talib.RSI(np.array(close), timeperiod=14)
    
  def plot_once(self, axis, dates):
    self.rsi_ = axis.plot(dates, self.rsi, color=white, lw=.7, antialiased=True, label=self.name)
    axis.axhline(70, color=white, lw=.5, linestyle="--")
    axis.axhline(30, color=white, lw=.5, linestyle="--")
    self.legend = axis.legend(loc="upper left", facecolor=darkish, edgecolor=darkish, fontsize="small")
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
    self.bar = None
    self.first = True
  
  def generate_values(self, open, high, low, close):
    self.macd_values, self.signal_values, self.hist_values = talib.MACD(np.array(close))

  def plot_once(self, axis, dates):
    self.axis = axis
    self.dates = copy.deepcopy(dates)
    self.macd = axis.plot(dates, self.macd_values, color=blue, lw=.7, antialiased=True, label="MACD")
    self.signal = axis.plot(dates, self.signal_values, color=red, lw=.7, antialiased=True, label="Signal")
    self.legend = axis.legend(loc="upper left", facecolor=darkish, edgecolor=darkish, fontsize="small")
    for text in self.legend.get_texts():
      text.set_color("white")
  
  def update(self):
    self.macd[0].set_ydata(self.macd_values)
    self.signal[0].set_ydata(self.signal_values)
    
    if self.first == True:
      self.bar = self.axis.bar(self.dates, self.hist_values, self.candle_width, color=green, antialiased=True, label="Histogram")
      for i in xrange(0, len(self.bar)):
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
  