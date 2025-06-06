#!/usr/bin/env python3

import serial
import threading
import logging
import time

from kiosk_utils import TicketPurpose, Ticket

class BarcodeReader(object):
    '''A class to read barcodes from a serial port and process them with a callback function.'''
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, timeout=1, callback=None, bounce = 2):
        """
        Initialize the BarcodeReader with the given serial port, baud rate, and callback function.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.callback = callback
        self.serial_connection = None
        self.running = False
        self.bounce = bounce
        self._bounce_timer = None
        self._lock = threading.Lock()

    def start(self):
        """
        Start the barcode reader by opening the serial connection and initiating the reading loop.
        """
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            logging.info(f"Barcode reader started on {self.port}")
        except serial.SerialException as e:
            logging.error(f"{e}")
            self.running = False

    def stop(self):
        """
        Stop the barcode reader by closing the serial connection.
        """
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()
            logging.info("Barcode reader stopped.")

    def _read_loop(self):
        """
        Internal method to continuously read data from the barcode scanner and send it to the callback.
        """
        while self.running:
            threading.Event().wait(self.timeout)
            if self._bounce_timer is not None and time.time() > self._bounce_timer + self.bounce:
                self._bounce_timer = None
            try:
                if self.serial_connection.in_waiting > 0:
                    barcode = self.serial_connection.readline().decode('utf-8').strip()
                    if barcode:
                        if not self._bounce_timer and self.callback:
                            self._bounce_timer = time.time()
                            with self._lock:
                                self.callback(barcode)
            except Exception as e:
                logging.error(e)
                self.running = False

def bc_callback(barcode):
    print(f"Received barcode: {barcode}")

def main():
    barcode_reader = BarcodeReader(callback=bc_callback,bounce=5)
    while not barcode_reader.running:
        threading.Event().wait(1)
        logging.info('Starting reader')
        barcode_reader.start()
    while barcode_reader.running:
        threading.Event().wait(1)
        print('.')

if __name__ == '__main__':
    main()

