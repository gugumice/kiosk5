#!/usr/bin/env python3
import cups
import logging

#sudo systemctl disable cups-browsed

def current_printer_connected(conn: cups.Connection, include_schemes: list = ['usb','driverless'])-> bool:
    '''
    Checks if previous printer is still reachable
    '''
    avilable_printers = conn.getDevices(include_schemes = include_schemes)
    connected_printers = conn.getPrinters()    
    for v_cp in connected_printers.values():
        for k_ap in avilable_printers.keys():
            #print('{}: {}\n\n{}: {}'.format(k_ap,v_ap,k_cp,v_cp))
            if v_cp['device-uri'] == k_ap:
                return(True)
    return(False)

def check_avilable_printers(conn: cups.Connection, include_schemes: list = ['usb','driverless'], driver_list: dict = {'HP'}) -> str:
    '''
    Checks if any printers are avilable and are on installation list
    Returns printer-make if success
    '''
    avilable_printers = conn.getDevices(include_schemes = include_schemes)
    if len(avilable_printers) == 0:
        raise Exception('Printing: No printers found on scheme(s) {}'.format(include_schemes))
    #Check if any avilable printers on approuved list
    common_found = None
    l_avil = [v['device-make-and-model'].split(' ')[0] for v in avilable_printers.values()]
    for l1 in driver_list.keys():
        for l2 in l_avil:
            if l1 == l2:
                common_found = l1
                break
    if common_found is None:
        raise Exception('Printing: No match. Printers found {}, allowed {}'.format(list(l_avil), list(driver_list.keys())))
    return(common_found)


def install_printer(conn: cups.Connection,
                    printer_make:str = 'HP',
                    printer_driver:str = 'HP LaserJet Series PCL 6 CUPS',
                    include_schemes: list = ['usb','driverless']) -> str:
    '''
    Installs kiosk printer, sets it as default, enabled
    Returns printer name as in Cups
    '''
    full_name = None
    uri = None
    avilable_printers = conn.getDevices(include_schemes = include_schemes)
    if len(avilable_printers) == 0:
        raise Exception('Printing: No printers found on scheme(s) {}'.format(include_schemes))
    #Get data form device
    for k,v in avilable_printers.items():
        if v['device-make-and-model'].split(' ')[0].startswith(printer_make):
            name = v['device-make-and-model']
            full_name = name.replace(' ','_')
            uri = k
            break
    ppd_name = list(conn.getPPDs(ppd_make_and_model = printer_driver).keys())[0]
    conn.addPrinter(name = full_name, ppdname = ppd_name, info = name, location = 'Local kiosk printer', device = uri)
    conn.acceptJobs(full_name)
    conn.setPrinterShared(full_name,False)
    conn.setDefault(full_name)
    conn.enablePrinter(full_name)
    return(name)

def delete_all_printers(conn:cups.Connection):
    '''
    Deletetes all printers
    '''
    printers = conn.getPrinters()
    if len(printers) == 0:
        return()
    for p in printers:
        try:
            conn.deletePrinter(p)
        except cups.IPPError as e:
            logging.error(e)


def main():
    conn = cups.Connection()
    config = {'include_schemes': ['usb','driverless'],
             'driver_list': {'HP':'HP LaserJet Series PCL 6 CUPS','Epson':'Epson driver','Kyocera':'HP LaserJet Series PCL 6 CUPS'}}
    
    if not current_printer_connected(conn, include_schemes=['usb','driverless']):
        printer_make = None
        try:
            printer_make = check_avilable_printers(conn, config['include_schemes'], config['driver_list'])
        except Exception as e:
            logging.error(e)
        else:
            delete_all_printers(conn)
            install_printer(conn, printer_make=printer_make, printer_driver = config['driver_list'][printer_make])
    
    print_queue = list(conn.getPrinters().keys())[0]
    job_id = conn.printTestPage(print_queue)
    print(job_id)
    
if __name__ == '__main__':
    main()
