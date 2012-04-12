#!/usr/bin/env python
# encoding: utf-8
"""
data.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from audio import AudioRecording
from frames import FrameRecording
import copy
import logging
import os
import utils

__all__ = [
    'Recording',
    'ImageCollection',
]

LOG = logging.getLogger('storyTime.data')

DEFAULT_IMAGE_TYPES = [
    'jpg', 'jpeg', 'png', 'tif', 'tiff', 'tga', 'ico', 'gif',
]


class Recording(object):
    """
    Recording keeps track of a FrameRecording, AudioRecording, and VideoRecording.
    
    These three recording objects can be managed as one through this class
    which simplifies the interface to the actual data created by Story Time.
    """
    
    attrs = ('name', 'duration', 'imageCount', 'fps')
    
    def __init__(self, name='Recording', frames=None, audio=None):
        self.name = name
        self.framerec = frames if frames is not None else FrameRecording()
        self.audiorec = audio if audio is not None else AudioRecording()
        # self.videorec = video if video is not None else VideoRecording()
    
    def __repr__(self):
        return '<Recording {0!r} {1!r} {2!r}>'.format(self.name, self.framerec, self.audiorec)
    
    def __getitem__(self, key):
        if key in self.attrs:
            return getattr(self, key)
    
    def has_key(self, key):
        return key in self.attrs
    
    @property
    def fps(self):
        return self.framerec.fps
    
    @property
    def duration(self):
        return self.framerec.duration
    
    @property
    def imageCount(self):
        return len(self.framerec)
    
    @staticmethod
    def fromDict(recordingDict):
        """ Return a new Recording using the given string """
        fr = FrameRecording(recordingDict['fps'])
        for f in recordingDict['frames']:
            fr.appendFrame(Frame.deserialize(f))
        ar = AudioRecording(recordingDict['audioFile'])
        return Recording(recordingDict['name'], fr, ar)
    
    def toString(self):
        """ Return this Recording as a serialized string """
        serializedFrames = []
        for f in self.framerec.frames:
            serializedFrames.append(f.serialize())
        fps = self.framerec.fps
        tempFile = self.audiorec.tempFile
        recordingDict = {
            'frames':serializedFrames, 'fps':fps,
            'audioFile': self.audiorec.filename, 'name':self.name
        }
        return recordingDict


class ImageCollection(object):
    """
    A collection of images to be sample from during a Story Time recording.
    An image collection can be seeded with a directory or combination of images.
    It can then be sorted and organized for better usability.
    
    Image collections also provide a current index to keep track of which
    image is being sampled and making it easy to get the previous/next image.
    Collection seeking will loop both ways.
    """
    def __init__(self, images=None, imageTypes=DEFAULT_IMAGE_TYPES):
        self.imageTypes = imageTypes
        self._index = 0
        self._images = images if images is not None else []
    
    def __iter__(self):
        for f in self.images:
            yield f
    
    def __getitem__(self, key):
        if not isinstance(key, (int, slice)):
            raise TypeError
        return self.images[key]
    
    def __delitem__(self, key):
        if not isinstance(key, (int, slice)):
            raise TypeError
        del self._images[key]
    
    def __len__(self):
        return len(self._images)
    
    def __repr__(self):
        return 'hi'
        return '<ImageCollection {0} image(s) | @{1}>'.format(len(self.images), self.index)
    
    @property
    def images(self):
        return self._images
    @images.setter
    def images(self, value):
        self._images = []
        if isinstance(value, (tuple, list)):
            for i in value:
                if isinstance(i, (str, unicode)) and self.isValidImage(i):
                    self._images.append(os.path.normpath(i))
        elif isinstance(value, (str, unicode)):
            self._images.append(os.path.normpath(value))
    
    @property
    def index(self):
        if self._index not in range(len(self)):
            # this desync is handled by clamping
            self._index = max(min(self._index, len(self) - 1), 0)
        return self._index
    @index.setter
    def index(self, value):
        if not isinstance(value, int):
            raise TypeError('expected int, got {0}'.format(type(value).__name__))
        self._index = self.validateIndex(value)
    
    def validateIndex(self, value):
        if len(self) == 0:
            return 0
        else:
            return value % len(self)
    
    def isValidImage(self, image):
        types = [x.strip('.').lower() for x in self.imageTypes]
        ext = os.path.splitext(image)[1].strip('.')
        return ext.lower() in types
    
    def clear(self):
        self.images = []
        self.index = 0
    
    def imageIndex(self, image):
        """
        Return the index of the given image within the collection
        Returns None if the image is not in the collection
        """
        if os.path.normpath(image) in self:
            return self.images.index(os.path.normpath(image))
    
    def append(self, image):
        """
        Append the given image or images to the collection.
        This is like a combined append/extend functionality.
        """
        if isinstance(image, (str, unicode)):
            self.images.append(os.path.normpath(image))
        elif isinstance(image, (list, tuple)):
            self.images.extend([os.path.normpath(i) for i in image])
    
    def extend(self, images):
        self.append(images)
    
    def loadDir(self, dir_, additive=False):
        if not os.path.isdir(dir_):
            raise OSError('directory does not exist: {0}'.format(dir_))
        files = os.listdir(dir_)
        imgs = [os.path.join(dir_, i) for i in files if self.isValidImage(i)]
        if additive:
            self.images.extend(imgs)
        else:
            self.images = imgs
        self.sort()
    
    def loadSequence(self, image):
        """ Load the image sequence associated with the given image """
        LOG.warning('loadSequence not yet implemented')
        self.images = image
    
    def sort(self, cmp_=None, key=None, reverse=False):
        if cmp_ is None:
            # case insensitive sort
            cmp_ = lambda x,y: cmp(x.lower(), y.lower())
        self.images.sort(cmp=cmp_, key=key, reverse=reverse)
    
    def current(self):
        if len(self.images) == 0:
            return
        return self[self.index]
    
    def prev(self, seek=True):
        if len(self.images) == 0:
            return
        if seek:
            self.index -= 1
            i = self.index
        else:
            i = self.validateIndex(self.index - 1)
        return self[i]
    
    def next(self, seek=True):
        if len(self.images) == 0:
            return
        if seek:
            self.index += 1
            i = self.index
        else:
            i = self.validateIndex(self.index + 1)
        return self[i]
    
    def seekToImage(self, image):
        """ Seek to the given image, if its in the collection. Otherwise ignore """
        index = self.imageIndex(image)
        if index is not None:
            self.index = index

