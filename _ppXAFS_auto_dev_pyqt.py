import sys
import os
import string
import io
import glob
import re
import yaml
import math
import time
import multiprocessing as multip
import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
import numpy.linalg as linalg
import scipy.optimize as optim
import pandas as PD
import shutil
import natsort
#import use_larch


from PyQt5 import QtCore, QtWidgets, QtGui
# from UI_ppXAFS import Ui_MainWindow

#
home_dir = QtCore.QDir()

#import progressbar as PB
import csv
#import h5py
#import time

# Ipos = 'I1'
# Ineg = 'I2'

class params:
    rbs = QtWidgets.QButtonGroup()
    rbs_ts = QtWidgets.QButtonGroup()
    cbs = []
    dfiles = []
    dir = ""
    if sys.platform == 'win32':
        home_dir = os.environ['HOMEPATH']
    else:
        home_dir = os.environ['HOME']
    mt_star_plus_c = []
    mt_plus_c = []
    delta_mt_plus = []
    mt_star_minus_c = []
    mt_minus_c = []
    delta_mt_minus = []
    cbs_t = []
    energy = []
    sumI0 = []
    sumI1 = []
    sumI2 = []
    I0 = []
    I_pos = []
    I_neg = []
    mt = []
    mt_star = []
    r_stdev_ut_star = []
    r_stdev_ut = []
    delta_mt = []
    OR = "#FF4500"
    chi_data = []
    chi_cb = []
    colors = ["OrangeRed", "Blue", "Brown", "Chartreuse", "Coral", "Crimson", "DarkGreen", "DarkBlue", "DarkMagenta", "DarkRed",
              "DeepPink", "FireBrick", "GoldenRod", "Grey", "GreenYellow", "Indigo", "LightCoral", "MediumBlue",
              "MediumVioletRed"]
    from_dir = ""
    to_dir = ""
    # decay_I0 = np.zeros(0)
    # decay_Ipos = np.zeros(0)
    # decay_Ineg = np.zeros(0)



from UI_ppXAFS_dev_pyqt5 import Ui_MainWindow
from plot_RawBk_pyqt5 import Ui_Dialog
from textBrowser_pyqt5 import Ui_Form
from dialog_autoLoad_pyqt5 import Ui_Dialog as Ui_Dialog_autoLoad
if sys.platform == 'win32':
    from UI_ppXAFS_win_pyqt5 import Ui_MainWindow
    from plot_RawBk_win_pyqt5 import Ui_Dialog
    from dialog_autoLoad_win_pyqt5 import Ui_Dialog as Ui_Dialog_autoLoad
    # params.home_dir =os.environ['HOMEPATH']

class UpdateStatsThread(QtCore.QThread):

    def __init__(self,  progressBar,waittime,parent=None):
        super(UpdateStatsThread, self).__init__(parent)
        self._running = False
        self.progressBar = progressBar
        self.waittime = waittime


    def stop(self, wait=False):
        self._running = False
        if wait:
            self.wait()

    def doWork(self):
        self.msleep(self.waittime)
        # print str(self.waittime) +' has passed.'
        # print str(self.progressBar.value() + self.waittime)
        self.progressBar.setValue(self.progressBar.value() + self.waittime)
        # return 1

def sub_Extract_data(filename):
    switch = "not read"
    #print cb.objectName()
    Fdat = open(filename,"rU")
    I0 = []
    I1 = []
    I2 = []
    energy = []
    for line in Fdat:
        line.rstrip()
        t_array = line.split()
        if switch == "not read":
            switch = "read"
        elif switch == "read":
            I0.append(float(t_array[3]))
            I1.append(float(t_array[4]))
            I2.append(float(t_array[5]))
            energy.append(float(t_array[0]))
    return np.array(energy), np.array(I0), np.array(I1), np.array(I2)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):

        QtWidgets.QMainWindow.__init__(self,parent)
        self.u = Ui_MainWindow()
        self.u.setupUi(self)
        self.textBrowser = Ui_Form()
        self.popup = QtWidgets.QDialog(self)
        self.textBrowser.setupUi(self.popup)
        self.popup.setParent(self)
        self.timer = QtCore.QBasicTimer()

        self.dialog = Ui_Dialog()
        self.plot_dialog = QtWidgets.QDialog()
        self.dialog.setupUi(self.plot_dialog)

        #print (self.u.lE_posneg.text().split(','))
        self.Ipos, self.Ineg = [x.rstrip().replace(' ','') for x in self.u.lE_posneg.text().split(',')]
        
        self.dialog_grid = QtWidgets.QVBoxLayout()
        fig_dialog = Figure(figsize=(320, 320), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0),tight_layout=True)
        self.ax_dialog = fig_dialog.add_subplot(111)
        self.ax_dialog.set_xlabel("Energy / eV")
        self.ax_dialog.set_ylabel("$\mu$ t")
        self.ax_dialog_right = self.ax_dialog.twinx()
        self.ax_dialog_right.set_ylabel("$\Delta\mu$ t")
        self.canvas_dialog = FigureCanvas(fig_dialog)
        self.dialog.widget.setLayout(self.dialog_grid)
        #self.dialog_grid.addWidget(self.canvas_dialog)
        navibar_dialog = NavigationToolbar(self.canvas_dialog,parent=None)
        self.dialog_grid.addWidget(self.canvas_dialog)
        self.dialog_grid.addWidget(navibar_dialog)

        self.autoLoad = Ui_Dialog_autoLoad()
        self.dil_auotLoad = QtWidgets.QDialog()
        self.autoLoad.setupUi(self.dil_auotLoad)

        def dialog_autoLoad():
            if self.dil_auotLoad.isHidden():
                self.dil_auotLoad.show()
                self.u.actionAuto_load.setChecked(True)
            else:
                self.dil_auotLoad.hide()
                self.u.actionAuto_load.setChecked(False)

        def close_autoLoad():
            if not self.dil_auotLoad.isHidden():
                self.dil_auotLoad.hide()
                self.u.actionAuto_load.setChecked(False)

        self.u.actionAuto_load.triggered.connect(dialog_autoLoad)
        self.autoLoad.pB_close.clicked.connect(close_autoLoad)

        def setProgressBar_Maximum(integer):
            self.autoLoad.progressBar.setMaximum(integer*1000)
            # print self.autoLoad.progressBar.maximum()

        self.autoLoad.spinBox.valueChanged[int].connect(setProgressBar_Maximum)
        self.QTimer = QtCore.QTimer()
        self.autoLoad.pB_exec.setEnabled(False)

        def check_state():
            if os.path.isdir(self.autoLoad.tB_DatDir.toPlainText()) and \
                    os.path.isdir(self.autoLoad.tB_cp_direction.toPlainText()) and \
                self.autoLoad.lE_posneg.text() != "" and self.autoLoad.lineEdit_2.text() != "":
                self.autoLoad.pB_exec.setEnabled(True)

        for tB in [self.autoLoad.tB_DatDir, self.autoLoad.tB_cp_direction, self.autoLoad.lineEdit, self.autoLoad.lineEdit_2]:
            tB.textChanged.connect(check_state)

        def F_from_cp_dir():
            dir_ = params.home_dir
            if params.from_dir != "":
                dir_ = params.from_dir
            FO_dialog = QtWidgets.QFileDialog(self)
            # print dir_
            Dir = FO_dialog.getExistingDirectory(dir = dir_)
            if Dir != "":
                self.autoLoad.tB_DatDir.clear()
                self.autoLoad.tB_DatDir.append(Dir)
                params.from_dir = Dir
        self.autoLoad.pB_cp_from.clicked.connect(F_from_cp_dir)

        def F_cp_direction():
            dir_ = params.home_dir
            if params.to_dir != "":
                dir_ = params.to_dir
            FO_dialog = QtWidgets.QFileDialog(self)
            Dir = FO_dialog.getExistingDirectory(dir = dir_)
            if Dir != "":
                self.autoLoad.tB_cp_direction.clear()
                self.autoLoad.tB_cp_direction.append(Dir)
                params.to_dir = Dir
        self.autoLoad.pB_cp_direction.clicked.connect(F_cp_direction)


        self.scroll_layout = QtWidgets.QVBoxLayout()
        scroll_widgets = QtWidgets.QWidget()
        scroll_widgets.setLayout(self.scroll_layout)
        self.u.scrollArea.setWidget(scroll_widgets)

        self.scroll_layout2 = QtWidgets.QVBoxLayout()
        scroll_widgets2 = QtWidgets.QWidget()
        scroll_widgets2.setLayout(self.scroll_layout2)
        self.u.scrollArea_2.setWidget(scroll_widgets2)

        self.u.pushButton_2.setText('Release All')
        self.ButtonGroup = QtWidgets.QButtonGroup()
        for rB in [self.u.rB_kpower0,self.u.rB_kpower1,self.u.rB_kpower2,self.u.rB_kpower3]:
            self.ButtonGroup.addButton(rB)

        #grid3.itemAt(0)
        self.grid = QtWidgets.QGridLayout()
        fig = Figure(figsize=(320, 320), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0),tight_layout=True)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Energy / eV")
        self.ax.set_ylabel("$\mu$ t")
        self.ax_right = self.ax.twinx()
        self.ax_right.set_ylabel("$\Delta\mu$ t")
        self.canvas = FigureCanvas(fig)
        self.u.widget.setLayout(self.grid)
        self.grid.addWidget(self.canvas,0,0)
        navibar_0 = NavigationToolbar(self.canvas, self.u.widget)
        self.u.widget.setLayout(self.grid)
        self.grid.addWidget(self.canvas,0,0)
        self.grid.addWidget(navibar_0)

        self.grid3 = QtWidgets.QGridLayout()
        fig3 = Figure(figsize=(320, 320), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0),tight_layout=True)
        self.ax4 = fig3.add_subplot(221)
        self.ax4.set_xlabel("t / ps")
        self.ax4.set_ylabel("$\mu$ t")
        self.ax4.set_title('Absorption')
        self.ax4_dut = fig3.add_subplot(223)
        self.ax4_dut.set_xlabel("t / ps")
        self.ax4_dut.set_ylabel("$\Delta\mu$ t")
        self.ax4_dut.set_title('difference')

        self.ax5 = fig3.add_subplot(222)
        self.ax5.set_xlabel("t / ps")
        self.ax5.set_ylabel("$\Delta\mu$ t")
        self.ax5.set_title('Sum')
        self.ax5_twin = fig3.add_subplot(224)
        self.ax5_twin.set_xlabel("t / ps")
        self.ax5_twin.set_ylabel("$\Delta\mu$ t")
        self.ax5_twin.set_title("difference")
        self.canvas3 = FigureCanvas(fig3)
        navibar_1 = NavigationToolbar(self.canvas3, self.u.widget_3)
        self.u.widget_3.setLayout(self.grid3)
        self.grid3.addWidget(self.canvas3,0,0)
        self.grid3.addWidget(navibar_1)

        self.gridI0 = QtWidgets.QGridLayout()
        fig_I0 = Figure(figsize=(320, 320), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0),tight_layout=True)
        self.canvasI0 = FigureCanvas(fig_I0)
        self.ax_I0 = fig_I0.add_subplot(211)
        self.ax_I0.set_xlabel("Energy / eV")
        self.ax_I0.set_ylabel("Intensity")
        self.ax_I0.set_title('I0')
        self.ax_ut = fig_I0.add_subplot(212)
        self.ax_ut.set_xlabel("Energy / eV")
        self.ax_ut.set_ylabel("$\mu$ t")
        self.ax_ut.set_title('Absorption')
        self.ax_dut = self.ax_ut.twinx()
        self.ax_dut.set_ylabel("$\Delta\mu$ t")
        self.u.widget_2.setLayout(self.gridI0)
        self.gridI0.addWidget(self.canvasI0,0,0)

        navibar_2 = NavigationToolbar(self.canvasI0, self.u.widget_2)
        self.u.widget_2.setLayout(self.gridI0)
        self.gridI0.addWidget(self.canvasI0,0,0)
        self.gridI0.addWidget(navibar_2)

        self.u.dsB_pre_start.valueChanged[float].connect(self.u.dsB_pre_end.setMinimum)
        self.u.dsB_post_start.valueChanged[float].connect(self.u.dsB_post_end.setMinimum)
        self.dialog.dsb_pos_bk_start.valueChanged[float].connect(self.dialog.dsb_pos_bk_end.setMinimum)
        self.dialog.dsb_pos_bk_end.valueChanged[float].connect(self.dialog.dsb_pos_bk_start.setMaximum)
        self.dialog.dsb_neg_bk_start.valueChanged[float].connect(self.dialog.dsb_neg_bk_end.setMinimum)
        self.dialog.dsb_neg_bk_end.valueChanged[float].connect(self.dialog.dsb_neg_bk_start.setMaximum)
        
        if sys.platform == 'win32':
            self.u.actionBoost.setEnabled(False)

        # params.spinBoxes = [self.u.spinBox,self.u.spinBox_2,self.u.spinBox_3,self.u.spinBox_4]
        # for sB in params.spinBoxes:
        #     sB.setMinimum(0)

        def makeplots(xlabel,ylabel):
            fig = Figure(figsize=(170, 120), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
            self.ax = fig.add_subplot(111)
            self.ax.set_xlabel(xlabel)
            self.ax.set_ylabel(ylabel)
            self.canvas = FigureCanvas(fig)
            return self.ax, self.canvas

        def openFiles():
            params.sumI0 = []
            params.sumI1 = []
            params.sumI2 = []
            while self.scroll_layout.count() >0:
                b = self.scroll_layout.takeAt(len(params.cbs)-1)
                params.cbs.pop()
                params.rbs.removeButton(params.rbs.buttons()[0])
                b.widget().deleteLater()
            if params.dir=="":
                dat_dir = home_dir.homePath()
            elif params.dir!="":
                dat_dir = params.dir
            FO_dialog = QtWidgets.QFileDialog(self)
            files = FO_dialog.getOpenFileNames(None, "", dat_dir, "data file(*.dat *csv)")
            if files[0]:
                finfo = QtCore.QFileInfo(files[0][0])
                params.dir = finfo.path()
                for fname in natsort.natsorted(files[0]):
                    info = QtCore.QFileInfo(fname)
                    cb = QtWidgets.QCheckBox(info.fileName())
                    cb.setObjectName(fname)
                    params.cbs.append(cb)
                    cb.toggle()
                    cb.clicked.connect(self.func_pB11)
                    rb = QtWidgets.QRadioButton()
                    rb.setObjectName(fname)
                    rb.toggled.connect(self.plot_each_XANES)
                    params.rbs.addButton(rb)
                    widget = QtWidgets.QWidget()
                    hlayout = QtWidgets.QHBoxLayout()
                    widget.setLayout(hlayout)
                    hlayout.addWidget(cb)
                    hlayout.addWidget(rb)
                    self.scroll_layout.addWidget(widget)
                params.sumI0, params.sumI1, params.sumI2, params.energy, params.r_stdev_ut_star, params.r_stdev_ut = self.extract_data()
                self.set_sBconditions()
                self.plotXANES(params.sumI0, params.sumI1, params.sumI2, params.energy)
                params.rbs.buttons()[0].toggle()

        def Save_ut():
            if params.dir=="":
                dat_dir = home_dir.homePath()
            elif params.dir!="":
                dat_dir = params.dir
            if len(params.mt_star) != 0:
                print ("Save")
            F0_dialog = QtWidgets.QFileDialog(self)
            file = F0_dialog.getSaveFileName(None,"",dat_dir,"data file(*.csv)")
            if file[0]:
                if re.match('\w+\.\w+$',os.path.basename(file[0])):
                    pass
                else:
                    file[0]+'.csv'
                df = PD.DataFrame()
                df.loc[:,'#Energy'] = params.energy[:]
                df.loc[:,'ut*'] = params.mt_star[:]
                df.loc[:,'ut'] = params.mt[:]
                df.loc[:,'delta_ut'] = params.delta_mt[:]
                df.to_csv(file[0],sep=" ",index=False)

                file = file[0].split('.')[0]+"_raw"+"."+file[0].split('.')[1]
                df = PD.DataFrame()
                df.loc[:,'#Energy'] = params.energy[:]
                df.loc[:,'ut*'] = params.sumI1/params.sumI0[:]
                df.loc[:,'ut'] = params.sumI2/params.sumI0[:]
                df.loc[:,'ratio:ut*_stdev'] = params.r_stdev_ut_star
                df.loc[:, 'ratio:ut_stdev'] = params.r_stdev_ut
                df.to_csv(file,sep=" ",index=False)
            

        def selectAll():
            if len(params.cbs) != 0:
                for cb in params.cbs:
                    if cb.isChecked():
                        pass
                    else:
                        cb.toggle()
            params.sumI0, params.sumI1, params.sumI2, params.energy, params.r_stdev_ut_star, params.r_stdev_ut = self.extract_data()
            self.plotXANES(params.sumI0, params.sumI1, params.sumI2, params.energy)



        def Save_TimeDecay():
            if params.dir=="":
                dat_dir = home_dir.homePath()
            elif params.dir!="":
                dat_dir = params.dir
            FO_dialog = QtWidgets.QFileDialog(self)
            files = FO_dialog.getSaveFileName(None,"",dat_dir, "CSV file(*.csv)")
            if files[0]:
                finfo = QtCore.QFileInfo(files[0])
                params.dir = finfo.path()
                filename = finfo.absoluteFilePath()
                t = []
                sum_I0 = []
                sum_I1 = []
                sum_I2 = []
                sum_mt_star = []
                sum_mt = []
                delta_ut = []
                if len(self.ax5.lines) != 0:
                    for cb in params.cbs_t:
                        if cb.isChecked():
                            I0, I1, I2, mt_star, mt =  self.readDecay(cb)
                            # print I1
                            sum_I0.append(I0)
                            sum_I1.append(I1)
                            sum_I2.append(I2)
                    #print sum_I0
                    t = self.ax5.lines[0].get_xdata()
                    sum_mt_star = self.ax5.lines[0].get_ydata()
                    sum_mt = self.ax5.lines[1].get_ydata()
                    delta_ut = self.ax5_twin.lines[0].get_ydata()
                    I0 = np.sum(np.array(sum_I0),axis=0)
                    I1 = np.sum(np.array(sum_I1),axis=0)
                    I2 = np.sum(np.array(sum_I2),axis=0)
                    print (len(t))
                    print (len(sum_mt_star))
                    print (len(sum_mt))
                    print (len(I0))
                    print ( len(I1))
                    print (len(I2))

                df = PD.DataFrame({'00_time / ps':t[:],'01_ut_pos':sum_mt_star[:],'02_ut_neg':sum_mt[:],
                                   '03_delta_ut':delta_ut[:],'04_I0':I0[:],'05_I1':I1[:],'06_I2':I2[:]})
                df.to_csv(filename,sep=" ",header=['#time / ps','ut_pos','ut_neg','delta_ut','I0','I_pos','I_neg'],index=False)



        def openFiles_TimeDecay():
            while self.scroll_layout2.count() >0:
                b = self.scroll_layout2.takeAt(len(params.cbs_t)-1)
                cb = params.cbs_t.pop()
                rb = params.rbs_ts.buttons()[0]
                params.rbs_ts.removeButton(rb)
                rb.deleteLater()
                cb.deleteLater()
                b.widget().deleteLater()
            self.checkDecay()
            if params.dir=="":
                dat_dir = home_dir.homePath()
            elif params.dir!="":
                dat_dir = params.dir
            FO_dialog = QtWidgets.QFileDialog(self)
            files = FO_dialog.getOpenFileNames(None,"",dat_dir, "data file(*.dat *csv)")
            if files[0]:
                finfo = QtCore.QFileInfo(files[0][0])
                params.dir = finfo.path()
                params.t = []
                for fname in files[0]:
                    info = QtCore.QFileInfo(fname)
                    cb = QtWidgets.QCheckBox(info.fileName())
                    cb.setObjectName('cB:'+fname)
                    rb = QtWidgets.QRadioButton()
                    rb.setObjectName('rB:'+fname)
                    widget = QtWidgets.QWidget()
                    hlayout = QtWidgets.QHBoxLayout()
                    widget.setLayout(hlayout)
                    cb.clicked.connect(self.plotDecay)
                    params.cbs_t.append(cb)
                    hlayout.addWidget(cb)
                    cb.toggle()
                    rb.toggled.connect(self.plot_each_Delay)
                    params.rbs_ts.addButton(rb)
                    hlayout.addWidget(rb)
                    self.scroll_layout2.addWidget(widget)
                #self.calcDecay()
                self.plotDecay()
                params.rbs_ts.buttons()[0].toggle()

        def release_all():
            num = 0
            if len(params.cbs_t) != 0:
                for cb in params.cbs_t:
                    if cb.isChecked():
                        num += 1
            # print num
            if num >= 1 and self.u.pushButton_2.text() == "Release All":
                for cb in params.cbs_t:
                    cb.setCheckState(QtCore.Qt.Unchecked)
                self.u.pushButton_2.setText("Select All")
                # print self.u.pushButton_2.text()
            elif len(params.cbs_t) > num and self.u.pushButton_2.text() == "Select All":
                for cb in params.cbs_t:
                    cb.setCheckState(QtCore.Qt.Checked)
                self.u.pushButton_2.setText("Release All")

        def changePage():
            self.u.stackedWidget.setCurrentIndex(self.u.comboBox.currentIndex())

        self.scroll_layout_exafs = QtWidgets.QVBoxLayout()
        scroll_widgets_exafs = QtWidgets.QWidget()
        scroll_widgets_exafs.setLayout(self.scroll_layout_exafs)
        self.u.scrollArea_3.setWidget(scroll_widgets_exafs)
        self.u.rB_kpower0.setChecked(QtCore.Qt.Checked)

        self.grid_chi = QtWidgets.QGridLayout()
        fig_chi = Figure(figsize=(320, 640), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        self.ax_chi = fig_chi.add_subplot(121)
        self.ax_chi.set_xlabel("k / \AA^-1")
        self.ax_chi.set_ylabel("k^x*$\chi$(k)")
        self.ax_chi.set_title('chi_k')
        self.ax_ft = fig_chi.add_subplot(122)
        self.ax_ft.set_xlabel("r / \AA")
        self.ax_ft.set_ylabel("FT[k^x*$\chi$(k)]")
        self.ax_ft.set_title('FT')
        self.canvas_chi = FigureCanvas(fig_chi)
        navibar_chi = NavigationToolbar(self.canvas_chi, self.u.widget_4)
        self.u.widget_4.setLayout(self.grid_chi)
        self.grid_chi.addWidget(self.canvas_chi,0,0)
        self.grid_chi.addWidget(navibar_chi)

        def open_chi():
            self.textBrowser.textBrowser.clear()
            self.textBrowser.textBrowser_2.clear()
            if params.dir=="":
                dat_dir = home_dir.homePath()
            elif params.dir!="":
                dat_dir = params.dir
            FO_dialog = QtWidgets.QFileDialog(self)
            file = FO_dialog.getOpenFileName(None, "",dat_dir,"chi file (*.chi *.dat)")
            if file[0] == "":
                pass
            else:
                f = open(file[0],'r')
                self.textBrowser.textBrowser_2.append(file[0])
                i = 1
                for line in f:
                    self.textBrowser.textBrowser.append(str(i)+": "+line.rstrip()+"\n")
                    i += 1
                self.textBrowser.spinBox.setMaximum(i-1)
                self.textBrowser.textBrowser.moveCursor(QtWidgets.QTextCursor.Start)
                self.popup.exec_()

        def read_chi():
            for comb in [self.u.comBox_Pos, self.u.comBox_Neg]:
                while comb.count() > 0:
                    comb.removeItem(comb.takeAt(comb.count()-1))
            while self.scroll_layout_exafs.count() >0:
                b = self.scroll_layout_exafs.takeAt(self.scroll_layout_exafs.count()-1)
                params.chi_cb.pop()
                b.widget().deleteLater()
            params.chi_data =[]
            num = self.textBrowser.spinBox.value()
            t_array = self.textBrowser.lE_posneg.text().split(',')
            columns_Names = []
            for term in t_array:
                columns_Names.append(os.path.basename(self.textBrowser.textBrowser_2.toPlainText()).split('.')[0]+':'+term.replace(' ',''))
            params.chi_data = PD.read_csv(self.textBrowser.textBrowser_2.toPlainText(), dtype=np.float64,skiprows=num, names = columns_Names, delimiter=r"\s+")
            array = columns_Names[:]
            for term in array:
                # print term.split(':')[1]
                if re.match(r"k_?.*",term.split(':')[1]):
                    array.pop(array.index(term))
            self.u.comBox_Pos.addItems(array)
            self.u.comBox_Neg.addItems(array)
            self.u.comBox_Neg.setCurrentIndex(self.u.comBox_Pos.currentIndex()+1)
            # print self.u.comBox_Pos.currentIndex()
            # self.u.comBox_Neg.addItems(params.chi_data)
            # self.u.comBox_Neg.setCurrentIndex(1)
            self.popup.done(1)

        def plot_chi():
            if self.u.comBox_Neg.count() != 0:
                i = 0
                kweight = float(self.ButtonGroup.checkedButton().text())
                while len(self.ax_chi.lines) !=0:
                        self.ax_chi.lines.pop()
                text_for_k = 'k'
                for key in params.chi_data.keys():
                    if re.match(r"k_?.*",key.split(':')[1]):
                        text_for_k = key.split(':')[1]
                # print params.chi_data[self.u.comBox_Pos.currentText().split(':')+':'+text_for_k]
                k_data = params.chi_data[self.u.comBox_Pos.currentText().split(':')[0]+':'+text_for_k].values
                self.ax_chi.plot(k_data,k_data**kweight*params.chi_data[self.u.comBox_Pos.currentText()].values,label='pos',color='r')
                self.ax_chi.plot(k_data,k_data**kweight*params.chi_data[self.u.comBox_Neg.currentText()].values,label='neg',color='k')
                self.ax_chi.legend()
                self.ax_chi.autoscale_view()
                self.ax_chi.relim()
                self.canvas_chi.draw()


        def plot_norm_and_bk():
            if not self.plot_dialog.isHidden():
                params.sumI0, params.sumI1, params.sumI2, params.energy, params.r_stdev_ut_star, params.r_stdev_ut = self.extract_data()
                self.plotXANES(params.sumI0, params.sumI1, params.sumI2, params.energy)

        def close_dialog():
            self.plot_dialog.hide()
            self.u.combo_fynctype.setCurrentIndex(self.dialog.combo_fynctype.currentIndex())
            self.u.checkBox_2.setCheckState(QtCore.Qt.Unchecked)

        def ShowClose_dialog():
            if not self.u.checkBox_2.isChecked():
                close_dialog()
            else:
                self.plot_dialog.show()

        self.dialog.pushButton.clicked.connect(close_dialog)

        self.u.pushButton_7.clicked.connect(openFiles_TimeDecay)
        self.u.pushButton_2.clicked.connect(release_all)
        self.u.pushButton_9.clicked.connect(Save_TimeDecay)
        self.u.pushButton.clicked.connect(openFiles)
        self.u.pushButton_13.clicked.connect(Save_ut)
        self.u.pushButton_11.clicked.connect(self.func_pB11)
        self.u.pushButton_10.clicked.connect(selectAll)
        self.u.pB_openchi.clicked.connect(open_chi)
        self.textBrowser.pushButton.clicked.connect(read_chi)
        self.u.checkBox_2.clicked.connect(ShowClose_dialog)
        for rB in [self.u.rB_kpower0,self.u.rB_kpower1,self.u.rB_kpower2,self.u.rB_kpower3]:
            rB.clicked.connect(plot_chi)
        for combo in [self.u.comBox_Pos, self.u.comBox_Neg]:
            combo.currentIndexChanged.connect(plot_chi)
        for sB in [self.dialog.dsb_pos_bk_start,self.dialog.dsb_pos_bk_end,
                            self.dialog.dsb_neg_bk_start,self.dialog.dsb_neg_bk_end]:
            sB.valueChanged.connect(plot_norm_and_bk)
        self.autoLoad.pB_exec.clicked.connect(self.doAction)
        self.u.combo_fynctype.currentIndexChanged[int].connect(self.dialog.combo_fynctype.setCurrentIndex)
        self.u.lE_posneg.textChanged[str].connect(self.u.lE_posneg_2.setText)
        self.u.lE_posneg_2.textChanged[str].connect(self.u.lE_posneg.setText)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.show()


    def find_near(self,Energy,req_Energy):
        array = np.absolute(Energy - req_Energy)
        return np.argmin(array)

    def extract_data(self):
        sumI0 = np.zeros(0)
        sumI1 = np.zeros(0)
        sumI2 = np.zeros(0)
        energy = []
        each_ut_star = []
        each_ut = []
        try:
            self.Ipos, self.Ineg = [x.rstrip().replace(' ','') for x in self.u.lE_posneg.text().split(',')]
            if len(params.cbs) != 0:
                checkedCB_objN = []
                for cb in params.cbs:
                    if cb.isChecked():
                        checkedCB_objN.append(cb.objectName())

                i = 0
                for cb in params.cbs:
                    if cb.isChecked():
                        switch = "not read"
                        # print cb.objectName()
                        Fdat = PD.read_csv(cb.objectName(),delim_whitespace=True)
                        #open(cb.objectName(),"rU")
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
            for cb in params.cbs:
                if cb.isChecked():
                    checkedCB_objN.append(cb.objectName())

        except Exception as e:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText(str(e))
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()
                    
        return sumI0, sumI1, sumI2, np.array(energy), \
               np.std(np.array(each_ut_star),axis=0)/math.sqrt(len(checkedCB_objN)),\
               np.std(np.array(each_ut),axis=0)/math.sqrt(len(checkedCB_objN))

    def set_sBconditions(self):
        if len(params.energy) != 0:
            for dsb in [self.u.dsB_pre_start,self.u.dsB_pre_end,self.u.dsB_post_start,self.u.dsB_post_end,
                        self.dialog.dsb_pos_bk_start,self.dialog.dsb_pos_bk_end,
                        self.dialog.dsb_neg_bk_start,self.dialog.dsb_neg_bk_end]:
                dsb.setMinimum(params.energy[0])
                dsb.setMaximum(params.energy[-1])
            self.u.dsB_pre_start.setValue(params.energy[0])
            self.u.dsB_pre_end.setValue(params.energy[0]+10.0)
            self.u.dsB_post_start.setValue(params.energy[-1]-10.0)
            self.u.dsB_post_end.setValue(params.energy[-1])
            self.dialog.dsb_pos_bk_start.setValue(params.energy[0])
            self.dialog.dsb_pos_bk_end.setValue(params.energy[0]+10.0)
            self.dialog.dsb_neg_bk_start.setValue(params.energy[0])
            self.dialog.dsb_neg_bk_end.setValue(params.energy[0]+10.0)

    def XANES_norm(self,energy, I0, I1,fit_s, fit_e, nor_bE0_s,nor_bE0_e,nor_aE0_s,nor_aE0_e,func_type):
        ut_ = I1/I0
        #find nearest point
        startpoint = self.find_near(energy,fit_s)
        endpoint = self.find_near(energy,fit_e)
        # linear
        if func_type == 1:
            fit_r = np.polyfit(energy[startpoint:endpoint],ut_[startpoint:endpoint],1)
            pre_edge = fit_r[0]*energy + fit_r[1]
            ut_wo_bk = ut_ - pre_edge
            base = np.average(ut_wo_bk[self.find_near(energy,nor_bE0_s):self.find_near(energy,nor_bE0_e)])
            after_edge = np.average(ut_wo_bk[self.find_near(energy,nor_aE0_s):self.find_near(energy,nor_aE0_e)])
            ut_nor = (ut_wo_bk-base)/(after_edge-base)
            return ut_nor, pre_edge
        #victoreen
        elif func_type == 2:
            fit_lin = np.polyfit(energy[startpoint:endpoint],ut_[startpoint:endpoint],1)
            def fit_f(x,C,D,Y):
                return Y + C/x**3 - D/x**4
            E_s_and_e = [energy[startpoint],energy[endpoint]]
            ut_s_and_e = [ut_[startpoint],ut_[endpoint]]
            X = np.vstack([E_s_and_e ,np.ones(len(E_s_and_e))]).T
            DAT = [energy[startpoint]**4*(ut_[startpoint]-fit_lin[1]),energy[endpoint]**4*(ut_[endpoint]-fit_lin[1])]
            c, d = linalg.lstsq(X,DAT)[0]
            # print c,d
            opt, pconv = optim.curve_fit(fit_f,energy[startpoint:endpoint],ut_[startpoint:endpoint],p0=[c,d,fit_lin[1]])
            # print opt
            pre_edge = fit_f(energy,opt[0],opt[1],opt[2])
            ut_wo_bk = ut_ - pre_edge
            base = np.average(ut_wo_bk[self.find_near(energy,nor_bE0_s):self.find_near(energy,nor_bE0_e)])
            after_edge = np.average(ut_wo_bk[self.find_near(energy,nor_aE0_s):self.find_near(energy,nor_aE0_e)])
            ut_nor = (ut_wo_bk-base)/(after_edge-base)
            return ut_nor, pre_edge
        #average
        elif func_type == 0:
            pre_edge = np.average(ut_[self.find_near(energy,nor_bE0_s):self.find_near(energy,nor_bE0_e)])
            ut_wo_bk = ut_ - pre_edge
            after_edge = np.average(ut_wo_bk[self.find_near(energy,nor_aE0_s):self.find_near(energy,nor_aE0_e)])
            ut_nor = ut_wo_bk/after_edge
            return ut_nor, pre_edge*np.ones(len(ut_))

    def plotXANES(self, I0,I1,I2,energy):
        #print len(params.cbs)
        axis = [self.ax,self.ax_right]
        # for ax_ in axis:
        #     while len(ax_.lines) !=0:
        #         ax_.lines.pop()
        fig = self.ax.figure
        fig.delaxes(self.ax)
        fig.delaxes(self.ax_right)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Energy / eV")
        self.ax.set_ylabel("$\mu$ t")
        self.ax_right = self.ax.twinx()
        self.ax_right.set_ylabel("$\Delta\mu$ t")
        pre_start = self.u.dsB_pre_start.value()
        pre_end = self.u.dsB_pre_end.value()
        post_start = self.u.dsB_post_start.value()
        post_end  = self.u.dsB_post_end.value()
        functype = self.dialog.combo_fynctype.currentIndex()
        #calculation : Pos.
        fit_s = self.dialog.dsb_pos_bk_start.value()
        fit_e = self.dialog.dsb_pos_bk_end.value()
        params.mt_star, pre_edge_star=self.XANES_norm(energy,I0,I1,fit_s,fit_e,
                                                 pre_start,pre_end,
                                                 post_start,post_end,functype)
        #calculation : Neg.
        fit_s = self.dialog.dsb_neg_bk_start.value()
        fit_e = self.dialog.dsb_neg_bk_end.value()
        params.mt, pre_edge =self.XANES_norm(energy,I0,I2,fit_s,fit_e,
                                        pre_start,pre_end,
                                        post_start,post_end,functype)
        self.ax.plot(params.energy,params.mt_star,color='r',label='$\mu t^*$')
        self.ax.plot(params.energy,params.mt,color='k',label='$\mu t$')
        params.delta_mt = params.mt_star - params.mt
        self.ax_right.plot(params.energy,params.delta_mt,color='b',marker='.',ls='-')
        if self.u.checkBox_2.isChecked():
            axis = [self.ax_dialog,self.ax_dialog_right]
            for ax_ in axis:
                while len(ax_.lines) !=0:
                    ax_.lines.pop()
            axis[0].plot(params.energy,I1/I0,color='r',ls='-',label='$\mu t$:pos')
            axis[0].plot(params.energy,I2/I0,color='k',ls='-',label='$\mu t$:neg')
            axis[1].plot(params.energy,params.delta_mt,color='k',ls='-',label='$\delta\mu t$')
            axis[0].plot(params.energy,pre_edge_star,color='r',ls='--',label='bk: pos')
            axis[0].plot(params.energy,pre_edge,color='k',ls='--',label='bk: neg')
            for ax_ in axis:
                ax_.relim()
                ax_.autoscale_view()
            axis[0].legend(loc=4)
            self.canvas_dialog.draw()
        self.ax.legend(loc=4)
        for ax_ in [self.ax,self.ax_right]:
            ax_.relim()
            ax_.autoscale_view()
        self.canvas.draw()

    def plot_each_XANES(self):
        #print len(params.cbs)
        # axis = [self.ax_I0,self.ax_ut,self.ax_dut]
        # for ax_ in axis:
        #     while len(ax_.lines) !=0:
        #         ax_.lines.pop()
        fig = self.ax_I0.figure
        fig.delaxes(self.ax_I0)
        fig.delaxes(self.ax_ut)
        fig.delaxes(self.ax_dut)
        self.ax_I0 = fig.add_subplot(211)
        self.ax_I0.set_xlabel("Energy / eV")
        self.ax_I0.set_ylabel("Intensity")
        self.ax_I0.set_title('I0')
        self.ax_ut = fig.add_subplot(212)
        self.ax_ut.set_xlabel("Energy / eV")
        self.ax_ut.set_ylabel("$\mu$ t")
        self.ax_ut.set_title('Absorption')
        self.ax_dut = self.ax_ut.twinx()
        self.ax_dut.set_ylabel("$\Delta\mu$ t")
        self.Ipos, self.Ineg = [x.rstrip().replace(' ','') for x in self.u.lE_posneg.text().split(',')]
        energy = np.zeros(0)
        # if len(params.cbs) != 0:
        #     params.energy = []
        #     i = 0
        rb = params.rbs.checkedButton()
        switch = "not read"
        #print rb.objectName()
        #Fdat = open(rb.objectName(),"rU")
        Fdat = PD.read_csv(rb.objectName(),delim_whitespace=True)
        I0 = []
        I1 = []
        I2 = []
        energy = Fdat['SetEne'].values
        I0 = Fdat['I0'].values
        I1 = Fdat[self.Ipos].values
        I2 = Fdat[self.Ineg].values
        # for line in Fdat:
        #     line.rstrip()
        #     t_array = line.split()
        #     if switch == "not read":
        #         switch = "read"
        #     elif switch == "read":
        #         I0.append(float(t_array[3]))
        #         I1.append(float(t_array[4]))
        #         I2.append(float(t_array[5]))
        #         energy = np.append(energy,float(t_array[0]))
        pre_start = self.u.dsB_pre_start.value()
        pre_end = self.u.dsB_pre_end.value()
        post_start = self.u.dsB_post_start.value()
        post_end = self.u.dsB_post_end.value()
        self.ax_I0.plot(energy,I0,color='k')
        ut_star = np.array(I1)/np.array(I0)
        # t_ut_corr = (t_ut - np.average(t_ut[self.find_near(energy,pre_start):self.find_near(energy,pre_end)+1]))
        # ut_star = t_ut_corr/np.average(t_ut_corr[self.find_near(energy,post_start):self.find_near(energy,post_end)+1])
        self.ax_ut.plot(params.energy,ut_star,color='r',label='$ut_{pos}$')
        ut = np.array(I2)/np.array(I0)
        # t_ut_corr = (t_ut - np.average(t_ut[self.find_near(energy,pre_start):self.find_near(energy,pre_end)+1]))
        # ut = t_ut_corr/np.average(t_ut_corr[self.find_near(energy,post_start):self.find_near(energy,post_end)+1])
        self.ax_ut.plot(params.energy,ut,color='b',label='$ut_{neg}$')
        self.ax_ut.legend(loc=4)
        self.ax_dut.plot(params.energy,ut_star-ut,color='b',label='$\Delta ut$')
        for ax_ in [self.ax_I0,self.ax_ut,self.ax_dut]:
            ax_.relim()
            ax_.autoscale_view()
        self.canvasI0.draw()

    def func_pB11(self):
        params.sumI0, params.sumI1, params.sumI2, params.energy,params.r_stdev_ut_star, params.r_stdev_ut = self.extract_data()
        self.plotXANES(params.sumI0, params.sumI1, params.sumI2, params.energy)

    def TimeHasPassed(self):
        print (str(self.autoLoad.progressBar.value()+1) +' s has passed.')
        self.autoLoad.progressBar.setValue(self.autoLoad.progressBar.value()+1)

    def calcDecay(self):
        self.Ipos, self.Ineg = [x.rstrip().replace(' ','') for x in self.u.lE_posneg_2.text().split(',')]
        if len(params.cbs_t) != 0:
            sum_ut_pos = []
            sum_ut_neg = []
            for cb in params.cbs_t:
                if cb.isChecked():
                    I0, I1, I2, mt_star, mt =  self.readDecay(cb)
                    if len(sum_ut_pos) == 0:
                        sum_ut_pos = mt_star[:]
                        sum_ut_neg = mt[:]
                    else:
                        sum_ut_pos += mt_star
                        sum_ut_neg += mt
            return sum_ut_pos, sum_ut_neg


    def readDecay(self,button):
        fileName = re.sub(r"rB:|cB:",'',button.objectName())
        t_ = []
        I0 = []
        I1 = []
        I2 = []
        mt_star = []
        mt_ = []
        Fdat = open(fileName,"rU")
        txt = ""
        for line in Fdat:
            txt += re.sub(r"\s+",',',line.rstrip())+"\n"
        csv_buffer = io.StringIO(txt)
        f = open('Text.txt','w')
        for line in csv_buffer:
            f.write(line)
        f.close()
        csv_buffer = io.StringIO(txt)
        df = PD.read_csv(csv_buffer,dtype=np.float64)
        # print df.keys()
        t_ = df['setdelay'].values
        # if len(params.t) == 0:
        #     params.t = t_[:]
        if len(params.t) == 0:
            if len(t_)%2 == 0:
                N = int(len(t_)/2)
                params.t = df['setdelay'].values[:N]
            elif len(t_)%2 == 1:
                N = int((len(t_)-1)/2)
                params.t = df['setdelay'].values[:N]
        if len(t_)%2 == 0:
            N = int(len(t_)/2)
            params.t = df['setdelay'].values[:N]
            I0 = df['I0'].values[:N] + df['I0'].values[N:len(t_)][::-1]
            I1 = df[self.Ipos].values[:N] + df[self.Ipos].values[N:len(t_)][::-1]
            I2 = df[self.Ineg].values[:N] + df[self.Ineg].values[N:len(t_)][::-1]
            mt_star = I1/I0
            mt = I2/I0
        elif len(t_)%2 == 1:
            N = (len(t_)-1)/2 #len(t_) = 2*N + 1
            I0 = df['I0'].values[:N] + df['I0'].values[N+1:len(t_)][::-1]
            I1 = df[self.Ipos].values[:N] + df[self.Ipos].values[N+1:len(t_)][::-1]
            I2 = df[self.Ineg].values[:N] + df[self.Ineg].values[N+1:len(t_)][::-1]
            mt_star = I1/I0
            mt = I2/I0
        if len(mt_star) != len(params.t):
            button.setCheckState(QtCore.Qt.Unchecked)
            button.setEnabled(False)
            if re.search(r"cB:",button.objectName()) is None:
                for rb in params.rbs_ts.buttons():
                    if rb.objectName() == button.objectName().replace('rB:','cB:'):
                        #rb.setCheckState(QtCore.Qt.Unchecked)
                        rb.setEnabled(False)
            else:
                for cb in  params.cbs_t:
                    if cb.objectName() == button.objectName().replace('cB:','rB:'):
                        cb.setCheckState(QtCore.Qt.Unchecked)
                        cb.setEnabled(False)
        return I0, I1, I2, mt_star, mt


    def checkDecay(self):
        if len(params.cbs_t) != 0:
            fname = params.dir +"/"+"I0.csv"
            f_I0 = open(fname, "w")
            fname = params.dir +"/"+"mt_star.csv"
            f_mt_star = open(fname, "w")
            fname = params.dir +"/"+"mt.csv"
            f_mt = open(fname,"w")
            for cb in params.cbs_t:
                Fdat = open(cb.objectName(),"rU")
                info = os.path.basename(cb.objectName())
                t_ = []
                t_I0 = []
                t_mt_star = []
                t_mt = []
                for line in Fdat:
                    if re.match(r"^energy",line):
                        print ("here!")
                        pass
                    else:
                        line.rstrip()
                        t_array = line.split()
                        t_.append(t_array[1])
                        t_I0.append(t_array[3])
                        t_mt_star.append(t_array[6])
                        t_mt.append(t_array[7])
                I0 = []
                mt_star = []
                mt = []
                if len(t_)%2 == 0:
                    print ("the length of t is even")
                    i = 0
                    half = len(t_)/2
                    while i < half:
                        I0.append(float(t_I0[i])+float(t_I0[len(t_)-1-i]))
                        mt_star.append(float(t_mt_star[i])+float(t_mt_star[len(t_)-1-i]))
                        mt.append(float(t_mt[i])+float(t_mt[len(t_)-1-i]))
                        i += 1
                elif len(t_)%2 == 1:
                    i = 0
                    half = (len(t_)-1)/2
                    while i < half-1:
                        I0.append(float(t_I0[i])+float(t_I0[len(t_)-1-i]))
                        mt_star.append(float(t_mt_star[i])+float(t_mt_star[len(t_)-1-i]))
                        mt.append(float(t_mt[i])+float(t_mt[len(t_)-1-i]))
                        i += 1
                text = info+", "
                for term in I0:
                    text += str(term) +","
                f_I0.write(text+"\n")
                text = info+", "
                for term in mt_star:
                    text += str(term) +","
                f_mt_star.write(text+"\n")
                text = info+", "
                for term in mt:
                    text += str(term) +","
                f_mt.write(text+"\n")

    def plotDecay(self):
        self.ax5.clear()
        self.ax5_twin.clear()
        # self.I0 = []
        # self.I_pos = []
        # self.I_neg = []
        sum_ut_pos = []
        sum_ut_neg = []
        num = 0
        if len(params.cbs_t) != 0:
            for cb in params.cbs_t:
                num += 1
                if cb.isChecked():
                    I0, I1, I2, mt_star, mt =  self.readDecay(cb)
                    # print I1
                    if len(mt_star) != 0:
                        sum_ut_pos.append(mt_star)
                        sum_ut_neg.append(mt)
            self.calcDecay()
            self.ax5.relim()
            self.ax5_twin.relim()
            self.ax5.plot(params.t,np.mean(np.array(sum_ut_pos),axis=0),'ro-',label='pos')
            self.ax5.plot(params.t,np.mean(np.array(sum_ut_neg),axis=0),'ks-',label='neg')
            y_error = math.sqrt(np.std(np.array(sum_ut_neg)))
            # self.ax5_twin.errorbar(params.t,np.mean(np.array(sum_ut_pos),axis=0)-np.mean(np.array(sum_ut_neg),axis=0),
            #                                 yerr=y_error*np.ones(len(np.mean(np.array(sum_ut_pos),axis=0))),fmt='-o',label=
            self.ax5_twin.plot(params.t,np.mean(np.array(sum_ut_pos),axis=0)-np.mean(np.array(sum_ut_neg),axis=0),'-ob',label='difference')
            self.ax5.autoscale_view()
            self.ax5_twin.autoscale_view()
            self.ax5.legend(loc=4)
            self.canvas3.draw()
        else:
            pass

    def plot_each_Delay(self):
        # while len(self.ax4.lines) != 0:
        #     self.ax4.lines[-1].remove()
        # fig3 = self.ax4.figure
        # fig3.delaxes(self.ax4)
        # self.ax4 = fig3.add_subplot(121)
        # self.ax4.set_xlabel("t / ps")
        # self.ax4.set_ylabel("$\mu$ t")
        # self.ax4.set_title('Data')
        self.ax4.clear()
        self.ax4_dut.clear()
        objName = ""
        for rb in params.rbs_ts.buttons():
            if rb.isChecked():
                I0, I1, I2, mt_star, mt =  self.readDecay(rb)
                self.ax4.plot(params.t,mt_star,'-', marker = 'o',color=params.OR,label='pos')
                self.ax4.plot(params.t,mt,'ko-',label='neg')
                self.ax4_dut.plot(params.t,mt_star - mt,'bo-',label='difference')
                #print params.dict_mt_star[rb.objectName().replace('rB:','')]
                break
            else:
                pass
        self.ax4.relim()
        self.ax4.autoscale_view()
        self.ax4_dut.relim()
        self.ax4_dut.autoscale_view()
        self.ax4.legend(loc=4)
        self.canvas3.draw()


    def timerEvent(self, e):
        updateProgressBar = UpdateStatsThread(self.autoLoad.progressBar,self.autoLoad.spinBox.value()*10)
        # if self.u.tabWidget.currentIndex() == 2:
        # elif self.u.tabWidget.currentIndex() == 1:
        if self.autoLoad.progressBar.value() >= self.autoLoad.spinBox.value()*1000:
            self.from_list = glob.glob(self.autoLoad.tB_DatDir.toPlainText()+'/'+self.common+'*'+'.'+self.ext)
            basenames_from = []
            for f in self.from_list:
                basenames_from.append(os.path.basename(f))
            self.to_list = glob.glob(self.autoLoad.tB_cp_direction.toPlainText()+'/'+self.common+'*'+'.'+self.ext)
            basenames_to = []
            for f in self.to_list:
                basenames_to.append(os.path.basename(f))
            if self.from_list == []:
                qerror = QtWidgets.QErrorMessage()
                qerror.showMessage('The conditions you set might be wrong or you need more time to wait...')
                self.timer.stop()
                self.autoLoad.pB_exec.setText('exec auto Load')
                self.autoLoad.pB_exec.setEnabled(False)
                self.autoLoad.pB_close.setEnabled(True)
            else:
                from_path = self.autoLoad.tB_DatDir.toPlainText()+'/'
                to_path = self.autoLoad.tB_cp_direction.toPlainText()+'/'
                for f in basenames_from:
                    if not to_path+f in self.to_list:
                        shutil.copy(from_path+f,to_path+f)
                    elif os.path.getsize(from_path+f) != os.path.getsize(to_path+f):
                        shutil.copy(from_path+f,to_path+f)
                if self.u.tabWidget.currentIndex() == 2:
                    while self.scroll_layout2.count() >0:
                        b = self.scroll_layout2.takeAt(len(params.cbs_t)-1)
                        params.cbs_t.pop()
                        params.rbs_ts.removeButton(params.rbs_ts.buttons()[0])
                        b.widget().deleteLater()
                    self.checkDecay()
                    if params.dir=="":
                        dat_dir = home_dir.homePath()
                    elif params.dir!="":
                        dat_dir = params.dir
                    # FO_dialog = QtWidgets.QFileDialog(self)
                    # files = FO_dialog.getOpenFileNames(parent = None,caption="",dir=dat_dir)
                    # finfo = QtCore.QFileInfo(files[0][0])
                    self.to_list = glob.glob(self.autoLoad.tB_cp_direction.toPlainText()+'/'+self.common+'*'+'.'+self.ext)
                    files = self.to_list[:]
                    params.dir = os.path.dirname(files[0])
                    for fname in files:
                        info = QtCore.QFileInfo(fname)
                        cb = QtWidgets.QCheckBox(info.fileName())
                        cb.setObjectName(fname)
                        rb = QtWidgets.QRadioButton()
                        rb.setObjectName(fname)
                        widget = QtWidgets.QWidget()
                        hlayout = QtWidgets.QHBoxLayout()
                        widget.setLayout(hlayout)
                        cb.clicked.connect(self.plotDecay)
                        params.cbs_t.append(cb)
                        hlayout.addWidget(cb)
                        cb.toggle()
                        rb.toggled.connect(self.plot_each_Delay)
                        params.rbs_ts.addButton(rb)
                        hlayout.addWidget(rb)
                        self.scroll_layout2.addWidget(widget)
                    self.calcDecay()
                    self.plotDecay()
                    params.rbs_ts.buttons()[0].toggle()
                elif self.u.tabWidget.currentIndex() == 0:
                    params.sumI0 = []
                    params.sumI1 = []
                    params.sumI2 = []
                    while self.scroll_layout.count() >0:
                        b = self.scroll_layout.takeAt(len(params.cbs)-1)
                        params.cbs.pop()
                        params.rbs.removeButton(params.rbs.buttons()[0])
                        b.widget().deleteLater()
                    if params.dir=="":
                        dat_dir = home_dir.homePath()
                    elif params.dir!="":
                        dat_dir = params.dir
                    FO_dialog = QtWidgets.QFileDialog(self)
                    # files = FO_dialog.getOpenFileNames(parent = None,caption="",dir=dat_dir)
                    # finfo = QtCore.QFileInfo(files[0][0])
                    self.to_list = glob.glob(self.autoLoad.tB_cp_direction.toPlainText()+'/'+self.common+'*'+'.'+self.ext)
                    files = self.to_list[:]
                    params.dir = os.path.dirname(files[0])
                    for fname in files:
                        info = QtCore.QFileInfo(fname)
                        cb = QtWidgets.QCheckBox(info.fileName())
                        cb.setObjectName(fname)
                        params.cbs.append(cb)
                        cb.toggle()
                        cb.clicked.connect(self.func_pB11)
                        rb = QtWidgets.QRadioButton()
                        rb.setObjectName(fname)
                        rb.toggled.connect(self.plot_each_XANES)
                        params.rbs.addButton(rb)
                        widget = QtWidgets.QWidget()
                        hlayout = QtWidgets.QHBoxLayout()
                        widget.setLayout(hlayout)
                        hlayout.addWidget(cb)
                        hlayout.addWidget(rb)
                        self.scroll_layout.addWidget(widget)
                    params.sumI0, params.sumI1, params.sumI2, params.energy, params.r_stdev_ut_star, params.r_stdev_ut = self.extract_data()
                    if self.u.dsB_pre_start.maximum() == 30000.0:
                        self.set_sBconditions()
                    self.plotXANES(params.sumI0, params.sumI1, params.sumI2, params.energy)
                    params.rbs.buttons()[0].toggle()
                self.autoLoad.progressBar.setValue(0)
        else:
            updateProgressBar.doWork()

    def doAction(self):
        self.autoLoad.progressBar.setValue(0)
        self.common= self.autoLoad.lE_posneg.text()
        self.ext = self.autoLoad.lineEdit_2.text()
        self.from_list = glob.glob(self.autoLoad.tB_DatDir.toPlainText()+'/'+self.common+'*'+'.'+self.ext)
        self.to_list = glob.glob(self.autoLoad.tB_cp_direction.toPlainText()+'/'+self.common+'*'+'.'+self.ext)
        # print self.from_list
        if self.timer.isActive():
            self.timer.stop()
            self.autoLoad.pB_exec.setText('exec auto Load')
            self.autoLoad.pB_close.setEnabled(True)
        else:
            # print 'Timer start'
            self.autoLoad.progressBar.setValue(0)
            self.timer.start(1, self)
            self.autoLoad.pB_close.setEnabled(False)
            self.autoLoad.pB_exec.setText('Stop')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    wid = MainWindow()
    sys.exit(app.exec_())
