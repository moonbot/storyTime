"""
controller.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""


from models import ImageCollectionModel, RecorderModel, RecordingModel
from models import *
from PySide.QtCore import *
from PySide.QtGui import *
import audio
import logging
import os
import utils

LOG = logging.getLogger('storyTime.controllers')

FPS_OPTIONS = {
    24:'Film (24 fps)',
    25:'PAL (25 fps)',
    30:'NTSC (30 fps)',
    48:'Show (48 fps)',
    50:'PAL Field (50 fps)',
    60:'NTSC Field (60 fps)',
}


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
            try:
                return QObject.eventFilter(self, obj, event)
            except:
                return False

    def keyPressEvent(self, event):
        return False
    
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
            self.handlePaths(paths)
        return True


class StoryTimeWindow(object):
    """
    The Main Story Time Window. Loads and attaches each of the main control
    widgets and connects them to a model.
    """
    
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StoryTimeWindow, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    @staticmethod
    def instance():
        return StoryTimeWindow._instance
    
    def __init__(self, parent=None):
        self.ui = utils.loadUi('views/main.ui', None)
        self.ui.setWindowTitle('Story Time')
        self.ui.setFocusPolicy(Qt.StrongFocus)
        self.ui.setAcceptDrops(True)
        self.ui.show()
        
        self._imageModel = ImageCollectionModel(self.ui)
        self._recordingModel = RecordingModel(self.ui)
        self._recorderModel = RecorderModel(self._imageModel, self._recordingModel, self.ui)
        
        # ImageViews
        # current image
        self.curImageView = ImageView(self.ui)
        self.curImageView.setModel(self._imageModel, self._imageModel.maps.curImage)
        self.ui.layoutCurImage.addWidget(self.curImageView)
        # prev image
        self.prevImageView = ImageView(self.ui)
        self.prevImageView.setModel(self._imageModel, self._imageModel.maps.prevImage)
        self.ui.layoutPrevImage.addWidget(self.prevImageView)
        # prev image
        self.nextImageView = ImageView(self.ui)
        self.nextImageView.setModel(self._imageModel, self._imageModel.maps.nextImage)
        self.ui.layoutNextImage.addWidget(self.nextImageView)
        # hide next/prev by default
        self.setImageViewVisible('prev', False)
        self.setImageViewVisible('next', False)
        # image slider to control the image collection model
        self.imageSlider = ImageSlider(self.ui)
        self.imageSlider.setModel(self._imageModel)
        self.imageSlider.ui.PrevImageCheck.toggled.connect(self.setPrevImageViewVisible)
        self.imageSlider.ui.NextImageCheck.toggled.connect(self.setNextImageViewVisible)
        self.ui.layoutControls.addWidget(self.imageSlider)
        
        
        # RecorderView
        self.recorderView = RecorderView(self.ui)
        self.recorderView.setModel(self._recorderModel)
        self.imageSlider.imageChanged.connect(self.recorderView.recordFrame)
        self.ui.layoutControls.addWidget(self.recorderView)
        
        
        # RecordingView
        self.recordingView = RecordingView(self.ui)
        self.recordingView.setModel(self._recordingModel)
        self.ui.layoutControls.addWidget(self.recordingView)
        
        
        # setup key press eater
        self.eventEater = EventEater()
        self.eventEater.keyPressEvent = self.keyPressEvent
        self.eventEater.handlePaths = self.loadPaths
        self.ui.installEventFilter(self.eventEater)
        self.imageSlider.installEventFilter(self.eventEater)
        self.recorderView.installEventFilter(self.eventEater)
        
        # build some dynamic menus
        self.buildAudioInputsMenu()
        self.ui.menuFPS.setEnabled(False)
        # hookup menu actions
        self.ui.menuFile.aboutToShow.connect(self.fileMenuAboutToShow)
        self.ui.actionNewRecording.triggered.connect(self._recordingModel.newRecording)
        self.ui.actionOpenRecording.triggered.connect(self.openRecording)
        self.ui.actionSaveRecordingAs.triggered.connect(self.saveRecordingAs)
        self.ui.actionExportMovie.triggered.connect(self.exportMovie)
        self.ui.actionExportForEditing.triggered.connect(self.exportForEditing)
        self.ui.actionOpenStoryTimeDir.triggered.connect(self.openStoryTimePath)
        self.ui.actionImportImages.triggered.connect(self.importImages)
        self.ui.actionClearImages.triggered.connect(self._imageModel.clearImages)
        self.ui.actionNewRecording.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_N))
        self.ui.actionOpenRecording.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_O))
        self.ui.actionSaveRecordingAs.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_S))
        self.ui.actionExportMovie.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_M))
        self.ui.actionExportForEditing.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_E))
        self.ui.actionImportImages.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_I))
    
    def setPrevImageViewVisible(self, visible):
        self.setImageViewVisible('prev', visible)
    
    def setNextImageViewVisible(self, visible):
        self.setImageViewVisible('next', visible)
    
    def setImageViewVisible(self, which, visible):
        index = {'prev':0, 'cur':1, 'next':2}[which]
        if not hasattr(self, '{0}ImageView'.format(which)):
            return
        view = getattr(self, '{0}ImageView'.format(which))
        view.setVisible(visible)
        self.ui.layoutImageViews.setStretch(index, int(visible))
    
    def buildAudioInputsMenu(self):
        # TODO: Implement
        return
        self.ui.menuAudioInputDevices.clear()
        self.ui.audioInputGroup = QActionGroup(self.ui)
        self.ui.audioInputGroup.triggered.connect(self.audioInputGroupTriggered)
        devices = audio.inputDevices()
        if len(devices) > 0:
            for d in devices:
                action = QAction(d['name'], self.ui)
                action.setData(d['index'])
                action.setCheckable(True)
                if d['index'] == self._model.audioInputDeviceIndex:
                    action.setChecked(True)
                self.ui.menuAudioInputDevices.addAction(action)
                self.ui.audioInputGroup.addAction(action)
        else:
            # no input devices found
            action = QAction('(No Input Devices)', self.ui)
            action.setEnabled(False)
            self.ui.menuAudioInputDevices.addAction(action)
        # insert separator and refresh button
        self.ui.menuAudioInputDevices.addSeparator()
        action = QAction('Refresh', self.ui)
        action.triggered.connect(self.buildAudioInputsMenu)
        self.ui.menuAudioInputDevices.addAction(action)
    
    def updateAudioInputsMenu(self):
        for action in self.ui.audioInputGroup.actions():
            checked = action.data() == self._model.audioInputDeviceIndex
            action.setChecked(checked)
    
    def audioInputGroupTriggered(self):
        value = self.ui.audioInputGroup.checkedAction().data()
        index = self._model.index(column=Mappings.audioInputDeviceIndex)
        self._model.setData(index, value)
    
    def keyPressEvent(self, event):
        # set the image index data the same way a mapping would
        if event.key() in (Qt.Key_Space, Qt.Key_Period, Qt.Key_Right, Qt.Key_Down):
            # update time and frame
            value = self._imageModel.imageIndex + 1
            self._imageModel.setDataForMapping(self._imageModel.imageIndex, value)
            return True
        if event.key() in (Qt.Key_Backspace, Qt.Key_Comma, Qt.Key_Left, Qt.Key_Up):
            # update time and frame
            value = self._imageModel.imageIndex - 1
            self._imageModel.setDataForMapping(self._imageModel.imageIndex, value)
            return True
        
        # some time slider hotkeys
        if event.key() == Qt.Key_R:
            self.recorderView.record()
            return True
        if event.key() == Qt.Key_P:
            self.recorderView.togglePlayback()
            return True
        if event.key() == Qt.Key_N:
            self.newRecording()
            return True
        if event.key() == Qt.Key_BracketRight:
            self.imageSlider.ui.NextImageCheck.toggle()
            return True
        if event.key() == Qt.Key_BracketLeft:
            self.imageSlider.ui.PrevImageCheck.toggle()
            return True
        
        return False
    
    def fileMenuAboutToShow(self):
        hasRecording = self._model.recordingCount > 0
        self.ui.actionSaveRecordingAs.setEnabled(hasRecording)
        self.ui.actionExportMovie.setEnabled(hasRecording)
        self.ui.actionExportForEditing.setEnabled(hasRecording)
    
    def openStoryTimePath(self):
        dir_ = self._model.getStoryTimePath()
        if os.path.isdir(dir_):
            utils.openDir(dir_)
    
    def loadPaths(self, paths):
        self._imageModel.loadPaths(paths)
    
    def openRecording(self):
        caption = 'Open Story Time Recording...'
        f = QFileDialog.getOpenFileName(
            self.ui,
            caption=caption,
            dir=self._model.getStoryTimePath(),
            filter='XML files (*.xml)',
        )[0]
        self._model.openRecording(f)
    
    def saveRecordingAs(self):
        caption = 'Save Story Time Recording...'
        f = self.getSaveDestination(caption)
        if f is not None:
            self._model.saveRecording(f)
            utils.openDir(os.path.dirname(f))
    
    def exportMovie(self):
        caption = 'Export Movie...'
        file = self.getSaveDestination(caption, filter='MOV files (*.mov)')
        if file is not None:
            progress = QProgressDialog('Exporting Movie...', 'Cancel', 0, 100, self.ui)
            progress.setWindowModality(Qt.WindowModal)
            self._model.exportMovie(file, progress=progress)
    
    def exportForEditing(self):
        caption = 'Export XML for Editing...'
        # get platform
        msgBox = QMessageBox(self.ui)
        msgBox.setText("Export XML for Editing...")
        msgBox.setInformativeText("Which platform?")
        winButton = msgBox.addButton('Windows', QMessageBox.ActionRole)
        macButton = msgBox.addButton('Mac', QMessageBox.ActionRole)
        abortButton = msgBox.addButton(QMessageBox.Cancel)

        msgBox.exec_()
        btn = msgBox.clickedButton()
        if btn == winButton:
            platform = 'win32'
        elif btn == macButton:
            platform = 'darwin'
        else:
            return
        
        file = self.getSaveDestination(caption)
        if file is not None:
            self._model.exportRecording(file, platform)
            utils.openDir(os.path.dirname(file))
    
    def importImages(self):
        caption = 'Import Image(s)'
        files = QFileDialog.getOpenFileNames(
            self.ui,
            caption=caption,
        )
        if len(files) > 0 and len(files[0]) > 0:
            self.loadPaths(files[0])
            LOG.debug('Imported {0}'.format(files[0]))
    
    def getSaveDestination(self, caption, filter='XML files (*.xml)', **kwargs):
        files = QFileDialog.getSaveFileName(
            self.ui,
            caption=caption,
            filter=filter,
            **kwargs
        )
        return files[0] if len(files[0]) > 0 else None
    
    def featureNotDone(self):
        msgBox = QMessageBox(self.ui)
        msgBox.setText('This feature is not done yet...')
        msgBox.setDefaultButton(QMessageBox.Ok)
        msgBox.exec_()


class ImageView(QWidget):
    """
    The image viewing widget for Story Time. Contains three graphics views
    for displaying the current, previous, and next images.
    """
    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)
        self.ui = utils.loadUi('views/imageView.ui', self)
        self._dataMapper = QDataWidgetMapper()
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

    def setModel(self, model, map):
        self._model = model
        self._dataMapper.setModel(model)
        self.ui.GraphicsPixmapItem = self.addPixmapItem(self.ui.GraphicsView)
        self._dataMapper.addMapping(self, map, 'pixmap')
        self._dataMapper.toFirst()
    
    def resizeEvent(self, event=None):
        self.ui.GraphicsView.fitInView(self.ui.GraphicsView.scene().itemsBoundingRect(), Qt.KeepAspectRatio)



class ImageSlider(QWidget):
    """
    The ImageSlider widget for Story Time. Contains a slider that controls
    which image is currently displayed, as well as labels providing information
    about the current image path as well as how many images there are.
    """
    
    imageChanged = Signal(str)
    
    def __init__(self, parent=None):
        super(ImageSlider, self).__init__(parent)
        #self.setupUi(self)
        self.ui = utils.loadUi('views/imageSlider.ui', self)
        self._dataMapper = QDataWidgetMapper()
        
        self.ui.ImageSlider.valueChanged.connect(self.imageSliderChanged)
    
    def imageSliderChanged(self):
        print('IMAGE CHANGED {0}'.format(self._model.curImagePath))
        self._dataMapper.submit()
        self.imageChanged.emit(self._model.curImagePath)
    
    def getSliderMaximum(self):
        return self.ui.ImageSlider.maximum()
    def setSliderMaximum(self, value):
        self.ui.ImageSlider.setMaximum(max(value - 1, 0))
        self.ui.ImageSliderProgress.repaint()
    sliderMaximum = Property('int', getSliderMaximum, setSliderMaximum)
    
    def setModel(self, model):
        self._model = model
        self.ui.CacheImagesBtn.clicked.connect(self._model.cacheAllImages)
        self.ui.ClearCacheBtn.clicked.connect(self._model.clearCache)
        self._dataMapper.setModel(model)
        self._dataMapper.addMapping(self.ui.ImagePath, model.maps.curImagePath, 'text')
        self._dataMapper.addMapping(self.ui.ImageSlider, model.maps.imageIndex, 'sliderPosition')
        self._dataMapper.addMapping(self, model.maps.count, 'sliderMaximum')
        #self._dataMapper.addMapping(self.ui.ImageSliderLabel, Mappings.curImageIndexLabel, 'text')
        self._dataMapper.toFirst()
        
    
    def installEventFilter(self, filter):
        # install the event filter on all appropriate objects
        self.ui.ImageSlider.installEventFilter(filter)
        self.ui.CacheImagesBtn.installEventFilter(filter)
        self.ui.ClearCacheBtn.installEventFilter(filter)



class RecordingView(QWidget):
    """
    The RecordingView widget for StoryTime. Controls/displays the current list
    of recordings. 
    """
    def __init__(self, parent=None):
        super(RecordingView, self).__init__(parent)
        self.ui = utils.loadUi('views/recordingsView.ui', self)
        self.ui.tableView.verticalHeader().setMovable(True)
        self.ui.NewBtn.clicked.connect(StoryTimeWindow.instance().newRecording)
    
    def setModel(self, model):
        self._model = model
        self.ui.tableView.setModel(model)       
        self.ui.tableView.selectionModel().currentChanged.connect(self.setSelection)
    
    def setSelection(self, current):
        LOG.debug('current selection: {0} {1}'.format(current.row(), current.column()))
        StoryTimeWindow.instance().timeSlider.setModelIndex(current)
        
    def doubleClicked(self, index):
        pass
    



class RecorderView(QWidget):
    """
    The Recorder widget for Story Time. Controls/displays the current
    playback state of a recording with a time slider and playback controls.
    """
    def __init__(self, parent=None):
        super(RecorderView, self).__init__(parent)
        #self.setupUi(self)
        self.ui = utils.loadUi('views/timeSlider.ui', self)
        self._dataMapper = QDataWidgetMapper()
        self._displayDataMapper = QDataWidgetMapper()
        
        self.ui.timeSlider.valueChanged.connect(self._dataMapper.submit)
        self.ui.audioCheck.toggled.connect(self._dataMapper.submit)
        self.ui.play.clicked.connect(self.play)
        self.ui.record.clicked.connect(self.record)
    
    def record(self):
        if self._model.isRecording or self._model.isPlaying:
            self.stop()
        else:
            self._model.record()
    
    def play(self):
        self._model.play()
    
    def stop(self):
        self._model.stop()
    
    def togglePlayback(self):
        if self._model.isRecording or self._model.isPlaying:
            self.stop()
        else:
            self.play()
    
    def recordFrame(self, imagePath=None):
        if imagePath is None:
            self._model.recordCurrentFrame
        else:
            self._model.recordFrame(imagePath)
    
    def toggleTimeDisplay(self):
        self._displayDataMapper.itemDelegate().toggleTimeDisplay()
        self._displayDataMapper.revert()
    
    def setModel(self, model):
        self._model = model
        
        self._dataMapper.setModel(model)
        self._dataMapper.addMapping(self.ui.audioCheck, model.maps.audioEnabled, 'checked')
        self._dataMapper.addMapping(self.ui.timeSlider, model.maps.frame, 'sliderPosition')
        self._dataMapper.toFirst()
        
        self._displayDataMapper.setModel(model)
        self._displayDataMapper.setItemDelegate(RecorderViewDisplayDelegate(self))
        self._displayDataMapper.addMapping(self.ui.name, model.maps.name)
        self._displayDataMapper.addMapping(self.ui.duration, model.maps.duration)
        self._displayDataMapper.addMapping(self.ui.imageCount, model.maps.imageCount)
        self._displayDataMapper.addMapping(self.ui.fps, model.maps.fps)
        self._displayDataMapper.addMapping(self.ui.timeSlider, model.maps.timelineDuration)
        self._displayDataMapper.addMapping(self.ui.timeDisplay, model.maps.frame)
        self._displayDataMapper.toFirst()
        self.ui.timeDisplay.clicked.connect(self.toggleTimeDisplay)
    
    def installEventFilter(self, filter):
        # install the event filter on all appropriate objects
        self.ui.timeSlider.installEventFilter(filter)
        self.ui.timeDisplay.installEventFilter(filter)
        self.ui.audioCheck.installEventFilter(filter)
        self.ui.play.installEventFilter(filter)
        self.ui.record.installEventFilter(filter)


class RecorderViewDisplayDelegate(QItemDelegate):
    """
    Remaps incoming times/durations to frames or timecodes.
    
    time, frame, timelineDuration,
    isRecording, isPlaying,
    audioEnabled, videoEnabled,
    name, duration, imageCount, fps
    """
    
    displayTimeInFrames = False
    
    def toggleTimeDisplay(self):
        self.displayTimeInFrames = not self.displayTimeInFrames
    
    def imageCountLabel(self, count):
        if count == 0:
            return 'no images'
        elif count == 1:
            return '1 image'
        elif count > 1:
            return '{0} images'.format(count)
    
    def setEditorData(self, editor, index):
        if index.column() == 1: # frame
            fps = index.model().index(column=10).data()
            if fps is not None:
                time = index.data()
                if not self.displayTimeInFrames:
                    time = utils.getTimecode(time, fps)
                editor.setText(str(time))
        
        elif index.column() == 2: # timeline duration
            fps = index.model().index(column=10).data()
            frames = int(index.data() * fps)
            editor.setMaximum(frames)
            editor.setTickInterval(fps)
        
        elif index.column() == 7: # name
            editor.setText(index.data())
        
        elif index.column() == 8: # duration
            fps = index.model().index(column=10).data()
            if fps is not None:
                time = utils.getTimecode(int(index.data() * fps), fps)
                editor.setText(time)
        
        elif index.column() == 9: # imageCount
            editor.setText(self.imageCountLabel(index.data()))
    
    def setModelData(self, editor, model, index):
        pass
        
    def updateIsPlaying(self, isPlaying):
        # record button state
        img = 'images/{0}.png'.format('stopBtn' if isPlaying else 'recordBtn')
        self.ui.RecordBtn.setIcon(QIcon(img))
        # enable/disable controls
        setVisuallyEnabled(self.ui.PlayBtn, not isPlaying)
        setVisuallyEnabled(self.ui.NewBtn, not isPlaying)
        setVisuallyEnabled(self.ui.AudioCheck, not isPlaying)
        setVisuallyEnabled(self.ui.RecordingName, not isPlaying)
        setVisuallyEnabled(self.ui.RecordingImageCount, not isPlaying)
        setVisuallyEnabled(self.ui.RecordingImageCountLabel, not isPlaying)
        setVisuallyEnabled(self.ui.RecordingDurationDisplay, not isPlaying)
    
    def updateIsRecording(self, isRecording):
        # bg color
        style = 'background-color: rgb{0};'.format( (60, 25, 25) if isRecording else (40, 40, 40) )
        self.ui.MainFrame.setStyleSheet(style)
        # enable/disable controls
        self.ui.TimeSlider.setEnabled(not isRecording)


def setVisuallyEnabled(control, enabled):
    style = '' if enabled else 'color: rgb(120, 120, 120);'
    control.setEnabled(enabled)
    control.setStyleSheet(style)


