#!/usr/bin/env python3

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import os, sys
import argparse
import logging
from queue import Queue

import kiosk_utils
import kiosk_config

# Global vars
config={}
queue_messages = Queue()

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
        self.after(config['button_debaunce_time_ms'], self.master.enable_buttons)
        
class MainFrame(ctk.CTkFrame):
    '''A custom frame class that inherits from CTkFrame.
    It contains a list of buttons and manages their state.'''
    def __init__(self, master=None, config:dict=config, queue_messages:Queue=queue_messages):
        super().__init__(master)
        self.master = master
        
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
        self.queue_messages = queue_messages
        self.bind('<<CkeckQueue>>', lambda e: self.check_queue())
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

    def check_queue(self):
        '''Check the queue for messages and process them.'''
        if not self.queue_messages.empty():
            message = self.queue_messages.get()
            logging.debug(f"Message from queue: {message}")
            if isinstance(message, kiosk_utils.Ticket):
                # Process the ticket
                logging.info(f"Processing ticket: {message.ticket_value} of type {message.ticket_type}")
                # Here you can add code to handle the ticket, e.g., print it or display it
            else:
                logging.warning(f"Unknown message type in queue: {type(message)}")
        # Schedule next check
        self.after(100, self.check_queue)
    def disable_buttons(self):
        '''Disable all buttons in the frame.'''
        for bttn in self.buttons:
            bttn.configure(state="disabled")
        #Delete previus after() if it exists
        if self._after_cancel_id is not None:
            self.after_cancel(self._after_cancel_id)
        # Schedule new reset of buttons to default state
        self._after_cancel_id = self.after(config['button_reset_to default_time_ms'],
                                           lambda: self.show_active_button(config['default_language_index']))
    def enable_buttons(self):
        '''Enable all buttons in the frame.'''
        for bttn in self.buttons:
            bttn.configure(state="normal")

    def show_active_button(self, button:int):
        '''Show the active button to user by changing image.'''
        self.active_button = button
        for bttn in self.buttons:
            if bttn.language[0] == button:
                bttn.configure(image=self._active_button_image)
            else:
                bttn.configure(image=self._normal_button_image)

class KioskApp(ctk.CTk):
    '''Main application class that inherits from CTk.'''
    def __init__(self, config=config):
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
 
        # Add the frame to the canvas
        self.canvas.create_window((100,200), width=self.frame.width, height=self.frame.height, window=self.frame, anchor=tk.NW)
 
def main():
    global config, queue_messages
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
            level=os.environ.get('LOGLEVEL', config['log_level']).upper(),
        )

    kiosk_app=KioskApp(config=config)
    kiosk_app.mainloop()
if __name__ == "__main__":
    main()