import os
import sys

def _init():
    global _global_dict
    _global_dict = {}

def set_value(name, value):
    _global_dict[name] = value

def get_value(name):
    return _global_dict[name]

def _exit():
    os.system('stty sane')
    sys.exit()
