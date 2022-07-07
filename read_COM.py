import serial

while 1:
    with serial.Serial('/dev/ttyACM0', 19200, timeout=10) as ser:
        print(ser.is_open)
        line = ser.readline()
        print(line)