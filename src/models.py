"""
model.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from data import *
from utils import enum, get_timecode
from PySide.QtCore import *
from PySide.QtGui import *
import audio
import logging
import math
import os

LOG = logging.getLogger('storyTime.models')

# TODO: cluster mappings that affect each other or create event pool presets
Mappings = enum(
    'isRecording', 'isPlaying', 'fps', 'curTime', 'timeDisplay', 'isTimeDisplayFrames', 'recordAudio', 'audioInputDeviceIndex', 'audioOutputDeviceIndex',
    'imageCount', 'curImageIndex', 'curImageIndexLabel', 'curImagePath', 'curImage', 'prevImage', 'nextImage',
    'recordingIndex', 'recordingName', 'recordingFps', 'recordingDuration', 'recordingDurationDisplay', 'recordingImageCount',
    'end',
)


class PixmapCache(object):
    def __init__(self):
        self.clear()
    
    def __getitem__(self, name):
        return self._data[self.normKey(name)]
    
    def __setitem__(self, name, value):
        self._data[self.normKey(name)] = value
    
    def __delitem__(self, name):
        del self._data[self.normKey(name)]
    
    def clear(self):
        self._data = {}
    
    def items(self):
        return self._data.items()
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def has_key(self, key):
        return self._data.has_key(self.normKey(key))
    
    def getPixmap(self, path):
        if not isinstance(path, (str, unicode)):
            return
        if os.path.isfile(path):
            if self.has_key(path):
                # pixmap already loaded
                return self[path]
            else:
                # load the pixmap
                pixmap = QPixmap(path)
                self[path] = pixmap
                return pixmap
        return None
    
    def normKey(self, path):
        return os.path.normpath(path).lower()
    
    def cache(self, paths, keepOld=False):
        normpaths = [self.normKey(p) for p in paths]
        removed = 0
        # remove unneded paths
        for k in self.keys():
            if k not in normpaths:
                del self[k]
                removed += 1
        # cache the rest
        added = 0
        for p in paths:
            if not self.has_key(p):
                self.getPixmap(p)
                added += 1
        LOG.debug('Updated pixmap cache. {0} removed, {1} added'.format(removed, added))



class StoryTimeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(StoryTimeModel, self).__init__(parent)
        
        # Recording / Playback
        self.isRecording = False
        self.isPlaying = False
        self._fpsOptions = FPS_OPTIONS
        self.customFps = 12
        # current display mode of the time (time code vs frames)
        self.isTimeDisplayFrames = False
        # current time of the playback timeline in frames
        self.curTime = 0
        # whether to record audio for the current recording or not
        self.recordAudio = True
        self.audioInputDeviceIndex = audio.defaultInputDeviceIndex()
        self.audioOutputDeviceIndex = audio.defaultOutputDeviceIndex()
        
        
        # all recording collections
        self.recordings = []
        # currently loaded/active recording collection index
        self.recordingIndex = 0
        # current image collection
        self.imageCollection = ImageCollection()
        # the pixmap cache for efficiency
        self.pixmapCache = PixmapCache()
        
        self.newRecording()
        LOG.debug('Model Initialized')
    
    def __repr__(self):
        return '<StoryTimeModel | {0.recordingCount} recording(s)>'.format(self)
    
    @property
    def fpsList(self):
        return sorted(self._fpsOptions.keys()) + [self.customFps]
    
    @property
    def fpsOptions(self):
        opts = self._fpsOptions.copy()
        opts.update( {self.customFps:self.fpsLabel(self.customFps)} )
        return opts
    
    def fpsLabel(self, fps):
        if fps in self._fpsOptions.keys():
            return self._fpsOptions[key]
        else:
            return 'Custom ({0} fps)'.format(fps)
    
    @property
    def timeDisplay(self):
        if self.isTimeDisplayFrames:
            return '{0}'.format(self.curTime)
        else:
            return get_timecode(self.curTime, self.recordingFps)
    
    def toggleTimeDisplay(self):
        self.isTimeDisplayFrames = not self.isTimeDisplayFrames
        self.mappingChanged(Mappings.isTimeDisplayFrames)
        self.mappingChanged(Mappings.timeDisplay)
    
    def secondsToFrames(self, seconds, fps=None):
        if fps is None:
            fps = self.recordingFps
        return int(seconds * fps)
    
    
    
    # Recording Properties
    
    @property
    def recordingCount(self):
        return len(self.recordings)
    
    @property
    def curRecording(self):
        return self.recordings[self.recordingIndex]
    
    @property
    def curFrameRecording(self):
        return self.curRecording.frames
    
    @property
    def curAudioRecording(self):
        return self.curRecording.audio
    
    def getAudioPath(self, name):
        return os.path.join(os.path.expanduser('~'), name)
    
    @property
    def recordingFps(self):
        return self.curFrameRecording.fps
    
    @property
    def recordingName(self):
        return self.curRecording.name
    
    @property
    def recordingDuration(self):
        if self.isRecording:
            # return the current time ceilinged to the nearest half minute
            minuteFrames = self.recordingFps * 30
            minutes = math.floor(float(self.curTime) / minuteFrames) + 2
            return int(minutes * minuteFrames)
        else:
            ad = self.secondsToFrames(self.curAudioRecording.duration)
            fd = self.curFrameRecording.duration
            #vduration = self.curVideoRecording.duration
            return max(ad, fd)
        
    
    @property
    def recordingDurationDisplay(self):
        return get_timecode(self.recordingDuration, self.recordingFps)
    
    @property
    def recordingImageCount(self):
        return len(self.curFrameRecording)
    
    def loadRecording(self, index):
        if index < 0 or index >= self.recordingCount:
            raise IndexError
        self.recordingIndex = index
        self.curTime = 0
        self.recordingDataChanged()
        self.imageDataChanged()
        self.mappingChanged(Mappings.curTime)
        self.mappingChanged(Mappings.timeDisplay)
    
    def newRecording(self):
        new = RecordingCollection()
        new.name = 'Recording {0}'.format(self.recordingCount + 1)
        new.audio.inputDeviceIndex = self.audioInputDeviceIndex
        new.audio.outputDeviceIndex = self.audioOutputDeviceIndex
        self.recordings.append(new)
        self.loadRecording(self.recordingCount - 1)
    
    def deleteRecording(self, index):
        # TODO: make sure we always have atleast one recording
        pass
    
    def recordCurrentFrame(self):
        self.recordFrame(self.curImageIndex)
    
    def recordFrame(self, index):
        """ Record the image at the given index for the current time """
        if index < 0 or index > len(self.images):
            return
        recordingIndex = self.curFrameRecording.getIndex(self.curTime)
        if recordingIndex is None:
            # the first frame
            recordingIndex = 0
        else:
            # insert after current frame
            recordingIndex += 1
        # get out time of the previous frame
        outTime = self.curFrameRecording.outTime(recordingIndex - 1)
        image = self.images[index]
        duration = self.curTime - outTime
        LOG.debug('{1:>4} - {2:<4}: {0}'.format(os.path.basename(image), outTime, outTime + duration))
        # if duration is 0, check and replace the frame at recordingIndex
        self.curFrameRecording.insert(recordingIndex, image, duration)
    
    
    # image collection methods
    
    def loadPaths(self, paths):
        """
        Process and load images corresponding to the given paths.
        Possible options:
        
        Single file: xml - open, all else - import directory
        Directory: import directory
        Multiple files: add files exactly
        """
        if len(paths) > 1:
            self.imageCollection.images = sorted(paths)
        else:
            path = paths[0]
            ext = os.path.splitext(path)[1]
            if ext == '.xml':
                # TODO: load the xml
                pass
            elif os.path.isdir(path):
                self.imageCollection.loadDir(path)
            else:
                # TODO: replace this with loading the image sequence
                self.imageCollection.loadDir(os.path.dirname(path))
        # emit signals
        self.imageDataChanged()
    
    def cacheAllImages(self):
        # cache the images
        LOG.debug('Caching images...')
        self.pixmapCache.cache(self.images)
    
    @property
    def imageCount(self):
        return len(self.images)
    
    @property
    def imagePadding(self):
        return len(str(self.imageCount))
    
    @property
    def images(self):
        return self.imageCollection.images
    
    @property
    def curImageIndex(self):
        return self.imageCollection.seek
    
    @property
    def curImageIndexLabel(self):
        return '{1:0{0.imagePadding}}/{0.imageCount}'.format(self, self.curImageIndex + 1)
    
    @property
    def curImagePath(self):
        return self.imageCollection.current()
    
    @property
    def curImage(self):
        return self.pixmapCache.getPixmap(self.curImagePath)
    
    @property
    def prevImage(self):
        return self.pixmapCache.getPixmap(self.imageCollection.prev(seek=False))
    
    @property
    def nextImage(self):
        return self.pixmapCache.getPixmap(self.imageCollection.next(seek=False))
    
    def loadImageAtTime(self, time):
        frame = self.curFrameRecording.getFrame(time)
        if frame is not None:
            self.imageCollection.seekToImage(frame.image)
            self.imageDataChanged()
            self.recordingDataChanged()
    
    def loadImage(self, index):
        self.imageCollection.seek = index
        self.imageDataChanged()
        self.recordingDataChanged()
    
    
    # qt model methods
    
    def rowCount(self, parent):
        return 1
    
    def columnCount(self, parent):
        return 1
    
    def data(self, index, role):
        #LOG.debug('mapping={0} role={1}'.format(Mappings.names[index.column()], role))
        if not index.isValid():
            return
        # we don't care about rows since our model
        # is essentially singular. the column is our mapping
        m = index.column()
        # return the current data for the corresponding mapping
        if hasattr(self, Mappings.names[m]):
            return getattr(self, Mappings.names[m])
    
    
    def setData(self, index, value, role = Qt.EditRole):
        """
        Receive and apply data input from the view/controllers. The model is updated
        appropriately based on what data is changed and to what values.
        """
        
        m = index.column()
        
        # stop if the value is not different
        if hasattr(self, Mappings.names[m]):
            # loose equality
            if str(getattr(self, Mappings.names[m])) == str(value):
                return False
        
        if m not in [Mappings.curTime]:
            LOG.debug('{0:>25} = {1!r} -> {2!r}'.format(Mappings.names[index.column()], getattr(self, Mappings.names[m]), value))
        
        if m == Mappings.curImageIndex:
            # only updates if the new index is different
            if self.isRecording:
                self.recordCurrentFrame()
            self.loadImage(value)
            return True
            
        elif m == Mappings.curTime:
            self.curTime = value
            if not self.isRecording:
                self.loadImageAtTime(value)
            self.timeDataChanged()
            return True
            
        elif m == Mappings.recordAudio:
            self.recordAudio = value
            self.mappingChanged(m)
        
        elif m == Mappings.audioInputDeviceIndex:
            self.audioInputDeviceIndex = value
            self.curAudioRecording.inputDeviceIndex = self.audioInputDeviceIndex
            self.mappingChanged(m)
        
        elif m == Mappings.isRecording:
            self.isRecording = value
            if not self.isRecording:
                # recording has just stopped. record the last frame
                self.recordCurrentFrame()
                if self.recordAudio:
                    self.curAudioRecording.stop()
                    self.curAudioRecording.save(self.getAudioPath(self.curRecording.name))
            else:
                if len(self.curFrameRecording) != 0:
                    # start a new recording cause this ones already been used
                    self.newRecording()
                if self.recordAudio:
                    self.curAudioRecording.record()
            self.recordingDataChanged()
            return True
        
        elif m == Mappings.isPlaying:
            self.isPlaying = value
            if self.isPlaying:
                if self.recordAudio and self.curAudioRecording.hasRecording:
                    self.curAudioRecording.stop()
                    self.curAudioRecording.play()
            else:
                self.curAudioRecording.stop()
            
        elif m == Mappings.recordingIndex:
            if self.recordAudio and self.isPlaying:
                self.curAudioRecording.stop()
            self.recordingIndex = max(min(value, self.recordingCount - 1), 0)
            if self.recordAudio and self.isPlaying:
                self.curAudioRecording.play()
            self.recordingDataChanged()
            return True
            
        elif m == Mappings.recordingName:
            # move the current audio file, if one exists
            if self.curAudioRecording.hasRecording:
                if os.path.isfile(self.curAudioRecording.filename):
                    os.remove(self.curAudioRecording.filename)
                self.curAudioRecording.save(self.getAudioPath(value))
            self.curRecording.name = value
            self.mappingChanged(Mappings.recordingName)
            return True
            
        
        return False
    
    def mappingChanged(self, mapping):
        self.dataChanged.emit(self.mappingIndex(mapping), self.mappingIndex(mapping))
    
    def imageDataChanged(self):
        self.mappingChanged(Mappings.imageCount)
        self.mappingChanged(Mappings.curImageIndex)
        self.mappingChanged(Mappings.curImageIndexLabel)
        self.mappingChanged(Mappings.curImagePath)
        self.mappingChanged(Mappings.curImage)
        self.mappingChanged(Mappings.prevImage)
        self.mappingChanged(Mappings.nextImage)
    
    def recordingDataChanged(self):
        self.mappingChanged(Mappings.recordingIndex)
        self.mappingChanged(Mappings.recordingName)
        self.mappingChanged(Mappings.recordingFps)
        self.mappingChanged(Mappings.recordingDuration)
        self.mappingChanged(Mappings.recordingDurationDisplay)
        self.mappingChanged(Mappings.recordingImageCount)
    
    def timeDataChanged(self):
        self.mappingChanged(Mappings.curTime)
        self.mappingChanged(Mappings.timeDisplay)
    
    def index(self, row=0, column=0, parent=None):
        return self.createIndex(row, column)
    
    def mappingIndex(self, mapping):
        return self.index(0, mapping)
    
    def parent(self, index):
        """ There is only one viable index, and therefore no feasible parent """
        return QModelIndex()


