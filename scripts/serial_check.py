#! /home/young/envs/nrf5/bin/python
#Auto connect between nrf52840 & nrf52832, read data and write in console

from numpy import *
from pyqtgraph.Qt import QtGui, QtCore
from random import randrange, uniform
from textwrap import wrap
import pyqtgraph as pg
import serial
import struct
import time

# Create object serial port
# portName = "COM6"
portName = "/dev/ttyACM0"
baudrate = 1000000
ser = serial.Serial(portName, baudrate)
state = 0

##print format: if real data is 28-29 -> 2928 -> 10536 -> :536.    ASCII code - 48 is value

def read_data():
    #start=time.time()
    global value
    value = ser.read(244)
    data1 = struct.unpack('<122H', value) #type data1: tuple, type data1[i]: int
    print(data1[121])

def send_data():
    ser.write(b'1\r\n')

### MAIN PROGRAM #####

while ser.writable() and state == 0:
    send_data()
    state=1

while ser.readable():
    read_data()
