#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from os import walk

window = tk.Tk()
window.title('Widgets and return')
window.geometry('400x600')

class AnimatedLabel(ttk.Frame):
    def __init__(self, parent, label_text, path):
        iimage = tk.PhotoImage(file=path)
        super().__init__(master = parent)
        ttk.Label(self,image = iimage).grid(row=0,column=0,sticky='nsew')
        ttk.Label(self,text=label_text).grid(row=0,column=1,sticky='nsew')
        self.pack(expand=True,fill='both', padx=10, pady=10)
#AnimatedLabel(window,'label','yellow/light_00027.png')
#image = tk.PhotoImage(file="yellow/light_00019.png")
# Display it within a label.
#label = ttk.Label(image=image)
#label.pack()

class Aa(ttk.Label):
    def __init__(self, path):
        self.image = tk.PhotoImage(file=path)
        super().__init__(image = self.image)

class AnimatedLabel(ttk.Label):
    '''
    Animated label: path - folder with animation sequence images
                    speed - time ms images are replaced
                    forthback - animation from 1st to last or forth and back
    '''
    def __init__(self, path: str, speed=50, forthback = False):
        self._images = self.import_folder(path)
        self.image_index = 0
        self._cnt = 1
        self.image_count = len(self._images) - 1
        self.animate = tk.StringVar(value='on')
        self.speed = speed
        super().__init__(image = self._images[self.image_index])
        self.inf_animate()
        self.forthback = forthback
    def import_folder(self, path):
        image_paths=[]
        for _, _, image_data in walk(path):
            image_data = sorted(image_data, key = lambda item: int(item [-9:-4]))
            image_data = ['{}/{}'.format(path,item) for item in image_data]
            image_paths.append(image_data)
        images = []
        for image_path in image_paths[0]:
            img = tk.PhotoImage(file=image_path)
            images.append(img)
        return(images)
    
    def inf_animate(self) -> None:
        if self.animate.get() == 'on':
            self.image_index += self._cnt
            if self.image_index > self.image_count-1:
                if self.forthback: self._cnt = -1 
                else: self.image_index=0
            if self.image_index < 0: self._cnt = 1
        self.configure(image = self._images[self.image_index])
        self.after(self.speed, self.inf_animate)


    
#Aa('yellow/light_00027.png').pack()
#label.pack()
 
AnimatedLabel('yellow',50,True).pack(expand=True)
window.mainloop()
