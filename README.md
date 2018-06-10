
WAVETREND ROBOT 1.0 BETA
==

Auto BUYS/SELLS when the Wavetrend Oscillator has an Intersection according to the direction.

Currently Supported Exchanges: binance

General information about the Wavetrend Oscillator can be found here:

https://www.youtube.com/watch?v=7vhIsk51_Ro

https://www.youtube.com/watch?v=MqJ1czF220M



![eos](https://i.imgur.com/GS51zV3.png)

![ont](https://i.imgur.com/hqJQ0x0.png)

Installation
==

Windows Installation
************************************************

Install python 2.7 then install the dependencies

pip install matplotlib==2.0.1

pip install pandas==0.22.0

pip install pygubu

pip install tzlocal

pip install python-binance

Choose the correct python 2.7 version of the TA-Lib package and architecture (win32/win_amd64),

install TA-Lib from:

https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

example command for installation:

pip install ta_lib-0.4.17-cp27-cp27m-win_amd64.whl

Then choose the correct PyQT4 version from here:

https://www.lfd.uci.edu/~gohlke/pythonlibs/

For example the package PyQt4‑4.11.4‑cp27‑cp27m‑win_amd64.whl is for python 2.7 and Windows 64-Bits.

Once downloaded, install the package:

pip install PyQt4‑4.11.4‑cp27‑cp27m‑win_amd64.whl



Linux Installation (Tested with Ubuntu)
******************************************************************************

sudo apt-get install tk-dev libpng-dev libffi-dev dvipng texlive-latex-base

sudo apt-get install python-tk

sudo pip2 install matplotlib==2.0.1

sudo pip2 install pandas==0.22.0

sudo pip2 install pygubu

sudo pip2 install tzlocal

sudo pip2 install python-binance

then.. with no spaces in pathname..

wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz

tar xvzf ta-lib-0.4.0-src.tar.gz

cd ta-lib

./configure --prefix=/usr

make

sudo make install

sudo pip2 install TA-Lib

sudo apt-get install python-qt4


Running
=========

Edit the config.py file and add your api keys.

Windows only:

Run the program within an elevated cmd.exe shell (it syncs the system time with the time of the exchange).

Run command:

python geforcemulti.py
(or for the older version [not recommended] type python geforcemulti_tk_old.py)

This is is still beta software and is currently being developed and tested!!! Use at your own risk.
