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
import silx.io as silxIO

countlimit = 1e3
_t = 1000
maxcount = 60

class worker(qt.QThread):
    finished = qt.pyqtSignal()
    counter = 0
    waiting = 10
    files = []
    file_added = qt.Signal(list)
    def __init__(self, dir,parent=None):
        super().__init__(parent)
        self._dir = dir

    def set_datdir(self,_dir):
        if os.path.isdir(_dir):
            self._dir = _dir
            print (f"Worker: set_directory: {self._dir}")
        else:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setText("Directory not found")
            msg.setStandardButtons(qt.QMessageBox.Ok)
            msg.exec_()

    def set_waiting_time(self,_waiting):
        self.waiting = _waiting
        print (f'Waiting time was set to {self.waiting:.1f} s')

    def run(self):
        if os.path.isdir(self._dir):
            print('worker started')
            # self.files = natsort.natsorted([self._dir+'/'+ f for f in os.listdir(self._dir) if os.path.isfile(self._dir+'/'+f) and '.dat' in f])
            while self.counter < maxcount:
                time.sleep(self.waiting)
                self.counter += 1
                _files = natsort.natsorted([self._dir+'/'+ f for f in os.listdir(self._dir) if os.path.isfile(self._dir+'/'+f) and '.dat' in f])
                if _files == self.files:
                    pass
                else:
                    print ('A new file was added.')
                    self.files = _files
                    self.file_added.emit(self.files)
                    self.counter = 0

            self.finished.emit()
        else:
            self._isRunning = False
    def stop(self):
        self._isRunning = False
        print ('worker finished')

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

        self.worker = worker('')

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
        self.scrollWidget = qt.QWidget()
        self.scrollWidget.setLayout(self.scroll_layout)

        self.scrollArea.setWidget(self.scrollWidget)

        self.sumI0 = []
        self.sumI1= []
        self.sumI2 = []
        self.cbs = []
        self.energy,self.r_stdev_ut_star, self.r_stdev_ut = [], [], []
        self.rbs = qt.QButtonGroup()

        self.qtimer = qt.QBasicTimer()
        self.counter = 0

        if sys.platform == 'win32':
            self.home_dir = os.environ['HOMEPATH']
        else:
            self.home_dir = os.environ['HOME']

        def strFilter():
            if self.rB_escan.isChecked():
                self.lE_filter.clear()
                self.lE_filter.setText('01001')
            elif self.rB_tscan.isChecked():
                self.lE_filter.clear()
                self.lE_filter.setText('\d{3}')

        self.rB_escan.toggled.connect(strFilter)
        self.rB_tscan.toggled.connect(strFilter)

        def selectDir():
            if self.lineEdit.text()=="" or not os.path.isdir(self.lineEdit.text()):
                dat_dir = self.home_dir
            elif os.path.isdir(self.lineEdit.text()):
                dat_dir = self.lineEdit.text()
            FO_dialog = qt.QFileDialog(self)
            f = FO_dialog.getExistingDirectory(self, "Select a directory", dat_dir,)
            if f:
                self.lineEdit.clear()
                self.lineEdit.setText(f)
                self.worker.set_datdir(f)
                _arr = f.split('/')
                self.textEdit.clear()
                self.textEdit.append(_arr[-1])

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
                    self.worker.set_datdir(os.path.dirname(files[0][0]))
                    finfo = qt.QFileInfo(files[0][0])
                    self.lineEdit.clear()
                    self.lineEdit.setText(finfo.path())
                    self.textBrowser.clear()

                    try:
                        _header = re.match(r'([a-z]+|[A-Z]+)', os.path.basename(files[0][0])).group(0)
                    except Exception as e:
                        _header = "__No_header__"
                    self.textBrowser.append(_header)

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
        self.pushButton_2.clicked.connect(selectDir)
        self.checkBox.toggled.connect(self.run_worker_process)
        self.pushButton_3.clicked.connect(self.saveData)
        self.lineEdit.textEdited.connect(self.refresh_dir)
        self.worker.finished.connect(self.display_worker_finished)
        self.worker.file_added.connect(self.auto_update_files)
        self.show()

    def run_worker_process(self):
        try:
            if (not self.checkBox.isChecked()) and self.worker.isRunning():
                self.worker.stop()
                msg = qt.QMessageBox()
                msg.setIcon(qt.QMessageBox.Warning)
                msg.setText(f"The worker stopped")
                msg.setStandardButtons(qt.QMessageBox.Ok)
                msg.exec_()
            elif self.checkBox.isChecked() and (not self.worker.isRunning()):
                self.worker.set_datdir(self.lineEdit.text())
                print (self.spinBox_3.value())
                self.worker.set_waiting_time(self.spinBox_3.value())
                self.refresh_dir()
                self.worker.files = []
                msg = qt.QMessageBox()
                msg.setIcon(qt.QMessageBox.Information)
                msg.setText("auto-updating started")
                msg.setStandardButtons(qt.QMessageBox.Ok)
                qt.QTimer.singleShot(1000, lambda : msg.done(0))
                msg.exec_()
                self.worker.start()
            else:
                msg = qt.QMessageBox()
                msg.setIcon(qt.QMessageBox.Warning)
                msg.setText(f"The worker does not work, {self.worker.isRunning()}, {self.checkBox.isChecked()}")
                msg.setStandardButtons(qt.QMessageBox.Ok)
                msg.exec_()
        except Exception as e:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setText(str(e))
            msg.setStandardButtons(qt.QMessageBox.Ok)
            msg.exec_()

    def auto_update_files(self,files):
        self.sumI0 = []
        self.sumI1 = []
        self.sumI2 = []
        while self.scroll_layout.count() > 0:
            b = self.scroll_layout.takeAt(len(self.cbs) - 1)
            self.cbs.pop()
            self.rbs.removeButton(self.rbs.buttons()[0])
            b.widget().deleteLater()
        if self.lineEdit.text() == "" or not os.path.isdir(self.lineEdit.text()):
            dat_dir = self.home_dir
        elif os.path.isdir(self.lineEdit.text()):
            dat_dir = self.lineEdit.text()

        try:
            if files:
                for fname in natsort.natsorted(files):
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

    def display_worker_finished(self):
        msg = qt.QMessageBox()
        msg.setIcon(qt.QMessageBox.Information)
        msg.setText(f"The worker finished")
        msg.setStandardButtons(qt.QMessageBox.Ok)
        msg.exec_()

    def refresh_dir(self):
        while self.scroll_layout.count() > 0:
            b = self.scroll_layout.takeAt(len(self.cbs) - 1)
            self.cbs.pop()
            self.rbs.removeButton(self.rbs.buttons()[0])
            b.widget().deleteLater()

    def saveData(self):
        if self.plot_xas.getCurve() and os.path.isdir(self.lineEdit.text()):
            df = {}
            xaxis= self.rB_tscan.isChecked()*('delay/ps')+self.rB_escan.isChecked()*('Energy/eV')
            for _legend in ['pos','neg','diff']:
                curve = self.plot_xas.getCurve(legend=_legend)
                _d = curve.getData()
                if _legend == 'pos':
                    df[xaxis] = _d[0]
                df[_legend] = _d[1]
                if _legend == 'diff':
                    df[f'err_{_legend}'] = _d[-1]
            pd.DataFrame(df)[[xaxis,'pos','neg','diff',f'err_{_legend}']].to_csv(f'{self.lineEdit.text()}/{self.textBrowser.toPlainText()}_avg.csv',
                        index=False,sep=' '
                        )
            silxIO.save1D(f'{self.lineEdit.text()}/{self.textBrowser.toPlainText()}_avg.spec',df[xaxis], [df['pos'],df['neg'],df['diff'],df['err_diff']],filetype='spec',csvdelim=' ',
                          xlabel=xaxis, ylabels=['pos','neg','diff',f'err_{_legend}'])

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
                        _label = 'SetEne'*self.rB_escan.isChecked() + 'setdelay'*self.rB_tscan.isChecked() 
                        if i == 0:
                            energy = Fdat[_label].values
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
                            cb.setCheckState(qt.Qt.Unchecked)
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
                   np.std(np.array(each_ut),axis=0)/math.sqrt(len(checkedCB_objN)),\
                   np.array(each_ut_star), np.array(each_ut)
        else:
            [None]*6

    def func_pB11(self):
        self.sumI0, self.sumI1, self.sumI2, self.energy,self.r_stdev_ut_star, self.r_stdev_ut, self.each_xas_on, self.each_xas_off = self.extract_data()
        if not 'NoneType' in str(type(self.sumI0)):
            # yerr = np.sqrt(self.r_stdev_ut_star**2 + self.r_stdev_ut**2)
            self.plotXANES(self.sumI0, self.sumI1, self.sumI2, self.each_xas_on, self.each_xas_off, self.energy)
        else:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setText("No data found")
            msg.setStandardButtons(qt.QMessageBox.Ok)
            msg.exec_()

    def plotXANES(self, I0, I1, I2, arr_xas_on, arr_xas_off, energy):
        self.plot_xas.remove(kind=('curve'))
        datdir = self.lineEdit.text()
        # print (os.path.basename(datdir))
        self.plot_xas.setGraphTitle(os.path.basename(datdir))
        if self.rB_escan.isChecked():
            xas_pos = I1/I0
            xas_pos = (xas_pos-xas_pos[:self.spinBox.value()].mean())/(xas_pos[-self.spinBox.value():].mean()-xas_pos[:self.spinBox.value()].mean())

            xas_neg = I2/I0
            xas_neg = (xas_neg-xas_neg[:self.spinBox.value()].mean())/(xas_neg[-self.spinBox.value():].mean()-xas_neg[:self.spinBox.value()].mean())
            self.plot_xas.addCurve(energy, xas_pos,legend="pos", symbol = 'x')
            self.plot_xas.addCurve(energy, xas_neg, legend="neg", symbol = 'x')

            each_xas_on_norm = (arr_xas_on-np.vstack(arr_xas_on[:,:self.spinBox.value()].mean(axis=1)))/np.vstack(arr_xas_on[:,-self.spinBox.value():].mean(axis=1)-arr_xas_on[:,:self.spinBox.value()].mean(axis=1))
            each_xas_off_norm = (arr_xas_off-np.vstack(arr_xas_off[:,:self.spinBox.value()].mean(axis=1)))/np.vstack(arr_xas_off[:,-self.spinBox.value():].mean(axis=1)-arr_xas_off[:,:self.spinBox.value()].mean(axis=1))

            diff_xas = each_xas_on_norm.mean(axis=0) - each_xas_off_norm.mean(axis=0)
            err_diff_xas = np.std(each_xas_on_norm - each_xas_off_norm,axis=0)/np.sqrt(each_xas_on_norm.shape[0])
            
            self.plot_xas.addCurve(energy, diff_xas, legend="diff",yaxis='right', symbol = 'o',yerror=err_diff_xas)
            self.plot_xas.setGraphXLabel('Energy [eV]')


        elif self.rB_tscan.isChecked():
            xas_pos = I1/I0
            xas_neg = I2/I0
            delays_all = np.round(energy)
            edelays = np.unique(delays_all)
            print (edelays)
            df = {
                'pos': np.array([]),
                'neg': np.array([]),
                'diff': np.array([]),
                'err': np.array([])
                }
            for dly in edelays:
                sel = np.where(np.abs(delays_all - dly) < 1)
                df['pos'] = np.append(df['pos'],xas_pos[sel].mean())
                df['neg'] = np.append(df['neg'],xas_neg[sel].mean())
                df['diff'] = np.append(df['diff'],(xas_pos[sel]-xas_neg[sel]).mean())
                df['err'] = np.append(df['err'],np.std(xas_pos[sel]-xas_neg[sel])/math.sqrt(xas_pos[sel].shape[0]))
            
            self.plot_xas.addCurve(edelays, df['pos'], legend="pos", symbol = 'x')
            self.plot_xas.addCurve(edelays, df['neg'], legend="neg", symbol = 'x')
            self.plot_xas.addCurve(edelays, df['diff'], legend="diff",yaxis='right', symbol = 'o',yerror=df['err'])
            self.plot_xas.setGraphXLabel('delay [ps]')

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
        _label = 'SetEne'*self.rB_escan.isChecked() + 'setdelay'*self.rB_tscan.isChecked() 
        energy = Fdat[_label].values
        I0 = Fdat['I0'].values
        I1 = Fdat[self.Ipos].values
        I2 = Fdat[self.Ineg].values

        self.plot_xas_each.addCurve(energy, I1/I0,legend='pos', symbol = 'x')
        self.plot_xas_each.addCurve(energy, I2/I0,legend='neg', symbol = 'x')
        self.plot_xas_each.addCurve(energy, I1/I0-I2/I0,legend='diff',yaxis='right', symbol = 'o')
        self.plotI0.addCurve(energy, I0,linewidth=1.5)
        _xlabel = self.rB_escan.isChecked()*'Energy [eV]' + self.rB_tscan.isChecked()*'delay [ps]'
        self.plot_xas_each.setGraphXLabel(_xlabel)
        self.plotI0.setGraphXLabel(_xlabel)


if __name__ == '__main__':
	window = Ui()
	app.exec_()
