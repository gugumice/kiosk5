#!/usr/bin/env python3
import requests
import tempfile
import logging
import cups
import os
import kiosk_utils
from queue import Queue

import kiosk_config

def connect_to_cups() -> cups.Connection:
    try:
        conn = cups.Connection()
        logging.debug('CUPS Connection established')
    except cups.IPPError as e:
        logging.error(f"Failed to connect to CUPS server: {e}")
        return(None)
    return(conn)

def check_default(ap,ip,dp) -> bool:
    '''
    Check if currend default printer is avilable
    '''
    for p_uri in ap.keys():
        if ip[dp]['device-uri'] == p_uri:
            return(True)
    return(False)

def add_printer(conn:cups.Connection = None,
                allowed_printers:dict = None,
                avilable_printers:dict = None) -> str:
    # Get parameters for new printer 
    params = dict
    # PPD
    n = None
    for k_al, v_al in allowed_printers.items():
        for k_pr, v_pr in avilable_printers.items():
            if v_pr['device-make-and-model'].startswith(k_al):
                n = v_al
                break
        if n is not None:
            break
    try:
        pn = conn.getPPDs(ppd_make_and_model = n)
    except cups.IPPError as e:
        logging.error(e)
        return(False, e)

    params = {'ppd_name': next(iter(pn)),
              'name' : n.replace(' ','_'),
              'info' : n,
              'location' : 'EGL',
              'device': k_pr
              }
    # Add printer
    try:
        conn.addPrinter(name = params['name'], ppdname = params['ppd_name'],
                        info = params['info'], location = params['location'],
                        device = params['device'])
       #self.addPrinter(name=self.name, ppdname = ppd_name, info = printer_name, location = 'Local printer', device = self.uri)
    except cups.IPPError as e:
        logging.error(e)
        return(False, e)
    else:
        conn.acceptJobs(params['name'])
        conn.setPrinterShared(params['name'],False)
        conn.setDefault(params['name'])
        conn.enablePrinter(params['name'])
    return(True, params['name'])

def delete_printers(conn:cups.Connection = None, printers:dict = None):
    printers = conn.getPrinters()
    if printers:
        for printer in printers:
            try:
                conn.deletePrinter(printer)
                logging.info(f"Deleted printer: {printer}")
            except cups.IPPError as e:
                logging.error(f"Failed to delete printer {printer}: {e}")

def init_printer(conn:cups.Connection = None, config:dict = None, queue_to_gui:Queue = None):        
    avilable_printers = conn.getDevices(include_schemes = config['include_schemes'])
    # No printers detected - exiting
    if len(avilable_printers) == 0:
        kiosk_utils.send_ticket(ticket_value='No printers found\n {}'.format(list(config['include_schemes'])),
                        ticket_type=kiosk_utils.TicketPurpose.PRN,
                        ticket_animate_cycles = 3,
                        queue_tx = queue_to_gui)
        return(False)
    installed_printers = conn.getPrinters()
    default_printer = conn.getDefault()
    if default_printer:
        # Check if current default printer is avilable
        # if so, purge unfinished print jobs & exit
        if check_default(avilable_printers,installed_printers,default_printer):
            try:
                conn.cancelAllJobs(uri = installed_printers[default_printer]['device-uri'], purge_jobs = True)
            except cups.IPPError as e:
                logging.error(e)
            else:
                logging.info('Purge old print jobs OK')
            logging.debug('Def prn ok')
            kiosk_utils.send_ticket(ticket_value='{}\n OK'.format(default_printer),
                    ticket_type=kiosk_utils.TicketPurpose.PRN,
                    ticket_animate_cycles = 1,
                    queue_tx=queue_to_gui)
            return(True)
        # Default printer not avlilable
        default_printer = False
    delete_printers(conn=conn, printers = installed_printers)
    kiosk_utils.send_ticket(ticket_value='{} printer(s) found\n{}'.format(len(avilable_printers),
                                                                          '\n'.join([pr[:18] for pr in avilable_printers])),
                    ticket_type=kiosk_utils.TicketPurpose.PRN,
                    ticket_animate_cycles = 1,
                    queue_tx=queue_to_gui)
    if add_printer(conn = conn, allowed_printers=config['printers'],
                    avilable_printers=avilable_printers):
        default_printer = conn.getDefault()
        kiosk_utils.send_ticket(ticket_value='{}\nprinter installed'.format(default_printer),
                ticket_type=kiosk_utils.TicketPurpose.PRN,
                ticket_animate_cycles = 1,
                queue_tx=queue_to_gui)
        logging.info('Printer {} installed'.format(default_printer))
        conn.printTestPage(default_printer)
        os.system('sudo shutdown -r now')
                        
    else:
        kiosk_utils.send_ticket(ticket_value='Error installing printer',
            ticket_type=kiosk_utils.TicketPurpose.ERR,
            ticket_animate_cycles = 1,
            queue_tx=queue_to_gui)
        logging.info('Printer not added')            
    return

def print_report(conn:cups.Connection = None, tmp_file:str = None) -> int:
    try:
        conn = cups.Connection()
    except cups.IPPError as e:
        logging.error(f"Failed to connect to CUPS server: {e}")
        return(False)
    printers = conn.getPrinters()
    if not printers:
        logging.error('No printers found in CUPS')
        return(None)
    printer = list(printers.keys())[0]  # Use the first available printer
    logging.info(f"Printing report on printer: {printer}")
    if tmp_file:
        job_id = conn.printFile(printer, tmp_file, "Test Report", options ={'print-color-mode': 'monochrome'})
        try:
            os.unlink(tmp_file)
        except FileNotFoundError as e:
            logging.error(e)
    else:
        job_id = conn.printTestPage(printer, options ={'print-color-mode': 'monochrome'}) 
    return(job_id)

def get_report_from_host(url, timeout = 10) -> list:
    '''
    Gets testing report from server, saves it to temporary file
    Returns status and link to temporary file
    '''
    e = None
    try:
        rep = requests.get(url, timeout= timeout)
    except requests.exceptions.HTTPError:
        e = 'HTTP error'
    except requests.exceptions.ReadTimeout:
        e = 'Read timeout'
    except requests.exceptions.ConnectionError:
        e = 'Connection error'
    except requests.exceptions.RequestException:
        e = 'Exception request'
    except Exception:
        e = 'Unknown error'
    finally:
        if e:
            kiosk_utils.send_ticket(ticket_value=f'ERR: {e}',
                                    ticket_type=kiosk_utils.TicketPurpose.BC)
            return(None)     
    if rep.status_code == 200 and rep.headers.get('Content-Type') == 'application/pdf':
        #Create tmp file for CUPS
        temp_file = tempfile.NamedTemporaryFile(prefix='kio_',suffix='.pdf', delete=False,)
        #Write content to tmp file
        with open(temp_file.name, 'wb') as tf:
            tf.write(rep.content)
        return([rep.status_code, temp_file.name])
    return([rep.status_code, None])

def main():
    logging.basicConfig(format="%(levelname)s:%(asctime)s - %(message)s", level=logging.DEBUG)
    config = kiosk_config.read_config(os.path.join(os.getcwd(),'kiosk.ini'))
    init_printer(config=config)

    
if __name__ == '__main__':
    main()
