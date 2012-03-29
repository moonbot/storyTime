"""
controller.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from models import Mappings, StoryTimeModel
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import QUiLoader
import logging
import os

LOG = logging.getLogger('storyTime.controllers')

def loadUi(path, parent=None, attach=False):
    loader = QUiLoader()
    file_ = QFile(path)
    file_.open(QFile.ReadOnly)
    widget = loader.load(file_, parent)
    if attach:
        attachUi(widget, parent)
    file_.close()
    return widget

def attachUi(widget, parent):
    if parent.layout() is None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        parent.setLayout(layout)
    parent.layout().addWidget(widget)


class EventEater(QObject):
    def eventFilter(self, obj, event):
        
        if event.type() == QEvent.KeyPress:
            return self.keyPressEvent(event)
            
        elif event.type() == QEvent.DragEnter:
            return self.dragEnterEvent(event)
            
        elif event.type() == QEvent.DragMove:
            return self.dragMoveEvent(event)
            
        elif event.type() == QEvent.Drop:
            return self.dropEvent(event)
            
        else:
            # standard event processing
            return QObject.eventFilter(self, obj, event)

    def keyPressEvent(self, event):
        pass
    
    def handlePaths(self, paths):
        pass
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
        return True

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
        return True

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            paths = []
            for url in event.mimeData().urls():
                paths.append(str(url.toLocalFile()))
            # tell the model to load the given paths
            self.handlePaths(paths)
        return True


#base, form = uic.loadUiType('views/main.ui')

class StoryTimeWindow(object):
    """
    The Main Story Time Window. Loads and attaches each of the main control
    widgets (ImageView, ImageSlider, TimeSlider) and connects them to a model.
    """
    
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StoryTimeWindow, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    @staticmethod
    def instance():
        return StoryTimeWindow._instance
    
    def __init__(self):        
        #super(StoryTimeWindow, self).__init__(parent)
        #self.setupUi(self)
        self.ui = loadUi('views/main.ui')
        self.ui.setFocusPolicy(Qt.StrongFocus)
        self.ui.setAcceptDrops(True)
        self.ui.setWindowTitle('Story Time')
        self.ui.show()
        
        # setup model
        self._model = StoryTimeModel(self.ui)
        
        # current image
        self.curImageView = ImageView(Mappings.curImage, 1, self.ui)
        self.curImageView.setModel(self._model)
        self.ui.layoutCurImage.addWidget(self.curImageView)
        # prev image
        self.prevImageView = ImageView(Mappings.prevImage, 0, self.ui)
        self.prevImageView.setModel(self._model)
        self.ui.layoutPrevImage.addWidget(self.prevImageView)
        # prev image
        self.nextImageView = ImageView(Mappings.nextImage, 2, self.ui)
        self.nextImageView.setModel(self._model)
        self.ui.layoutNextImage.addWidget(self.nextImageView)
        
        self.setImageViewVisible('prev', False)
        self.setImageViewVisible('next', False)
        
        self.imageSlider = ImageSlider(self.ui)
        self.imageSlider.setModel(self._model)
        self.ui.layoutControls.addWidget(self.imageSlider)
        
        self.timeSlider = TimeSlider(self.ui)
        self.timeSlider.setModel(self._model)
        self.ui.layoutControls.addWidget(self.timeSlider)
        
        # setup key press eater
        self.eventEater = EventEater()
        self.eventEater.keyPressEvent = self.keyPressEvent
        self.eventEater.handlePaths = self._model.loadPaths
        self.ui.installEventFilter(self.eventEater)
        self.imageSlider.installEventFilter(self.eventEater)
        self.timeSlider.installEventFilter(self.eventEater)
        
        # hookup menu actions
        self.ui.actionNewRecording.triggered.connect(self.newRecording)
        self.ui.actionOpenRecording.triggered.connect(self.openRecording)
        self.ui.actionSaveRecording.triggered.connect(self.saveRecording)
        self.ui.actionSaveRecordingAs.triggered.connect(self.saveRecordingAs)
        self.ui.actionImportImages.triggered.connect(self.importImages)
        self.ui.actionExportForFCP.triggered.connect(self.exportForFCP)
        self.ui.actionExportForPremiere.triggered.connect(self.exportForPremiere)
    
    def setPrevImageViewVisible(self, visible):
        self.setImageViewVisible('prev', visible)
    
    def setNextImageViewVisible(self, visible):
        self.setImageViewVisible('next', visible)
    
    def setImageViewVisible(self, which, visible):
        if not hasattr(self, '{0}ImageView'.format(which)):
            return
        view = getattr(self, '{0}ImageView'.format(which))
        view.setVisible(visible)
        self.ui.layoutImageViews.setStretch(view.index, int(visible))
        
    
    def loadPaths(self, paths):
        self._model.loadPaths(paths)
    
    def keyPressEvent(self, event):
        # set the image index data the same way a mapping would
        if event.key() in (Qt.Key_Space, Qt.Key_Period, Qt.Key_Right, Qt.Key_Down):
            index = self._model.mappingIndex(Mappings.curImageIndex)
            value = self._model.curImageIndex + 1
            self._model.setData(index, value)
            return True
        if event.key() in (Qt.Key_Backspace, Qt.Key_Comma, Qt.Key_Left, Qt.Key_Up):
            index = self._model.mappingIndex(Mappings.curImageIndex)
            value = self._model.curImageIndex - 1
            self._model.setData(index, value)
            return True
        
        # some time slider hotkeys
        if event.key() == Qt.Key_R:
            self.timeSlider.recordBtnAction()
        if event.key() == Qt.Key_P:
            self.timeSlider.togglePlayback()
        if event.key() == Qt.Key_B:
            self.timeSlider.toFirst()
        if event.key() == Qt.Key_E:
            self.timeSlider.toLast()
    
    def newRecording(self):
        self._model.newRecording()
        LOG.debug('New recording')
    
    def openRecording(self):
        caption = 'Open Story Time Recording...'
        f = QFileDialog.getOpenFileName(
            self.ui,
            caption=caption,
            filter='XML files (*.xml)',
        )
        LOG.debug('Opening story time file: {0}'.format(f))
    
    def saveRecording(self):
        LOG.debug('Saving current recording where it was last saved.')
    
    def saveRecordingAs(self):
        caption = 'Save Story Time Recording...'
        files = QFileDialog.getSaveFileName(
            self.ui,
            caption=caption,
            filter='XML files (*.xml)',
        )
        LOG.debug('Saving story time file: {0}'.format(files[0]))
    
    def importImages(self):
        caption = 'Import Image(s)'
        files = QFileDialog.getOpenFileNames(
            self.ui,
            caption=caption,
        )
        if len(files) > 0 and len(files[0]) > 0:
            self.loadPaths(files[0])
            LOG.debug('Imported {0}'.format(files[0]))
    
    def exportForFCP(self):
        LOG.debug('Exporting for FCP')
    
    def exportForPremiere(self):
        LOG.debug('Exporting for Premiere')



class ImageView(QWidget):
    """
    The image viewing widget for Story Time. Contains three graphics views
    for displaying the current, previous, and next images.
    """
    def __init__(self, pixmapMapping, index, parent=None):
        super(ImageView, self).__init__(parent)
        self.ui = loadUi('views/imageView.ui', self, True)
        self._dataMapper = QDataWidgetMapper()
        self.pixmapMapping = pixmapMapping
        # for use when adjusting layout stretch
        self.index = index
        self.ui.GraphicsView.setStyleSheet( 'QGraphicsView { border-style: none; }' )
    
    def getPixmap(self):
        return self.ui.GraphicsPixmapItem.pixmap()
    def setPixmap(self, data):
        self.ui.GraphicsPixmapItem.setPixmap(data)
        self.resizeEvent()
    pixmap = Property("QPixmap", getPixmap, setPixmap)
    
    def addPixmapItem(self, graphicsView):
        item = QGraphicsPixmapItem()
        scene = QGraphicsScene()
        scene.addItem(item)
        graphicsView.setScene(scene)
        return item

    def setModel(self, model):
        self._model = model
        self._dataMapper.setModel(model)
        self.ui.GraphicsPixmapItem = self.addPixmapItem(self.ui.GraphicsView)
        self._dataMapper.addMapping(self, self.pixmapMapping, 'pixmap')
        self._dataMapper.toFirst()
    
    def resizeEvent(self, event=None):
        self.ui.GraphicsView.fitInView(self.ui.GraphicsView.scene().itemsBoundingRect(), Qt.KeepAspectRatio)



class ImageSlider(QWidget):
    """
    The ImageSlider widget for Story Time. Contains a slider that controls
    which image is currently displayed, as well as labels providing information
    about the current image path as well as how many images there are.
    """
    def __init__(self, parent=None):
        super(ImageSlider, self).__init__(parent)
        #self.setupUi(self)
        self.ui = loadUi('views/imageSlider.ui', self, True)
        self._dataMapper = QDataWidgetMapper()
        
        self.ui.ImageSlider.valueChanged.connect(self._dataMapper.submit)
        self.ui.PrevImageCheck.toggled.connect(StoryTimeWindow.instance().setPrevImageViewVisible)
        self.ui.NextImageCheck.toggled.connect(StoryTimeWindow.instance().setNextImageViewVisible)
    
    def setSliderMaximum(self, value):
        self.ui.ImageSlider.setMaximum(max(value - 1, 0))
    def getSliderMaximum(self):
        return self.ui.ImageSlider.maximum()
    sliderMaximum = Property('int', getSliderMaximum, setSliderMaximum)
    
    def setModel(self, model):
        self._model = model
        self.ui.CacheImagesBtn.clicked.connect(self._model.cacheAllImages)
        self._dataMapper.setModel(model)
        self._dataMapper.addMapping(self.ui.ImagePath, Mappings.curImagePath, 'text')
        self._dataMapper.addMapping(self.ui.ImageSlider, Mappings.curImageIndex, 'sliderPosition')
        self._dataMapper.addMapping(self, Mappings.imageCount, 'sliderMaximum')
        self._dataMapper.addMapping(self.ui.ImageSliderLabel, Mappings.curImageIndexLabel, 'text')
        self._dataMapper.toFirst()
        
    
    def installEventFilter(self, filter):
        # install the event filter on all appropriate objects
        self.ui.ImageSlider.installEventFilter(filter)
        self.ui.CacheImagesBtn.installEventFilter(filter)




class TimeSlider(QWidget):
    """
    The TimeSlider widget for Story Time. Controls/displays the current
    playback state of the current recording.
    """
    def __init__(self, parent=None):
        super(TimeSlider, self).__init__(parent)
        #self.setupUi(self)
        self.ui = loadUi('views/timeSlider.ui', self, True)
        self._dataMapper = QDataWidgetMapper()
        
        # used to keep track of playback time
        self.time = QElapsedTimer()
        self.timer = QTimer()
        self.timer.timerEvent = self.timerEvent
        
        # hide hidden controls
        self.ui.IsRecordingCheck.setVisible(False)
        self.ui.IsPlayingCheck.setVisible(False)
        
        self.ui.RecordingIndex.valueChanged.connect(self.recordingIndexChanged)
        self.ui.TimeSlider.valueChanged.connect(self._dataMapper.submit)
        self.ui.IsPlayingCheck.toggled.connect(self.updateIsPlaying)
        self.ui.IsRecordingCheck.toggled.connect(self.updateIsRecording)
        self.ui.PlayBtn.clicked.connect(self.play)
        self.ui.RecordBtn.clicked.connect(self.recordBtnAction)
        self.ui.NewBtn.clicked.connect(StoryTimeWindow.instance().newRecording)
    
    @property
    def timerInterval(self):
        return (1 / self._model.recordingFps) * 1000
    
    def setSliderMaximum(self, value):
        self.ui.TimeSlider.setMaximum(value)
    def getSliderMaximum(self):
        return self.ui.TimeSlider.maximum()
    sliderMaximum = Property('int', getSliderMaximum, setSliderMaximum)
    
    def recordingIndexChanged(self):
        if self.isPlaying and not self.isRecording:
            self.play()
        self._dataMapper.submit()
    
    def updateIsPlaying(self, isPlaying):
        # record button state
        img = 'images/{0}.png'.format('stopBtn' if isPlaying else 'recordBtn')
        self.ui.RecordBtn.setIcon(QIcon(img))
        # enable/disable controls
        setVisuallyEnabled(self.ui.PlayBtn, not isPlaying)
        setVisuallyEnabled(self.ui.NewBtn, not isPlaying)
        setVisuallyEnabled(self.ui.RecordingName, not isPlaying)
        setVisuallyEnabled(self.ui.RecordingImageCount, not isPlaying)
        setVisuallyEnabled(self.ui.RecordingImageCountLabel, not isPlaying)
        setVisuallyEnabled(self.ui.RecordingDurationDisplay, not isPlaying)
        self._dataMapper.submit()
    
    def updateIsRecording(self, isRecording):
        # bg color
        style = 'background-color: rgb{0};'.format( (60, 25, 25) if isRecording else (40, 40, 40) )
        self.ui.MainFrame.setStyleSheet(style)
        # enable/disable controls
        self.ui.TimeSlider.setEnabled(not isRecording)
        setVisuallyEnabled(self.ui.AudioCheck, not isRecording)
        setVisuallyEnabled(self.ui.RecordingIndex, not isRecording)
        self._dataMapper.submit()
    
    def recordBtnAction(self):
        if self.isRecording or self.isPlaying:
            self.stop()
        else:
            self.record()
    
    @property
    def isRecording(self):
        return self.ui.IsRecordingCheck.checkState() == Qt.Checked
    
    @property
    def isPlaying(self):
        return self.ui.IsPlayingCheck.checkState() == Qt.Checked
    
    def record(self):
        self.ui.IsRecordingCheck.setCheckState(Qt.Checked)
        self.play()
    
    def play(self, time=0):
        self.ui.IsPlayingCheck.setCheckState(Qt.Checked)
        self.time.restart()
        self.timer.start(self.timerInterval)
    
    def stop(self):
        self.ui.IsPlayingCheck.setCheckState(Qt.Unchecked)
        self.ui.IsRecordingCheck.setCheckState(Qt.Unchecked)
        self.timer.stop()
    
    def togglePlayback(self):
        if self.isRecording or self.isPlaying:
            self.stop()
        else:
            self.play()
    
    def toFirst(self):
        if not self.isPlaying and not self.isRecording:
            self.ui.TimeSlider.setSliderPosition(0)
            self._dataMapper.submit()
    
    def toLast(self):
        if not self.isPlaying and not self.isRecording:
            self.ui.TimeSlider.setSliderPosition(self._model.recordingDuration)
            self._dataMapper.submit()
    
    def timerEvent(self, event):
        sec = self.time.elapsed() * 0.001
        frames = int(sec * self._model.recordingFps)
        self.ui.TimeSlider.setSliderPosition(frames)
        # determine whether to loop or not
        if not self.isRecording and frames >= self._model.recordingDuration:
            # reached the end of playback
            self.stop()
        self._dataMapper.submit()
    
    def setModel(self, model):
        self._model = model
        self.ui.TimeDisplay.clicked.connect(self._model.toggleTimeDisplay)
        self._dataMapper.setModel(model)
        self._dataMapper.addMapping(self.ui.RecordingIndex, Mappings.recordingIndex, 'value')
        self._dataMapper.addMapping(self.ui.RecordingName, Mappings.recordingName, 'text')
        self._dataMapper.addMapping(self.ui.RecordingImageCount, Mappings.recordingImageCount, 'text')
        self._dataMapper.addMapping(self.ui.RecordingDurationDisplay, Mappings.recordingDurationDisplay, 'text')
        self._dataMapper.addMapping(self, Mappings.recordingDuration, 'sliderMaximum')
        self._dataMapper.addMapping(self.ui.IsRecordingCheck, Mappings.isRecording, 'checked')
        self._dataMapper.addMapping(self.ui.TimeSlider, Mappings.curTime, 'sliderPosition')
        self._dataMapper.addMapping(self.ui.TimeDisplay, Mappings.timeDisplay, 'text')
        self._dataMapper.toFirst()
        
    
    def installEventFilter(self, filter):
            # install the event filter on all appropriate objects
        self.ui.TimeSlider.installEventFilter(filter)
        self.ui.TimeDisplay.installEventFilter(filter)
        self.ui.AudioCheck.installEventFilter(filter)
        self.ui.PlayBtn.installEventFilter(filter)
        self.ui.RecordingIndex.installEventFilter(filter)
        self.ui.RecordBtn.installEventFilter(filter)
        self.ui.NewBtn.installEventFilter(filter)



def setVisuallyEnabled(control, enabled):
    style = '' if enabled else 'color: rgb(120, 120, 120);'
    control.setEnabled(enabled)
    control.setStyleSheet(style)



class StoryTimeControl(object):
    
    #audioHandler = AudioHandler()
    UPDATE_INTERVAL = 500
    
    
    def ctl_process_export(self, caption, operatingSystem):
        """
        Export the current application state to a Final Cut Pro XML file.
        
        `caption` -- the caption of the file browsing dialog
        `operatingSystem` -- the operating system to export the file to
        """
        if len(self.images.get()) > 0:
            path = self.view_browse_save_as(caption)
            if path is not None and path != '':
                fcpkw = {
                    'name':os.path.splitext(os.path.split(path)[1])[0],
                    'images':zip(self.images.get(), self.create_frames_list()),
                    'audioPath':self.audioPath.get(),
                    'fps':self.fps.get(),
                    'ntsc':(self.fps.get() % 30 == 0),
                    'OS':operatingSystem
                }
                with open(path, 'w') as exportFile:
                    exportFile.write(FcpXml(**fcpkw).getStr())
                self.ctl_make_audio_path()
                
    def ctl_make_audio_path(self):
        """Set the audio path for a new file"""
        imagePath = self.images.get()[0]
        dirname = os.path.dirname(imagePath) + '/'
        dirname = os.path.join(dirname, 'audio')
        if os.path.exists(dirname):
            #filename = utils.get_latest_version(dirname)
            filename = dirname
            if not filename:
                filename = self.ctl_get_audio_path_name(filename)
        else:
            os.mkdir(dirname)
            filename = self.ctl_get_audio_path_name(filename)
        self.audioPath.set(filename)
        
    def ctl_get_audio_path_name(self, path):
        """Return the base audio filename corresponding to the given path"""
        fullbase = os.path.basename(path)
        base = fullbase.split('.')[0]
        path = '{0}Audio.wav'.format(base)
        return path
    
    # Playback and Recording Functions
    # --------------------------------
    
    def ctl_toggle_record(self):
        if len(self.images.get()) > 0:
            if not (self.recording.get() == self.BUTTON_STATES.DISABLED):
                self.recording.set(not self.recording.get())
                if self.recording.get() == self.BUTTON_STATES.ON:
                    self.timecode.set(self.countdownms.get())
                    self.view_start_disp_timer()
                    if self.recordAudio.get():
                        self.audioHandler.start_recording()
                    self.curFrame.set(1)
                    self.curImgFrame.set(1)
                    self.timing_data.set([])
                    if self.recordTiming.get():
                        self.view_update_timer()
                    else:
                    	# changed to timing_data, starts at first     
                    	self.view_start_timer(self.timing_data.get()[self.curFrame.get() - 1]['timing'])
                    self.startFrame.set(self.curFrame.get())
                    self.playing.set(self.BUTTON_STATES.DISABLED)
                else:
                    self.ctl_stop()
    
    def ctl_toggle_play(self):
        if len(self.images.get()) > 0:
            if not (self.playing.get() == self.BUTTON_STATES.DISABLED):
                self.playing.set(not self.playing.get())
                if self.playing.get() == self.BUTTON_STATES.ON:
                    self.timecode.set(0)
                    self.view_start_disp_timer()
                    self.audioHandler.start_playing()
                    self.curFrame.set(1)
                    self.curImgFrame.set(1)
                    self.view_start_timer(self.timing_data.get()[self.curFrame.get() - 1]['timing'])
                    self.startFrame.set(self.curFrame.get())
                    self.recording.set(self.BUTTON_STATES.DISABLED)
                else:
                    self.ctl_stop()
        
    def ctl_goto_recframe(self, frame):
        """Go to the given frame in timing_data"""
        if len(self.timing_data.get()) > 0:
            self.curFrame.set(frame)
            self.curImgFrame.set(self.timing_data.get()[frame-1]['imageNum'])
    
    def ctl_goto_imgframe(self, frame):
        """Go to the given frame from images"""
        if len(self.images.get()) > 0:
            self.curImgFrame.set(frame)
    
    def ctl_inc_frame(self):
        """Increment the current frame"""
        if not len(self.images.get()) > 0 :
            return
        if self.curFrame.get() == len(self.timing_data.get()) and self.recording.get() != self.BUTTON_STATES.ON:
            self.ctl_stop()
        elif self.recording.get() == self.BUTTON_STATES.ON and self.recordTiming.get():
            self.ctl_record_frame()
        if self.loop.get() and self.curImgFrame.get() == len(self.images.get()):
            self.curImgFrame.set(1)
            return
        self.curImgFrame.set(self.curImgFrame.get() + 1)
    
    def ctl_dec_frame(self):
        """Decrement the current frame"""
        if not len(self.images.get()) > 0 :
            return
        if self.recording.get() == self.BUTTON_STATES.ON and self.recordTiming.get():
            self.ctl_record_frame()
        if self.loop.get() and self.curImgFrame.get() == 1:
            self.curImgFrame.set(len(self.images.get()))
            return
        self.curImgFrame.set(self.curImgFrame.get() - 1)
    
    def ctl_record_frame(self):
    	"""
    	Record the current frame with the current time.
    	Gets called on inc and dec when recording.
    	Adds a dict object to the data list
    	eg. [{'image':'currentImage.jpg', 'time':<currentTime>}, ...]
    	"""
    	self.timing_data.get().append({'image':self.images.get()[self.curImgFrame.get() - 1],
    	   'timing':self.view_update_timer(), 'imageNum':(self.curImgFrame.get() -1)})
        
    def ctl_stop(self):
        """Stop playback and recording"""
        if self.recording.get() == self.BUTTON_STATES.ON:
            self.ctl_record_frame()
            self.ui.recSlider.setRange(1,len(self.timing_data.get()))
        self.recording.set(self.BUTTON_STATES.OFF)
        self.playing.set(self.BUTTON_STATES.OFF)
        self.audioHandler.stop_recording()
        self.audioHandler.stop_playing()
        self.view_stop_disp_timer()
        
    def ctl_update_playback(self):
        """Whilst playing, increment the frame """
        if self.curFrame.get() == len(self.timing_data.get()):
            self.ctl_stop()
            return
        elif (self.playing.get() == self.BUTTON_STATES.ON) or (self.recording.get() == self.BUTTON_STATES.ON and not self.recordTiming.get()):
            self.curFrame.set(self.curFrame.get() + 1)
            #self.curImgFrame.set(self.images.get().index(self.timing_data.get()[self.curFrame.get() - 1]['image']))
            self.view_start_timer(self.timing_data.get()[self.curFrame.get() - 1]['timing'])
            
    def ctl_update_timecode(self, value):
        if self.countdownms.get() > 0 and self.recording.get() == self.BUTTON_STATES.ON:
            countdownTime = self.countdownms.get() - value
            if countdownTime < 0:
                countdownTime = 0
            self.timecode.set(countdownTime)
        else:
            self.timecode.set(value)
                
    # Options Functions
    # -----------------
    
    def ctl_change_fps(self, index):
        self.fpsIndex.set(index)
        if self.fpsIndex.get() == len(self.fpsOptions.get()) - 1:
            newFps = self.view_query_custom_fps()
            self.fpsOptions.get()[-1][0] = 'Custom ({0} fps)...'.format(newFps)
            self.fpsOptions.get()[-1][1] = newFps
            self.fpsOptions.set(self.fpsOptions.get())
        self.fps.set(self.fpsOptions.get()[self.fpsIndex.get()][1])
                
    def ctl_toggle_record_timing(self, value):
        self.recordTiming.set(value)
        if not self.recordTiming.get() and not self.recordAudio.get():
            self.recording.set(self.BUTTON_STATES.DISABLED)
        else:
            self.recording.set(self.BUTTON_STATES.OFF)
    
    def ctl_toggle_loop(self, value):
        self.loop.set(value)
    
    def ctl_toggle_record_audio(self, value):
        self.recordAudio.set(value)
        if not self.recordTiming.get() and not self.recordAudio.get():
            self.recording.set(self.BUTTON_STATES.DISABLED)
        else:
            self.recording.set(self.BUTTON_STATES.OFF)
            
    def ctl_set_recording_countdown(self):
        countdownTime = self.view_query_countdown_time()
        if countdownTime is not None:
            self.countdown.set(countdownTime)
            self.timecode.set(self.countdownms.get())
            
            
    # Specialty Functions
    # -------------------
    
    def create_frames_list(self):
        """Return a list of image times converted to the current fps"""
        incFrames = self.timing_data.get()[:]
        total = 0
        for i in range(0, len(self.timing_data.get())):
            total = total + self.timing_data.get()[i]['timing']
            incFrames[i] = int(total * self.fps.get() / 1000)
        fpsFrames = incFrames[:]
        #We can ignore the value at index 0 because it's already the
        #correct value.
        for i in range(1, len(self.timing_data.get())):
            fpsFrames[i] = incFrames[i] - incFrames[i-1]
            if fpsFrames[i] < 1:
                fpsFrames[i] = 1
        return fpsFrames
    
    def filter_image_paths(self, paths):
        """
        Remove paths with invalid file extensions and return the
        resulting list.
        """
        return [path for path in paths if os.path.splitext(path)[1] in self.view_get_image_formats()]
    
    def to_xml(self):
        """Create a StoryTime XML string from the current application state"""
        xmlDoc = xml.dom.minidom.Document()
        stElement = xmlDoc.createElement('storyTime')
        xmlDoc.appendChild(stElement)
        fpsElement = xmlDoc.createElement('fps')
        stElement.appendChild(fpsElement)
        fpsText = xmlDoc.createTextNode(str(self.fps.get()))
        fpsElement.appendChild(fpsText)
        audioElement = xmlDoc.createElement('audio')
        stElement.appendChild(audioElement)
        audioText = xmlDoc.createTextNode(self.audioPath.get())
        audioElement.appendChild(audioText)
        framesElement = xmlDoc.createElement('frames')
        stElement.appendChild(framesElement)
        for i in range(0, len(self.timing_data.get())):
            frameElement = xmlDoc.createElement('frame')
            framesElement.appendChild(frameElement)
            pathElement = xmlDoc.createElement('path')
            frameElement.appendChild(pathElement)
            pathText = xmlDoc.createTextNode(self.timing_data.get()[i]['image'])
            pathElement.appendChild(pathText)
            msElement = xmlDoc.createElement('ms')
            frameElement.appendChild(msElement)
            msText = xmlDoc.createTextNode(str(self.timing_data.get()[i]['timing']))
            msElement.appendChild(msText)
        return xmlDoc.toprettyxml('\t', '\n')
    
    def from_xml(self, xmlStr):
        """Update the application state based on a StoryTime XML string"""
        xmlStr = xmlStr.replace('\n', '')
        xmlStr = xmlStr.replace('\t', '')
        xmlDoc = xml.dom.minidom.parseString(xmlStr)
        mainElement = xmlDoc.getElementsByTagName('storyTime')[0]
        fps = int(mainElement.getElementsByTagName('fps')[0].childNodes[0].nodeValue)
        audioPath = mainElement.getElementsByTagName('audio')[0].childNodes[0].nodeValue
        framesElement = mainElement.getElementsByTagName('frames')[0]
        images = []
        times = []
        for frameElement in framesElement.childNodes:
            images.append(frameElement.childNodes[0].childNodes[0].nodeValue)
            times.append(int(frameElement.childNodes[1].childNodes[0].nodeValue))
        self.fps.set(fps)
        self.images.set(images)
        self.times.set(times)
        self.audioPath.set(audioPath)       