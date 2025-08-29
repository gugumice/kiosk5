#!/usr/bin/env python3

import tkinter as tk
import customtkinter as ctk
from PIL import Image
import os, sys
import time
import argparse
import logging
from queue import Queue
import threading
import kiosk_utils
import kiosk_config

from kiosk_animated_label import AnimatedGifLabelAcc, load_gif_frames
import kiosk_th2

# Global vars
config={}
queue_from_gui = Queue()
queue_to_gui = Queue()
img_cache = dict()

# Polling interval for sevice thread (BC reader etc...)
polling_int = .5

class KioskButton(ctk.CTkButton):
    '''A custom button class that inherits from CTkButton.
    It represents a button for selecting a report language.'''
    def __init__(self, master=None, language:list = None, **kwargs):
        super().__init__(master, **kwargs)
        self.language = language
        self.configure(command=lambda: self.on_click(self.language),
                       #corner_radius=50,
                       text =  language[1],
                       border_spacing = 5,
                       font=config['font'], 
                       fg_color="#0c6875",
                       hover_color="#0c6875",
                       #bg_color="#0c6875",
                       bg_color="transparent",
                       text_color="white",)
        self.master = master

    def on_click(self, language):
        '''Callback function for button click event.'''
        self.master.show_active_button(self.language[0])
        self.master.disable_buttons()
        #self.master.queue_from_gui.put(language)
        kiosk_utils.set_brightness(config['screen_brightness_active'])
        self.after(config['button_debounce_time_ms'], self.master.enable_buttons)
        logging.debug(f"Button clicked: {language[1]}")
        
class MainFrame(ctk.CTkFrame):
    '''A custom frame class that inherits from CTkFrame.
    It contains a list of buttons and manages their state.'''
    def __init__(self, master=None, config:dict=config, queue_from_gui:Queue=queue_from_gui):
        super().__init__(master)
        self.master = master
        self.queue_from_gui = queue_from_gui
        # Load the images for the buttons
        active_img = Image.open(os.path.join(config['assets_loader'],config['images'][0]))
        normal_img = Image.open(os.path.join(config['assets_loader'],config['images'][1]))
        # Get CTkImage from the images
        self._active_button_image=ctk.CTkImage(active_img,size=active_img.size)
        self._normal_button_image=ctk.CTkImage(normal_img,size=normal_img.size)
        self.active_button = config['default_language_index']
        ## Set the size of the frame
        self.width =300
        self.height = 500
        self.configure(width=self.width, height=self.height, border_width=5,  fg_color="transparent", bg_color="transparent")
        #Variable to store the after_cancel id
        self._after_cancel_id = None
        # Create a list of buttons
        self.buttons = list()
        # Create buttons for each language
        for bttn in enumerate(config['languages']):
            self.buttons.append(KioskButton(self, language=bttn, text=bttn[1], image = self._normal_button_image))
            self.buttons[-1].pack(padx=2, pady=2, fill=ctk.BOTH, expand=True)
        # Set the default button to be active
        self.show_active_button(config['default_language_index'])

    def disable_buttons(self):
        '''Disable all buttons in the frame.'''
        for bttn in self.buttons:
            bttn.configure(state="disabled")
        #Delete previus after() if it exists
        if self._after_cancel_id is not None:
            self.after_cancel(self._after_cancel_id)
        # Schedule new reset of buttons & screen brightness to default state
        self._after_cancel_id = self.after(config['button_reset_to_default_time_ms'],
                                           lambda: [self.show_active_button(config['default_language_index']),
                                                    kiosk_utils.set_brightness(config['screen_brightness_normal']
                                                                                if kiosk_utils.is_working_time(start=config['working_hours'][0],
                                                                                  end=config['working_hours'][1],
                                                                                  workdays=config['working_days']) 
                                                                                else config['screen_brightness_inactive'])])
    def enable_buttons(self):
        '''Enable all buttons in the frame.'''
        for bttn in self.buttons:
            bttn.configure(state="normal")

    def show_active_button(self, button:int):
        '''
        Show the active button to user by changing image.
        '''

        self.active_button = button
        for bttn in self.buttons:
            if bttn.language[0] == button:
                bttn.configure(image=self._active_button_image)
            else:
                bttn.configure(image=self._normal_button_image)
        self.queue_from_gui.put((button, config['languages'][button]))

class PopupFrame(ctk.CTkFrame):
    '''A custom frame class that inherits from CTkFrame.
    It is used to display a popup message.
    https://www.reddit.com/r/learnpython/comments/10szjeh/comment/j74jupu/
    
    '''
    def __init__(self, master=None, config:dict=config):
        super().__init__(master)
        self._config = config
        self.configure(width=self._config['button_frame_width'], height=self._config['button_frame_height'],
                       fg_color='#fff', bg_color='#fff')
        self.pack_propagate(False)  # Prevent the frame from resizing to fit its contents
        self._message_value = tk.StringVar(self)
        self.icon = None
        
        self.label = ctk.CTkLabel(self, textvariable = self._message_value, font=('DejaVu Sans Mono', 20),
                     justify=tk.LEFT, padx=0, pady=0)
        self.label.pack(side = tk.BOTTOM, expand=True, fill=tk.BOTH)
        self._prev_ticket_type = None

    def update(self, ticket:kiosk_utils.Ticket=None):
        self._message_value.set(ticket.ticket_value if ticket.ticket_value else '')
    
        if ticket.ticket_type == self._prev_ticket_type:
            logging.debug(f"Ticket type unchanged: {ticket.ticket_type}") 
            return()
        logging.debug(f"Ticket type changed: {ticket.ticket_type}")
        self._prev_ticket_type = ticket.ticket_type
        # Erase previous AnimatedIcon <<<<<<<<<<<<<<<<<<<<<<<<<<<
        if self.icon is not None:
            self.icon.stop_animation()
            self.icon.destroy()
            self.icon = None
        # Create AnimatedLabel by TicketPurpose
        if ticket.ticket_type == kiosk_utils.TicketPurpose.SYS:
            gif_path = os.path.join(self._config['assets_loader'],self._config['animated_icon_sys'])
        elif ticket.ticket_type == kiosk_utils.TicketPurpose.PRN:
            gif_path = os.path.join(self._config['assets_loader'],self._config['animated_icon_prn'])
        elif ticket.ticket_type == kiosk_utils.TicketPurpose.BCR:
            gif_path = os.path.join(self._config['assets_loader'],self._config['animated_icon_bc'])
        elif ticket.ticket_type == kiosk_utils.TicketPurpose.NET:
            gif_path = os.path.join(self._config['assets_loader'],self._config['animated_icon_net'])
        elif ticket.ticket_type == kiosk_utils.TicketPurpose.ERR:
            gif_path = os.path.join(self._config['assets_loader'],self._config['animated_icon_not_ok'])
        elif ticket.ticket_type == kiosk_utils.TicketPurpose.AOK:
            gif_path = os.path.join(self._config['assets_loader'],self._config['animated_icon_ok'])
        elif ticket.ticket_type == kiosk_utils.TicketPurpose.PRG:
            gif_path = os.path.join(self._config['assets_loader'],self._config['animated_icon_in_progress'])
        elif ticket.ticket_type == kiosk_utils.TicketPurpose.INC:
            gif_path = os.path.join(self._config['assets_loader'],self._config['animated_icon_no_data'])
        self.icon = AnimatedGifLabelAcc(self, gif_path = gif_path,
                                    delay=config['animated_icon_delay'], 
                                    width=config['animated_icon_width'],
                                    height=config['animated_icon_height'],
                                    img_cache=img_cache)
        self.icon.pack(side = tk.BOTTOM,padx=0,pady=40)
        self.icon.start_animation(ticket.ticket_animate_cycles)
        
class KioskPopup(ctk.CTkToplevel):
    '''A custom popup class that inherits from CTkToplevel.'''
    def __init__(self, **kwargs):
        '''
        Initialize the popup with a message and set its properties.
        '''
        super().__init__(**kwargs)
        self.overrideredirect(True)
        self.geometry("{}x{}+100+200".format(config['button_frame_width'],config['button_frame_height']))
        self.title = 'KioskPopup'
        self.attributes("-topmost", True)
        self.time_created = time.time()
        self.frame = PopupFrame(master = self, config = config)
        
        self.frame = PopupFrame(master = self, config = config)
        self.frame.pack(fill=tk.BOTH, expand=True)
    
    def close_popup(self):
        '''Callback function for closing the popup.'''
        logging.debug("Closing popup")
        #self.frame._icon.stop_animation()
        #self.frame.destroy()

        self.destroy()
        self.update

class KioskApp(ctk.CTk):
    '''Main application class that inherits from CTk.'''
    def __init__(self, config=config, queue_to_gui:Queue=queue_to_gui):
        super().__init__()
        self.bg_image = tk.PhotoImage(file = 
                        os.path.join(config['assets_loader'],config['bg_image']) if config['bg_image'] else None)
        self.height = config['screen_height']
        self.width =config['screen_width']
        # Create a canvas
        self.canvas = tk.Canvas(self, height=self.height, width=self.width, background="lightblue")
        self.canvas.pack()
        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor=ctk.NW)
        # Create a frame
        self.frame = MainFrame(self, config = config)
        self.popup_active = False
        self.popup_a = False
        # Add the frame to the canvas
        self.popup_window = None
        self.canvas.create_window((100,200), width=self.frame.width, height=self.frame.height, window=self.frame, anchor=tk.NW)
        self.queue_to_gui = queue_to_gui
        self.check_queue()  # Check the queue
    
    def check_queue(self):
        print('^', end='', flush=True)  # Print a dot to indicate the listener is running
        self.after(500, self.check_queue)
        
        if self.popup_window is not None and self.popup_window.winfo_exists():
            #print(self.popup_window.frame.icon.stopped)
            print(self.popup_window.frame.icon.stopped())
            if not self.popup_window.frame.icon.stopped():
                print('blocked')
                return()
            
        if not self.queue_to_gui.empty():
            ticket = self.queue_to_gui.get_nowait()
            if not isinstance(ticket, kiosk_utils.Ticket):
                logging.error(f"Invalid message: {ticket}")
                return()
            # If the message is a Ticket, process it
            # Close popup if it exists &  got EOT
            if ticket.ticket_type == kiosk_utils.TicketPurpose.EOT:
                if self.popup_window is not None and self.popup_window.winfo_exists():
                    self._close_popup()

            else:
                # Create popup to display ticket
                if self.popup_window is None or not self.popup_window.winfo_exists():
                    self.popup_window = KioskPopup(master = self)
                else:
                    self.popup_window.deiconify()
                self.popup_window.frame.update(ticket=ticket)
        else:
            self._close_popup()
        
    def _close_popup(self):
        if self.popup_window is not None and self.popup_window.winfo_exists():
            self.popup_window.withdraw()
 
def main(polling_int = .5):
    global config, queue_to_gui, queue_from_gui, img_cache
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
    else:
        logging.basicConfig(
            format="%(asctime)s - %(message)s",
            filename=config["log_file"],
            filemode="w",
            level=os.environ.get('LOGLEVEL', config['log_level']).upper(),)
    img_cache = load_gif_frames(os.path.join(config['assets_loader'], 'img_cache'))
    logging.debug('Finished loading image cache {}'.format(len(img_cache)))
    th_ev = threading.Event()
    t1 = threading.Thread(target=kiosk_th2.service_thread, kwargs = {'th_ev': th_ev, 'polling_int':polling_int,
                                                               'config':config, 
                                                               'queue_from_gui':queue_from_gui,
                                                               'queue_to_gui':queue_to_gui}, 
                                                               daemon=True)
    t1.start()
    logging.info('Servive_thread: {}'.format(t1.is_alive()))
    kiosk_app=KioskApp(config=config)
    kiosk_app.mainloop()
    print("Exiting application...")
    th_ev.set()
    t1.join()

if __name__ == "__main__":
    main(polling_int)


