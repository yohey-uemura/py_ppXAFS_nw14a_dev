#!/usr/bin/env /Users/uemuray/Library/jupyterlab-desktop/jlab_server/envs/xraylarch/bin/python
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


class Ui(qt.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ metho
        uic.loadUi('MainWindow.ui', self)
		
        self.plot_xas = PlotWindow(control = True)
        print (self.plot_xas.getConsoleAction())
        layout = qt.QVBoxLayout()
        self.widget.setLayout(layout)
        self.plot_xas.setGraphXLabel('Energy /eV')
        self.plot_xas.setGraphYLabel('XAS')
        self.plot_xas.setGraphYLabel('diffXAS', axis='right')
        layout.addWidget(self.plot_xas)

        layout2 = qt.QVBoxLayout()
        self.widget_2.setLayout(layout2)

        self.plotI0 = Plot1D()
        self.plotI0.setGraphXLabel('Energy /eV')
        self.plotI0.setGraphYLabel('I0 intensity')
        layout2.addWidget(self.plotI0)
        self.plot_xas_each = Plot1D()
        self.plot_xas_each.setGraphXLabel('Energy /eV')
        self.plot_xas_each.setGraphYLabel('XAS')
        self.plot_xas_each.setGraphYLabel('diffXAS', axis='right')
        layout2.addWidget(self.plot_xas_each)

        self.scroll_layout = qt.QVBoxLayout()
        self.scrollArea.setLayout(self.scroll_layout)

        self.sumI0 = []
        self.sumI1= []
        self.sumI2 = []
        self.cbs = []
        self.energy,self.r_stdev_ut_star, self.r_stdev_ut = [], [], []
        self.rbs = qt.QButtonGroup()

        if sys.platform == 'win32':
            self.home_dir = os.environ['HOMEPATH']
        else:
            self.home_dir = os.environ['HOME']

        def openFiles():
            self.sumI0 = []
            self.sumI1 = []
            self.sumI2 = []
            while self.scroll_layout.count() >0:
                b = self.scroll_layout.takeAt(len(self.cbs)-1)
                self.cbs.pop()
                self.rbs.removeButton(self.rbs.buttons()[0])
                b.widget().deleteLater()
            if self.lineEdit.text()=="" or not os.path.isdir(self.lineEdit.text()):
                dat_dir = self.home_dir
            elif os.path.isdir(self.lineEdit.text()):
                dat_dir = self.lineEdit.text()
            FO_dialog = qt.QFileDialog(self)
            files = FO_dialog.getOpenFileNames(None, "", dat_dir, "data file(*.dat)")
            try:
                if files[0]:
                    finfo = qt.QFileInfo(files[0][0])
                    self.lineEdit.clear()
                    self.lineEdit.setText(finfo.path())
                    for fname in natsort.natsorted(files[0]):
                        info = qt.QFileInfo(fname)
                        cb = qt.QCheckBox(info.fileName())
                        cb.setObjectName(fname)
                        self.cbs.append(cb)
                        cb.toggle()
                        cb.clicked.connect(self.func_pB11)
                        rb = qt.QRadioButton()
                        rb.setObjectName(fname)
                        rb.toggled.connect(self.plot_each_XANES)
                        self.rbs.addButton(rb)
                        widget = qt.QWidget()
                        hlayout = qt.QHBoxLayout()
                        widget.setLayout(hlayout)
                        hlayout.addWidget(cb)
                        hlayout.addWidget(rb)
                        self.scroll_layout.addWidget(widget)
                    self.func_pB11()
            except Exception as e:
                msg = qt.QMessageBox()
                msg.setIcon(qt.QMessageBox.Warning)
                msg.setText(str(e))
                msg.setStandardButtons(qt.QMessageBox.Ok)
                msg.exec_()
            #     params.sumI0, params.sumI1, params.sumI2, params.energy, params.r_stdev_ut_star, params.r_stdev_ut = self.extract_data()
            #     self.set_sBconditions()
            #     self.plotXANES(params.sumI0, params.sumI1, params.sumI2, params.energy)
            #     params.rbs.buttons()[0].toggle()

        self.pushButton.clicked.connect(openFiles)
        self.show()
        
    def extract_data(self):
        sumI0 = np.zeros(0)
        sumI1 = np.zeros(0)
        sumI2 = np.zeros(0)
        energy = []
        each_ut_star = []
        each_ut = []
        try:
            self.Ipos, self.Ineg = [x.rstrip().replace(' ','') for x in self.lineEdit_2.text().split(',')]
            if len(self.cbs) != 0:
                checkedCB_objN = []
                for cb in self.cbs:
                    if cb.isChecked():
                        checkedCB_objN.append(cb.objectName())

                i = 0
                for cb in self.cbs:
                    if cb.isChecked():
                        switch = "not read"
                        Fdat = pd.read_csv(cb.objectName(),delim_whitespace=True)
                        I0 = []
                        I1 = []
                        I2 = []
                        if i == 0:
                            energy = Fdat['SetEne'].values
                        I0 = Fdat['I0'].values
                        I1 = Fdat[self.Ipos].values
                        I2 = Fdat[self.Ineg].values

                        if i == 0:
                            sumI0 = np.zeros(len(I0))
                            sumI1 = np.zeros(len(I0))
                            sumI2 = np.zeros(len(I0))
                            mt = np.zeros(len(I0))
                            mt_star = np.zeros(len(I0))
                            delta_mt = np.zeros(len(I0))
                        print (len(I0), len(sumI0))
                        if len(I0) != len(sumI0):
                            cb.setCheckState(QtCore.Qt.Unchecked)
                            cb.setEnabled(False)
                        else:
                            sumI0 += np.array(I0)
                            sumI1 += np.array(I1)
                            sumI2 += np.array(I2)
                            each_ut_star.append(np.array(I1)/np.array(I0))
                            each_ut.append(np.array(I2) / np.array(I0))
                        i +=1
            checkedCB_objN = []
            for cb in self.cbs:
                if cb.isChecked():
                    checkedCB_objN.append(cb.objectName())

        except Exception as e:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setText(str(e))
            msg.setStandardButtons(qt.QMessageBox.Ok)
            msg.exec_()

        if sumI0.sum() != 0:
            return sumI0, sumI1, sumI2, np.array(energy),\
                   np.std(np.array(each_ut_star),axis=0)/math.sqrt(len(checkedCB_objN)),\
                   np.std(np.array(each_ut),axis=0)/math.sqrt(len(checkedCB_objN))
        else:
            [None]*6

    def func_pB11(self):
        self.sumI0, self.sumI1, self.sumI2, self.energy,self.r_stdev_ut_star, self.r_stdev_ut = self.extract_data()
        if not 'NoneType' in str(type(self.sumI0)):
            self.plotXANES(self.sumI0, self.sumI1, self.sumI2, self.energy)
        else:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setText("No data found")
            msg.setStandardButtons(qt.QMessageBox.Ok)
            msg.exec_()

    def plotXANES(self, I0,I1,I2,energy):
        self.plot_xas.remove(kind=('curve'))
        xas_pos = I1/I0
        xas_pos = (xas_pos-xas_pos[:self.spinBox.value()].mean())/(xas_pos[-self.spinBox.value():].mean()-xas_pos[:self.spinBox.value()].mean())

        xas_neg = I2/I0
        xas_neg = (xas_neg-xas_neg[:self.spinBox.value()].mean())/(xas_neg[-self.spinBox.value():].mean()-xas_neg[:self.spinBox.value()].mean())
        self.plot_xas.addCurve(energy, xas_pos,legend="pos")
        self.plot_xas.addCurve(energy, xas_neg, legend="neg")
        self.plot_xas.addCurve(energy, xas_pos-xas_neg, legend="diff",yaxis='right')

    def plot_each_XANES(self):
        #self.Ipos, self.Ineg = [x.rstrip().replace(' ','') for x in self.u.lE_posneg.text().split(',')]
        energy = np.zeros(0)
        rb = self.rbs.checkedButton()
        switch = "not read"
        #print rb.objectName()
        #Fdat = open(rb.objectName(),"rU")
        Fdat = pd.read_csv(rb.objectName(),delim_whitespace=True)
        I0 = []
        I1 = []
        I2 = []
        energy = Fdat['SetEne'].values
        I0 = Fdat['I0'].values
        I1 = Fdat[self.Ipos].values
        I2 = Fdat[self.Ineg].values

        self.plot_xas_each.addCurve(energy, I1/I0,legend='pos')
        self.plot_xas_each.addCurve(energy, I2/I0,legend='neg')
        self.plot_xas_each.addCurve(energy, I1/I0-I2/I0,legend='diff',yaxis='right')
        self.plotI0.addCurve(energy, I0)


if __name__ == '__main__':
	window = Ui()
	app.exec_()
