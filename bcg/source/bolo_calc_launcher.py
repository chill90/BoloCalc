import os
import sys
import simplejson
import numpy as np
from copy import copy
from datetime import datetime
from PyQt5 import QtGui, QtCore, QtWidgets, Qt
from bcglib.gen_class import Class
from bcglib.bolo_calc_gui import BoloCalcGui


class BoloCalcLauncher(BoloCalcGui):

    def __init__(self):
        self.experiments = ['Simons Array', 'Simons Observatory']
        self.styles = ['QtCurve', 'Oxygen',  'Breeze', 'Windows', 'WindowsXP', 'WindowsVista', 'Fusion']
        self.style = self.styles[-1]

    def create_bolo_calc_gui(self):
        qt_app = QtWidgets.QApplication([])
        display_style = Qt.QStyleFactory.create('{0}'.format(self.style))
        qt_app.setStyle(display_style)
        screen_resolution = qt_app.desktop().screenGeometry()
        gui = BoloCalcGui(screen_resolution)
        gui.showMaximized()
        exit(qt_app.exec_())

    def run(self):
        self.create_bolo_calc_gui()


if __name__ == '__main__':
    bolo_calc_launcher = BoloCalcLauncher()
    bolo_calc_launcher.run()
