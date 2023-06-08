# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 14:34:27 2023

@author: nw14a
"""

import numpy as np
from silx.io.specfile import SpecFile

nI0 = 12
nI1 = 13
nI2 = 14

def plot_scan(_plt, datdir, filename, scanNumber,motorName):
    _plt.clear()
    sf = SpecFile(datdir+'/'+filename)
    
    mydata = sf['{:d}.1'.format(scanNumber)].data
    motor = mydata[0]
    I0 = mydata[nI0]
    I1 = mydata[nI1]
    I2 = mydata[nI2]
    
    _plt.addCurve(motor, I1/I0,legend='pos',color='red')
    _plt.addCurve(motor, I2/I0,legend='neg',color='blue')
    _plt.addCurve(motor, I1/I0-I2/I0,legend='diff',color='green',yaxis='right')
    # _plt.addCurve(motor, I1/I2,legend='diff2',color='magenta',yaxis='right')
    _plt.setGraphXLabel(motorName)