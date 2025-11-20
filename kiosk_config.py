#!/usr/bin/env python3
import configparser
import logging
import os
import ast

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
        'font': ('DejaVu Sans Mono',50), # Font used in the interface
        'button_debounce_time_ms': 1000, # Time in milliseconds to debounce button presses
        'button_reset_to default_time_ms': 10*1000, # Time in milliseconds to activate default button after last press
        #Settings for display brighetness 0 - 255
        'screen_brightness_active': 255,
        'screen_brightness_normal': 100,
        'screen_brightness_inactive': 50,
        'working_hours': [7,19],
        'working_days': [1,2,3,4,5],
        'screen_brightness_to_min': 30,
        'screen_brightness_path': "/sys/class/backlight/rpi_backlight/brightness",
        #Settings for button frame size
        'button_frame_height': 500,
        'button_frame_width': 300,
        'button_frame_posXY': [100,200],
        #Settings for screen size
        'screen_width': 480,
        'screen_height': 800,
        #Settings for popup messages
        'popup_display_time': 5000,

        #Settings for animated icon
        'animated_icon_height': 100,
        'animated_icon_width': 100,
        'animated_icon_delay': 100,
        'animated_icon_sys': 'sloading.gif',
        'animated_icon_prn': 'printer.gif',
        'animated_icon_bc': 'barcode.gif',
        'animated_icon_ok': 'verified.gif',
        'animated_icon_not_ok': 'alarm.gif',
        'animated_icon_no_data': 'report_not_ready.gif',
        'animated_icon_in_progress': 'work-in-progress.gif',
        'animated_icon_net': 'wifi.gif',

        'text_label_font_size': 20,
        'text_label_font': 'DejaVu Sans Mono',
        'report_not_ready_msg': ['NR','NR','NR'],
        'report_num_pages': ['NR','NR','NR'],

        # Barcode reader settings
        'bc_reader_bounce' : 3, # Bounce time in seconds for barcode reader
        'bc_reader_boudrate' : 9600,
        'bc_reader_port' : '/dev/ttyACM0',
        'bc_timeout' : .5,
        'bc_regex' : '^\d{7,9}#\d{4,5}',

        #Host settings
        'host' : '10.100.50.104',
        'httpreq_timeout': 15, 
        'report_delay' : 5,
        'url' : 'http://{}/csp/sarmite/ea.kiosk.pdf.cls?HASH={}&LANG={}',
        'url_test' : 'http://10.100.50.102/sarmite/m5menu.csp',


        #printers':  {"HP": "HP LaserJet Series PCL 6 CUPS"},
        'include_schemes' : ['usb','driverless'],
        'printers' : {"HP": "HP LaserJet Series PCL 6 CUPS"},
        'watchdog_device' : None
    }
    if not os.path.isfile(filename):
        logging.critical("Config file {} does not exist!".format(filename))
        return(None)
    
    cf = configparser.ConfigParser(allow_no_value=True,
                                converters={'list'  : lambda x: list(int(item) if item.isdigit() else item for item in x.split(',')),
                                            'tuple' : lambda x: tuple(int(item) if item.isdigit() else item for item in x.split(',')),
                                            'none'  : lambda x: None if x == 'None' else x,
                                            'dict'  : lambda x: ast.literal_eval(''.join(['{',x,'}']))
                                            },)
    cf.read(filename)
    #Tuple containing load commands
    commands =(
        "kiosk_config['log_file'] = cf.getnone('INTERFACE','log_file')",
        "kiosk_config['log_level'] = cf.get('INTERFACE','log_level')",
        "kiosk_config['languages'] = cf.getlist('INTERFACE','languages')",
        "kiosk_config['assets_loader'] = cf.get('INTERFACE','assets_loader')",
        "kiosk_config['bg_image'] = cf.get('INTERFACE','bg_image')",
        "kiosk_config['font'] = cf.gettuple('INTERFACE','font')",
        "kiosk_config['button_debounce_time_ms'] = cf.getint('INTERFACE','button_debounce_time_ms')",
        "kiosk_config['button_reset_to_default_time_ms'] = cf.getint('INTERFACE','button_reset_to_default_time_ms')",
        "kiosk_config['default_language_index'] = cf.getint('INTERFACE','default_language_index')",
        "kiosk_config['screen_brightness_active'] = cf.getint('INTERFACE','screen_brightness_active')",
        "kiosk_config['screen_brightness_normal'] = cf.getint('INTERFACE','screen_brightness_normal')",
        "kiosk_config['screen_brightness_inactive'] = cf.getint('INTERFACE','screen_brightness_inactive')",
        "kiosk_config['working_hours'] = cf.getlist('INTERFACE','working_hours')",
        "kiosk_config['working_days'] = cf.gettuple('INTERFACE','working_days')",
        "kiosk_config['screen_brightness_to_min'] = cf.getint('INTERFACE','screen_brightness_to_min')",
        "kiosk_config['screen_brightness_path'] = cf.get('INTERFACE','screen_brightness_path')",

        "kiosk_config['screen_width'] = cf.getint('INTERFACE','screen_width')",
        "kiosk_config['screen_height'] = cf.getint('INTERFACE','screen_height')",

        "kiosk_config['animated_icon_height'] = cf.getint('INTERFACE', 'animated_icon_height')",
        "kiosk_config['animated_icon_width'] = cf.getint('INTERFACE', 'animated_icon_width')",
        "kiosk_config['animated_icon_delay'] = cf.getint('INTERFACE', 'animated_icon_delay')",

        "kiosk_config['animated_icon_sys'] = cf.get('INTERFACE', 'animated_icon_sys')",
        "kiosk_config['animated_icon_prn'] = cf.get('INTERFACE', 'animated_icon_prn')",
        "kiosk_config['animated_icon_bc'] = cf.get('INTERFACE', 'animated_icon_bc')",
        "kiosk_config['animated_icon_ok'] = cf.get('INTERFACE', 'animated_icon_ok')",
        "kiosk_config['animated_icon_not_ok'] = cf.get('INTERFACE', 'animated_icon_not_ok')",
        "kiosk_config['animated_icon_no_data'] = cf.get('INTERFACE', 'animated_icon_no_data')",
        "kiosk_config['animated_icon_in_progress'] = cf.get('INTERFACE', 'animated_icon_in_progress')",
        "kiosk_config['animated_icon_net'] = cf.get('INTERFACE', 'animated_icon_net')",

        "kiosk_config['text_label_font_size'] = cf.getint('INTERFACE', 'text_label_font_size')",
        "kiosk_config['text_label_font'] = cf.get('INTERFACE', 'text_label_font')",

        "kiosk_config['button_frame_height'] = cf.getint('INTERFACE','button_frame_height')",
        "kiosk_config['button_frame_width'] = cf.getint('INTERFACE','button_frame_width')",
        "kiosk_config['button_frame_posXY'] = cf.getlist('INTERFACE','button_frame_posXY')",
        "kiosk_config['popup_display_time'] = cf.getint('INTERFACE','popup_display_time')",

        "kiosk_config['bc_reader_bounce'] = cf.getint('BARCODE','bc_reader_bounce')",
        "kiosk_config['bc_reader_boudrate'] = cf.getint('BARCODE','bc_reader_boudrate')",
        "kiosk_config['bc_reader_port'] = cf.get('BARCODE','bc_reader_port')",
        "kiosk_config['bc_timeout'] = cf.getfloat('BARCODE','bc_timeout')",
        "kiosk_config['bc_regex'] = r'{}'.format(cf.get('BARCODE','bc_regex'))",

        "kiosk_config['host'] = cf.get('REPORT','host')",
        "kiosk_config['httpreq_timeout'] = cf.getint('REPORT','httpreq_timeout')",
        "kiosk_config['report_delay'] = cf.getint('REPORT','report_delay')",
        "kiosk_config['url'] = cf.get('REPORT','url')",
        "kiosk_config['url_test'] = cf.get('REPORT','url_test')",
        "kiosk_config['printers'] = cf.getdict('REPORT','printers')",
        "kiosk_config['button_printer_reset'] = cf.getlist('REPORT','button_printer_reset')",
        "kiosk_config['include_schemes'] = cf.getlist('REPORT','include_schemes')",
        "kiosk_config['report_not_ready_msg'] = cf.getlist('REPORT','report_not_ready_msg')",
        "kiosk_config['report_num_pages'] = cf.getlist('REPORT','report_num_pages')",
        "kiosk_config['watchdog_device'] = cf.getnone('WATCHDOG','watchdog_device')"
        )
    

    for c in commands:
        try:
            #print('Executing: {}'.format(c))
            exec(c)
        except configparser.Error as e:
            logging.error(e)
 
    return(kiosk_config)

def main():
    f = os.path.join(os.getcwd(),'kiosk.ini')
    logging.basicConfig(format='%(levelname)s:%(asctime)s - %(message)s', level=logging.DEBUG)
    cfg = read_config(f)
    print(cfg)


if __name__ == '__main__':
    main()
