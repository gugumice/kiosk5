
import logging
import threading
import os,re
import time
from queue import Queue
import cups

import kiosk_utils
from kiosk_bcr import BarcodeReader
import kiosk_report

config = dict()
polling_int = .5
lang = str()

conn = None #cups.Connection object placeholder

def proc_queue(msg, config=config):
    '''
    Process the message from the queue.
    '''
    logging.debug(f"Processing message: {msg}")
    kiosk_utils.speak_status(os.path.join(config['assets_loader'], 'lang_{}.wav'.format(msg[1])), background=True)

def service_thread(th_ev: threading.Event, polling_int: float = 0.5,
                   config: dict = None, queue_from_gui: Queue = None, queue_to_gui: Queue = None):
    global lang, conn
    time.sleep(1)
    
    lang = [config['default_language_index'], config['languages'][config['default_language_index']]]
    last_msg_time = time.time()
    conn = None
    queue_from_gui.queue.clear()  # Clear the queue to avoid processing old messages
    
    while conn is None:
        conn =  kiosk_report.connect_to_cups()
        if not conn:
            kiosk_utils.send_ticket(ticket_value = 
            'Error connecting to CUPS',
            ticket_type=kiosk_utils.TicketPurpose.ERR,
            ticket_animate_cycles = 1,
            queue_tx=queue_to_gui)
            time.sleep(5)

    # Check for request to delete printers in CUPS
    kiosk_utils.speak_status(os.path.join(config['assets_loader'], 'attn.wav'), background=True)
    kiosk_utils.send_ticket(ticket_value='<{}> to reset printers'.format(config['languages'][1]),
                        ticket_type=kiosk_utils.TicketPurpose.PRN,
                        ticket_animate_cycles = 1,
                        queue_tx=queue_to_gui)

    time.sleep(5)
    if not queue_from_gui.empty():
        msg = queue_from_gui.get_nowait()
        last_msg_time = time.time()
        if msg[0] == 1:
            logging.info(f"Printer reset request: {msg}")
            kiosk_report.delete_printers(conn=conn)
            kiosk_utils.send_ticket(ticket_value='Deleting all printers\non CUPS',
                    ticket_type=kiosk_utils.TicketPurpose.PRN,
                    ticket_animate_cycles = 1,
                    queue_tx=queue_to_gui)
            time.sleep(3)
            # Check for printers
    printer_ok = False
    while not printer_ok:
        printer_ok = kiosk_report.init_printer(conn = conn, config = config, queue_to_gui = queue_to_gui)
        time.sleep(3)

    # Check Connection to Cache host
        time.sleep(1)
    s ='\n'.join(('Service thread started',
                'IP: {}'.format(kiosk_utils.host_info()[0]),
                'Host: {}'.format(kiosk_utils.host_info()[1]),
                'Watchdog: {}'.format(config['watchdog_device'])
                ))
    kiosk_utils.send_ticket(ticket_value=s,
                            ticket_type=kiosk_utils.TicketPurpose.SYS,
                            ticket_animate_cycles = 3,
                            queue_tx=queue_to_gui)
    cnt = 0
    while not kiosk_utils.host_connection_ok(config['url_test']):
        cnt += 1
        kiosk_utils.send_ticket(ticket_value='Connection to\n{}\nfailed\nRetrying ({})...'
                                .format(config['url_test'].split('/')[2], cnt),
                                ticket_type=kiosk_utils.TicketPurpose.NET,
                                ticket_animate_cycles=1,
                                queue_tx=queue_to_gui)
        time.sleep(1)

    kiosk_utils.send_ticket(ticket_value='Host connection OK\n{}'.format(config['url_test'].split('/')[2][:18]),
                            ticket_type=kiosk_utils.TicketPurpose.NET,
                            ticket_animate_cycles = 1,
                            queue_tx=queue_to_gui)
    # Initialize the barcode reader
    bc_reader  = BarcodeReader(port=config['bc_reader_port'],
                            baudrate=config['bc_reader_boudrate'],
                            bounce=config['bc_reader_bounce'],
                            callback=bc_callback,
                            timeout=config['bc_timeout'],
                            config = config,
                            queueTX=queue_to_gui)
    bc_reader.start()
    cnt = 0
    while not bc_reader.running:
        cnt += 1
        kiosk_utils.send_ticket(ticket_value='Err starting BC reader:\n{}\nRetrying ({})...'.format(bc_reader.status, cnt),
                                ticket_type=kiosk_utils.TicketPurpose.BCR,
                                ticket_animate_cycles = 3,
                                queue_tx=queue_to_gui)
        bc_reader.start()
        time.sleep(5)

    kiosk_utils.send_ticket(ticket_value='Barcode reader OK\n{}'.format(bc_reader.status),
                        ticket_type=kiosk_utils.TicketPurpose.BCR,
                        ticket_animate_cycles = 1,
                        queue_tx=queue_to_gui)

    


    #END of the startup sequence
    #Clear popup screen
    kiosk_utils.send_ticket(ticket_type=kiosk_utils.TicketPurpose.EOT,
                            queue_tx=queue_to_gui)
    queue_from_gui.queue.clear()  # Clear the queue to avoid processing old messages
    # Start the main loop to listen for barcode reads
    while not th_ev.is_set():
        #print('^', end='', flush=True)  # Print a dot to indicate the listener is running
            
        if time.time() > last_msg_time + config['screen_brightness_to_min'] * 60 \
            and not kiosk_utils.is_working_time(start=config['working_hours'][0],
                                            end=config['working_hours'][1],
                                            workdays=config['working_days']):
            kiosk_utils.set_brightness(config['screen_brightness_inactive'])
            logging.debug("Screen brightness set to inactive level {}".format(config['screen_brightness_inactive']))
            last_msg_time = time.time()

        if not queue_from_gui.empty():
            msg = queue_from_gui.get_nowait()
            proc_queue(msg, config=config)
            kiosk_utils.send_ticket(ticket_type=kiosk_utils.TicketPurpose.BCR,
                    ticket_animate_cycles = 1,
                    queue_tx=queue_to_gui)
            
            lang = msg 
        bc_reader.next()
        th_ev.wait(polling_int)  # Wait for the specified interval

def bc_callback(*args) -> bool:
    """
    Callback function to handle the barcode read event.
    time.sleep used to ~ sync screen & audio with printer as there is no real-time feedback from printer.
    
    """
    global lang, conn
    barcode = args[0]
    config = args[1]
    queue_to_gui = args[2]
    reg_ex = config['bc_regex']
    logging.debug(f"Received barcode: {barcode}, lang: {lang[1]}")
    # Remove leading bc prefix if necessary
    if not barcode[0].isnumeric():
        barcode=barcode[1:]
    if re.match(reg_ex, barcode):
        barcode = barcode.replace('#','%23')
        kiosk_utils.speak_status(os.path.join(config['assets_loader'], 'attn.wav'), background=True)
        report_url = config['url'].format(config['host'],barcode,lang[1])
        r = kiosk_report.get_report_from_host(report_url, timeout = config['httpreq_timeout'])
        kiosk_utils.send_ticket(ticket_value = '<{}>'.format(r[0]),
                ticket_type=kiosk_utils.TicketPurpose.AOK,
                ticket_animate_cycles = 1,
                queue_tx=queue_to_gui)
        time.sleep(1)
        if r[0] == 200:
            report_pages = kiosk_utils.get_numpages_from_pdf(r[1])
            kiosk_utils.speak_status(os.path.join(config['assets_loader'], 'start_print{}.wav'.format(lang[1])), background=False)

            if report_pages<11:
                kiosk_utils.speak_status(os.path.join(config['assets_loader'],
                                                      'NumPages_{}_{}.wav'.format(report_pages, lang[1])), background=False)
            else:
                kiosk_utils.speak_status(os.path.join(config['assets_loader'],
                                        'NumPages_10more_{}.wav'.format(lang[1])), background=False)
            
            kiosk_utils.send_ticket(ticket_type=kiosk_utils.TicketPurpose.PRN,
                ticket_animate_cycles = 2,
                ticket_value='{}:\n{}'.format(config['report_num_pages'][lang[0]], report_pages),
                queue_tx=queue_to_gui)
            
            time.sleep(config['report_delay'])

            if kiosk_report.print_report(conn=conn, tmp_file=r[1]) is not None:
                kiosk_utils.send_ticket(ticket_type=kiosk_utils.TicketPurpose.AOK,
                    ticket_animate_cycles = 1,
                    queue_tx=queue_to_gui)
                kiosk_utils.speak_status(os.path.join(config['assets_loader'], 'end_print{}.wav'.format(lang[1])), background=False)
                return()

        if r[0] == 409:
            kiosk_utils.send_ticket(ticket_value = 
                        config['report_not_ready_msg'][lang[0]].replace('\\', '\n'),
                        ticket_type=kiosk_utils.TicketPurpose.ERR,
                        ticket_animate_cycles = 2,
                        queue_tx=queue_to_gui)
            kiosk_utils.speak_status(os.path.join(config['assets_loader'], 'not_ready{}.wav'.format(lang[1])), background=False)
            return()

        kiosk_utils.send_ticket(ticket_type=kiosk_utils.TicketPurpose.ERR,
                                    ticket_animate_cycles = 2,
                                    queue_tx=queue_to_gui)
        kiosk_utils.speak_status(os.path.join(config['assets_loader'], 'error-attn.wav'), background=False)
        return()

    kiosk_utils.speak_status(os.path.join(config['assets_loader'], 'barcode_invalid{}.wav'.format(lang[1])), background=True)
    kiosk_utils.send_ticket(ticket_type=kiosk_utils.TicketPurpose.ERR,
                            ticket_animate_cycles = 2,
                            queue_tx=queue_to_gui)
    
def main():
    global config
    logging.basicConfig(format="%(levelname)s:%(asctime)s - %(message)s", level=logging.DEBUG)
