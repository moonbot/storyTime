import sys, os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qt_ui import Ui_MainWindow
from countdown import Ui_Dialog
from storyTime.gui import StoryTimeControl
from storyTime import utils

#LOG = get_log(__name__)

BUTTON_DEACTIVATE = 'QPushButton { background-color: rgb(70,70,70) }'
BUTTON_ACTIVATE = 'QPushButton { background-color: rgb(255,125,125) }'

def run_gui(**kwargs):
    """Create an instance of the sync gui and show it."""
    #LOG.debug('Initializing StoryTime Gui...')
    app = QApplication(sys.argv)
    app.setStyle('Plastique')
    win = StoryView()
    win.show()
    app.exec_()
    
    
class CountdownDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.hoursText.setText(QString('0'))
        self.ui.minutesText.setText(QString('0'))
        self.ui.secondsText.setText(QString('0'))
        self.ui.hoursText.setInputMask(QString('00'))
        self.ui.minutesText.setInputMask(QString('00'))
        self.ui.secondsText.setInputMask(QString('00'))
        
    def get_time(self):
        """Return the total number of milliseconds specified by the dialog"""
        hours = minutes = seconds = 0
        try:
            hours = int(self.ui.hoursText.text())
        except: pass
        try:
            minutes = int(self.ui.minutesText.text())
        except: pass
        try:
            seconds = int(self.ui.secondsText.text())
        except: pass
        return {'hours':hours, 'minutes':minutes, 'seconds':seconds}


class StoryView(QMainWindow, StoryTimeControl):
    oldHeight = 0
    curImage = None
    prevTimer = None
    startTime = 0
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        # load ui class
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('StoryTime')
        self.center_window()
        # init and connect to model
        self.init_model()
        self.observe_model()
        # init timers
        self.timer = QTime()
        self.timer.start()
        self.timerEvent = self.playTimerEvent
        self.time = QTime()
        self.time.start()
        self.dispTimer = QTimer()
        self.dispTimer.timerEvent = self.dispTimerEvent
        # init scene
        self.scene = QGraphicsScene()
        self.ui.graphicsView_2.setScene(self.scene)
        # allow file drag and drop
        self.setAcceptDrops(True)
        self.ui.graphicsView_2.setAcceptDrops(True)
        self.ui.graphicsView_2.dragEnterEvent = self.dragEnterEvent
        self.ui.graphicsView_2.dragMoveEvent = self.dragMoveEvent
        self.ui.graphicsView_2.dropEvent = self.dropEvent
        # add keyboard shortcuts
        self.ui.actionOpen.setShortcut(QKeySequence.Open)
        self.ui.actionImport_Image_Sequence.setShortcut(QKeySequence.Italic)
        self.ui.actionSave.setShortcut(QKeySequence.Save)
        self.ui.actionSave_As.setShortcut(QKeySequence.SaveAs)
        # group fps options
        fpsGroup = QActionGroup(self)
        self.ui.action24.setActionGroup(fpsGroup)
        self.ui.action25.setActionGroup(fpsGroup)
        self.ui.action30.setActionGroup(fpsGroup)
        self.ui.action48.setActionGroup(fpsGroup)
        self.ui.action50.setActionGroup(fpsGroup)
        self.ui.action60.setActionGroup(fpsGroup)
        self.ui.actionCustom.setActionGroup(fpsGroup)
        #Ugly fix to get menu thingies working
        #TODO: Get rid of this
        self.connect(self.ui.actionOpen, SIGNAL("triggered()"), self.cb_open)
        self.connect(self.ui.actionImport_Image_Sequence, SIGNAL("triggered()"), self.cb_import_sequence)
        self.connect(self.ui.actionImport_Directory, SIGNAL("triggered()"), self.cb_import_directory)
        self.connect(self.ui.actionSave, SIGNAL("triggered()"), self.cb_save)
        self.connect(self.ui.actionSave_As, SIGNAL("triggered()"), self.cb_save)
        self.connect(self.ui.actionExport_To_FCP, SIGNAL("triggered()"), self.cb_save_as)
        self.connect(self.ui.actionExport_To_Premiere, SIGNAL("triggered()"), self.cb_export_premiere)
        
    # Inherited View Functions
    # ------------------------
        
    def view_browse_open(self, caption):
        return str(QFileDialog.getOpenFileName(self, QString(caption)))
    
    def view_browse_open_dir(self, caption):
        return str(QFileDialog.getExistingDirectory(self, QString(caption)))
    
    def view_browse_save_as(self, caption):
        return str(QFileDialog.getSaveFileNameAndFilter(
                self, caption=QString(caption),
                directory=QString('C:\\'),
                filter=QString('XML files (*.xml)'))[0])
    
    def view_update_timer(self):
        return self.timer.restart()
    
    def view_start_timer(self, ms):
        self.prevTimer = self.startTimer(ms)
        
    def view_start_disp_timer(self):
        self.dispTimer.stop()
        self.startTime = self.time.elapsed()
        self.dispTimer.start(self.UPDATE_INTERVAL)
        
    def view_stop_disp_timer(self):
        self.dispTimer.stop()
    
    def view_query_custom_fps(self):
        fpsData = QInputDialog.getInt(
                    self, QString('Custom...'),
                    QString('Enter Custom Fps'),
                    self.fps.get(), 0 , 1000, 1)
        if fpsData[0]:
            return int(fpsData[0])
        
    def view_query_countdown_time(self):
        countdownDialog = CountdownDialog(self)
        if countdownDialog.exec_():
            return countdownDialog.get_time()
        
    def view_get_image_formats(self):
        imageformats = []
        for imageformat in QImageReader.supportedImageFormats():
            imageformats.append('.' + str(imageformat))
        return imageformats
    
    def center_window(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
                  (screen.height()-size.height())/2)
        
    def set_button_state(self, button, state, name):
        if state == self.BUTTON_STATES.ON:
            button.setStyleSheet(BUTTON_ACTIVATE)
            button.setText(QString('Stop'))
            button.setEnabled(True)
            self.ui.timingBox.setEnabled(False)
            self.ui.audioBox.setEnabled(False)
        elif state == self.BUTTON_STATES.OFF:
            button.setStyleSheet(BUTTON_DEACTIVATE)
            button.setText(QString(name))
            button.setEnabled(True)
            self.ui.timingBox.setEnabled(True)
            self.ui.audioBox.setEnabled(True)
        elif state == self.BUTTON_STATES.DISABLED:
            button.setStyleSheet(BUTTON_DEACTIVATE)
            button.setText(QString(name))
            button.setEnabled(False)
        button.clearFocus()
        
    # Event Functions
    # ---------------
        
    def keyPressEvent(self, event):
        if event.key()==Qt.Key_Space or event.key()==Qt.Key_Right:
            self.ctl_inc_frame()
        elif event.key()==Qt.Key_Backspace or event.key()==Qt.Key_Left:
            self.ctl_dec_frame()
            
    def resizeEvent(self, event):    	
    	# if len(self.images.get()) != 0:
    		# dScreen = self.ui.graphicsView_2.geometry()
    		# if dScreen.height() != self.oldHeight:
		        # print('resizing')
			# pixmap = QPixmap(self.images.get()[0])
			# pixmap.scaledToHeight(dScreen.height(), Qt.FastTransformation)
			# self.curImage = QGraphicsPixmapItem(pixmap)
			# displayWidth = pixmap.width()
			# displayHeight = pixmap.height()
			# print 'displayWidth: ' + str(displayWidth)
			# print 'dScreen width: ' + str(dScreen.width())
			# print 'displayHeight: ' + str(displayHeight)
			# print 'dScreen Height: ' + str(dScreen.height()) + '\n'
			# self.curImage.scale(2.0, 2.0)
			# self.curImage.setTransformationMode(Qt.FastTransformation)
			# displayWidth = pixmap.width()
			# displayHeight = pixmap.height()
			# imgScale = 1.0 
			# print 'displayWidth: ' + str(displayWidth)
			# print 'dScreen width: ' + str(dScreen.width())
			# print 'displayHeight: ' + str(displayHeight)
			# print 'dScreen Height: ' + str(dScreen.height()) + '\n'
			# while(displayWidth > dScreen.width() or
			#     displayHeight > dScreen.height()):
			#     displayWidth /= 2
			#     displayHeight /= 2
			#     imgScale /= 2
			# print 'displayHeight: ' + str(displayHeight)
			# print 'displayWidth: ' + str(displayWidth)		
			# self.curImage.scale(imgScale, imgScale)
			# self.curImage.setTransformationMode(Qt.FastTransformation)
			# self.scene.addItem(self.curImage)
			# self.ui.graphicsView_2.setFixedSize(displayWidth, displayHeight)
			# self.setGeometry(QRect(1,1,1,1))
			# print('resized')
	self.center_window()
        
    	
	#self.center_window()
    	#size = self.geometry()
    	#dScreen = QDesktopWidget().screenGeometry()
    	#self.ui.graphicsView_2.setFixedSize(dScreen.width()-20,dScreen.height()-5)
    	#self.setGeometry(QRect(1,1,1,1))

    def playTimerEvent(self, event):
        self.killTimer(self.prevTimer)
        self.ctl_update_playback()
        
    def dispTimerEvent(self, event):
        self.ctl_update_timecode(self.time.elapsed() - self.startTime)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            paths = []
            for url in event.mimeData().urls():
                paths.append(str(url.toLocalFile()))
            self.ctl_process_dropped_paths(paths)
        
    # Observer functions
    # ------------------
    
    def ob_recording(self):
        self.set_button_state(self.ui.recordBtn, self.recording.get(), "Record")
    
    def ob_playing(self):
        self.set_button_state(self.ui.playBtn, self.playing.get(), "Play")
    
    def ob_cur_frame(self):
        self.ui.timeSlider.setValue(self.curFrame.get())
        totalImages = len(self.timing_data.get())
        curFrameStr = utils.fmt_leading_zeroes(self.curFrame.get(), len(str(totalImages)))
        label = '{0}/{1}'.format(curFrameStr, totalImages)
        self.ui.timeLabel.setText(QString(label))
        pixmap = QPixmap(self.timing_data.get()[self.curFrame.get() - 1]['image'])
        self.curImage.setPixmap(pixmap)
    
    def ob_images(self):
        """Initialize the graphics view and load the first image"""
        pixmap = QPixmap(self.images.get()[0])
        self.curImage = QGraphicsPixmapItem(pixmap)
        displayWidth = pixmap.width()
        displayHeight = pixmap.height()
        imgScale = 1.0
        dScreen = QDesktopWidget().screenGeometry()
        while(displayWidth > dScreen.width() or
              displayHeight > dScreen.height()):
            displayWidth /= 1.5
            displayHeight /= 1.5
            imgScale /= 1.5
	self.curImage.scale(imgScale, imgScale)
        self.curImage.setTransformationMode(Qt.FastTransformation)
        self.scene.addItem(self.curImage)
        self.ui.graphicsView_2.setFixedSize(displayWidth+5, displayHeight+5)
        self.setGeometry(QRect(1,1,1,1))
        self.center_window()
        self.ui.timeSlider.setRange(1,len(self.images.get()))
        
    
    def ob_fps_options(self):
        self.ui.actionCustom.setText(QString(self.fpsOptions.get()[-1][0]))

    def ob_timecode(self):
        tc = self.timecode.get()
        sec = (tc/1000)%60
        min = (tc/(60*1000))%60
        hours = tc/(60*60*1000)
        self.ui.curTimeLabel.setText(QTime(hours, min, sec).toString('hh:mm:ss'))
        
    # UI Callbacks
    # ------------
    
    @pyqtSlot(name='on_actionOpen_triggered')
    def cb_open(self):
        self.ctl_open()
    
    @pyqtSlot(name='on_actionImport_Image_Sequence_triggered')
    def cb_import_sequence(self):
        self.ctl_import_from_sequence()
        
    @pyqtSlot(name='on_actionImport_Directory_triggered')
    def cb_import_directory(self):
        self.ctl_import_directory()
        
    @pyqtSlot(name='on_actionExport_To_FCP_triggered')
    def cb_export_fcp(self):
        self.ctl_export_fcp()
        
    @pyqtSlot(name='on_actionExport_To_Premiere_triggered')
    def cb_export_premiere(self):
        self.ctl_export_premiere()
    
    @pyqtSlot(name='on_actionSave_triggered')
    def cb_save(self):
        self.ctl_save()
        
    @pyqtSlot(name='on_actionSave_As_triggered')
    def cb_save_as(self):
        self.ctl_save_as()
        
    @pyqtSlot(name='on_recordBtn_clicked')
    def cb_record_clicked(self):
        self.ctl_toggle_record()
        
    @pyqtSlot(name='on_playBtn_clicked')
    def cb_play_clicked(self):
        self.ctl_toggle_play()
        
    @pyqtSlot(name='on_action24_triggered')
    def cb_24_triggered(self):
        self.ctl_change_fps(0)
        
    @pyqtSlot(name='on_action25_triggered')
    def cb_25_triggered(self):
        self.ctl_change_fps(1)
        
    @pyqtSlot(name='on_action30_triggered')
    def cb_30_triggered(self):
        self.ctl_change_fps(2)
        
    @pyqtSlot(name='on_action48_triggered')
    def cb_48_triggered(self):
        self.ctl_change_fps(3)
        
    @pyqtSlot(name='on_action50_triggered')
    def cb_50_triggered(self):
        self.ctl_change_fps(4)
        
    @pyqtSlot(name='on_action60_triggered')
    def cb_60_triggered(self):
        self.ctl_change_fps(5)
        
    @pyqtSlot(name='on_actionCustom_triggered')
    def cb_custom_triggered(self):
        self.ctl_change_fps(6)
        
    @pyqtSlot(name='on_actionSet_Recording_Countdown_triggered')
    def cb_set_recording_countdown_triggered(self):
        self.ctl_set_recording_countdown()
        
    @pyqtSlot(int, name='on_timeSlider_valueChanged')
    def cb_timeslider_valuechanged(self, value):
        self.ctl_goto_frame(value)
        
    @pyqtSlot(int, name='on_timeSlider_sliderMoved')
    def cb_timeslider_slidermoved(self, value):
        self.ctl_stop()
        
    @pyqtSlot(int, name='on_timingBox_stateChanged')
    def cb_timingbox_statechanged(self, value):
        self.ctl_toggle_record_timing(value)
        
    @pyqtSlot(int, name='on_audioBox_stateChanged')
    def cb_audiobox_statechanged(self, value):
        self.ctl_toggle_record_audio(value)