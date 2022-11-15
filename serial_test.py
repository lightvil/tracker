import serial
from threading import Thread, Event
from time import sleep

__serial_port = serial.Serial(
  #port="/dev/ttyTHS1",
  port="/dev/ttyUSB0",
  baudrate=9600,
  bytesize=serial.EIGHTBITS,
  parity=serial.PARITY_NONE,
  stopbits=serial.STOPBITS_ONE,
  timeout = 1,
)

def serial_thread_loop():
    try:
        print('serial_thread_loop: START')
        while True:
            if serial_thread_event.isSet(): 
                break
            c = __serial_port.readline().decode()
            c = c.strip()
            if len(c) == 0:
                continue;
            print("SERIAL : " + c)
    finally:
        print('serial_thread_loop: END')

serial_thread_event = Event()
serial_thead = Thread(target=serial_thread_loop)
serial_thead.start()

sleep(1)
__serial_port.write(b"Z\r\n")
__serial_port.flush()
sleep(1)
__serial_port.write(b"X\r\n")
__serial_port.flush()
sleep(1)

print('start writing to serial port')
try :
    while True:
        line = input()
        line = line.strip()
        if line == 'q':
            print('keyboard interrupt : END')
            break
        line = line + "\r\n"
        encoded = line.encode()
        print("WRITING:" + str(encoded))
        __serial_port.write(encoded)
        __serial_port.flush()
        #print('x' + str(x));
        #__serial_port.write(b'x')
        #__serial_port.write(str(x).encode())
        #__serial_port.flush()
except KeyboardInterrupt:
  print('keyboard interrupt : END')
finally:
  __serial_port.close()
  serial_thread_event.set();

