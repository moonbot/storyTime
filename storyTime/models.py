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
    # recording props
    'name', 'durationDisplay', 'imageCount', 'duration', 'fps', 'timerInterval', 
    
    # model normal attrs
    'recordings', 'recordingCount', 'isRecording', 'isPlaying', 'curTime',
    'isTimeDisplayFrames', 'audioInputDeviceIndex', 'audioOutputDeviceIndex',
    # model properties (from imageCollection or pixmapCache)
    'audioEnabled', 'recordingCount', 'imageCollectionCount', 'curImageIndex',
    'curImageIndexLabel', 'curImagePath', 'curImage', 'prevImage', 'nextImage',
    
    # special (info from both model and a recording)
    'timelineDuration', 'timelineDurationDisplay', 'timeDisplay',
    
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
        
        self.recordingProps = ('name', 'fps', 'timerInterval', 'duration', 'durationDisplay', 'imageCount')
        self.specialProps = ('timelineDuration', 'timeDisplay')
        
        # Recording / Playback
        # all recording collections
        self.recordings = []
        # playback/recording states
        self.isRecording = False
        self.isPlaying = False
        # current time of the playback timeline in frames
        self.curTime = 0
        # current display mode of the time (time code vs frames)
        self.isTimeDisplayFrames = False
        # whether to record audio for the current recording or not
        self.audioInputDeviceIndex = audio.defaultInputDeviceIndex()
        self.audioOutputDeviceIndex = audio.defaultOutputDeviceIndex()
        # available fps options
        self._fpsOptions = FPS_OPTIONS
        # custom fps option
        self.customFps = 12
        
        
        self.audioEnabled = True
        # current image collection
        self.imageCollection = ImageCollection()
        # the pixmap cache for efficiency
        self.pixmapCache = PixmapCache()
        
        self.newRecording()
        LOG.debug('Model Initialized')
    
    def __repr__(self):
        return '<StoryTimeModel | {0.recordingCount} recording(s)>'.format(self)
    
    
    
    # properties
    
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
    def recordingCount(self):
        return len(self.recordings)
    
    @property
    def imageCollectionCount(self):
        return len(self.images)
    
    @property
    def curImageIndex(self):
        return self.imageCollection.seek
    
    @property
    def curImageIndexLabel(self):
        return '{1:0{0.imagePadding}}/{0.imageCollectionCount}'.format(self, self.curImageIndex + 1)
    
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
    
    @property
    def imagePadding(self):
        return len(str(self.imageCollectionCount))
    
    @property
    def images(self):
        return self.imageCollection.images
    @images.setter
    def images(self, value):
        self.imageCollection.images = value
        self.imageDataChanged()
    
    
    # 'special' properties
    
    def timelineDuration(self, index):
        recording = self.recordings[index.row()]
        if self.isRecording:
            # return the current time ceilinged to the nearest half minute
            minuteFrames = recording.fps * 30
            minutes = math.floor(float(self.curTime) / minuteFrames) + 2
            return int(minutes * minuteFrames)
        else:
            ad = self.secondsToFrames(index, recording.audioDuration)
            fd = recording.frameDuration
            #vd = recording.videuDuration
            return max(ad, fd)
    
    def timelineDurationDisplay(self, index):
        dur = self.timelineDuration(index)
        recording = self.recordings[index.row()]
        return utils.getTimecode(dur, recording.fps)
    
    def timeDisplay(self, index):
        """ Return the current time as a timecode """
        recording = self.recordings[index.row()]
        if self.isTimeDisplayFrames:
            return '{0}'.format(self.curTime)
        else:
            return utils.getTimecode(self.curTime, recording.fps)
    
    
    
    # methods
    
    def toggleTimeDisplay(self):
        self.isTimeDisplayFrames = not self.isTimeDisplayFrames
        self.mappingChanged(QModelIndex(), Mappings.isTimeDisplayFrames)
        self.mappingChanged(QModelIndex(), Mappings.timeDisplay)
    
    def secondsToFrames(self, index, seconds, fps=None):
        recording = self.recordings[index.row()]
        if fps is None:
            fps = recording.fps
        return int(seconds * fps)
        
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
        new = RecordingCollection()
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
    
    def loadImage(self, imageIndex):
        self.imageCollection.seek = imageIndex
        # update cache
        self.pixmapCache.add(self.nextImage)
        self.imageDataChanged()
    
    def clearImages(self):
        self.images = []
        self.pixmapCache.clear()
        self.imageDataChanged()
    
    # qt model methods
    
    def rowCount(self, parent):
        return len(self.recordings)
    
    def columnCount(self, parent):
        return 3
    
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
    
    def imageDataChanged(self):
        attrs = (
            'imageCollectionCount',
            'curImageIndex',
            'curImageIndexLabel',
            'curImagePath',
            'curImage',
            'prevImage',
            'nextImage',
        )
        self.multiMappingChanged(self.index(), attrs)
    
    def recordingDataChanged(self, index):
        attrs = (
            'recordingIndex',
            'recordingName',
            'recordingFps',
            'recordingDuration',
            'recordingDurationDisplay',
            'recordingImageCount',
        )
        self.multiMappingChanged(index, attrs)
    
    def timeDataChanged(self, index):
        attrs = (
            'curTime',
            'timeDisplay',
        )
        self.multiMappingChanged(index, attrs)
    
    def multiMappingChanged(self, index, attrs):
        for attr in attrs:
            self.mappingChanged(index, getattr(Mappings, attr))
    
    def mappingChanged(self, index, mapping):
        index = self.index(index.row(), mapping)
        self.dataChanged.emit(index, index)
    
    def index(self, row=0, column=0, parent=None):
        return self.createIndex(row, column)
    
    def parent(self, index):
        """ There is only one viable index, and therefore no feasible parent """
        return QModelIndex()


