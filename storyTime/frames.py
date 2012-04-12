#!/usr/bin/env python
# encoding: utf-8
"""
storyTime.frames

Created by Bohdon Sayre on 2012-04-12.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""


class FrameRecording(object):
    """
    A recording created by Story Time.
    
    All times on a FrameRecording are stored in frames, not seconds.
    
    FrameRecordings provide a pretty expansive interface for modification.
    This includes subscription and iteration akin to a list,
    eg. myRecording[4:12] to retrieve frames 4 through 12.
    """
    def __init__(self, fps=24):
        self.fps = fps
        self.start = 0
        self._frames = []
    
    def __repr__(self):
        return '<FrameRecording | {0.start}-{0.end}@{0.fps} | {1} frame(s)>'.format(self, len(self.frames))
    
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
    
    def __len__(self):
        return len(self._frames)
    
    def __add__(self, other):
        if isinstance(other, FrameRecording):
            new = copy.deepcopy(self)
            for f in other:
                new.append(f.image, f.duration)
            return new
        return NotImplemented
    
    @property
    def frames(self):
        return self._frames
    
    @property
    def end(self):
        return self.start + self.duration
    
    @property
    def duration(self):
        return sum([f.duration for f in self.frames])
    
    @property
    def images(self):
        return sorted(list(set([f.image for f in self.frames])))
    
    def clear(self):
        self._frames = []
    
    def append(self, image, duration):
        f = Frame(image, duration)
        self.appendFrame(f)
    
    def appendFrame(self, f):
        if not isinstance(f, Frame):
            raise TypeError('expected a Frame, got {0}'.format(type(f).__name__))
        self._frames.append(f)
    
    def insert(self, index, image, duration):
        f = Frame(image, duration)
        self._frames.insert(index, f)
    
    def pop(self, index):
        if index < len(self.frames):
            return self._frames.pop(index)
    
    
    def relativeTime(self, time):
        """ Convert the given absolute time to a time relative to start """
        return time - self.start
    
    def absoluteTime(self, time):
        """ Convert the given relative time to an absolute time """
        return time + self.start
    
    def getIndex(self, time):
        """ Return the index of the frame at the given time """
        if len(self) == 0:
            return
        rtime = self.relativeTime(time)
        if rtime < 0:
            return 0
        elif rtime >= self.duration:
            return len(self.frames) - 1
        t = 0
        for i, f in enumerate(self.frames):
            t += f.duration
            if rtime < t:
                return i
    
    def getFrame(self, time):
        """ Return the frame at the given time """
        index = self.getIndex(time)
        if index is not None:
            return self.frames[self.getIndex(time)]
        
    def inTime(self, index):
        if index < len(self):
            rtime = sum([f.duration for f in self.frames[:index]])
            return self.absoluteTime(rtime)
        return self.absoluteTime(0)
    
    def outTime(self, index):
        if index < len(self):
            rtime = sum([f.duration for f in self.frames[:index+1]])
            return self.absoluteTime(rtime)
        return self.absoluteTime(0)
    



class Frame(object):
    """
    A specific frame within a FrameRecording. Frames only care about the
    image they represent and how long that image is displayed. Their
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
    
    def serialize(self):
        return {'image':self.image, 'duration':self.duration}
    
    @staticmethod
    def deserialize(dictonary):
        return Frame(dictonary['image'], dictonary['duration'])

