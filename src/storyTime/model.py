"""
model.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

import copy
import logging
import os

LOG = logging.getLogger(__name__)

FPS_OPTIONS = {
    24:'Film (24 fps)',
    25:'PAL (25 fps)',
    30:'NTSC (30 fps)',
    48:'Show (48 fps)',
    50:'PAL Field (50 fps)',
    60:'NTSC Field (60 fps)',
}

DEFAULT_IMAGE_TYPES = [
    'jpg', 'jpeg', 'png', 'tif', 'tiff', 'tga',
]

class FrameRecording(object):
    """
    A recording created by Story Time. Times are stored
    in frames as Story Time is primarily a frame-based tool.
    
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
        self._frames.append(f)
    
    def insert(self, index, image, duration):
        f = Frame(image, duration)
        self._frames.insert(index, f)
    
    def insert_recording(self, other):
        if isinstance(other, FrameRecording):
            new = copy.deepcopy(self)
        raise TypeError
    
    def pop(self, index):
        if index < len(self.frames):
            return self._frames.pop(index)
    
    
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



class AudioRecording(object):
    """
    An audio recording. Times are represented in seconds.
    """
    def __init__(self):
        self.mtime = 0
        self.duration = 0
    
    def __repr__(self):
        return '<AudioRecording | {0.duration} sec>'.format(self) 

class VideoRecording(object):
    pass


class RecordingCollection(object):
    """
    RecordingCollection keeps track of a FrameRecording and AudioRecording pair.
    The main Story Time model creates a list of recording collections to
    associate frame timings with audio recordings.
    """
    def __init__(self, frames=None, audio=None):
        self.frames = frames if frames is not None else FrameRecording()
        self.audio = audio if audio is not None else AudioRecording()
        # self.video = video if video is not None else VideoRecording()
    
    def __repr__(self):
        return '<RecordingCollection {0!r} {1!r}>'.format(self.frames, self.audio)


class ImageCollection(object):
    """
    A collection of images to be sample from during a Story Time recording.
    An image collection can be seeded with a directory or combination of images.
    It can then be sorted and organized for better usability.
    
    Image collections also provide a seeking interface to keep track of which
    image was last sampled and making it easy to get the previous/next frame.
    Collection seeking will loop both ways.
    """
    def __init__(self, images=None, imageTypes=DEFAULT_IMAGE_TYPES):
        self.imageTypes = imageTypes
        self._seek = 0
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
        return '<ImageCollection {0} image(s) | @{1.seek}>'.format(len(self.images), self)
    
    def getImages(self):
        return self._images
    def setImages(self, value):
        self._images = []
        if isinstance(value, (tuple, list)):
            for i in value:
                if isinstance(i, (str, unicode)):
                    self._images.append(os.path.normpath(i))
        elif isinstance(value, (str, unicode)):
            self._images.append(os.path.normpath(value))
    images = property(getImages, setImages)
    
    def getSeek(self):
        if self._seek < 0 or self._seek >= len(self.images):
            # this desync is handled by clamping
            self._seek = max(min(self._seek, len(self.images)-1), 0)
        return self._seek
    def setSeek(self, value):
        if not isinstance(value, int):
            raise TypeError
        if len(self._images) == 0:
            self._seek = 0
        else:
            self._seek = value % len(self._images)
    seek = property(getSeek, setSeek)
    
    def is_valid_image(self, image):
        types = [x.strip('.') for x in self.imageTypes]
        ext = os.path.splitext(image)[1].strip('.')
        return ext in types
    
    def clear(self):
        self._images = []
    
    def append(self, image):
        """
        Append the given image or images to the collection.
        This is like a combined append/extend functionality.
        """
        if isinstance(image, (str, unicode)):
            self._images.append(os.path.normpath(image))
        elif isinstance(image, (list, tuple)):
            self._images.extend([os.path.normpath(i) for i in image])
    
    def extend(self, images):
        self.append(images)
    
    def load_dir(self, dir_):
        if not os.path.isdir(dir_):
            raise OSError('directory does not exist: {0}'.format(dir_))
        files = os.listdir(dir_)
        self.images = [i for i in files if self.is_valid_image(i)]
        self.sort()
    
    def load_sequence(self, image):
        """ Load the image sequence associated with the given image """
        LOG.warning('load_sequence not yet implemented')
        self._images = image
    
    def sort(self, *args, **kwargs):
        self._images.sort(*args, **kwargs)
    
    def current(self):
        return self[self.seek]
    
    def prev(self):
        self.seek -= 1
        return self[self.seek]
    
    def next(self):
        self.seek += 1
        return self[self.seek]


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


