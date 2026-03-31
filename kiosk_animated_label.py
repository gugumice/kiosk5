#!/usr/bin/env python3

import tkinter as tk
import os
import pickle
from PIL import Image, ImageSequence, ImageTk
import logging
import kiosk_config
from time import sleep

def gif_frames_to_dict(config:dict = None, gifs_keys:list = None) -> dict:
    '''
    Load GIFs to dict as frames
    args
    : config - kiosk configuration file
    : gifs_keys - List of keys on kiosk config.ini that points to GIF files to be cached
    
    Returns: dict with Image sequences indexed by GIF  file name

    '''
    if gifs_keys is None:
        raise Exception('load_frames: No config')
    width = config['animated_icon_width']
    height = config['animated_icon_height']
    gif_cache = dict()
    for gif in gifs_keys:
        p = os.path.join(config['assets_loader'],config[gif])
        logging.info('Adding {} to dict'.format(p))
        try:
            img = Image.open(os.path.join(config['assets_loader'],config[gif]))
        except Exception as e:
            logging.error(e)
        else:
            gif_frames = list()
            for frame in ImageSequence.Iterator(img):
                frame = frame.copy().convert("RGBA")
                if width and height:
                    frame = frame.resize((width,height))
                gif_frames.append(frame)
            gif_cache[config[gif]] = gif_frames
    return(gif_cache)

def save_gif_frames(source:dict, cache_path:str = None) -> None:
    '''
    Save Dict with GIF frames
    to folder using Pickle
    '''
    if cache_path is None:
        raise Exception('Destination path not specified')
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    for k,v in source.items():
        p = os.path.join(cache_path,'{}.pkl'.format(k))
        logging.debug('Writing to {}'.format(p))
        try:
            with open(p,'wb') as pf:
                pickle.dump(v, pf)
        except Exception as e:
            logging.error(e)
        else:
            logging.debug('Success')

def load_gif_frames(source_dir:str=None):
    '''
    Loads GIFs from Pickle files to Dict
    '''
    img_cache=dict()
    if source_dir is None:
        raise Exception('Invalid args: source_dir')
    if not os.path.exists(source_dir):
        raise Exception('{} not found.'.format(source_dir))
    pickle_files = [f for f in os.listdir(source_dir) if f.endswith(".pkl")]
    for f in pickle_files:
        p = os.path.join(source_dir,f)
        logging.debug('Writing {} to cache'.format(p))
        try:
            with open(p,'rb') as pf:
                img_cache[f[:f.rfind('.')]] = pickle.load(pf)
        except Exception as e:
            logging.error(e)
    return(img_cache)

class AnimatedGifLabelAcc(tk.Label):
    def __init__(self, master, gif_path:str, delay:int=50, width:int=None, height:int=None, img_cache = None):
        super().__init__(master,
                        width = width,
                        height = height,
                        padx = 0,
                        pady = 0)
        self.width = width
        self.height = height
        self.gif_path = gif_path
        self.delay = delay  # Time between frames in ms
        self.Bd = 0
        self.frames = []
        self.gif_path = gif_path
        self.img_cache = dict() if img_cache is None else img_cache
        self._load_frames()
        self.current_frame = 0
        self._is_animating = False
        self._anim_cycles = 0
        self._curr_cycle = 0

    def _load_frames(self) -> None:
        '''
        Creates GIF frames or loads them from img_cache
        If GIF frames nor in img_cache - saves trames there
        '''
        gif_file_name = os.path.basename(self.gif_path)
        d = dict()
        if gif_file_name not in self.img_cache:
            logging.debug('{} not in cache'.format(gif_file_name))
            img = Image.open(self.gif_path)
            self.frames.clear()
            frames = list()
            for frame in ImageSequence.Iterator(img):
                frame = frame.copy().convert("RGBA")
                if self.width and self.height:
                    frame = frame.resize((self.width, self.height))
                frames.append(frame)
            for frame in frames:
                self.frames.append(ImageTk.PhotoImage(frame))
            # Save image
            cache_path = os.path.join(os.path.dirname(self.gif_path), 'img_cache')
            if not os.path.exists(cache_path):
               os.makedirs(cache_path)
            # Create dict for saving
            dict_for_cache = dict()
            dict_for_cache[gif_file_name] = frames
            # Compose Pickle file name
            pkl_name = os.path.join(cache_path,'.'.join((gif_file_name,'pkl')))
            try:
                with open(pkl_name,'wb') as pf:
                    pickle.dump(frames, pf)
            except Exception as e:
                logging.error(e)
            else:
                logging.debug('Success writing to {}'.format(pkl_name))
        else:
            logging.debug('{} in cache'.format(gif_file_name))
            self.frames.clear()
            for frame in self.img_cache[gif_file_name]:
                self.frames.append(ImageTk.PhotoImage(frame))

    def start_animation(self, cycles = 0):
        if not self._is_animating:
            self._is_animating = True
            self._anim_cycles = cycles
            self._animate()

    def stop_animation(self):
        self._is_animating = False

    def stopped(self):
        return not self._is_animating
    
    def _animate(self):
        if not self._is_animating or not self.frames:
            return
        self.config(image=self.frames[self.current_frame])
        self.current_frame += 1
        if self.current_frame > len(self.frames) - 1:
            self.current_frame = 0
            if self._anim_cycles > 0:
                self._curr_cycle += 1
        if self._anim_cycles == 0 or self._curr_cycle < self._anim_cycles:
            self.after(self.delay, self._animate)
        else:
            self.stop_animation()

def main():
    logging.basicConfig(format="%(levelname)s:%(asctime)s - %(message)s", level=logging.DEBUG)
    config = kiosk_config.read_config(os.path.join(os.getcwd(),'kiosk.ini'))
    image_cache = dict()
    try:
        image_cache = load_gif_frames(os.path.join(config['assets_loader'],'img_cache'))
    except:
        pass
    print('{} gif(s) loaded'.format(len(image_cache)))
    print(image_cache.keys())

    root = tk.Tk()
    root.geometry("300x300")
    gif_label = AnimatedGifLabelAcc(root, "assets/loading.gif", delay=40, width=200, height=200, img_cache = image_cache)
    gif_label.pack(expand=True)
    gif_label.start_animation(1)
    
    root.mainloop()



if __name__ == "__main__":
    main()
