import serial

with serial.Serial() as ser:
    ser.baudrate = 19200
    ser.port = '/dev/ttyACM0'
    ser.open()
    ser.write(b'hello')