"""
storyTime

Created by Chris Lewis on 2011-06-13.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

__version__ = '0.2.0'
__all__ = [
    'LOG',
    'run',
    'log_path',
]

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from storyTime import model, controller
import logging
import logging.handlers
import os
import sys

LOG = logging.getLogger(__name__)

def run():
    logFormat = '(%(relativeCreated)5d) %(levelname)-5s %(threadName)s.%(name)s %(funcName)s: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=logFormat)
    
    rotating = logging.handlers.RotatingFileHandler(log_path(), maxBytes=512*1024, backupCount=1)
    rotating.setFormatter(logging.Formatter(logFormat))
    
    root = logging.getLogger()
    root.addHandler(rotating)
    LOG.debug('%s %s', 'StoryTime', __version__)
    
    LOG.debug('Initializing StoryTime...')
    
    app = QApplication(sys.argv)
    app.setStyle('Plastique')
    m = model.StoryTimeModel()
    v = uic.loadUi('views/main.ui')
    c = controller.StoryTimeController(m, v)
    LOG.debug('Running application...')
    v.show()
    return app.exec_()

def log_path():
    dir_ = os.path.dirname(__path__[0])
    if not os.path.isdir(dir_):
        dir_ = os.path.dirname(dir_)
    return os.path.join(dir_, 'storyTime.log')

