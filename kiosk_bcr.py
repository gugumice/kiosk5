#!/usr/bin/env python3

import serial
import logging
import time
from queue import Queue

running = False

class BarcodeReader(object):
    '''A class to read barcodes from a serial port and process them with a callback function.'''
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, timeout=1, callback=None, bounce=2, config=None, queueTX:Queue=None, ):
        """
        Initialize the BarcodeReader with the given serial port, baud rate, and callback function.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._callback = callback
        self.serial_connection = None
        self.running = False
        self.bounce = bounce
        self._bounce_timer = None
        self._config = config
        self._queueTX = queueTX
        self.status = None

    def start(self):
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logging.info(f"Barcode reader started on {self.port}")
            self.running = True
            self.status = f"OK_opn BC{self.port}"
        except serial.SerialException as e:
            logging.error(e)
            self.status = f"Err_opn BC: {self.port}"
    
    def _cb(self, *args, **kwargs):
        """
        Internal callback function to handle the barcode read event.
        Calls the user-defined callback if provided.
        """
        if self._callback:
            self._callback(*args, **kwargs)
        else:
            logging.warning("No callback function defined for barcode reader.")
    
    def next(self):
        try:
            if self.serial_connection.in_waiting > 0:
                barcode = self.serial_connection.readline().decode('utf-8').strip()
                self.status = f"OK_read {self.port}"
                if barcode:
                    logging.info(f"Barcode read: {barcode}")
                    if self._bounce_timer is None or time.time() > self._bounce_timer + self.bounce:
                        self._bounce_timer = time.time()
                        self._cb(barcode, self._config, self._queueTX)
                    else:
                        logging.debug(f"Barcode {barcode} ignored due to bounce protection.")

        except serial.SerialException as e:
            logging.error(f"Error reading from barcode reader: {e}")
            self.status = f"Err_read {self.port}"
    
    def stop(self):
        """
        Stop the barcode reader by closing the serial connection.
        """
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()
            logging.info("Barcode reader stopped.")
            self.status = f"Stopped {self.port}"
def bc_callback(*args):
    """Callback function to handle the barcode read event."""
    barcode = args[0] if args else "No barcode"
    print(f"Received barcode: {barcode}")

def main():
    """Main function to initialize and run the barcode reader."""
    global running
    logging.basicConfig(format="%(levelname)s:%(asctime)s - %(message)s", level=logging.DEBUG)
    logging.info("Starting barcode reader...")
    bc_reader = BarcodeReader(port='/dev/ttyACM0',baudrate=9600,callback=bc_callback, bounce=5)
    print(bc_reader.status)
    running = bc_reader.running
    while running:
        print('.', end='', flush=True)  # Print a dot to indicate the listener is running
        bc_reader.next()
        time.sleep(1)
    bc_reader.stop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Barcode reader stopped by user.")
        running = False
