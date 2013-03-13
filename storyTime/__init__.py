"""
storyTime

Created by Chris Lewis on 2011-06-13.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

__version__ = '0.2.4'

from PySide.QtGui import QApplication
from utils import isFrozen, modulePath
import controllers
import getpass
import logging
import logging.handlers
import os
import sys

LOG = logging.getLogger('storyTime')

def setupLog():
    logFormat = '(%(relativeCreated)5d) %(levelname)-5s %(threadName)s.%(name)s %(funcName)s: %(message)s'
    if not isFrozen():
        logging.basicConfig(level=logging.DEBUG, format=logFormat)
    rotating = logging.handlers.RotatingFileHandler(logPath(), maxBytes=512*1024, backupCount=1)
    rotating.setFormatter(logging.Formatter(logFormat))
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(rotating)
    root.info("INIT")

def logPath():
    name = 'storyTime_{0}.log'.format(getpass.getuser())
    return os.path.join(modulePath(), name)

def main():
    setupLog()
    LOG.debug('%s %s', 'StoryTime', __version__)

    app = QApplication(sys.argv)
    app.setStyle('Plastique')
    wnd = controllers.StoryTimeWindow()
    if len(sys.argv) > 1:
        wnd.loadPaths(sys.argv[1:])
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
