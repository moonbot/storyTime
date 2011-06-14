import sys, os

from PyQt4 import QtCore, QtGui

from qt_ui import Ui_MainWindow
from storytime.gui import StoryTimeControl

#LOG = get_log(__name__)

BUTTON_DEACTIVATE = 'QPushButton { background-color: rgb(70,70,70) }'
BUTTON_ACTIVATE = 'QPushButton { background-color: rgb(255,125,125) }'

def run_gui(**kwargs):
    """Create an instance of the sync gui and show it."""
    #LOG.debug('Initializing StoryTime Gui...')
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Plastique')
    win = StoryView()
    win.show()
    app.exec_()

class StoryView(QtGui.QMainWindow, StoryTimeControl):
    
    curImage = None
    prevTimer = None
    
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        # load ui class
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('StoryTime')
        self.center_window()
        # init and connect to model
        self.init_model()
        self.observe_model()
        # init timer
        self.timer = QtCore.QTime()
        self.timer.start()
        self.timerEvent = self.playTimerEvent
        # init scene
        self.scene = QtGui.QGraphicsScene()
        self.ui.graphicsView_2.setScene(self.scene)
        # add keyboard shortcuts
        self.ui.actionOpen.setShortcut(QtGui.QKeySequence.Open)
        #Ctrl+I
        self.ui.actionImport_Image_Sequence.setShortcut(QtGui.QKeySequence.Italic)
        self.ui.actionSave.setShortcut(QtGui.QKeySequence.Save)
        self.ui.actionSave_As.setShortcut(QtGui.QKeySequence.SaveAs)
        
    def observe_model(self):
        self.recording.add_observer(self.ob_recording)
        self.playing.add_observer(self.ob_playing)
        self.curFrame.add_observer(self.ctl_ob_cur_frame)
        self.curFrame.add_observer(self.ob_cur_frame)
        self.images.add_observer(self.ob_images)
        self.fpsOptions.add_observer(self.ob_fps_options)
        
    def view_browse_open(self, caption):
        return str(QtGui.QFileDialog.getOpenFileName(self, QtCore.QString(caption)))
    
    def view_browse_save_as(self):
        return str(QtGui.QFileDialog.getSaveFileNameAndFilter(
                self, caption=QtCore.QString('Save As...'),
                directory=QtCore.QString('C:\\'),
                filter=QtCore.QString('XML files (*.xml)'))[0])
    
    def view_update_timer(self):
        return self.timer.restart()
    
    def view_start_timer(self, ms):
        self.prevTimer = self.startTimer(ms)
    
    def view_query_custom_fps(self):
        fpsData = QtGui.QInputDialog.getInt(
                    self, QtCore.QString('Custom...'),
                    QtCore.QString('Enter Custom Fps'),
                    self.fps.get(), 0 , 1000, 1)
        if fpsData[0]:
            return int(fpsData[0])
    
    def center_window(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
                  (screen.height()-size.height())/2)
        
    def set_button_state(self, button, state, name):
        if state == self.BUTTON_STATES.ON:
            button.setStyleSheet(BUTTON_ACTIVATE)
            button.setText(QtCore.QString('Stop'))
            button.setEnabled(True)
        elif state == self.BUTTON_STATES.OFF:
            button.setStyleSheet(BUTTON_DEACTIVATE)
            button.setText(QtCore.QString(name))
            button.setEnabled(True)
        elif state == self.BUTTON_STATES.DISABLED:
            button.setStyleSheet(BUTTON_DEACTIVATE)
            button.setText(QtCore.QString(name))
            button.setEnabled(False)
        button.clearFocus()
        
    def keyPressEvent(self, event):
        if event.key()==QtCore.Qt.Key_Space or event.key()==QtCore.Qt.Key_Right:
            self.ctl_inc_frame()
        elif event.key()==QtCore.Qt.Key_Backspace or event.key()==QtCore.Qt.Key_Left:
            self.ctl_dec_frame()
            
    def resizeEvent(self, event):
        self.center_window()
        
    def playTimerEvent(self, event):
        self.killTimer(self.prevTimer)
        self.ctl_update_playback()
            
    #UI Callbacks
    @QtCore.pyqtSlot(name='on_actionOpen_triggered')
    def cb_open(self):
        self.ctl_open()
    
    @QtCore.pyqtSlot(name='on_actionImport_Image_Sequence_triggered')
    def cb_import_sequence(self):
        self.ctl_import_from_sequence()
        
    @QtCore.pyqtSlot(name='on_actionImport_Directory_triggered')
    def cb_import_directory(self):
        self.ctl_import_directory()
        
    @QtCore.pyqtSlot(name='on_actionExport_To_FCP_triggered')
    def cb_export_fcp(self):
        self.ctl_export_fcp()
    
    @QtCore.pyqtSlot(name='on_actionSave_triggered')
    def cb_save(self):
        self.ctl_save()
        
    @QtCore.pyqtSlot(name='on_actionSave_As_triggered')
    def cb_save_as(self):
        self.ctl_save_as()
        
    @QtCore.pyqtSlot(name='on_recordBtn_clicked')
    def cb_record_clicked(self):
        self.ctl_toggle_record()
        
    @QtCore.pyqtSlot(name='on_playBtn_clicked')
    def cb_play_clicked(self):
        self.ctl_toggle_play()
        
    @QtCore.pyqtSlot(int, name='on_comboBox_activated')
    def cb_combobox_activated(self, index):
        self.ctl_change_fps(index)
        
    @QtCore.pyqtSlot(int, name='on_timeSlider_valueChanged')
    def cb_timeslider_valuechanged(self, value):
        self.ctl_goto_frame(value)
        
    @QtCore.pyqtSlot(int, name='on_timeSlider_sliderMoved')
    def cb_timeslider_slidermoved(self, value):
        self.ctl_stop()
        
    #Observer functions
    def ob_recording(self):
        self.set_button_state(self.ui.recordBtn, self.recording.get(), "Record")
    
    def ob_playing(self):
        self.set_button_state(self.ui.playBtn, self.playing.get(), "Play")
    
    def ob_cur_frame(self):
        self.ui.timeSlider.setValue(self.curFrame.get())
        label = '{0}/{1}'.format(self.curFrame.get(), len(self.images.get()))
        self.ui.timeLabel.setText(QtCore.QString(label))
        pixmap = QtGui.QPixmap(self.images.get()[self.curFrame.get() - 1])
        self.curImage.setPixmap(pixmap)
    
    def ob_images(self):
        pixmap = QtGui.QPixmap(self.images.get()[0])
        self.curImage = QtGui.QGraphicsPixmapItem(pixmap)
        displayWidth = pixmap.width()
        displayHeight = pixmap.height()
        imgScale = 1.0
        dScreen = QtGui.QDesktopWidget().screenGeometry()
        while(displayWidth > dScreen.width() or
              displayHeight > dScreen.height()):
            displayWidth /= 2
            displayHeight /= 2
            imgScale /= 2
        self.curImage.scale(imgScale, imgScale)
        self.curImage.setTransformationMode(QtCore.Qt.FastTransformation)
        self.scene.addItem(self.curImage)
        self.ui.graphicsView_2.setFixedSize(displayWidth+5, displayHeight+5)
        self.setGeometry(QtCore.QRect(1,1,1,1))
        self.center_window()
        self.ui.timeSlider.setRange(1,len(self.images.get()))
    
    def ob_fps_options(self):
        for i in range(0, len(self.fpsOptions.get())):
            self.ui.comboBox.setItemText(i, QtCore.QString(self.fpsOptions.get()[i][0]))