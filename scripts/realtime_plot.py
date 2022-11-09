#! /home/young/envs/nrf5/bin/python
import csv
import queue
import random
import struct
import sys
import time

from numpy import *
import numpy as np

import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
import serial


path = ''
port = ''
freq = 20  # kHz
period = 1/(1000*freq)  # sec
timerange = 1000  # unit:ms, range for x-axis
n = 0
fp = ''


class MyThread(QtCore.QThread):
    """
    Data processing thread
    """
    signal = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(MyThread, self).__init__(parent=parent)

    def __del__(self):
        self.exiting = True
        self.wait()

    def run(self):
        if(fp != ""):
            self.writer = csv.writer(fp)  # fp: file name

        self.Xm = np.linspace(0, 0, freq * timerange) #show samples for timerange (ms)

        while port.readable():
            # read 244 bytes
            # note that it is blocking!
            self.value = port.read(244)

            # 122's of little endian unsigned short (122 * 2 bytes)
            self.data = struct.unpack('<122H', self.value)  # type data1: tuple, type data1[i]: int
            self.length = len(self.data)
            # assert self.length == 122
            
            i = 0
            while i < self.length - 2:  # length - 2: remove last number (m_adc_evt_counter)
                if self.data[i] != '' and self.data[i] != '\n':
                    global n
                    if fp != '':  # save data
                        time = n * period
                        self.savedata = (time, self.data[i])  # savedata = (X,Y), X=time & Y=value
                        n = n + 1
                        self.writer.writerow(self.savedata)

                    self.Xm[:-1] = self.Xm[1:]  ##Xm[]=[0,1,2,...n]: Xm{:-1]=[0,1,2...n-1], Xm[1:]=[1,...n]: change Xm to [1,2,...n,n]
                    #self.Xm[-1] = int(self.data[i]) ##Xm: [1,2,...n,data[i]]
                    self.Xm[-1] = self.data[i]  ##Xm: [1,2,...n,data[i]]
                i = i + 1

            # emit a signal every 244 bytes
            self.signal.emit(self.Xm)


class LoginWidget(QtGui.QWidget):
    """
    User interface
    """
    def __init__(self, parent=None):
        super(LoginWidget, self).__init__(parent)

        self.myThread = MyThread()
        
        layout = QtGui.QHBoxLayout()
        seclayout = QtGui.QVBoxLayout()

        self.tb = QtGui.QToolBar()
        self.times = QtCore.QTime()

        # Command buttons
        self.startbutton = QtGui.QPushButton('Start Plotting')
        self.stopbutton = QtGui.QPushButton('Stop Plotting')
        self.savebutton = QtGui.QPushButton('Save File')

        # Setting
        boxSetting = QtGui.QGroupBox('Setting')
        settingLayout = QtGui.QVBoxLayout()
        
        # USB Port
        comLayout = QtGui.QHBoxLayout()
        comLabel = QtGui.QLabel("Port              ")
        self.comline = QtGui.QLineEdit(self)
        self.comline.setText("COMx")
        comLayout.addWidget (comLabel)
        comLayout.addWidget (self.comline)
        settingLayout.addLayout(comLayout)
        
        # Rate
        rateLayout = QtGui.QHBoxLayout()
        settingLayout.addLayout(rateLayout)
        
        # ConnectButton
        self.connectbutton = QtGui.QPushButton("Connect")
        settingLayout.addWidget(self.connectbutton)
        self.connectbutton.clicked.connect(self.connectport)
        boxSetting.setLayout(settingLayout)
        
        # Control
        boxButtons = QtGui.QGroupBox('Control')
        buttonlayout = QtGui.QVBoxLayout()
        buttonlayout.addWidget(self.savebutton)
        buttonlayout.addWidget(self.startbutton)
        buttonlayout.addWidget(self.stopbutton)
        boxButtons.setLayout(buttonlayout)
        
        seclayout.addWidget(boxSetting, 20)
        seclayout.addWidget(boxButtons, 80)
        
        layout.addLayout(seclayout,10)

        self.startbutton.clicked.connect(self.start)
        self.stopbutton.clicked.connect(self.stop)
        self.savebutton.clicked.connect(self.save)

        self.startbutton.setEnabled(False)
        self.stopbutton.setEnabled(False)
        self.savebutton.setEnabled(False)

        ##Plot
        graphlayout = QtGui.QVBoxLayout()
        self.plot1 = pg.PlotWidget()
        self.plot1.setLabels(title='Streaming data', bottom='Samples', left='ADC Value')
        graphlayout.addWidget(self.plot1)
        layout.addLayout(graphlayout,90)
        self.setLayout(layout)

        ##for multichannel: active other curves
        self.curve1 = self.plot1.getPlotItem().plot()
        """self.curve2 = self.plot2.getPlotItem().plot()
        self.curve3 = self.plot3.getPlotItem().plot()
        self.curve4 = self.plot4.getPlotItem().plot()"""

        #self.windowWidth = 100000
        self.Yvalue = np.linspace(0, 0, 4096)  # Set Y
        #self.Xvalue = linspace(0,100,2)  ##Set Xvalue
        #self.ptr=0

        self.finished = True
        self.run = False

    # Command buttons
    def connectport(self):
        if (self.comline.text() != ''):
            global port

            # which baud rate it would choose?
            port = serial.Serial(self.comline.text(), 1000000)
            self.savebutton.setEnabled(True)
            self.startbutton.setEnabled(True)
            
    # Graph
    def plotter(self, data):
        """
        MyThread notifies fresh data

        fresh data is displayed as a line plot
        """
        if self.run == True:
            self.Yvalue = data
            if self.finished == True:
                self.finished = False
                # Here: data plot
                self.curve1.setData(self.Yvalue)
                """self.curve2.setData(self.Yvalue)
                self.curve3.setData(self.Yvalue)
                self.curve4.setData(self.Yvalue)"""
                self.finished = True
    
    # Commands
    def start(self):
        if port.writable():
            port.write(b'1\r\n')
            self.stopbutton.setEnabled(True)
            print('send')
        self.run = True
        self.times.start()

        # start a data acquisition thread
        self.myThread.start()
        self.myThread.signal.connect(self.plotter)

    def stop(self):
        global fp

        if (fp != ''):
            fp.close()
        
        self.run = False
        
        if port.writable():
            port.write(b'2\r\n')
            print('stop')

    def save(self):
        self.fname = QtGui.QFileDialog.getSaveFileName(self, "Save File", "", "Text files (*.csv)")
        self.path = self.fname[0]
        print(self.path)
        global fp
        fp = open(self.path, "a", newline="")
        print(fp)
        if (fp != ''):
            self.writer=csv.writer(fp)
            self.header= ("Time(s)","Value (ADC)")
            self.writer.writerow(self.header)
    ##Commands done


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.centralwidget = QtGui.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.login_widget_1 = LoginWidget(self)
        self.horizontalLayout.addWidget(self.login_widget_1)

    def confirmExit(self):
        self.ret = QtGui.QMessageBox.warning(self, "Application", "Exit?",
                                             QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        if self.ret == QtGui.QMessageBox.Cancel:
            return False
        return True
    
    def closeEvent(self, event):
        if (self.confirmExit()):
            global fp
            fp.close()
            event.accept()
        else:
            event.ignore()
    
       
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    w = MainWindow()
    w.setWindowTitle('Real time recording')
    w.show()
    sys.exit(app.exec_())
