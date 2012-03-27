"""
model.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from data import *
from utils import enum
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import logging
import os

LOG = logging.getLogger(__name__)

# TODO: cluster mappings that affect each other or create event pool presets
Mappings = enum(
    'isRecording', 'isPlaying', 'fps', 'curTime', 'imageCount',
    'curImageIndex', 'curImageIndexLabel', 'curImage', 'curImagePath', 'end',
)

class StoryTimeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(StoryTimeModel, self).__init__(parent)
        
        # Recording / Playback
        self._isRecording = False
        self._isPlaying = False
        self._fpsOptions = FPS_OPTIONS
        self.customFps = 12
        self.fps = 24
        self.loop = True
        # all recording collections
        self.recordings = []
        # currently loaded/active recording collection
        self.curRecording = None
        # current time of the playback timeline
        self.curTime = 0
        # current image collection
        self.imageCollection = ImageCollection()
        LOG.debug('Model Initialized')
    
    def __repr__(self):
        return '<StoryTimeModel | {0} recording(s)>'.format(len(self.recordings))
    
    @property
    def isRecording(self):
        return self._isRecording
    
    @property
    def isPlaying(self):
        return self._isPlaying
    
    @property
    def fpsList(self):
        return sorted(self._fpsOptions.keys()) + [self.customFps]
    
    @property
    def fpsOptions(self):
        opts = self._fpsOptions.copy()
        opts.update( {self.customFps:self.fps_label(self.customFps)} )
        return opts
    
    def fps_label(self, fps):
        if fps in self._fpsOptions.keys():
            return self._fpsOptions[key]
        else:
            return 'Custom ({0} fps)'.format(fps)
    
    
    # recordings manipulation
    
    @property
    def curFrameRecording(self):
        return self.curRecording.frames
    
    @property
    def curAudioRecording(self):
        return self.curRecording.audio
    
    def load_recording(self, index):
        if index < 0 or index >= len(self.recordings):
            raise IndexError
        self.curRecording = self.recordings[index]
    
    def new_recording(self):
        self.curRecording = RecordingCollection()
        self.recordings.append(self.curRecording)
    
    
    # image collection methods
    
    @property
    def imageCount(self):
        return len(self.images)
    
    @property
    def images(self):
        return self.imageCollection.images
    
    @property
    def curImageIndex(self):
        return self.imageCollection.seek
    
    @property
    def curImagePath(self):
        return self.imageCollection.current()
    
    def prevImage(self):
        return self.imageCollection.prev()
    
    def nextImage(self):
        return self.imageCollection.next()
    
    
    # qt model methods
    
    def rowCount(self, parent):
        return 1
    
    def columnCount(self, parent):
        return 1
    
    def data(self, index, role):
        LOG.debug('mapping={0} role={1}'.format(Mappings.names[index.column()], role))
        if not index.isValid():
            return
        
        # we don't care about rows since our model
        # is essentially singular. the column is our mapping
        mapping = index.column()
        
        if mapping == Mappings.imageCount:
            return self.imageCount
        elif mapping == Mappings.curImagePath:
            return self.curImagePath
        elif mapping == Mappings.curImageIndex:
            return self.curImageIndex
        elif mapping == Mappings.curImageIndexLabel:
            return '{0:0{pad}}/{1}'.format(self.curImageIndex, self.imageCount, pad=len(str(self.imageCount)))
    
    
    def setData(self, index, value, role = Qt.EditRole):
        LOG.debug('mapping={0} value={1}'.format(Mappings.names[index.column()], value.toPyObject()))
        
        mapping = index.column()
        
        if mapping == Mappings.curImageIndex:
            self.imageCollection.seek = value.toPyObject()
            self.dataChanged.emit(index, index)
            return True
        
        self.dataChanged.emit(index, index)
        return False
    
    def index_range(self, start, end):
        return (self.index(start), self.index(end))
    
    def index(self, row, column=0, parent=None):
        return self.createIndex(row, column)
    
    def parent(self, index):
        """ There is only one viable index, and therefore no feasible parent """
        return QModelIndex()


