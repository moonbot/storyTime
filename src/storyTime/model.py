"""
model.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

import copy
import logging
import os

LOG = logging.getLogger(__name__)

FPS_LABELS = {
    24:'Film (24 fps)',
    25:'PAL (25 fps)',
    30:'NTSC (30 fps)',
    48:'Show (48 fps)',
    50:'PAL Field (50 fps)',
    60:'NTSC Field (60 fps)',
}

class Recording(object):
    """
    Represents a specific recording created by Story Time.
    Times are stored in frames as Story Time is primarily
    a frame-based tool.
    """
    def __init__(self, fps=24):
        self.fps = fps
        self.start = 0
        self._frames = []
    
    def __repr__(self):
        return '<Recording | {0.start}-{0.end}@{0.fps} | {1} frame(s)>'.format(self, len(self.frames))
    
    def __iter__(self):
        for f in self.frames:
            yield f
    
    def __getitem__(self, key):
        if not isinstance(key, (int, slice)):
            raise TypeError
        return self.frames[key]
    
    def __delitem__(self, key):
        if not isinstance(key, (int, slice)):
            raise TypeError
        del self._frames[key]
    
    def __add__(self, other):
        if isinstance(other, Recording):
            new = copy.deepcopy(self)
            for f in other:
                new.append(f.image, f.duration)
            return new
        return NotImplemented
    
    def getFrames(self):
        return self._frames
    frames = property(getFrames)
    
    def getEnd(self):
        return self.start + self.duration
    end = property(getEnd)
    
    def getDuration(self):
        return sum([f.duration for f in self.frames])
    duration = property(getDuration)
    
    def getIndeces(self):
        return range(len(self.frames))
    indeces = property(getIndeces)
    
    def relative_time(self, time):
        """ Convert the given absolute time to a time relative to start """
        return time - self.start
    
    def absolute_time(self, time):
        """ Convert the given relative time to an absolute time """
        return time + self.start
    
    def get_frame(self, time):
        rtime = self.relative_time(time)
        if rtime < 0:
            return
        t = 0
        for f in self.frames:
            t += f.duration
            if rtime < t:
                return f
        return None
        
    def in_time(self, index):
        if index < len(self.frames):
            rtime = sum([f.duration for f in self.frames[:index]])
            return self.absolute_time(rtime)
    
    def out_time(self, index):
        if index < len(self.frames):
            rtime = sum([f.duration for f in self.frames[:index+1]])
            return self.absolute_time(rtime)
    
    def clear(self):
        self._frames = []
    
    def append(self, image, duration):
        f = Frame(image, duration)
        self._frames.append(f)
    
    def insert(self, index, image, duration):
        f = Frame(image, duration)
        self._frames.insert(index, f)
    
    def insert_recording(self, other):
        if isinstance(other, Recording):
            new = copy.deepcopy(self)
        raise TypeError
    
    def pop(self, index):
        if index < len(self.frames):
            return self._frames.pop(index)



class Frame(object):
    """
    A specific frame within a Recording.
    Frames only care about the image they represent
    and how long that image is displayed. Their
    cut information is stored in the recording.
    """
    def __init__(self, image, duration):
        """
        `image` - the full path to the image this frame represents
        `duration` - the frame duration of the image, min = 1
        """
        self.image = image
        self.duration = duration
    
    def __eq__(self, other):
        if isinstance(other, Frame):
            return self.image == other.image and self.duration == other.duration
        return NotImplemented
    
    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result
    
    def __repr__(self):
        return 'Frame({0!r}, {1})'.format(os.path.basename(self.image), self.duration)
    
    def getImage(self):
        if self._image is None:
            return ''
        return self._image
    def setImage(self, value):
        if isinstance(value, (str, unicode)):
            self._image = os.path.normpath(value)
        else:
            self._image = None
    image = property(getImage, setImage)
    
    def getDuration(self):
        return self._duration
    def setDuration(self, value):
        self._duration = max(1, int(value))
    duration = property(getDuration, setDuration)




class StoryTimeModel(object):
    
    def __init__(self):
        self.fps_labels = FPS_LABELS
        self.fps = 24
        self.isRecording = False
        self.isPlaying = False
        
        self.startFrame = 0
        model = {
            'recording':self.BUTTON_STATES.OFF,
            'playing':self.BUTTON_STATES.OFF,
            'startFrame':0,
            'curFrame':0,
            'curImgFrame':1,
            'timing_data':[],
            'images':[],
            'fps':24,
            'fpsOptions':FPS_OPTIONS,
            'fpsIndex':0,
            'savePath':'',
            'audioPath':'',
            'recordTiming':True,
            'recordAudio':True,
            'loop':True,
            'timecode':0,
            'countdown':None,
            'countdownms':0
        }
        LOG.debug('Model Initialized')

