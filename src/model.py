"""
model.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from data import *
import logging
import os

LOG = logging.getLogger(__name__)


class StoryTimeModel(object):
    def __init__(self):
        # File Settings
        self.workingDir = os.getcwd()
        
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
    def images(self):
        return self.imageCollection.images
    
    def curImage(self):
        return self.imageCollection.current()
    
    def prevImage(self):
        return self.imageCollection.prev()
    
    def nextImage(self):
        return self.imageCollection.next()
    


