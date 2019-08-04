WAVETREND
==
Wavetrend is a trading terminal for Bitcoin and Altcoins

SUPPORTED EXCHANGES
=====
BINANCE, BITFINEX, KRAKEN

FEATURES
=====

* Neural Network Automatic Trading

* Able to view many symbols at once using tab Switch

* Squeeze Detection: "Bollinger Band in Keltner Channel",

    see https://admiralmarkets.com/analytics/traders-blog/bollinger-bands-r-with-admiral-keltner-breakout-strategy

* Supported Indicators: RSI, Bollinger Bands, Directional Movement Index (ADX/+DI/-DI), MACD, STOCH

* Supported Candle Modes: Classic Candlestick, Heikin Ashi, Better Bollinger Bands 

CONFIGURATION
=====

edit config.txt

INSTALLATION
=====
requirements: python3 64-bit

requirements inside requirements.txt (please use the correct versions especially for ccxt lib)

install TA-Lib from:

https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

example command for installation:

pip install ta_lib-0.4.17-cp27-cp27m-win_amd64.whl

For the macOS installation first install homebrew,
then install python inside homebrew and use this python
including pip installation manager.
To install ta-lib with brew type:
brew install ta-lib

RUNNING
=====
python geforcemulti.py

Windows users can use the EXE build inside
releasebuilds\: unzip the file and run wavetrend.exe

NEURAL NETWORK LEVERAGE TRADING
=====
The neural network calculates train data from the Binance
Exchange and executes leverage trading on the Bitfinex Exchange.
So you need both API keys configured inside config.txt.
Procedure for trading with the automatic neural network:

* Configure both API Keys for Binance and Bitfinex

* Put enough USD into the "Margin Wallet" of Bitfinex

* Run the program with the command "python geforcemulti.py"

* Select the Binance Exchange symbol "BTC/USDT" and "1h"  timeframe then click on OK

* Select "+neural nework" in the tab menu of the symbol at the top of Wavetrend

* Now enter the leverage amount you want to use for each trade.
  Recommended is 2x times the amount you have in the margin wallet
  of Bitfinex you can also enter a smaller amount.

* Select if this is a trending market or choppy sideways market. Please be aware that
  for a choppy sideways market you will require a lot of memory such as 12 GB RAM for the neural
  network to operate.
  The selection trending market will enter trades more quickly the choppy sideways market will wait
  for a breakout from the sideways market and enter a long or short position.

* Now the neural network is learning for 30 minutes. After the 30 minutes
  it will calculate each minute if a trade is profitable and correct for a given price,
  once it finds a good opportunity it will open a long or short position.
  Now wait for a given time, it can take up to a day to make profits. If the neural
  network sees the position was incorrect it will automatically turn long/short sides,
  this can happen sometimes. Most of the times the neural network acts correctly.
  Once you make enough profit you can close the position and restart the program and
  neural network for the next trade.
  
* Be sure to have enough RAM as the neural networks collects much data in memory.

* Python version 64 Bit is required for the neural network to function.

ToDo:

The neural network might block the UI a bit during calculating the values.

Currently only BTC/USDT symbol is valid for the neural network trading.

SUPPORTED OPERATING SYSTEMS
=====
Linux, Windows, macOS

EXCHANGE FEES
=====
BITFINEX FEES: https://www.bitfinex.com/fees

BINANCE FEES: https://www.binance.com/en/fee/schedule

KRAKEN FEES: https://www.kraken.com/features/fee-schedule
