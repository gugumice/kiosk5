#!/usr/bin/env python3
import threading
from kiosk_bcr import BarcodeReader
import kiosk_config
import argparse
import os, sys
from kiosk_utils import Ticket, TicketPurpose, send_ticket
import kiosk_service
import logging
from queue import Queue

queue_from_gui = Queue() # Queue for receiving messages from service thread
queue_to_gui = Queue() # Queue for sending messages to service thread
polling_int = 0.5

logging.basicConfig(
    format="%(asctime)s - %(message)s",
    level=os.environ.get("LOGLEVEL", "DEBUG")
)

def main():
    global config, queue_from_gui, queue_to_gui, polling_int    
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
    # Start service thread
    # Start service thread
    th_ev = threading.Event()
    t1 = threading.Thread(
        target=kiosk_service.service_thread,
        kwargs=dict(
            th_ev=th_ev,
            polling_int=polling_int,
            config=config,
            queue_from_gui=queue_from_gui,
            queue_to_gui=queue_to_gui,
        ),
        daemon=True)
    t1.start()
    logging.info("Service_thread: {}".format(t1.is_alive()))
    running = True
    try:
        while running:
            print('.', end='', flush=True)  # Print a dot to indicate the listener is running
            threading.Event().wait(1)
            if not queue_to_gui.empty():
                message = queue_to_gui.get()
                logging.debug(f"Message from queue: {message.ticket_value}: {message.ticket_type}")
                if isinstance(message, Ticket):
                    # Process the ticket
                    logging.info(f"Processing ticket: {message.ticket_value} of type {message.ticket_type}")
                else:
                    logging.warning(f"Unknown message type in queue: {type(message)}")
        t1.thread.join()
    except KeyboardInterrupt:
        logging.info('Keyboard interrupt received, stopping barcode reader')
        sys.exit(1)
    
    # Start the main loop of the application    


    
if __name__ == '__main__':
    print('Starting kiosk service...')
    main()