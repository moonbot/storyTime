"""
storyTime

Created by Chris Lewis on 2011-06-13.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

__version__ = '0.2.0'

from PySide.QtGui import QApplication
import controllers
import logging
import logging.handlers
import os
import sys

LOG = logging.getLogger('storyTime')

def setupLog():
    logFormat = '(%(relativeCreated)5d) %(levelname)-5s %(threadName)s.%(name)s %(funcName)s: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=logFormat)
    rotating = logging.handlers.RotatingFileHandler(logPath(), maxBytes=512*1024, backupCount=1)
    rotating.setFormatter(logging.Formatter(logFormat))
    root = logging.getLogger()
    root.addHandler(rotating)

def logPath():
    dir_ = os.path.dirname(__file__)
    return os.path.join(dir_, 'storyTime.log')

if __name__ == '__main__':
    setupLog()
    LOG.debug('%s %s', 'StoryTime', __version__)
    
    app = QApplication(sys.argv)
    app.setStyle('Plastique')
    wnd = controllers.StoryTimeWindow()
    # load any given files
    if len(sys.argv) > 1:
        wnd.loadPaths(sys.argv[1:])
    sys.exit(app.exec_())

