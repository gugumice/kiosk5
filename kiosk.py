#!/usr/bin/env python3

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

config={'languages': ['LAT','ENG','RUS'],
       'images_lolder': 'pict',
       'images': ['red_button.png', 'red_button_50.png'],  
       'bg_image': 'EGL_background.png',
       'font': ('DejaVu Sans Mono',50),
       'button_debaunce_time_ms': 1000,
       'button_reset_to default_time_ms': 10*1000,
       'default_language': 0}

class KioskButton(ctk.CTkButton):
    '''A custom button class that inherits from CTkButton.'''
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
    def __init__(self, master=None, languages=None):
        super().__init__(master)
        # Load the images for the buttons
        active_img = Image.open('{}/{}'.format(config['images_lolder'],config['images'][0]))
        normal_img = Image.open('{}/{}'.format(config['images_lolder'],config['images'][1]))
        # Get CTkImage from the images
        self._active_button_image=ctk.CTkImage(active_img,size=active_img.size)
        self._normal_button_image=ctk.CTkImage(normal_img,size=normal_img.size)
        self.active_button = config['default_language']
        ## Set the size of the frame
        self.width =300
        self.height = 500
        self.configure(width=self.width, height=self.height, border_width=5,  fg_color="transparent", bg_color="transparent")
        
        self.master = master
        #Variable to store the after_cancel id
        self._after_cancel_id = None
        # Create a list of buttons
        self.buttons = list()
        # Create buttons for each language
        for bttn in enumerate(languages):
            self.buttons.append(KioskButton(self, language=bttn, text=bttn[1], image = self._normal_button_image))
            self.buttons[-1].pack(padx=2, pady=2, fill=ctk.BOTH, expand=True)
        # Set the default button to be active
        self.show_active_button(config['default_language'])

    def disable_buttons(self):
        '''Disable all buttons in the frame.'''
        for bttn in self.buttons:
            bttn.configure(state="disabled")
        #Delete previus after() if it exists
        if self._after_cancel_id is not None:
            self.after_cancel(self._after_cancel_id)
        # Schedule new reset of buttons to default state
        self._after_cancel_id = self.after(config['button_reset_to default_time_ms'], lambda: self.show_active_button(config['default_language']))
    def enable_buttons(self):
        '''Enable all buttons in the frame.'''
        for bttn in self.buttons:
            bttn.configure(state="normal")

    def show_active_button(self, button:int):
        '''Show the active button image.'''
        self.active_button = button
        for bttn in self.buttons:
            if bttn.language[0] == button:
                bttn.configure(image=self._active_button_image)
            else:
                bttn.configure(image=self._normal_button_image)


class app(ctk.CTk):   
    def __init__(self, height = 800, width=480, bg_image=None):
        super().__init__()

        self.bg_image = tk.PhotoImage(file = bg_image)
        self.height = height
        self.width = width
    
        # Create a canvas
        self.canvas = tk.Canvas(self, height=height, width=width, background="lightblue")
        self.canvas.pack()
        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor=ctk.NW)
 
        # Create a frame
        self.frame = MainFrame(self, languages=config['languages'])
 
        # Add the frame to the canvas
        self.canvas.create_window((100,200), width=self.frame.width, height=self.frame.height, window=self.frame, anchor=tk.NW)
 
def main():
    a=app(width=480, height=800, bg_image='{}/{}'.format(config['images_lolder'],config['bg_image']))
    a.mainloop()
if __name__ == "__main__":
    main()
