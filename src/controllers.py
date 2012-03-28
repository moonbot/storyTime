"""
controller.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from models import Mappings, StoryTimeModel

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import QUiLoader
#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
#from PyQt4 import uic
#Property = pyqtProperty
import logging

LOG = logging.getLogger(__name__)

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
            
        elif event.type() == QEvent.DragLeave:
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
    def __init__(self):
        #super(StoryTimeWindow, self).__init__(parent)
        #self.setupUi(self)
        self.ui = loadUi('views/main.ui')
        self.ui.show()
        
        # setup model
        self._model = StoryTimeModel(self.ui)
        
        self.imageView = ImageView(self.ui)
        self.imageView.setModel(self._model)
        self.ui.layoutImageView.addWidget(self.imageView)
        
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
        self.imageView.installEventFilter(self.eventEater)
        self.imageSlider.installEventFilter(self.eventEater)
        self.timeSlider.installEventFilter(self.eventEater)
    
    def loadPaths(self, paths):
        self._model.loadPaths(paths)
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Period, Qt.Key_Right, Qt.Key_Down):
            self._model.loadNextImage()
            return True
        if event.key() in (Qt.Key_Backspace, Qt.Key_Comma, Qt.Key_Left, Qt.Key_Up):
            self._model.loadPrevImage()
            return True



class ImageView(QWidget):
    """
    The image viewing widget for Story Time. Contains three graphics views
    for displaying the current, previous, and next images.
    """
    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)
        #self.setupUi(self)
        self.ui = loadUi('views/imageView.ui', self, True)
        self.ui.dragEnterEvent = self.dragEnterEvent
        self.ui.dragMoveEvent = self.dragMoveEvent
        self.ui.dropEvent = self.dropEvent
        self._dataMapper = QDataWidgetMapper()

        self.ui.GraphicsViewPrev.setVisible(False)
        self.ui.GraphicsViewNext.setVisible(False)


    def getPixmap(self):
        return self.ui.GraphicsPixmapItem.pixmap()
    def setPixmap(self, data):
        self.ui.GraphicsPixmapItem.setPixmap(data)
    pixmap = Property("QPixmap", getPixmap, setPixmap)

    """def getPrevPixmap(self):
        return self.ui.GraphicsPixmapItemPrev.pixmap()
    def setPrevPixmap(self, data):
        self.ui.GraphicsPixmapItemPrev.setPixmap(data)
    prevPixmap = Property("QPixmap", getPrevPixmap, setPrevPixmap)

    def getNextPixmap(self):
        return self.ui.GraphicsPixmapItemNext.pixmap()
    def setNextPixmap(self, data):
        self.ui.GraphicsPixmapItemNext.setPixmap(data)
    nextPixmap = Property("QPixmap", getNextPixmap, setNextPixmap)"""
    
    def addPixmapItem(self, graphicsView, pixmap):
        item = QGraphicsPixmapItem(pixmap)
        scene = QGraphicsScene()
        scene.addItem(item)
        graphicsView.setScene(scene)
        return item

    def setModel(self, model):
        self._model = model
        self._dataMapper.setModel(model)
        # add graphics item for each view
        self.ui.GraphicsPixmapItem = self.addPixmapItem(self.ui.GraphicsView, model.curImage)
        self._dataMapper.addMapping(self, Mappings.curImage, 'pixmap')
        self._dataMapper.toFirst()
    
    def installEventFilter(self, filter):
            # install the event filter on all appropriate objects
        self.ui.GraphicsView.installEventFilter(filter)    
        self.ui.GraphicsViewPrev.installEventFilter(filter)
        self.ui.GraphicsViewNext.installEventFilter(filter)



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
        
        QObject.connect(self.ui.ImageSlider, SIGNAL('valueChanged(int)'), self._dataMapper.submit)
    
    def setSliderMaximum(self, value):
        self.ui.ImageSlider.setMaximum(max(value - 1, 0))
    def getSliderMaximum(self):
        return self.ui.ImageSlider.maximum()
    sliderMaximum = Property('int', getSliderMaximum, setSliderMaximum)
    
    def setModel(self, model):
        self._model = model
        self._dataMapper.setModel(model)
        self._dataMapper.addMapping(self.ui.ImagePath, Mappings.curImagePath, 'text')
        self._dataMapper.addMapping(self.ui.ImageSlider, Mappings.curImageIndex, 'sliderPosition')
        self._dataMapper.addMapping(self, Mappings.imageCount, 'sliderMaximum')
        self._dataMapper.addMapping(self.ui.ImageSliderLabel, Mappings.curImageIndexLabel, 'text')
        self._dataMapper.toFirst()
        
        QObject.connect(self.ui.CacheImagesBtn, SIGNAL('clicked()'), self._model.cacheAllImages)
    
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
        
        # hide hidden controls
        self.ui.IsRecordingCheck.setVisible(False)
        self.ui.IsPlayingCheck.setVisible(False)
        
        QObject.connect(self.ui.TimeSlider, SIGNAL('valueChanged(int)'), self._dataMapper.submit)
        QObject.connect(self.ui.IsRecordingCheck, SIGNAL('toggled(bool)'), self.updateIsRecording)
        QObject.connect(self.ui.RecordBtn, SIGNAL('clicked()'), self.recordBtnClicked)
    
    def setSliderMaximum(self, value):
        self.ui.TimeSlider.setMaximum(value)
    def getSliderMaximum(self):
        return self.ui.TimeSlider.maximum()
    sliderMaximum = Property('int', getSliderMaximum, setSliderMaximum)
    
    def updateIsRecording(self, isRecording):
        # bg color
        style = 'background-color: rgb{0};'.format( (60, 25, 25) if isRecording else (40, 40, 40) )
        self.ui.MainFrame.setStyleSheet(style)
        # record button state
        img = 'images/{0}.png'.format('stopBtn' if isRecording else 'recordBtn')
        self.ui.RecordBtn.setIcon(QIcon(img))
        # enable/disable buttons
        self.ui.TimeSlider.setEnabled(not isRecording)
        setVisuallyEnabled(self.ui.PlayBtn, not isRecording)
        setVisuallyEnabled(self.ui.NewBtn, not isRecording)
        setVisuallyEnabled(self.ui.RecordingName, not isRecording)
        setVisuallyEnabled(self.ui.ImageCountDisplay, not isRecording)
        setVisuallyEnabled(self.ui.DurationDisplay, not isRecording)
        setVisuallyEnabled(self.ui.AudioCheck, not isRecording)
    
    def playBtnClicked(self):
        pass
    
    def recordBtnClicked(self):
        if self.ui.IsRecordingCheck.checkState() == Qt.Checked:
            LOG.debug('Stopping recording')
            self.ui.IsRecordingCheck.setCheckState(Qt.Unchecked)
        elif self.ui.IsPlayingCheck.checkState() == Qt.Checked:
            LOG.debug('Stopping playback')
            self.ui.IsPlayingCheck.setCheckState(Qt.Unchecked)
        else:
            LOG.debug('Recording...')
            self.ui.IsRecordingCheck.setCheckState(Qt.Checked)
    
    def setModel(self, model):
        self._model = model
        self._dataMapper.setModel(model)
        self._dataMapper.addMapping(self.ui.IsRecordingCheck, Mappings.isRecording, 'checked')
        self._dataMapper.addMapping(self.ui.TimeSlider, Mappings.curTime, 'sliderPosition')
        self._dataMapper.addMapping(self.ui.TimeDisplay, Mappings.timeDisplay, 'text')
        self._dataMapper.addMapping(self, Mappings.duration, 'sliderMaximum')
        self._dataMapper.toFirst()
        
        # connect some things to the model
        QObject.connect(self.ui.TimeDisplay, SIGNAL('clicked()'), self._model.toggleTimeDisplay)
    
    def installEventFilter(self, filter):
            # install the event filter on all appropriate objects
        self.ui.TimeSlider.installEventFilter(filter)
        self.ui.PlayBtn.installEventFilter(filter)
        self.ui.RecordBtn.installEventFilter(filter)



def setVisuallyEnabled(control, enabled):
    style = '' if enabled else 'color: rgb(120, 120, 120);'
    control.setEnabled(enabled)
    control.setStyleSheet(style)



class StoryTimeControl(object):
    
    #audioHandler = AudioHandler()
    UPDATE_INTERVAL = 500
        
    # File Handling Functions
    # -----------------------
    
    def ctl_process_dropped_paths(self, paths):
        """
        Decides what to do with paths dropped onto the file.  Possible options:
        
        Single file:
        .xml: open
        anything else: import sequence
        
        Directory:
        import directory
        
        Multiple files:
        import files as sequence
        """
        
        if len(paths) > 1:
            paths = self.filter_image_paths(paths)
            self.ctl_process_import(paths)
        else:
            ext = os.path.splitext(paths[0])[1]
            if ext == '.xml':
                with open(paths[0], 'r') as openFile:
                    self.from_xml(openFile.read())
                self.savePath.set(paths[0])
                self.audioHandler = AudioHandler(self.images.get()[0])
            elif os.path.isdir(paths[0]):
                self.ctl_process_import(utils.listdir(paths[0]))
            else:
                for imageformat in self.view_get_image_formats():
                    if imageformat == ext:
                        # TODO: implement internal version of sequences
                        LOG.warning('Import Image Sequence not yet implemented...')
                        self.ctl_process_import(paths)
    
    def ctl_open(self):
        """Browse for and open a StoryTime XML file"""
        path = self.view_browse_open('Open...')
        if path is not None and path != '':
            with open(path, 'r') as openFile:
                self.from_xml(openFile.read())
            self.savePath.set(path)
            self.audioHandler = AudioHandler(self.images.get()[0])
    
    def ctl_import_from_sequence(self):
        """Browse for and import an image sequence"""
        path = self.view_browse_open('Import Image Sequence...')
        if path is not None and path != '':
            LOG.warning('Import Image Sequence not yet implemented...')
            self.ctl_process_import(path)
            
    def ctl_import_directory(self):
        """Browse for and import an image directory"""
        path = self.view_browse_open_dir('Import Image Directory...')
        if path is not None and path != '':
            self.ctl_process_import(utils.listdir(path))
        
                
    def ctl_process_import(self, paths):
        """Update the current application state from the list of image files."""
        paths = self.filter_image_paths(paths)
        paths.sort()
        if len(paths) > 0:
            #self.times.set([1000 for x in range(0,len(self.images.get()))])
            n = 1
            for i in paths:
                self.timing_data.get().append({'timing':1000,'image':i, 'imageNum':n})
                n += 1
            self.images.set(paths)
            self.startFrame.set(1)
            self.curFrame.set(1)
            self.curImgFrame.set(1)
            self.ctl_make_audio_path()
    
    def ctl_export_premiere(self):
        """
        Export the current application state to a Final Cut Pro XML file
        formatted for Premiere.
        """
        self.ctl_process_export('Export to Premiere...', 'win')
                
    def ctl_export_fcp(self):
        """
        Export the current application state to a Final Cut Pro XML file
        formatted for Final Cut Pro
        """
        self.ctl_process_export('Export to Final Cut Pro...', 'mac')
                    
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
            
    def ctl_save(self):
        """Save the current application state to a StoryTime XML file"""
        if self.savePath.get() == '':
            self.ctl_save_as()
            return
        self.ctl_make_audio_path()
        with open(self.savePath.get(), 'w') as saveFile:
            saveFile.write(self.to_xml())
            
    def ctl_save_as(self):
        """Browse and save the current application state to a StoryTime XML file"""
        if len(self.images.get()) > 0:
            path = self.view_browse_save_as('Save As...')
            if path is not None and path != '':
                with open(path, 'w') as saveFile:
                    saveFile.write(self.to_xml())
                self.savePath.set(path)
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
            
    # Observer Functions
    # -----------------
        
    def ctl_ob_audio_path(self):
        self.audioHandler.filename = self.audioPath.get()
        
    def ctl_ob_countdown(self):
        cd = self.countdown.get()
        if cd is None:
            return
        hoursMs = cd['hours'] * 60 * 60 * 1000
        minutesMs = cd['minutes'] * 60 * 1000
        secondsMs = cd['seconds'] * 1000
        self.countdownms.set(hoursMs + minutesMs + secondsMs)
        
    def ctl_ob_cur_frame(self):
        if self.curFrame.get() < 1:
            #if len(self.timing_data.get()) > 0:
            self.curFrame.set(1)
        if self.curImgFrame.get() < 1:
            #if len(self.images.get()) > 0: 
            self.curImgFrame.set(1)
        if self.curFrame.get() > len(self.timing_data.get()):
            self.curFrame.set(len(self.timing_data.get()))
        if self.curImgFrame.get() > len(self.images.get()):
            self.curImgFrame.set(len(self.images.get()))         