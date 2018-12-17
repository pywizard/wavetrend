import sys
import numpy as np
import ccxt
import time
import datetime
import talib
import math
import copy

client = ccxt.hitbtc2({
 'apiKey': "",
 'secret': "",
 'enableRateLimit': True
})

client_bin = ccxt.binance({
 'apiKey': "",
 'secret': "",
 'enableRateLimit': True
})

def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

def get_symbol_price(symbol):
  sym = client.fetch_ticker(symbol)
  return float(sym["last"])

def orderbook(exchange, symbol):
  return exchange.fetch_order_book(symbol)

def get_asset_from_symbol(symbol):
  return symbol.split("/")[0]

def get_quote_from_symbol(symbol):
  return symbol.split("/")[1]

def trade_buy(percent, symbol):
  try:
    price = get_symbol_price(symbol)
    if symbol.endswith("USDT"):
      asset_balance = float(client.fetch_balance()["USDT"]["free"])
      amount = truncate((asset_balance / price) * percent, 2)
    elif symbol.endswith("USD"):
      asset_balance = float(client.fetch_balance()["USD"]["free"])
      amount = truncate((asset_balance / price) * percent, 2)                  
    else:
      asset_balance = float(client.fetch_balance()["BTC"]["free"])
      amount = truncate((asset_balance / price) * percent, 2)
    
    book = orderbook(client, symbol)
    asks_added = 0
    for ask in book["asks"]:
      asks_added = asks_added + ask[1]
      if asks_added > amount:
        price = ask[0]
        print "TRADE BUY " + symbol
        print str(amount) + " " + str(price)
        client.create_limit_buy_order(symbol, amount, price)
        return
  except:
    print get_full_stacktrace()
    return  

def trade_sell(percent, symbol):
  try:
    asset_balance = truncate(float(client.fetch_balance()[get_asset_from_symbol(symbol)]["free"]), 2)
    amount = truncate(asset_balance * percent, 2)
    book = orderbook(client, symbol)
    bids_added = 0
    for bid in book["bids"]:
      bids_added = bids_added + bid[1]
      if bids_added > amount:
        price = bid[0]
        print "TRADE SELL " + symbol
        print str(amount) + " " + str(price)
        client.create_limit_sell_order(symbol, amount, price)
        return       
  except:
    print get_full_stacktrace()
    return

def check_orders(symbol):
  open_orders = client.fetch_open_orders()
  found = False
  for order in open_orders:
    if order['symbol'] == symbol:
      client.cancel_order(order['id'])
      found = True
  return found

def getData(timeframe_entered, days_entered, currency_entered, few_candles, client):
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

symbol = sys.argv[1]
bought = False
sold = False

prices2 = []
while True:
  date, open_, high, low, close, vol, limit = getData("1h", 10, symbol, False, client)
  date_list    = xrange(0, len(open_))
  open_list    = copy.deepcopy(open_)
  close_list   = copy.deepcopy(close)
  high_list    = copy.deepcopy(high)
  low_list     = copy.deepcopy(low)
  volume_list  = copy.deepcopy(vol)
  elements        = len(open_)

  for i in xrange(1, elements):
      close_list[i] = (open_list[i] + close_list[i] + high_list[i] + low_list[i])/4
      open_list[i]  = (open_list[i-1] + close_list[i-1])/2
      high_list[i]  = max(high_list[i], open_list[i], close_list[i])
      low_list[i]   = min(low_list[i], open_list[i], close_list[i])
    
  green_1 = False

  if close_list[-1] > open_list[-1] and close_list[-1]*0.00035 < close_list[-1] - open_list[-1]:
    green_1 = True
  
  print "HITBTC " + symbol + " CLOSE: " + str(close_list[-1]) + " OPEN: " + str(open_list[-1])

  date, open_, high, low, close, vol, limit = getData("1h", 10, symbol, False, client_bin)
  date_list    = xrange(0, len(open_))
  open_list    = copy.deepcopy(open_)
  close_list   = copy.deepcopy(close)
  high_list    = copy.deepcopy(high)
  low_list     = copy.deepcopy(low)
  volume_list  = copy.deepcopy(vol)
  elements        = len(open_)

  for i in xrange(1, elements):
      close_list[i] = (open_list[i] + close_list[i] + high_list[i] + low_list[i])/4
      open_list[i]  = (open_list[i-1] + close_list[i-1])/2
      high_list[i]  = max(high_list[i], open_list[i], close_list[i])
      low_list[i]   = min(low_list[i], open_list[i], close_list[i])
    
  green_2 = False
  if close_list[-1] > open_list[-1] and close_list[-1]*0.00035 < close_list[-1] - open_list[-1]:
    green_2 = True
  
  print "BINANCE " + symbol + " CLOSE: " + str(close_list[-1]) + " OPEN: " + str(open_list[-1])
  
  if green_1 == False and green_2 == False and sold == False:
    sold = True
    bought = False
    trade_sell(.97, symbol)
    time.sleep(10)
    if check_orders(symbol) == True:
     trade_sell(.97, symbol)
     time.sleep(10)
     if check_orders(symbol) == True:
      trade_sell(.97, symbol)
    
  elif green_1 == True and green_2 == True and bought == False:
    bought = True
    sold = False
    trade_buy(.23, symbol)
    time.sleep(10)
    if check_orders(symbol) == True:
      trade_buy(.23, symbol)  
      time.sleep(10)
      if check_orders(symbol) == True:
        trade_buy(.23, symbol)  
        
  time.sleep(1)
