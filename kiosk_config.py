#!/usr/bin/env python3
import configparser
import logging
import os

def read_config(filename):
    '''
    Sets default config values values
    Reads values from config file
    '''
    kiosk_config = {
        'log_file': None, # Set to valid path if dedicated log file is needed
        'log_level': 'INFO', # Set to logging.DEBUG for debug level logging
        # User interface settings
        'languages': ['LAT','ENG','RUS'],
        'default_language_index': 0,  # Default language index
        'assets_loader': 'assets', # Path to assets directory, relative to the script
        'images': ['red_button.png', 'red_button_50.png'], # List of images used in the interface
        'bg_image': 'EGL_background.png',
        'font': ('DejaVu Sans Mono',50), # Font used in the interface
        'button_debaunce_time_ms': 1000, # Time in milliseconds to debounce button presses
        'button_reset_to default_time_ms': 10*1000, # Time in milliseconds to activate default button after last press
        #Settings for display brighetness 0 - 255
        'screen_brightness_active': 255,
        'screen_brightness_normal': 100,
        'screen_brightness_inactive': 50,
        'screen_width': 800,
        'screen_height': 480,

        # Barcode reader settings
        'bc_reader_port' : '/dev/ttyACM0',
        'bc_timeout' : .5,
        'bc_regex' : '^\d{7,9}#\d{4,5}',

        #Host settings
        'host' : '10.100.50.104',
        'httpreq_timeout': 15, 
        'report_delay' : 5,
        'url' : 'http://{}/csp/sarmite/ea.kiosk.pdf.cls?HASH={}&LANG={}',
        'url_test' : 'http://10.100.50.102/sarmite/m5menu.csp',

        'printers':  {"HP": "HP LaserJet Series PCL 6 CUPS"},
        'watchdog_device' : None
    }
    if not os.path.isfile(filename):
        logging.critical("Config file {} does not exist!".format(filename))
        return(None)
    
    cf = configparser.ConfigParser(allow_no_value=True,
                            converters={'list': lambda x: [int(i.strip()) for i in x.split(',')],
                                        'list_s' : lambda x: [i.strip() for i in x.split(',')],
                                        'tuple' : lambda x: tuple(int(item) if item.isdigit() else item for item in x.split(','))})
    cf.read(filename)
    #Tuple containing load commands
    commands =(
        "kiosk_config['log_file'] = cf.get('INTERFACE','log_file')",
        "kiosk_config['log_level'] = cf.get('INTERFACE','log_level')",
        "kiosk_config['languages'] = cf.getlist_s('INTERFACE','languages')",
        "kiosk_config['assets_loader'] = cf.get('INTERFACE','assets_loader')",
        "kiosk_config['images'] = cf.getlist_s('INTERFACE','images')",
        "kiosk_config['bg_image'] = cf.get('INTERFACE','bg_image')",
        "kiosk_config['font'] = cf.gettuple('INTERFACE','font')",
        "kiosk_config['button_debounce_time_ms'] = cf.getint('INTERFACE','button_debounce_time_ms')",
        "kiosk_config['button_reset_to_default_time_ms'] = cf.getint('INTERFACE','button_reset_to_default_time_ms')",
        "kiosk_config['default_language_index'] = cf.getint('INTERFACE','default_language_index')",
        "kiosk_config['screen_brightness_active'] = cf.getint('INTERFACE','screen_brightness_active')",
        "kiosk_config['screen_brightness_normal'] = cf.getint('INTERFACE','screen_brightness_normal')",
        "kiosk_config['screen_brightness_inactive'] = cf.getint('INTERFACE','screen_brightness_inactive')",
        "kiosk_config['screen_width'] = cf.getint('INTERFACE','screen_width')",
        "kiosk_config['screen_height'] = cf.getint('INTERFACE','screen_height')",

        "kiosk_config['bc_reader_port'] = cf.get('BARCODE','bc_reader_port')",
        "kiosk_config['bc_timeout'] = cf.getfloat('BARCODE','bc_timeout')",
        "kiosk_config['bc_regex'] = r'{}'.format(cf.get('BARCODE','bc_regex'))",

        "kiosk_config['host'] = cf.get('REPORT','host')",
        "kiosk_config['httpreq_timeout'] = cf.getint('REPORT','httpreq_timeout')",
        "kiosk_config['report_delay'] = cf.getint('REPORT','report_delay')",
        "kiosk_config['url'] = cf.get('REPORT','url')",
        "kiosk_config['url_test'] = cf.get('REPORT','url_test')",
        "kiosk_config['button_printer_reset'] = cf.getlist('REPORT','button_printer_reset')",
        "kiosk_config['printers'] = cf.get('REPORT','printers')",

        "kiosk_config['watchdog_device'] = cf.get('WATCHDOG','watchdog_device')"
        )
    for c in commands:
        try:
            #print('Executing: {}'.format(c))
            exec(c)
        except configparser.Error as e:
            logging.error(e)
    # Check if log_file is set to 'None' and convert it to None    
    if kiosk_config['log_file'] == 'None': kiosk_config['log_file'] = None  

    return(kiosk_config)

def main():
    f = os.path.join(os.getcwd(),'kiosk.ini')
    cfg = read_config(f)
    print(cfg)

if __name__ == '__main__':
    main()