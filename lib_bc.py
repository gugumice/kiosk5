#!/usr/bin/env python3
from time import sleep
import serial

def bc_callback(**kargv):
    #print('Barcode: {} {}'.format(kargv['barcode']))
    print(kargv)

class Bc(object):
    def __init__(self, port:str='/dev/ttyACM0', baudrate:int=9600, timeout:float = 1, callback_fn = None):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial_conn = None
        self._running = False
        self._error  = None
        self._callback_fn = callback_fn
    
    @property
    def running(self):
        return(self._running)
    
    @property
    def error(self):
        return(self._status)
    
    def _cb(self, *args, **kwargs):
        '''
        Callback func
        '''
        if self._callback_fn:
            return(self._callback_fn(*args, **kwargs))
        
    def start(self):
        try:
            self._serial_conn = serial.Serial(port = self._port, baudrate = self._baudrate, timeout = self._timeout)
            self._running = True
        except Exception as e:
            self._error = e
            self.stop()

    def next(self):
        if self._running and self._serial_conn.in_waiting > 0:
            try:
                barcode = self._serial_conn.readline().decode('ascii').rstrip('\r\n')
                self._cb(barcode = barcode)
            except serial.SerialException as e:
                self._error = e

    def stop(self):
        self._running = False
        if self._serial_conn and self._serial_conn.is_open:
            self._serial_conn.close()
        
def main():
    b = Bc(callback_fn = bc_callback)
    b.start()
    while b.running:
        sleep(1)
        b.next()

if __name__ == '__main__':
        main()
    
