# WAVETREND V1.3 Software Manual



### Video Introduction

[Watch the Introduction video here: https://github.com/pywizard/wavetrend/blob/master/media/wavetrend.mp4?raw=true](https://github.com/pywizard/wavetrend/blob/master/media/wavetrend.mp4?raw=true)



### Introduction

Wavetrend version 1.3 is a trading terminal for Bitcoin, Altcoins and Instruments such as CFDs, Currencies and Metals. It fetches and displays real-time market data in a convenient way. This market data is displayed so that the user can analyse the markets to make buy and sell decisions on the specific financial exchange. 

The Wavetrend software currently supports three Bitcoin/Altcoin exchanges, these are:

- Bitfinex, https://bitfinex.com
- Binance, https://binance.com
- Kraken, https://kraken.com

It allows to view nearly all available instruments (such as BTC/USD, LTC/USD, ETH/USD etc.) for the specific exchange in real time.

The Wavetrend software supports the Oanda (https://oanda.com) exchange to display charts and market  analysis tools for markets other than Bitcoins and Altcoins.



### Exchange and Instrument Selection

When the Wavetrend software is launched it shows the instrument selection dialog. At the top left of the window the user can select the desired exchange that should be used to display the market data for a specific instrument. This selection is named "Select Exchange". Once the user selects the exchange the instruments are loaded below.

![](https://github.com/pywizard/wavetrend/blob/master/manual/Wavetrend%20V1.3%20Software%20Manual/Pictures/Exchange%20and%20Instrument%20Selection.PNG?raw=true)

   													**Exchange Selections for Bitfinex and Oanda**



The loaded instruments are displayed different for each exchange:

- Bitfinex Exchange

  - The instruments are colored and there are displayed four columns for each exchange. The instruments are sorted descending depending on the instruments volume for the last 24 hours counted in US-Dollar.
    - The color green and red indicates either rising or falling markets in the last 24 hours. If the market for the specific instrument has risen in the last 24 hours then the instrument is colored green, if the market has fallen in the last 24 hours the instrument is colored red respectively.
    - The columns for each instrument are: 
      - Price Change; the Price Change is either positive or negative and is counted in the instruments quote symbol for the last 24 hours. For example if the user sees BTC/USD the quote is USD and the Price Change column displays the value in USD. If the user sees for example ETH/BTC the quote is BTC and the Price Change is displayed in BTC.
      - Price Change %; The Price Change % column displays either a positive or negative percentage value for the given instrument and the last 24 hours the instrument has been traded.
      - Volume; The Volume column displays the volume traded in the last 24 hours and is counted in US-Dollar.

- Binance Exchange

  - The very same display used for Bitfinex is also used for Binance, please refer to the above description "Bitfinex Exchange".

- Kraken Exchange

  - For the Kraken Exchange there are displayed two columns, these are Symbol and Volume.

    The symbol refers to the instrument like BTC/USD, LTC/USD, ETH/BTC etc. and the Volume refers to the traded Volume of the instrument in the last 24 hours and is counted in US-Dollar.

- Oanda Exchange

  - For the Oanda Exchange there are displayed three columns, these are Instrument, Name and Type.

    Instrument can be any available instrument the Oanda Exchange is providing such as US30_USD, SPX500_USD, EUR_USD, AUD_JPY, XAU_XAG, XAU_USD etc. The Name column shows a human readable form of the instrument and the type shows what kind of instrument is being displayed. For example US30_USD is traded as a CFD, EUR_USD is a currency, XAU_USD is a metal (gold in this case as displayed in the Name field).



##### Timeframe selection

Below the instrument selection there is another field that must be selected and is very important for the market analysis. It selects the timeframe the chart and other market analysis tools will be displayed in.

Each exchange has its own set of timeframe selection. For the Bitfinex exchange for example the user will be able to select these timeframes: 1d (One Day Chart), 12h (Twelve Hour Chart), 6h (Six Hour Chart) ... and so on, then the minute charts: 30m (Thirty Minute Chart), 15m (Fifteen Minute Chart), 5m (Five Minute Chart) etc. Finally the 1w (One Week Chart).



##### Theme selection

Wavetrend Version 1.3 has two themes / styles the user can select during startup, these are the Dark and Light Themes. The Dark Theme shows a nearly black application background and the colors are adjusted to the black background, the Light Theme shows a white application background and the colors are adjusted to the white background. Once the theme is selected the application runs using this theme until the user exits the application.



### Main View

![]()Once the instrument has been selected the main view opens. For each instrument added the application adds a new tab at the top of the main view. When you have several instruments added in the tabbed view the tabs can be switched into with the mouse or using the F1-F12 hot-keys.

The initial view shows the instruments Chart and instrument Volume of the Chart at the top region. On top of the Chart there is a price display on the right side showing the price and time of the instrument. Below from the Chart the indicators are shown. On the right side of the window there is displayed the Orderbook and Trades control.





![](https://github.com/pywizard/wavetrend/blob/master/manual/Wavetrend%20V1.3%20Software%20Manual/Pictures/Main%20View.PNG?raw=true)

​                                                                     **Main View Of The Application**





![](https://github.com/pywizard/wavetrend/blob/master/manual/Wavetrend%20V1.3%20Software%20Manual/Pictures/Tabbed%20View.PNG?raw=true)

​    															**The Tabbed View With Many Instruments**





##### Chart and Indicators

For the initial loaded instrument view the chart is displayed the following way:

- Candlestick type candles.
- A Bollinger Band with default settings: time period 20, deviation multiplier up 2, deviation multiplier down 2.
- For a selected one week chart, 3 day chart, one day chart or 12 hour chart the candle scanner is active and there are displayed candle pattern names at the top of the chart. For each candle that has a  detected candle pattern the affected candle is displayed in yellow color inside the chart view. For all other timeframes the candle scanner feature is inactive.
- The Squeeze detection is enabled for all timeframes. A Squeeze in the chart indicates a Hot-Spot in the market where the Bollinger Bands are inside the Keltner Channel Bands. A Squeeze is indicated by dots in the Chart where the Keltner Channel Bands are located while the Bollinger Band is inside them and a text at the bottom line where the Squeeze is located.
- Positive green and negative red colored volume bars.
- Three indicators, these are from top to bottom:
  - RSI (Relative Strength Index)
  - DMI (Directional Movement Index) including the ADX (Average Directional Index).
    - When the current ADX value is below or equal to 25 the application displays the text "Absent or Weak Trend" for the current market and timeframe. When the current ADX value is above 25 and below or equal to 50 the application shows the text "Strong Trend" for the current market and timeframe. When the current ADX value is above 50 and below or equal to 75 the application shows the text "Very Strong Trend"for the current market and timeframe. Current ADX values above 75 show a text "Extremely Strong Trend" for the current market and selected timeframe.
  - MACD (Moving Average Convergence/Divergence)
  - An optional STOCH (Stochastic) indicator in case oscillating markets is selected for the instruments chart options.



![](https://github.com/pywizard/wavetrend/blob/master/manual/Wavetrend%20V1.3%20Software%20Manual/Pictures/Main%20View%20Detailed.PNG)

​         									**Right Side Of Main View With Details**





![](https://github.com/pywizard/wavetrend/blob/master/manual/Wavetrend%20V1.3%20Software%20Manual/Pictures/Main%20View%20Detailed%202.PNG?raw=true)

​			**Left Side Bottom Of Main View With The Indicators And Current Indicator Values**



##### Orderbook and Trades View

For Bitcoin / Altcoin markets there is displayed an Orderbook and a Trades View.

The Orderbook consists of a listing of current bids and asks, each listing has three columns. The bids are ordered descending and the asks are ordered ascending. Each bid and ask has three columns inside the Orderbook table. The Price, Quantity and Sum. The Price column displays the current price for the bid and ask at the given price level. The Quantity displays the amount the instrument is to be bought or sold at the given price. The Sum displays the accumulated bid and ask amount.

For both bid and asks the three biggest quantities currently traded are displayed. The biggest bids are shown in green color and the biggest asks are shown in red color. The deeper the color the higher is the quantity shown in the second column.

The Trades View displays the historic trades done. It has three columns, these are Time, Price and Quantity.

The Time column shows how many seconds, minutes and hours the trade was executed at. The Price column shows at what price the trade was executed at. The quantity shows the amount of the symbol that has been bought or sold in the past. The rows of the Trades View are colored green and red, the colors indicate more specifically in case of green that the "Maker" of the trade was on the buy side and in the case of red indicate that the "Maker" of the trade was on the sell side.



![](https://github.com/pywizard/wavetrend/blob/master/manual/Wavetrend%20V1.3%20Software%20Manual/Pictures/Orderbook%20and%20Trades%20View.PNG?raw=true)

​                                                               **Orderbook and Trades View**



##### Chart Options

Once the chart is loaded there are several options available in the charts tab. When the user clicks on the triangle at the charts tab a menu opens with the following options that change the chart:

- Trending
  - For a Trending market the MACD indicator is switched on and displayed and the STOCH indicator is switched off.
- Oscillating
  - For an Oscillating market the STOCH indicator is switched on and displayed and the MACD indicator is switched on. 
- Candlestick
  - Clicking on the Candlestick option makes the chart use candlestick candles instead of heikin ashi candles.
- Heikin Ashi
  - Clicking on the Heikin Ashi option makes the chart use heikin ashi candles instead of candlestick candles
- Better BBand on/off
  - The Better BBand option switches the Better BBands on and off. The Better BBand changes the Bollinger Band to a timeperiod of 15 and displays the candles in a way that one can see when the prices moves between the upper bollinger band, the middle bollinger band and the lower bollinger band. Green candles indicate that the price will rise above the middle bollinger band and will rise in general. Red candles indicate the price will fall below the middle bollinger band and will fall in general. Yellow candles indicate the price is in an undecided phase and might rise or fall.
- Chart Only on/off
  - When switching this option on the Chart is displayed without the indicators displayed at the bottom. This makes the chart bigger.
- Close
  - Clicking on this menu option with unload and close the selected Chart.



# CONFIGURATION

Edit config.txt and your Exchange API Keys.



# INSTALLATION

Requirements: python3 64-bit

Install requirements you find inside requirements.txt (please use the correct versions)

In case of Windows: The newest Visual C++ Redistributable for Visual Studio Package for the according Python3 compilation.

install TA-Lib from:

https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

For the macOS installation first install homebrew,
then install python inside homebrew and use this python
including pip installation manager.
To install ta-lib with brew type:
brew install ta-lib

# RUNNING

python geforcemulti.py

