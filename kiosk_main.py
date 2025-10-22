#!/usr/bin/env python3


import tkinter as tk
import customtkinter as ctk
from PIL import Image
import os
import logging

from queue import Queue

import kiosk_config
import kiosk_utils

config = dict()
queue_to_gui = Queue()
class KioskButton(ctk.CTkButton):
    def __init__(self, master=None,  
                 lang:list = None,
                 active: bool = False,
                 button_debounce_time_ms:int = 5000):
        super().__init__(master)
        self.master = master
        self.lang = lang
        self.active = active
        self._button_debounce_time_ms = button_debounce_time_ms
        self.configure(
            command=lambda: self.master.on_click(self.lang),
            border_width =20,
            border_spacing=10,
            corner_radius = 50,
            text = self.lang[1],
            hover = False,
            font=("Noto Sans Mono",80, "bold"))
        self.idle()
        
    def idle(self):
        self.configure(state="normal",
                       border_color="#008ca4",
                       fg_color=("white","#008ca4"),
                       text_color= ("#008ca4","white"),
                       bg_color="transparent")
    
    def pressed(self):
        self.active = True
        self.configure(
                text_color="white",
                fg_color=("#008ca4")
                )
    def state_disable(self):
        self.configure(state = "disabled")
    
    def state_normal(self):
        self.configure(state = "normal")

class MainFrame(ctk.CTkFrame):
    """A custom frame class that inherits from CTkFrame.
    It contains a list of buttons and manages their state.
    """
    def __init__(self, master=None, width:int = 300, height:int = 500, posXY:list = [100,200], config:dict = None):
        super().__init__(master)
        self.master = master
        self.config = config
        # Set the size of the frame
        self.width = width
        self.height = height
        self.posXY = posXY
        self.buttons = list()
        self.selected_button = config['default_language_index']
        self.configure(
            width=self.width,
            height=self.height,
            border_width=1,
            border_color = "grey",
            fg_color="white",
            bg_color="white",
        )
        self._reset_to_default_bttn = None
        self.init_buttons()
        self.enable_buttons(self.selected_button)
        self.set_def_timeout()
    
    def init_buttons(self):
        for lang in enumerate(self.config['languages']):
            button = KioskButton(self, lang=lang,
                                 active=False,
                                 button_debounce_time_ms = 500)
            self.buttons.append(button)
            self.buttons[-1].pack(padx=25, pady=25, fill=ctk.BOTH, expand=True)
            logging.debug('bttns_init: {}'.format(lang))
    
    def debounce_buttons(self, debounce_time:int):
        self.disable_buttons()
        self.after(debounce_time, self.enable_buttons())
        logging.debug('bttns_debounce')

    def disable_buttons(self, active_button_index):
        logging.debug('bttns_disabled')
        for idx, button in enumerate(self.buttons):
            button.state_disable()
            if idx == active_button_index:
                button.pressed()
            else:
                button.idle()

    def deactivate_buttons(self):
        logging.debug('bttns_deactivated')
        for button in self.buttons:
            button.active = False

    def enable_buttons(self,active_button_index):
        logging.debug('bttns_enabled, act: {}'.format(active_button_index))
        for idx, button in enumerate(self.buttons):
            button.state_normal()
            if idx == active_button_index:
                button.pressed()
            else:
                button.idle()

    def set_def_timeout(self):
        logging.info('setting default timeout: {}'.format(self.config["button_reset_to_default_time_ms"]))
        kiosk_utils.set_brightness(
            config["screen_brightness_normal"]
            if kiosk_utils.is_working_time(
                start=config["working_hours"][0],
                end=config["working_hours"][1],
                workdays=config["working_days"],
            )
            else config["screen_brightness_inactive"],
            config['screen_brightness_path']
        )
        self._reset_to_default_bttn = self.after(self.config["button_reset_to_default_time_ms"],
                                            self.set_to_default_bttn)

    def set_to_default_bttn(self):
        logging.info('setting to default button: {}'.format(self.config['default_language_index']))
        if self.selected_button != self.config['default_language_index']:
            self.enable_buttons(self.config['default_language_index'])

        self.set_def_timeout()


    def on_click(self, lang):
        logging.debug('bttns_sel: {}'.format(lang))
        self.selected_button = lang[0]
        #Debounce
        self.disable_buttons(self.selected_button)
        self.after(self.config['button_debounce_time_ms'], self.enable_buttons, self.selected_button)
        #Reset to def button & check screen backlight
        if self._reset_to_default_bttn:
            self.after_cancel(self._reset_to_default_bttn)
        self.set_def_timeout()
        
class KioskApp(ctk.CTk):
    """Main application class that inherits from CTk."""
    def __init__(self, config=config, queue_to_gui: Queue = queue_to_gui):
        super().__init__()
        self.config = config
        self.bind('<Control-slash>', quit)      # forward-slash
        self.bg_image = (
            tk.PhotoImage(
                file=os.path.join(self.config["assets_loader"], self.config["bg_image"])
            )
            if self.config["bg_image"]
            else None
        )

        self.height = self.config["screen_height"]
        self.width = self.config["screen_width"]

        # Canvas for popup widgets
        self.canvas = tk.Canvas(
            self, height=self.height, width=self.width, background="lightblue"
        )
        self.canvas.pack()
        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor=ctk.NW)

        # Main frame
        self.frame = MainFrame(self, width=self.config['button_frame_width'],
                                height=self.config['button_frame_height'],
                                posXY = self.config['button_frame_posXY'],
                                config = self.config)
        self.popup_window = None

        self.canvas.create_window(
            self.frame.posXY,
            width=self.frame.width,
            height=self.frame.height,
            window=self.frame,
            anchor=tk.NW,
        )
    # def quit(self, event):
    #     print('\nExit requested by user')
    #     quit

def main():
    config = kiosk_config.read_config(os.path.join(os.getcwd(),'kiosk.ini'))
        # Logging
    if config["log_file"] is None:
        logging.basicConfig(
            format="%(asctime)s - %(message)s",
            level=os.environ.get("LOGLEVEL", config["log_level"]).upper(),
        )
    else:
        logging.basicConfig(
            format="%(asctime)s - %(message)s",
            filename=config["log_file"],
            filemode="w",
            level=os.environ.get("LOGLEVEL", config["log_level"]).upper(),
        )
    kiosk_app = KioskApp(config=config)
    kiosk_app.mainloop()

if __name__ == '__main__':
    main()
