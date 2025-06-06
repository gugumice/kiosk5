#!/usr/bin/env python3
import threading
from kiosk_bcr import BarcodeReader
import kiosk_config
import argparse
import os, sys
from kiosk_utils import Ticket, TicketPurpose, send_ticket
import logging
from queue import Queue

queue_from_iface = Queue() # Queue for receiving messages from service thread
queue_from_serv = Queue() # Queue for sending messages to service thread

def main():
    global config, queue_from_iface, queue_from_serv
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="EGL testing report kiosk application.")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="file",
        help="Name config file. Default: kiosk.ini",
        default=os.path.join(os.getcwd(),'kiosk.ini'),
    )
    args = parser.parse_args()
    if not os.path.isfile('{}'.format(args.config)):
        print('Config file not found in current directory.')
        sys.exit(1)
    # Read the config file
    config = kiosk_config.read_config(os.path.join(os.getcwd(),'kiosk.ini'))

    #Set logging
    if config["log_file"] is None:
        logging.basicConfig(format="%(asctime)s - %(message)s", level=os.environ.get('LOGLEVEL', config['log_level']).upper())
        
        #logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
    else:
        logging.basicConfig(
            format="%(asctime)s - %(message)s",
            filename=config["log_file"],
            filemode="w",
            level=os.environ.get('LOGLEVEL', config['log_level']).upper(),
        )
    logging.info('Starting kiosk service'.format(config))
    serv_thread = threading.Thread(target=service_thread, daemon=True)
    serv_thread.start()
    running = True
    try:
        while running:
            threading.Event().wait(1)
            if not queue_from_serv.empty():
                message = queue_from_serv.get()
                logging.debug(f"Message from queue: {message.ticket_value}: {message.ticket_type}\n")
                if isinstance(message, Ticket):
                    # Process the ticket
                    logging.info(f"Processing ticket: {message.ticket_value} of type {message.ticket_type}")
                    if message.ticket_type == TicketPurpose.BC and message.ticket_value == 'Exit':
                        logging.info('Exit ticket received, stopping service thread')
                        running = False
                        # Handle barcode ticket
                        logging.info(f"Handling barcode ticket: {message.ticket_value}")
                        process_barcode(message.ticket_value)
                else:
                    logging.warning(f"Unknown message type in queue: {type(message)}")
        serv_thread.join()
    except KeyboardInterrupt:
        logging.info('Keyboard interrupt received, stopping barcode reader')
        sys.exit(1)
    
    # Start the main loop of the application    


def service_thread():
    global queue_from_serv, queue_from_iface, config
    # Initialize the barcode reader
    
    send_ticket('Initializing barcode reader...',ticket_type=TicketPurpose.BC, queue_tx=queue_from_serv)

    barcode_reader = BarcodeReader(
        bounce=config['bc_reader_bounce'],
        port=config['bc_reader_port'],
        baudrate=config['bc_reader_boudrate'],
        timeout=config['bc_timeout'],
        callback=process_barcode
    )
    send_ticket('Starting barcode reader on {}'.format(config['bc_reader_port']),ticket_type=TicketPurpose.BC, queue_tx=queue_from_serv)
    # Start the barcode reader
    while not barcode_reader.running:
        threading.Event().wait(1)
        barcode_reader.start()
    send_ticket('Barcode reader started on {}'.format(config['bc_reader_port']),ticket_type=TicketPurpose.BC, queue_tx=queue_from_serv)
    #Barcode reader loop
    while barcode_reader.running:
        threading.Event().wait(1)
    # If error reading data from barcode
    barcode_reader.stop()
    send_ticket('Barcode reader stopped', ticket_type=TicketPurpose.BC, queue_tx=queue_from_serv)
    send_ticket('Exit', ticket_type=TicketPurpose.BC, queue_tx=queue_from_serv)
    
def process_barcode(barcode):
    send_ticket(ticket_value=f"Barcode received: {barcode}", ticket_type=TicketPurpose.BC, queue_tx=queue_from_serv)
    

if __name__ == '__main__':
    print('Starting kiosk service...')
    main()