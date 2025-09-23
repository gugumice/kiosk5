#!/usr/bin/env python3
'''
Testing tkinter, screen orientation, touchscreen
'''

import tkinter as tk
from tkinter import ttk

languages = ('LV', 'EN', 'RU')

kio_style = ttk.Style()
print(kio_style.theme_names())
kio_style.theme_use('clam')

# class KioStyles(ttk.Style):
#     def __init__(self):
#         super().__init__()
#         self.theme_use('clam')
#         self.configure('big.TButton', font=(None, 60), foreground='#fefefe', background='#008ca4', anchor="center", )
#         self.map('big.TButton', foreground=[('active', '#fefefe')], background=[('active', '#008ca4')])


class KioApplication(tk.Tk):
    def __init__(self, geometry="480x800", useTk=True, sync=False, use=None):
        super().__init__()
        self.geometry(geometry)
        #self.overrideredirect(True)
        self.frames = list()
        for l in enumerate(languages):
            f = KioFrame(self, l, border=1, borderwidth=1, relief=tk.SUNKEN)
            self.frames.append(f)

class KioFrame(ttk.Frame):
    def __init__(self, parent, language:list, border=0, borderwidth=0, relief=tk.FLAT):
        super().__init__(parent)
        self.configure(border=border, borderwidth=borderwidth, relief=relief)
        self.parent = parent
        self.language = language
        self.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)
        self.button = ttk.Button(self, text=language[1], command=self.select_report_language, style="TButton")
        self.button.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)
        
    def select_report_language(self):
        pass

def main():
    app = KioApplication()
    app.mainloop()

if __name__ == "__main__":
    main()
