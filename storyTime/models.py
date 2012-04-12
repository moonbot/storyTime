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

LOG = logging.getLogger(__name__)

FFMPEG = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'


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
        self.maps = enum()
    
    def __getitem__(self, key):
        if key in self.maps.names:
            return getattr(self, key)
    
    def __setitem__(self, key, value):
        if key in self.maps.names:
            setattr(self, key, value)
    
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
            return
        
        key = self.maps.names[index.column()]
        if role in (Qt.EditRole, ):
            if self.has_key(key):
                self[key] = value
    
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
    
    @property
    def prevImagePath(self):
        return self.imageCollection.prev(seek=False)
    
    @property
    def nextImagePath(self):
        return self.imageCollection.next(seek=False)
    
    def clearImages(self):
        self.images = []
        self.pixmapCache.clear()
        self.allMappingsChanged()



class RecorderModel(MappingModel):
    """
    The RecorderModel is a singular (non-list) model that contains
    information useful for a functioning timeline. This includes
    the current time, framerate, and information like the current
    state of playback for the timeline.
    
    The RecorderModel holds a Recording on which it operates.
    """
    def __init__(self, parent=None):
        super(StoryTimeModel, self).__init__(parent)
        self.maps = utils.enum(
            'time', 'fps', 'frame', 'duration',
            'isRecording', 'isPlaying',
            'audioEnabled', 'videoEnabled',
        )
        
        self._recording = None
        self.time = 0
        self.fps = 24
        self._isRecording = False
        self._isPlaying = False
        self._audioEnabled = True
        self._videoEnabled = True
        LOG.debug('RecorderModel Initialized')
    
    def __repr__(self):
        return '<RecorderModel | {0.time}>'.format(self)
    
    @property
    def frame(self):
        return self.time * self.fps
    @frame.setter
    def frame(self, value):
        self.time = float(value) / self.fps
    
    @property
    def duration(self):
        if self.isRecording:
            # return the current time ceilinged to the nearest half minute
            minuteFrames = self.fps * 30
            minutes = math.floor(float(self.time) / minuteFrames) + 2
            return int(minutes * minuteFrames)
        elif self._recording is not None:
            return self._recording.duration
    
    @property
    def isRecording(self):
        return self._isRecording
    @isRecording.setter
    def isRecording(self, value):
        self._isRecording = value
    
    @property
    def isPlaying(self):
        return self._isPlaying
    @isPlaying.setter
    def isPlaying(self, value):
        self._isPlaying = value
    
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
    
    
    
    
    def deleteRecording(self, index):
        # TODO: replace with removeRows
        # TODO: make sure we always have atleast one recording
        pass
    
    def recordCurrentFrame(self, index):
        self.recordFrame(index, self.curImageIndex)
    
    def recordFrame(self, index, imageIndex):
        """ Record the image at the given index for the current time """
        if imageIndex not in range(len(self.images)):
            return
        recording = self.recordings[index.row()]
        frameIndex = recording.frames.getIndex(self.curTime)
        if frameIndex is None:
            # the first frame
            frameIndex = 0
        else:
            # insert after current frame
            frameIndex += 1
        # get out time of the previous frame
        outTime = recording.frames.outTime(frameIndex - 1)
        image = self.images[imageIndex]
        duration = self.curTime - outTime
        if duration == 0:
            LOG.warning('skipping frame recording, duration is 0: {0}. outTime {1} curTime {2}'.format(image, outTime, self.curTime))
            return
        LOG.debug('frameIndex: {3}, {1:>4} - {2:<4}: {0}'.format(os.path.basename(image), outTime, outTime + duration, frameIndex))
        recording.frames.insert(frameIndex, image, duration)
    
    
    # image collection methods
    
    def loadPaths(self, paths):
        """
        Process and load images/recordings corresponding to the given paths.
        
        directories / images - load image(s)
            Directory: import directory
            Single file: import image's directory (TODO: load sequence)
            Multiple files: add files exactly
        .xml - load recording(s)
        
        """
        xmls = [p for p in paths if os.path.splitext(p)[-1] in ['.xml']]
        images = [p for p in paths if p not in xmls]
        # handle images first
        if len(images) == 1:
            image = images[0]
            if os.path.isdir(image):
                self.imageCollection.loadDir(image)
            else:
                self.imageCollection.loadDir(os.path.dirname(image))
        elif len(images) > 1:
            self.imageCollection.images = sorted(images)
        # emit signals
        self.imageDataChanged()
        
        # handle recordings
        for xml in xmls:
            self.openRecording(xml)
    
    
    def updateRecordingName(self, index):
        recording = self.recordings[index.row()]
        if recording.name.startswith('Story Time Recording'):
            try:
                index = int(recording.name.split(' ')[-1])
            except:
                return
            # update the recording's name to match
            recording.name = self.getNewRecordingName(index)
            self.mappingChanged(index, Mappings.recordingName)
    
    def cacheAllImages(self):
        # cache the images
        LOG.debug('Caching images...')
        self.pixmapCache.cache(self.images)
    
    def clearCache(self):
        LOG.debug('Clearing cache {0}'.format(self.pixmapCache.count))
        self.pixmapCache.clear()
    
    def toXml(self, index, platform=None):
        """
        Export the current recording collection to an editorial xml file.
        
        `platform` -- the target platform for which we are exporting.
            this is where path mapping will be taken into account.
        
        """
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
        xml = self.toXml(platform, index)
        with open(filename, 'wb') as fp:
            fp.write(xml)
        LOG.info('Exported recording: {0}'.format(filename))
    
    def openRecording(self, filename=None):
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
        # force extension
        filename = '{0}.xml'.format(os.path.splitext(filename)[0])
        # if filename is none should try to use lastSavedFilename for the current recording collection
        with open(filename, 'wb') as fp:
            pickle.dump(self.recordings[index.row()].toString(), fp)
        LOG.debug('Saved recording to {0}'.format(filename))
        
    
    def exportMovie(self, filename, index, progress=None):        
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
    
    def loadImageAtTime(self, index, time):
        recording = self.recordings[index.row()]
        frame = recording.frames.getFrame(time)
        if frame is not None:
            self.imageCollection.seekToImage(frame.image)
            self.pixmapCache.add(self.nextImage)
            self.imageDataChanged()
            self.recordingDataChanged()
    
    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return
        
        if role in (Qt.DisplayRole, Qt.EditRole):
            # get the mapping and source object
            m = index.column()
            attr = Mappings.names[m]
            src = self.recordings[index.row()] if attr in self.recordingProps else self
            
            if attr == 'name':
                print('retrieving {0}: {1}'.format(attr, getattr(src, attr)))
            
            if attr in self.specialProps:
                if hasattr(self, attr):
                    return getattr(self, attr)(index)
            else:
                if hasattr(src, attr):
                    return getattr(src, attr)
    
    
    def setData(self, index, value, role=Qt.EditRole):
        """
        Receive and apply data input from the view/controllers. The model is updated
        appropriately based on what data is changed and to what values.
        """
        
        # get the mapping and source object
        m = index.column()
        attr = Mappings.names[m]
        print('setting row, col {0}, {1}, {2}'.format(index.row(), index.column(), attr))
        src = self.recordings[index.row()] if attr in self.recordingProps else self
        print('continuing to set {0}'.format(attr))
        
        # special props cant be set
        if attr in self.specialProps:
            return False
        
        # stop if the value is not different
        if hasattr(src, attr):
            # loose equality
            curValue = getattr(src, attr)
            if str(curValue) == str(value):
                return False
        else:
            return False
        
        if m not in [Mappings.curTime]:
            LOG.debug('{0:>25} = {1!r} -> {2!r}'.format(attr, curValue, value))
        
        
        # src == self
        # -----------
        
        if m == Mappings.curImageIndex:
            if self.isRecording:
                self.recordCurrentFrame(index)
            self.loadImage(value)
            return True
            
        elif m == Mappings.curTime:
            self.curTime = value
            if not self.isRecording:
                self.loadImageAtTime(index, value)
            self.timeDataChanged(index)
            return True
            
        elif m == Mappings.audioEnabled:
            self.audioEnabled = value
            # check to see if we should update our device index
            if self.audioEnabled and self.audioInputDeviceIndex == -1:
                self.audioInputDeviceIndex = audio.defaultInputDeviceIndex()
            self.mappingChanged(index, m)
        
        elif m == Mappings.audioInputDeviceIndex:
            self.audioInputDeviceIndex = value
            self.curAudioRecording.inputDeviceIndex = self.audioInputDeviceIndex
            self.mappingChanged(index, m)
        
        # TODO: elif m == audioOutputDeviceIndex:
        
        
        # TODO: MOVE ALL RECORDING/PLAYING TO THE RECORDING COLLECTION
        elif m == Mappings.isRecording:
            raise NotImplementedError('bitches...')
            #self.isRecording = value
            #if not self.isRecording:
            #    # recording has just stopped. record the last frame
            #    self.recordCurrentFrame(index)
            #    if self._audioEnabled:
            #        # TODO: save the recording and audio (xml, wav) to getStoryTimePath
            #        self.curAudioRecording.stop()
            #        self.curAudioRecording.save(self.getAudioPath(self.recordings[self.recordingIndex].name))
            #    self.saveRecording(self.getRecordingPath(self.recordings[self.recordingIndex].name))
            #else:
            #    if len(self.curFrameRecording) != 0:
            #        # start a new recording cause this ones already been used
            #        self.newRecording()
            #    if self._audioEnabled:
            #        self.curAudioRecording.record()
            #self.recordingDataChanged()
            return True
        
        # TODO: MOVE ALL RECORDING/PLAYING TO THE RECORDING COLLECTION
        elif m == Mappings.isPlaying:
            raise NotImplementedError('bitches plus...')
            #self.isPlaying = value
            #if self.isPlaying:
            #    if self._audioEnabled and self.curAudioRecording.hasRecording:
            #        self.curAudioRecording.stop()
            #        self.curAudioRecording.play()
            #else:
            #    self.curAudioRecording.stop()
            return True
        
        
        # src == recording
        # ----------------
        
        elif m == Mappings.name:
            src.name = value
            self.dataChanged.emit(index, index)
            return True
        
        return False



class RecordingModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(RecordingsModel, self).__init__(parent)
        self.maps = utils.enum(*Recording.attrs)
        self.recordings = []
        self.newRecording()
        LOG.debug('RecordingModel initialized')

    def __repr__(self):
        return '<RecordingModel | {0} recording(s)>'.format(self.rowCount())
    
    def getNewRecordingName(self, index=None):
        if index is None:
            index = self.recordingCount + 1
        if len(self.images) > 0:
            f = os.path.splitext(os.path.basename(self.images[0]))[0]
            name = '{f} {0:03}'.format(index, f=f)
            return name
        else:
            return 'Story Time Recording {0:03}'.format(index)
    
    def newRecording(self):
        new = Recording()
        new.name = self.getNewRecordingName()
        new.audio.inputDeviceIndex = self.audioInputDeviceIndex
        new.audio.outputDeviceIndex = self.audioOutputDeviceIndex
        self.addRecording(new)
    
    def addRecording(self, recording):
        self.insertRows(len(self.recordings), [recording])
    
    def insertRows(self, position, recordings, parent=QModelIndex()):
        rows = len(recordings)
        self.beginInsertRows(parent, position, position + rows - 1)
        for r in recordings:
            self.recordings.insert(position, r)
        self.endInsertRows()
        return True
    
    def rowCount(self, index=None):
        return len(self.recordings)

    def columnCount(self, index=None):
        return 1


