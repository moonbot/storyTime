"""
view.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from PyQt4 import QtCore, QtGui
from storyTime.ui import mainUI
import logging
import sys

LOG = logging.getLogger(__name__)

_APP = None

def init_app():
    global _APP
    if _APP is None:
        _APP = QtGui.QApplication(sys.argv)
        _APP.setStyle('Plastique')
    return _APP

def app():
    return init_app()


class StoryTimeView(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.ui = mainUI.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('Story Time')
        LOG.debug('View Initialized')


class StoryTimeControlUI(object):
    
    # Main View Functions
    # -------------------
    
    def view_browse_open(self, caption):
        """Return the path of the selected file"""
        raise NotImplementedError
    
    def view_browse_open_dir(self, caption):
        """Return the path of the selected directory"""
        raise NotImplementedError
    
    def view_browse_save_as(self, caption):
        """Return the path of the selected file"""
        raise NotImplementedError
    
    def view_update_timer(self):
        """Refresh the timer and returns the time since the previous call"""
        raise NotImplementedError
    
    def view_start_timer(self, ms):
        """Start a timer to call an event in ms milliseconds"""
        raise NotImplementedError
    
    def view_start_disp_timer(self):
        """Start the timer used for the UI's timecode"""
        raise NotImplementedError
    
    def view_stop_disp_timer(self):
        """Stop the timer used for the UI's timecode"""
        raise NotImplementedError
    
    def view_query_custom_fps(self):
        """Query the user for a custom fps and return the value"""
        raise NotImplementedError
    
    def view_query_countdown_time(self):
        """Query the user for a countdown time and return the value"""
        raise NotImplementedError
    
    def view_get_image_formats(self):
        """Return a list of valid image formats"""
        raise NotImplementedError
    
    # Observer View Functions
    # -----------------------
    
    def ob_recording(self):
        raise NotImplementedError
    
    def ob_playing(self):
        raise NotImplementedError
    
    def ob_cur_frame(self):
        raise NotImplementedError
    
    def ob_images(self):
        raise NotImplementedError
    
    def ob_fps_options(self):
        raise NotImplementedError
    
