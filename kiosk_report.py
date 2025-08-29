#!/usr/bin/env python3
import requests
import tempfile
import logging
import cups
import os
import kiosk_utils

import kiosk_config

def check_printers(config):
    conn = cups.Connection()
    # Check if any printers are available
    devices = conn.getDevices(include_schemes=config['include_schemes'])
    if not devices:
        return([None, 'No connected printers'])
    printers = conn.getPrinters().keys()
    logging.debug('Printers found: {}'.format(list(printers)))
    conn = None
    if not printers:
        return(None)
    return(printers)

def delete_printers():
    """
    Delete printers from the CUPS server if they are not connected.
    :return: None
    :raises cups.IPPError: If there is an error deleting printers
    """
    conn= cups.Connection()
    printers = conn.getPrinters()
    if printers:
        for printer in printers:
            try:
                conn.deletePrinter(printer)
                logging.info(f"Deleted printer: {printer}")
            except cups.IPPError as e:
                logging.error(f"Failed to delete printer {printer}: {e}")

def print_report(tmp_file:str = None) -> int:
    '''
    Print test report from temporary file or test page if no file is provided.
    '''
    
    try:
        conn = cups.Connection()
    except cups.IPPError as e:
        logging.error(f"Failed to connect to CUPS server: {e}")
        return(None)
    printers = conn.getPrinters()
    if not printers:
        logging.error('No printers found in CUPS')
        return(None)
    printer = list(printers.keys())[0]  # Use the first available printer
    logging.info(f"Printing report on printer: {printer}")
    if tmp_file:
        job_id = conn.printFile(printer, tmp_file, "Test Report", options ={'print-color-mode': 'monochrome'})
    else:
        job_id = conn.printTestPage(printer, options ={'print-color-mode': 'monochrome'})
    return(job_id)

def get_report_from_host(url, timeout = 10):
    '''
    Gets testing report from server, saves it to temporary file
    Returns status and link to temporary file
    '''
    e = None
    try:
        rep = requests.get(url, )
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
    bc = '25657193#1192'
    regex = config['bc_regex']
    
if __name__ == '__main__':
    main()