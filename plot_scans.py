# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 14:16:13 2023

@author: nw14a
"""

import sys, os, string, io, glob, re, yaml, math, time
import numpy as np
import pandas as pd
import shutil, natsort

import PyQt5.QtCore
from PyQt5 import uic
import silx
from silx.gui import qt
app = qt.QApplication([])
import time
import silx.gui.colors as silxcolors
from silx.gui.plot import PlotWindow, Plot1D, Plot2D, PlotWidget,items
import silx.gui.colors as silxcolors


plot1d = Plot1D()
plot1d.show()

if __name__ == '__main__':
	app.exec_()