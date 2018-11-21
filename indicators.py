import talib
import numpy as np
from colors import *

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
    self.plus_di = axis.plot(self.dates, self.plus_di_values, color=blue, lw=.7)
    self.minus_di = axis.plot(self.dates, self.minus_di_values, color=orange, lw=.7)
    self.adx = axis.plot(self.dates, self.adx_values, color=red, lw=.7)
  
  def update(self):
    self.plus_di[0].set_ydata(self.plus_di_values)
    self.minus_di[0].set_ydata(self.minus_di_values)
    self.adx[0].set_ydata(self.adx_values)
  
  def xaxis_get_start(self):
    start_x = 0
    for i in xrange(0, len(self.adx_values)):
        if not np.isnan(self.adx_values[i]):
          start_x = i
          break
    return start_x

class indicator_BBANDS():
  def __init__(self):
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
    self.rsi_ = axis.plot(dates, self.rsi, color=white, lw=.5, antialiased=True)
  
  def update(self):
    self.rsi_[0].set_ydata(self.rsi)
  
  def xaxis_get_start(self):
    return 0
  