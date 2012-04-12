"""
model.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from data import *
from PySide.QtCore import *
from PySide.QtGui import *
import audio, utils, fcpxml
import logging
import math
import os
import tempfile
import shutil
import pdb
import subprocess
import sys
import pickle

__all__ = [
    'MappingModel',
    'ImageCollectionModel',
    'RecorderModel',
    'RecordingModel',
]

LOG = logging.getLogger(__name__)

FFMPEG = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'


class PixmapCache(object):
    def __init__(self):
        self.maxCount = 150
        self.clear()

    def __getitem__(self, name):
        return self._data[self.normKey(name)]

    def __setitem__(self, name, value):
        key = self.normKey(name)
        if key not in self._list:
            self._list.append(key)
        self._data[key] = value
        self.checkCount()

    def __delitem__(self, name):
        key = self.normKey(name)
        del self._data[key]
        self._list.remove(key)

    @property
    def count(self):
        return len(self._list)

    def checkCount(self):
        """Check the current cache count and removed images if necessary"""
        while self.count > max(0, self.maxCount):
            self.pop()

    def clear(self):
        self._list = []
        self._data = {}

    def pop(self):
        if self.count > 0:
            del self[self._list[0]]

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def has_key(self, key):
        return self._data.has_key(self.normKey(key))

    def add(self, path):
        self.getPixmap(path)

    def getPixmap(self, path):
        if not isinstance(path, (str, unicode)):
            return QPixmap()
        if os.path.isfile(path):
            if self.has_key(path):
                # pixmap already loaded
                return self[path]
            else:
                # load the pixmap
                pixmap = QPixmap(path)
                self[path] = pixmap
                return pixmap
        return QPixmap()

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


class MappingModel(QAbstractItemModel):
    """
    The MappingModel is designed for a model that uses
    a `maps` attribute to provide an enum of available properties.
    """
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(MappingModel, cls).__new__(cls, *args, **kwargs)
        else:
            def init_pass(self, *args, **kwargs): pass
            cls.__init__ = init_pass
        return cls._inst
    
    def __init__(self, parent=None):
        super(MappingModel, self).__init__(parent)
        self.maps = utils.enum()
    
    def __getitem__(self, key):
        if key in self.maps.names:
            return getattr(self, key)
    
    def __setitem__(self, key, value):
        if key in self.maps.names:
            try:
                setattr(self, key, value)
            except:
                print('cant set {0}'.format(key))
    
    def has_key(self, key):
        return key in self.maps.names
    
    def allMappingsChanged(self, row=0):
        for i in range(len(self.maps.names)):
            index = self.index(row, i)
            self.dataChanged.emit(index, index)
    
    def mappingChanged(self, mapping, row=0):
        allMappings = self.influencedMappings(mapping)
        for m in allMappings:
            index = self.index(row, m)
            self.dataChanged.emit(index, index)
    
    def influencedMappings(self, mapping):
        return [mapping]
    
    def dataForMapping(self, mapping, role=Qt.DisplayRole, row=0):
        index = self.index(row, mapping)
        return self.data(index, role)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return
        
        key = self.maps.names[index.column()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            if self.has_key(key):
                return self[key]
    
    def setDataForMapping(self, mapping, value, role=Qt.EditRole, row=0):
        index = self.index(row, mapping)
        self.setData(index, value, role)
    
    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        
        key = self.maps.names[index.column()]
        if role in (Qt.EditRole, ):
            if self.has_key(key):
                self[key] = value
                self.mappingChanged(index.column())
                return True
        
        return False
    
    def rowCount(self, parent):
        return 1
    
    def columnCount(self, parent):
        return 1
    
    def index(self, row=0, column=0, parent=None):
        return self.createIndex(row, column)
    
    def parent(self, index):
        return QModelIndex()


class ImageCollectionModel(MappingModel):
    """
    The ImageCollectionModel is a singular (non-list) model that provides
    access to images through the ImageCollection class. Despite the fact
    that ImageCollection's hold a list of images, this model is designed
    to represent one 'current' image and the images immediately next to it
    in an ordered list.
    """
    def __init__(self, parent=None):
        super(ImageCollectionModel, self).__init__(parent)
        self.maps = utils.enum(
            'count', 'imageIndex', 'images',
            'curImage', 'prevImage', 'nextImage',
            'curImagePath', 'prevImagePath', 'nextImagePath',
        )
        
        # current image collection
        self.imageCollection = ImageCollection()
        # the pixmap cache for efficiency
        self.pixmapCache = PixmapCache()
        LOG.debug('ImageCollectionModel initialized')
    
    def __repr__(self):
        return '<ImageCollectionModel | {0} image(s)>'.format(len(self.imageCollection))
    
    @property
    def count(self):
        return len(self.imageCollection)
    
    @property
    def imageIndex(self):
        return self.imageCollection.index
    @imageIndex.setter
    def imageIndex(self, value):
        self.imageCollection.index = value
        self.pixmapCache.add(self.nextImage)
    
    @property
    def images(self):
        return self.imageCollection.images
    @images.setter
    def images(self, value):
        self.imageCollection.images = value

    @property
    def curImage(self):
        return self.pixmapCache.getPixmap(self.curImagePath)

    @property
    def prevImage(self):
        return self.pixmapCache.getPixmap(self.prevImagePath)

    @property
    def nextImage(self):
        return self.pixmapCache.getPixmap(self.nextImagePath)
    
    @property
    def curImagePath(self):
        return self.imageCollection.current()
    @curImagePath.setter
    def curImagePath(self, value):
        self.imageCollection.seekToImage(value)
    
    @property
    def prevImagePath(self):
        return self.imageCollection.prev(seek=False)
    
    @property
    def nextImagePath(self):
        return self.imageCollection.next(seek=False)
    
    def cacheAllImages(self):
        # cache the images
        LOG.debug('Caching images...')
        self.pixmapCache.cache(self.images)
    
    def clearCache(self):
        LOG.debug('Clearing cache {0}'.format(self.pixmapCache.count))
        self.pixmapCache.clear()
    
    def clearImages(self):
        self.images = []
        self.pixmapCache.clear()
        self.allMappingsChanged()
    
    def loadPaths(self, paths):
        """
        Process and load images corresponding to the given paths.
        
        Directory: import all images in directory
        Single file: import the image's directory (TODO: load sequence)
        Multiple files: add files exactly
        """
        if len(paths) == 1:
            path = paths[0]
            if os.path.isdir(path):
                self.imageCollection.loadDir(path)
            else:
                self.imageCollection.loadDir(os.path.dirname(path))
        elif len(paths) > 1:
            self.imageCollection.images = paths
            self.imageCollection.sort()
        # emit signals
        self.allMappingsChanged()
    
    def influencedMappings(self, mapping):
        if mapping == self.maps.imageIndex:
            return [
                self.maps.curImage,
                self.maps.prevImage,
                self.maps.nextImage,
                self.maps.curImagePath,
                self.maps.prevImagePath,
                self.maps.nextImagePath,
            ]
        return [mapping]



class RecorderModel(MappingModel):
    """
    The RecorderModel is a singular (non-list) model that contains
    information useful for a functioning timeline. This includes
    the current time, framerate, and information like the current
    state of playback for the timeline.
    
    The RecorderModel holds a Recording on which it operates, and
    also needs a reference to an ImageCollectionModel from which it
    pulls frames while recording.  It also can then set data on
    the ImageCollectionModel such as the current frame by reading
    information from the Recording that it has.
    """
    def __init__(self, imgmodel, recmodel, parent=None):
        super(RecorderModel, self).__init__(parent)
        self.maps = utils.enum(
            'time', 'frame', 'timelineDuration',
            'isRecording', 'isPlaying',
            'audioEnabled', 'videoEnabled',
            # recording properties
            *Recording.attrs
        )
        
        self.imageModel = imgmodel
        self.recordingModel = recmodel
        
        self._time = 0
        self._isRecording = False
        self._isPlaying = False
        self._audioEnabled = True
        self._videoEnabled = True
        self._recording = self.recordingModel.recordings[0]
        
        # used to keep track of playback time
        self._playTimer = QElapsedTimer()
        self._updateTimer = QTimer()
        self._updateTimer.timerEvent = self.updateTime
        LOG.debug('RecorderModel Initialized')
    
    def __repr__(self):
        return '<RecorderModel | {0.time}>'.format(self)
    
    def __getitem__(self, key):
        # retrieves recording attrs from the recording,
        # and everything else from this model
        if key in self.maps.names:
            if key in Recording.attrs:
                if self._recording is not None:
                    return self._recording[key]
            else:
                return getattr(self, key)
    
    @property
    def time(self):
        return self._time
    @time.setter
    def time(self, value):
        self._time = value
        # if not recording, update image collection
        if not self.isRecording:
            if self.isPlaying and self.frame >= self.recording.duration:
                self.stop() # or loop
            self.imageModel.imagePath = self.imagePathAtTime(value)
    
    @property
    def frame(self):
        if self.recording is None:
            return 0
        return self.time * self.recording.fps
    @frame.setter
    def frame(self, value):
        if self.recording is not None:
            self.time = int(float(value) / self.recording.fps)
    
    @property
    def timelineDuration(self):
        if self.isRecording:
            # return the current time ceilinged to the nearest half minute
            minuteFrames = self.recording.fps * 30
            minutes = math.floor(float(self.frame) / minuteFrames) + 2
            return int(minutes * minuteFrames)
        elif self.recording is not None:
            return self.recording.duration
    
    @property
    def isRecording(self):
        return self._isRecording
    
    @property
    def isPlaying(self):
        return self._isPlaying
    
    @property
    def audioEnabled(self):
        return self._audioEnabled
    @audioEnabled.setter
    def audioEnabled(self, value):
        if isinstance(value, bool):
            # check to see if we are able to enable
            self._audioEnabled = False
            if len(audio.inputDevices()) > 0:
                self._audioEnabled = value
    
    @property
    def videoEnabled(self):
        return self._videoEnabled
    @videoEnabled.setter
    def videoEnabled(self, value):
        self._videoEnabled = value
    
    
    @property
    def recording(self):
        return self._recording
    
    @property
    def timerInterval(self):
        if self.recording is not None:
            return (1.0 / self.recording.fps) * 1000
    
    def record(self):
        pass
    
    def play(self):
        pass
    
    def recordingChanged(self):
        """
        Called when the current recording of the recorder model gets changed.
        Will play the new recording from the beginning.
        """
        if self.isPlaying and not self.isRecording:
            self.play()
    
    def imagePathAtTime(self, time):
        """
        Get the image path for the given recorder time from the current recording.
        """
        if self.recording is not None:
            frametime = int(float(time) / self.recording.fps)
            return self.recording.framerec.getFrame(frametime)
    
    def recordCurrentFrame(self):
        imagePath = self.imageModel.curImagePath
        self.recordFrame(imagePath)
    
    def recordFrame(self, imagePath):
        """ Record the given image onto the current Recording """
        framerec = self.recording.framerec
        frameIndex = framerec.getIndex(self.time)
        if frameIndex is None:
            # the first frame
            frameIndex = 0
        else:
            # insert after current frame
            frameIndex += 1
        # get out time of the previous frame
        outTime = framerec.outTime(frameIndex - 1)
        duration = self.time - outTime
        if duration == 0:
            LOG.warning('skipping frame recording, duration is 0: {0}. outTime {1} curTime {2}'.format(image, outTime, self.time))
            return
        LOG.debug('frameIndex: {3}, {1:>4} - {2:<4}: {0}'.format(os.path.basename(imagePath), outTime, outTime + duration, frameIndex))
        framerec.insert(frameIndex, imagePath, duration)
    
    
    def updateTime(self, event=None):
        if self.isPlaying or self.isRecording:
            time = self._playTimer.elapsed() * 0.001
            self.setDataForMapping(self.maps.time, time)



class RecordingModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(RecordingModel, self).__init__(parent)
        self.maps = utils.enum(*Recording.attrs)
        self.recordings = []
        self.newRecording()
        LOG.debug('RecordingModel initialized')

    def __repr__(self):
        return '<RecordingModel | {0} recording(s)>'.format(self.rowCount())
    
    def getNewRecordingName(self, num=None):
        if num is None:
            num = self.rowCount() + 1
            return 'Story Time Recording {0:03}'.format(num)
    
    def toXml(self, index, platform=None):
        """
        Export the current recording collection to an editorial xml file.

        `platform` -- the target platform for which we are exporting.
            this is where path mapping will be taken into account.

        """
        raise NotImplementedError
        recording = self.recordings[index.row()]
        frameImages = [f.image for f in recording.frames.frames]
        frameDurations = [f.duration for f in recording.frames.frames]
        if platform is None:
            platform = sys.platform

        if len(recording) > 0:
            fcpkw = {
                'name':recording.name,
                'images':zip(frameImages, frameDurations),
                'audioPath':recording.audio.filename,
                'fps':recording.fps,
                'ntsc':(recording.fps % 30 == 0),
                'platform':platform,
            }
            return fcpxml.FcpXml(**fcpkw).toString()

    def exportRecording(self, filename, index, platform='win'):
        raise NotImplementedError
        xml = self.toXml(platform, index)
        with open(filename, 'wb') as fp:
            fp.write(xml)
        LOG.info('Exported recording: {0}'.format(filename))

    def openRecording(self, filename=None):    
        raise NotImplementedError
        if not os.path.isfile(filename):
            LOG.warning('cannot open file, does not exist: {0}'.format(filename))
            return
        with open(filename, 'rb') as fp:
            data = pickle.load(fp)
        recording = Recording.fromDict(data)
        self.addRecording(recording)

        # attempt to load audio
        audioFile = os.path.splitext(filename)[0] + '.wav'
        if os.path.isfile(audioFile):
            recording.audio.load(audioFile)

        LOG.info('Loaded recording: {0}'.format(filename))
        # TODO: figure out a better way to encapsulate this functionality
        allImages = sorted(list(set(self.images + recording.frames.images)))
        self.images = allImages

    def saveRecording(self, index, filename=None):    
        raise NotImplementedError
        # force extension
        filename = '{0}.xml'.format(os.path.splitext(filename)[0])
        # if filename is none should try to use lastSavedFilename for the current recording collection
        with open(filename, 'wb') as fp:
            pickle.dump(self.recordings[index.row()].toString(), fp)
        LOG.debug('Saved recording to {0}'.format(filename))


    def exportMovie(self, filename, index, progress=None):       
        raise NotImplementedError     
        recording = self.recordings[index.row()]

        if recording.duration == 0:
            LOG.debug('cannot export recording of duration 0')
            return

        img_fmt = self.exportFrameRecordingSequence(recording.frames, progress)
        if img_fmt is None:
            return

        args = [
            FFMPEG,
            '-y',
            '-f', 'image2',
            '-i', img_fmt,
        ]
        if recording.audio.hasRecording:
            args += [
                '-i', recording.audio.filename,
                '-acodec', 'libvo_aacenc',
                '-ab', '256k',
            ]
        args += [
            '-r', recording.fps,
            '-vcodec', 'libx264',
            '-cqp', '31',
            '-g', '12',
            '-t', float(recording.duration) / recording.fps,
            filename,
        ]
        args = [str(a) for a in args]
        LOG.debug('ffmpeg command:\n {0}'.format(' '.join(args)))
        subprocess.Popen(args)

    def exportFrameRecordingSequence(self, recording, progress=None):
        """
        Save the given frame recording out to an
        image sequence and return the sequence format
        """
        raise NotImplementedError
        # get temporary directory
        dir_ = os.path.join(tempfile.gettempdir(), 'storyTimeMovieExport')
        if not os.path.isdir(dir_):
            os.makedirs(dir_)
        LOG.debug('copying images to temp directory for video export: {0}'.format(dir_))

        # create img naming format
        frames = recording.frames
        ext = os.path.splitext(frames[0].image)[-1]
        imgFmt = os.path.join(dir_, 'storyTimeExport.%06d{0}'.format(ext))

        # progress bar prep
        if progress is not None:
            progress.setLabelText('Exporting image sequence to be encoded...')
            progress.setMaximum(recording.duration)

        for i, image in enumerate([f.image for f in frames for d in range(f.duration)]):
            shutil.copyfile(image, imgFmt % i)
            if progress is not None:
                progress.setValue(i)
                if progress.wasCanceled():
                    return

        if progress is not None:
            progress.setValue(recording.duration)

        return imgFmt
    
    def newRecording(self):
        new = self.addRecording()
        new.name = self.getNewRecordingName()
        #new.audio.inputDeviceIndex = defaultAudioInputDeviceIndex
        #new.audio.outputDeviceIndex = defaultAudioOutputDeviceIndex
    
    def addRecording(self):
        self.insertRows(self.rowCount(), 1)
        return self.recordings[-1]
    
    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self.recordings.insert(position, Recording())
        self.endInsertRows()
        return True
    
    def removeRows(self, position, rows, parent=QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            self.recordings.pop(position)
        self.endRemoveRows()
        return True
    
    def rowCount(self, parent=None):
        return len(self.recordings)
    
    def columnCount(self, parent=None):
        return 3
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return
        
        if role in (Qt.DisplayRole, Qt.EditRole):
            rec = self.recordings[index.row()]
            attr = self.maps.names[index.column()]
            if rec.has_key(attr):
                return rec[attr]
    
    def setData(self, index, value, role=Qt.EditRole):
        return False
    
    def index(self, row, column, parent=None):
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()


