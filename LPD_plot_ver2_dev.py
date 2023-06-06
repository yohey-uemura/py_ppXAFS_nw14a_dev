#!/usr/bin/env /gpfs/exfel/sw/software/xfel_anaconda3/1.1.2/bin/python
import numpy as np                                                                              
import silx                                                                                     
from silx.gui import qt                                                                         
import time                                                                                     
import silx.gui.colors as silxcolors                                                            
from silx.gui.plot import Plot1D, Plot2D, PlotWidget,items                                      
import silx.gui.colors as silxcolors

qapp = qt.QApplication([])                                                                      

from xes_pc import Ui_MainWindow

from karabo_bridge import Client                                                                

Ecutoff = 3.0
Eemission = 6.0
Nmax= 20

_ip, _port = '10.253.1.64', 43252
#_ip, _port = '127.0.0.1', 43557
                                                                                                
#plot1d = Plot1D()                                                                              
#plot1d.show()


krb_client = Client('tcp://{:s}:{:d}'.format(_ip,_port),timeout=3)          
#data, metadata = krb_client.next()                                                             
# print (data['FXE_XAD_JF1M/DET/JNGFR01:daqOutput']['data.adc'].shape)
# jf_md_src = 'FXE_XAD_JF500K/DET/JNGFR03:daqOutput'
# jf_md_src = 'FXE_XAD_JF1M/DET/JNGFR01:daqOutput'

lpd_src = 'FXE_DET_LPD1M-1/DET/3CH0:xtdf'
# motor_src = 'FXE_SMS_USR/MOTOR/UM13'
# motor_src = 'FXE_AUXT_LIC/DOOCS/PPODL'

roi_x = [10,25]
roi_y = [55,70] 

cycle = 20


    
class Plot2DWithContextMenu(Plot2D):                                                            
    """This class adds a custom context menu to PlotWidget's plot area."""                      
    plotData = qt.pyqtSignal()                                                                  
    timer = qt.QBasicTimer()                                                                    
    def __init__(self, plot2d_off, plot1d_dif, hist, pB, lcdNumber, cmb, lcds, *args, **kwargs):                                                        
        super(Plot2DWithContextMenu, self).__init__( *args, **kwargs)                            
                                                                                                
        plotArea = self.getWidgetHandle()

        self.plot2d_off = plot2d_off
        self.plot1d_diff = plot1d_dif
        self.plot_diff2d = hist
        self.pB = pB
        self.cmbBox = cmb
        self.lcdNumber = lcdNumber
        # self.lcd_ppodl = lcds[0]
        # self.lcd_um02 = lcds[1]
        # self.lcd_um03 = lcds[2]
        # self.lcd_um05 = lcds[3]
        # self.lcd_um13 = lcds[4]
        
        self.lcds = lcds

        # Set plot area custom context menu                                                    
                                                                                                
        plotArea.setContextMenuPolicy(qt.Qt.CustomContextMenu)                                  
        plotArea.customContextMenuRequested.connect(self._contextMenu)

        def print_hello():
            print ("Hello")
        
        self.pB.clicked.connect(self.doAction)
        self.plotData.connect(self.plot_)
        
    def _contextMenu(self, pos):
    
        """
        Handle plot area customContextMenuRequested signal.                                
        :param QPoint pos: Mouse position relative to plot area
        # Create the context menu                                                              
        """
                                                                                                
        menu = qt.QMenu(self)
        menu.addSeparator()
        action_Refresh = menu.addAction("Refresh the data")
        self.action_autoRefresh = menu.addAction("")
        self.action_autoRefresh.setText("Refresh the plot automatically")
        plotArea = self.getWidgetHandle()
        globalPosition = plotArea.mapToGlobal(pos)
        action = menu.exec_(globalPosition)
        if action == action_Refresh:
            if self.timer.isActive():
                pass
            else:
                self.plotData.emit()
        elif action == self.action_autoRefresh:
            self.doAction()
            # self.action_autoRefresh.setText('Stop auto-refreshing')                          
    def doAction(self):
        if self.timer.isActive():
            print ("Timer stopped.")
            self.timer.stop()
            self.action_autoRefresh.setText("Refresh the plot automatically")
            self.pB.setText('start')

        else:
            print ("Timer started.")
            self.action_autoRefresh.setText('Stop auto-refreshing')
            self.count = 0
            self.lpd_on = np.zeros((256,256))
            self.lpd_off = np.zeros((256,256))
            self.xrd_on = []
            self.xrd_off = []
            self.trainids_on = np.array([])
            self.trainids_off = np.array([])
            #print (self)
            self._n = 1000
            self.hist_results = np.zeros(self._n)
            data, metadata= krb_client.next()
            
            self.plot2d_off.clear()
            self.plot1d_diff.clear()
            self.plot_diff2d.clear()
            self.motor_src = self.cmbBox.currentText()
            if self.motor_src != 'No Scan':
                tmtr = data[self.motor_src]['targetPosition.value']
                self.lcdNumber.display(tmtr)
            self.clear()
            self.pB.setText('stop')
            self.timer.start(0.025,self)

    def timerEvent(self, event):
        if self.motor_src != 'No Scan':
            try:
                start = time.time()
                data, metadata= krb_client.next()
                tid = metadata[lpd_src]['timestamp.tid']
                print ("############### "+'id {:d}'.format(tid)+" ###############")
                print ("   ######" +'client {:.3f}s'.format(time.time()-start) +"######" )
              
                start = time.time()

                lpd = data[lpd_src]['image.data'][0]
                amtr = data[self.motor_src]['actualPosition.value']
                tmtr = data[self.motor_src]['targetPosition.value']
                

                if tid%2 == 0:
                    self.lpd_on += lpd
                    self.trainids_on = np.append(self.trainids_on,tid)
                elif tid%2 == 1:
                    self.lpd_off += lpd
                    self.trainids_off = np.append(self.trainids_off,tid)
                    print ("   ######" +'Process {:.3f}s: {:d}'.format(time.time()-start,self.count) +"######" )
                    self.count += 1
                    #print (len(x),len(I0))
                if self.count > cycle:
                    start = time.time()
                    print ('plot!')
                    self.addImage(self.lpd_on,colormap=silxcolors.Colormap(name='magma'))
                    self.plot2d_off.addImage(self.lpd_off)
                    _xrd_on = self.lpd_on[roi_x[0]:roi_x[1],:].sum(axis=0)
                    _xrd_off = self.lpd_off[roi_x[0]:roi_x[1],:].sum(axis=0)
                    _xrd_on[np.isnan(_xrd_on)] = 0
                    _xrd_off[np.isnan(_xrd_off)] = 0
                    self.plot1d_diff.addCurve(np.arange(256),_xrd_on/_xrd_on.sum()-_xrd_off/_xrd_off.sum(),resetzoom=False)
                    self.plot1d_diff.addCurve(np.arange(256),_xrd_on/_xrd_on.sum(),yaxis='right',legend='evens',resetzoom=False)
                    self.plot1d_diff.addCurve(np.arange(256),_xrd_off/_xrd_off.sum(),yaxis='right',legend='odds',resetzoom=False)
                    if len(self.xrd_on) !=0:
                        self.plot_diff2d.addImage(np.array(self.xrd_on)-np.array(self.xrd_off),colormap=silxcolors.Colormap(name='viridis'))
                        print ("   ######" +'Plot {:.3f}s'.format(time.time()-start) +"######" )
                    for k in range(5):
                        _src = self.cmbBox.itemText(k)
                        _val = data[_src]['actualPosition.value']
                        self.lcds[k].display(_val)
                    self.count = 0
                elif np.abs(self.lcdNumber.value() - tmtr) > 0.01:
                    print ("plot 2")
                    _xrd_on = self.lpd_on[roi_x[0]:roi_x[1],:].sum(axis=0)
                    _xrd_off = self.lpd_off[roi_x[0]:roi_x[1],:].sum(axis=0)
                    _xrd_on[np.isnan(_xrd_on)] = 0
                    _xrd_off[np.isnan(_xrd_off)] = 0
                    self.xrd_on.append(_xrd_on/_xrd_on.sum())
                    self.xrd_off.append(_xrd_off/_xrd_off.sum())
                    self.plot_diff2d.addImage(np.array(self.xrd_on)-np.array(self.xrd_off),colormap=silxcolors.Colormap(name='viridis'))
                    self.lpd_on = np.zeros((256,256))
                    self.lpd_off = np.zeros((256,256))
                    self.count = 0
                    self.lcdNumber.display(tmtr)
            except Exception as e:
                print (e)
                pass
        elif self.motor_src == 'No Scan':
            self.plot_()

    def plot_(self):
        j = 1
        lpd_on = np.zeros((256,256))
        lpd_off = np.zeros((256,256))
        motor_src = self.cmbBox.currentText()
        while j <= 10:
            try:
                start = time.time()
                data, metadata= krb_client.next()
                tid = metadata[lpd_src]['timestamp.tid']
                print ("############### "+'id {:d}'.format(tid)+" ###############")
                print ("   ######" +'client {:.3f}s'.format(time.time()-start) +"######" )
                # print (data[jf_md_src]['data.adc'].shape)
                start = time.time()
                lpd = data[lpd_src]['image.data'][0]
                print (lpd.shape)
                #amtr = data[motor_src]['actualPosition.value']
                #tmtr = data[motor_src]['targetPosition.value']

                if tid%2 == 0:
                    lpd_on += lpd
                    #self.trainids_on = np.append(self.trainids_on,tid)
                elif tid%2 == 1:
                    lpd_off += lpd
                    #self.trainids_off = np.append(self.trainids_off,tid)
                print ("   ######" +'Process {:.3f}s'.format(time.time()-start) +"######" )
                
            except Exception as e:
                print (e)
            j += 1
        self.addImage(lpd_on,colormap=silxcolors.Colormap(name='magma'))
        self.plot2d_off.addImage(lpd_off)
        _xrd_on = lpd_on[roi_x[0]:roi_x[1],:].sum(axis=0)
        _xrd_off = lpd_off[roi_x[0]:roi_x[1],:].sum(axis=0)
        self.plot1d_diff.addCurve(np.arange(256),_xrd_on/_xrd_on.sum()-_xrd_off/_xrd_off.sum(),resetzoom=False)
        self.plot1d_diff.addCurve(np.arange(256),_xrd_on/_xrd_on.sum(),yaxis='right',legend='evens',resetzoom=False)
        self.plot1d_diff.addCurve(np.arange(256),_xrd_off/_xrd_off.sum(),yaxis='right',legend='odds',resetzoom=False)


class MainWindow(qt.QMainWindow):
    def __init__(self, *args, **kwargs):                                                        
        super(MainWindow, self).__init__(*args, **kwargs)

        self.u = Ui_MainWindow()
        self.u.setupUi(self)

        self.plot2d_off = Plot2D(backend='mpl')
        self.plot2d_off.setGraphTitle('odds')
        self.plot_diff = Plot1D(backend='mpl')
        self.plot_diff.setGraphTitle('diff')
        self.plot_diff2d = Plot2D(backend='mpl')
        lcds = [self.u.lcdNumber_ppodl, self.u.lcdNumber_um02, self.u.lcdNumber_um03,self.u.lcdNumber_um05,self.u.lcdNumber_um13]
        self.plot2d = Plot2DWithContextMenu(self.plot2d_off, self.plot_diff, self.plot_diff2d, self.u.pB_start,self.u.lcdNumber, self.u.comboBox, lcds, backend='mpl')
        self.plot2d.setGraphTitle('evens')
        
        
        self.u.comboBox.addItem('FXE_AUXT_LIC/DOOCS/PPODL')
        for x in [2,3,5,13]:
            self.u.comboBox.addItem('FXE_SMS_USR/MOTOR/UM{:02d}'.format(x))
        
        self.u.comboBox.addItem('No Scan')

        vlayout1 = qt.QVBoxLayout()
        self.u.wdgt_xes_evens.setLayout(vlayout1)
        vlayout1.addWidget(self.plot2d)
        vlayout2 = qt.QVBoxLayout()
        self.u.wdgt_xes_odds.setLayout(vlayout2)
        vlayout2.addWidget(self.plot2d_off)
        vlayout3 =qt.QVBoxLayout()
        self.u.wdgt_display.setLayout(vlayout3)
        vlayout3.addWidget(self.plot_diff)
        vlayout4 =qt.QVBoxLayout()
        self.u.wdgt_etc.setLayout(vlayout4)
        vlayout4.addWidget(self.plot_diff2d)

        
        self.show()
        

#plot2d.show()
#plot2d_off.show()
#plot_diff.show()


if __name__=="__main__":
    mw = MainWindow()
    qapp.exec_()
