__version__ = '0.1.0'
__author__ = 'Chris Lewis' #with a lot of help/reference from Bohdon Sayre

import sys, os
import logging

_LOG_LEVEL = logging.DEBUG if int(os.getenv('MBOT_DEBUG', False)) else logging.INFO
_PATHDIR = os.path.dirname(__path__[0])
if not os.path.isdir(_PATHDIR):
    _PATHDIR = os.path.dirname(_PATHDIR)


def get_log(name):
    log = logging.getLogger(name)
    log.setLevel(_LOG_LEVEL)
    log.handlers = []
    filename = os.path.join(_PATHDIR, 'storyTime.log')
    sh = logging.FileHandler(filename)
    f = logging.Formatter('%(asctime)s %(name)-14s %(levelname)-7s %(message)s')
    sh.setFormatter(f)
    sh.setLevel(_LOG_LEVEL)
    log.addHandler(sh)
    return log


class StoryTimeError(Exception):
    pass

def run(**kwargs):
    import gui
    gui.run_gui(**kwargs)
    log = get_log(__name__)
    for handle in log.handlers:
        handle.close()