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

LOG = logging.getLogger('storyTime.models')

# TODO: cluster mappings that affect each other or create event pool presets
Mappings = utils.enum(
    'isRecording', 'isPlaying', 'fps', 'curTime', 'timeDisplay', 'isTimeDisplayFrames', 'audioEnabled', 'audioInputDeviceIndex', 'audioOutputDeviceIndex',
    'imageCount', 'curImageIndex', 'curImageIndexLabel', 'curImagePath', 'curImage', 'prevImage', 'nextImage',
    'recordingIndex', 'recordingName', 'recordingFps', 'recordingDuration', 'recordingDurationDisplay', 'recordingImageCount',
    'end',
)

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
        self.audioEnabled = True
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
            return utils.getTimecode(self.curTime, self.recordingFps)
    
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
    
    def getRecordingAtIndex(self, index):
        return self.recordings[index]        
    
    def getAudioEnabled(self):
        return self._audioEnabled
    def setAudioEnabled(self, value):
        if isinstance(value, bool):
            # check to see if we are able to enable
            self._audioEnabled = False
            if len(audio.inputDevices()) > 0:
                self._audioEnabled = value
    audioEnabled = property(getAudioEnabled, setAudioEnabled)
    
    def getStoryTimePath(self):
        return os.path.expanduser('~/storyTime')
    
    def getAudioPath(self, name):
        filename = utils.normalizeFilename('{date}_{name}'.format(name=name, date=utils.timeString()))
        path = os.path.join(self.getStoryTimePath(), filename)
        return path
    
    def getRecordingPath(self, name):
        filename = utils.normalizeFilename('{date}_{name}'.format(name=name, date=utils.timeString()))
        path = os.path.join(self.getStoryTimePath(), filename)
        return path
    
    def moveAudioRecording(self, src, dst, recording):
        if os.path.isfile(src):
            os.remove(src)
        recording.save(dst)
    
    @property
    def recordingFps(self):
        return self.curFrameRecording.fps
    
    @property
    def recordingName(self):
        return self.curRecording.name
    
    def getNewRecordingName(self, index=None):
        if index is None:
            index = self.recordingCount + 1
        if len(self.images) > 0:
            f = os.path.splitext(os.path.basename(self.images[0]))[0]
            name = '{f} {0:03}'.format(index, f=f)
            return name
        else:
            return 'Story Time Recording {0:03}'.format(index)
    
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
        return utils.getTimecode(self.recordingDuration, self.recordingFps)
    
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
        new.name = self.getNewRecordingName()
        new.audio.inputDeviceIndex = self.audioInputDeviceIndex
        new.audio.outputDeviceIndex = self.audioOutputDeviceIndex
        self.addRecording(new)
    
    def addRecording(self, recording):
        self.recordings.append(recording)
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
        if duration == 0:
            LOG.warning('skipping frame recording, duration is 0: {0}. outTime {1} curTime {2}'.format(image, outTime, self.curTime))
            return
        LOG.debug('index: {3}, {1:>4} - {2:<4}: {0}'.format(os.path.basename(image), outTime, outTime + duration, recordingIndex))
        self.curFrameRecording.insert(recordingIndex, image, duration)
    
    
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
        # update the recording's name, if applicable
        self.updateRecordingName()
        # emit signals
        self.imageDataChanged()
        
        # handle recordings
        for xml in xmls:
            self.openRecording(xml)
        self.recordingDataChanged()
    
    
    def updateRecordingName(self):
        if self.curRecording.name.startswith('Story Time Recording'):
            try:
                index = int(self.curRecording.name.split(' ')[-1])
            except:
                return
            # update the recording's name to match
            self.curRecording.name = self.getNewRecordingName(index)
            self.mappingChanged(Mappings.recordingName)
    
    def cacheAllImages(self):
        # cache the images
        LOG.debug('Caching images...')
        self.pixmapCache.cache(self.images)
    
    def clearCache(self):
        LOG.debug('Clearing cache {0}'.format(self.pixmapCache.count))
        self.pixmapCache.clear()
    
    def toXml(self, platform=None, index=None):
        """
        Export the current recording collection to an editorial xml file.
        
        `platform` -- the target platform for which we are exporting.
            this is where path mapping will be taken into account.
        
        """
        if index is None:
            index = self.recordingIndex
        recording = self.recordings[index]
        frameImages = [f.image for f in recording.frames.frames]
        frameDurations = [f.duration for f in recording.frames.frames]
        if platform is None:
            platform = sys.platform
        
        if len(self.curFrameRecording) > 0:
            fcpkw = {
                'name':recording.name,
                'images':zip(frameImages, frameDurations),
                'audioPath':recording.audio.filename,
                'fps':recording.fps,
                'ntsc':(recording.fps % 30 == 0),
                'platform':platform,
            }
            return fcpxml.FcpXml(**fcpkw).toString()
    
    def exportRecording(self, filename, platform='win', index=None):
        if index is None:
            index = self.recordingIndex
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
        recording = RecordingCollection.fromString(data)
        self.addRecording(recording)
        
        # attempt to load audio
        audioFile = os.path.splitext(filename)[0] + '.wav'
        if os.path.isfile(audioFile):
            recording.audio.load(audioFile)
        
        LOG.info('Loaded recording: {0}'.format(filename))
        # TODO: figure out a better way to encapsulate this functionality
        allImages = sorted(list(set(self.images + recording.frames.images)))
        self.images = allImages
    
    def saveRecording(self, filename=None, index=None):
        if index is None:
            index = self.recordingIndex
        # force extension
        filename = '{0}.xml'.format(os.path.splitext(filename)[0])
        # if filename is none should try to use lastSavedFilename for the current recording collection
        with open(filename, 'wb') as fp:
            pickle.dump(self.recordings[index].toString(), fp)
        LOG.debug('Saved recording to {0}'.format(filename))
        
    
    def exportMovie(self, filename, index=None, progress=None):
        if index is None:
            index = self.recordingIndex
        recording = self.recordings[index]
        
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
                '-acodec', 'aac',
                '-ab', '256',
            ]
        args += [
            '-r', self.recordingFps,
            '-vcodec', 'libx264',
            '-g', '12',
            '-t', float(recording.duration) / self.recordingFps,
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
    
    @property
    def imageCount(self):
        return len(self.images)
    
    @property
    def imagePadding(self):
        return len(str(self.imageCount))
    
    @property
    def images(self):
        return self.imageCollection.images
    @images.setter
    def images(self, value):
        self.imageCollection.images = value
        self.imageDataChanged()
    
    @property
    def curImageIndex(self):
        return self.imageCollection.seek
    
    @property
    def curImageIndexLabel(self):
        index = self.curImageIndex
        if self.imageCount > 0:
            index += 1
        return '{1:0{0.imagePadding}}/{0.imageCount}'.format(self, index)
    
    @property
    def curImagePath(self):
        path = self.imageCollection.current()
        return path if path is not None else ''
    
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
            self.pixmapCache.add(self.nextImage)
            self.imageDataChanged()
            self.recordingDataChanged()
    
    def loadImage(self, index):
        self.imageCollection.seek = index
        # update cache
        self.pixmapCache.add(self.nextImage)
        self.imageDataChanged()
        self.recordingDataChanged()
    
    def clearImages(self):
        self.images = []
        self.pixmapCache.clear()
        self.imageDataChanged()
    
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
            
        elif m == Mappings.audioEnabled:
            self.audioEnabled = value
            # check to see if we should update our device index
            if self.audioEnabled and self.audioInputDeviceIndex == -1:
                self.audioInputDeviceIndex = audio.defaultInputDeviceIndex()
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
                if self._audioEnabled:
                    # TODO: save the recording and audio (xml, wav) to getStoryTimePath
                    self.curAudioRecording.stop()
                    self.curAudioRecording.save(self.getAudioPath(self.curRecording.name))
                self.saveRecording(self.getRecordingPath(self.curRecording.name))
            else:
                if len(self.curFrameRecording) != 0:
                    # start a new recording cause this ones already been used
                    self.newRecording()
                if self._audioEnabled:
                    self.curAudioRecording.record()
            self.recordingDataChanged()
            return True
        
        elif m == Mappings.isPlaying:
            self.isPlaying = value
            if self.isPlaying:
                if self._audioEnabled and self.curAudioRecording.hasRecording:
                    self.curAudioRecording.stop()
                    self.curAudioRecording.play()
            else:
                self.curAudioRecording.stop()
            
        elif m == Mappings.recordingIndex:
            if self._audioEnabled and self.isPlaying:
                self.curAudioRecording.stop()
            self.recordingIndex = max(min(value, self.recordingCount - 1), 0)
            if self._audioEnabled and self.isPlaying:
                self.curAudioRecording.play()
            self.recordingDataChanged()
            return True
            
        elif m == Mappings.recordingName:
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


