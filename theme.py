from PyQt5 import QtGui
THEME_TYPE_DARK = 1
THEME_TYPE_LIGHT = 2

class Theme:
    def __init__(self, theme_type):
        self.theme_type = theme_type
        if self.theme_type == THEME_TYPE_DARK:
            self.green = "#50B787"
            self.greenish = "#138484"
            self.blue = "#0000FF"
            self.red = "#E0505E"
            self.orange = "#FFA500"
            self.black = "#131D27"
            self.darkish = "#363C4E"
            self.white = "#C6C7C8"
            self.grayscale_light = "#7B7B7B"
            self.grayscale_dark = "#2F3241"
            self.grayscale_lighter = "#D9D9D9"

            self.colorup = "#134F5C"
            self.colordown = "#A61C00"
            self.colorup2 = "#53B987"
            self.colordown2 = "#EB4D5C"
            self.indicator_color1 = "#134F5C"
            self.indicator_color1_2 = "#53B987"
            self.indicator_color2 = "#7F7F28"
            self.indicator_color2_2 = "#FF7F28"
            self.indicator_color3 = "#A61C00"
            self.indicator_color3_2 = "#EB4D5C"

            self.green2 = "#2c681d"
            self.red2 = "#681d1d"
            self.dialog_red = QtGui.QColor(220, 0, 0)
            self.dialog_green = QtGui.QColor(0, 220, 0)
            self.orderbook_bg = QtGui.QColor(33, 47, 60)
            self.orderbook_fg = QtGui.QColor(208, 211, 212)
            self.orderbook_bids_1 = QtGui.QColor(11, 83, 69)
            self.orderbook_bids_2 = QtGui.QColor(14, 102, 85)
            self.orderbook_bids_3 = QtGui.QColor(17, 122, 101)
            self.orderbook_asks_1 = QtGui.QColor(100, 30, 22)
            self.orderbook_asks_2 = QtGui.QColor(123, 36, 28)
            self.orderbook_asks_3 = QtGui.QColor(146, 43, 33)
            self.trades_green = QtGui.QColor(17, 122, 101)
            self.trades_red = QtGui.QColor(146, 43, 33)
            self.trades_fg = QtGui.QColor(208, 211, 212)
        elif self.theme_type == THEME_TYPE_LIGHT:
            self.green = "#26A69A"
            self.greenish = "#92D2CC"
            self.blue = "#2196F3"
            self.red = "#EF5350"
            self.orange = "#FFA500"
            self.black = "#FFFFFF"
            self.darkish = "#E1ECF2"
            self.white = "#50535E"
            self.grayscale_light = "#50535E"
            self.grayscale_dark = "#E0E3EB"
            self.grayscale_lighter = "#50535E"

            self.colorup = "#26A69A"
            self.colorup2 = "#26A69A"
            self.colordown = "#EF5350"
            self.colordown2 = "#EF5350"
            self.indicator_color1 = self.colorup
            self.indicator_color1_2 = self.colorup
            self.indicator_color2 = "#FF7F28"
            self.indicator_color2_2 = "#FF7F28"
            self.indicator_color3 = self.colordown
            self.indicator_color3_2 = self.colordown

            self.dialog_green = self.green
            self.dialog_red = self.red
            self.green2 = self.green
            self.red2 = self.red
            self.orderbook_bg = QtGui.QColor(255, 255, 255)
            self.orderbook_fg = QtGui.QColor(0, 0, 0)
            self.orderbook_bids_1 = QtGui.QColor(38, 166, 154)
            self.orderbook_bids_2 = QtGui.QColor(46, 196, 182)
            self.orderbook_bids_3 = QtGui.QColor(53, 224, 208)
            self.orderbook_asks_1 = QtGui.QColor(239, 83, 80)
            self.orderbook_asks_2 = QtGui.QColor(239, 126, 123)
            self.orderbook_asks_3 = QtGui.QColor(241, 163, 162)
            self.trades_green = QtGui.QColor(53, 224, 208)
            self.trades_red = QtGui.QColor(241, 163, 162)
            self.trades_fg = QtGui.QColor(0, 0, 0)
