"""
storyTime

Created by Chris Lewis on 2011-06-13.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

__version__ = '0.1.0'

import logging
import os
import sys

LOG = logging.getLogger('storyTime')

def run(**kwargs):
    import gui
    gui.run_gui(**kwargs)
    for handle in LOG.handlers:
        handle.close()

def _setup_log():
    level = logging.DEBUG
    fh = _get_file_handler()
    fh.setLevel(level)
    LOG.addHandler(fh)
    LOG.setLevel(level)

def _get_file_handler():
    dir_ = os.path.dirname(__path__[0])
    # if the current path is actually a file
    if not os.path.isdir(dir_):
        dir_ = os.path.dirname(dir_)
    filename = os.path.join(dir_, 'storyTime.log')
    fmt = logging.Formatter('%(asctime)s %(name)-14s %(levelname)-7s %(message)s')
    fh = logging.FileHandler(filename)
    fh.setFormatter(fmt)
    return fh


_setup_log()
