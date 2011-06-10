import sys, os
import StringIO

from PyQt4 import QtCore, QtGui
from PIL import Image

from storyTime import get_log
from storyTime.gui.qt_ui import Ui_MainWindow
from storyTime.gui.fps_ui import Ui_Dialog
from storyTime.gui import StoryTimeControl
from production import sequences
from PyQt4.uic.Compiler.qtproxies import QtGui
from gui.qt import BUTTON_ACTIVATE, BUTTON_DEACTIVATE

LOG = get_log(__name__)

BUTTON_DEACTIVATE = 'QPushButton { background-color: rgb(70,70,70) }'
BUTTON_ACTIVATE = 'QPushButton { background-color: rgb(255,125,125) }'

def run_gui(**kwargs):
    """Create an instance of the sync gui and show it."""
    LOG.debug('Initializing StoryTime Gui...')
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Plastique')
    win = StoryView()
    win.show()
    app.exec_()

class StoryView(QtGui.QMainWindow, StoryTimeControl):
    
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        # center on screen
        self.centerWindow()
        # load ui class
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle('StoryTime')
        
        self.timer = QtCore.QTime()
        self.timer.start()
        
        self.ui.timeSlider.setRange(0,0)
        self.ui.timeSlider.setValue(0)
        self.ui.timeLabel.setText(QtCore.QString('0/0'))
        
        self.scene = QtGui.QGraphicsScene()
        self.ui.graphicsView_2.setScene(self.scene)
        
        self.connect(self.ui.recordBtn, QtCore.SIGNAL('clicked()'), self.recordHandler)
        self.connect(self.ui.playBtn, QtCore.SIGNAL('clicked()'), self.playHandler)
        self.connect(self.ui.timeSlider, QtCore.SIGNAL('valueChanged(int)'), self.sliderHandler)
        self.connect(self.ui.timeSlider, QtCore.SIGNAL('sliderMoved(int)'), self.sliderMovedHandler)
        self.connect(self.ui.comboBox, QtCore.SIGNAL('activated(int)'), self.fpsHandler) 
        self.connect(self.ui.actionOpen, QtCore.SIGNAL('triggered()'), self.openHandler)
        self.connect(self.ui.actionImport_Image_Sequence, QtCore.SIGNAL('triggered()'), self.importHandler)
        self.connect(self.ui.actionSave, QtCore.SIGNAL('triggered()'), self.saveHandler)
        self.connect(self.ui.actionSave_As, QtCore.SIGNAL('triggered()'), self.saveAsHandler)
        
        self.ui.actionOpen.setShortcut(QtGui.QKeySequence.Open)
        self.ui.actionImport_Image_Sequence.setShortcut(QtGui.QKeySequence.Italic)
        self.ui.actionSave.setShortcut(QtGui.QKeySequence.Save)
        self.ui.actionSave_As.setShortcut(QtGui.QKeySequence.SaveAs)
        
    def recordHandler(self):
        self.recording = not self.recording
        if self.recording:
            self.playing = False
            self.timer.start()
            self.startFrame = self.ui.timeSlider.value() - 1
            self.curFrame = self.startFrame
            self.ui.recordBtn.clearFocus()
        else:
            self.stop()
        pass
    
    def playHandler(self):
        self.playing = not self.playing
        if self.playing:
            self.ui.playBtn.clearFocus()
        else:
            self.stop()
        pass
    
    def sliderHandler(self, value):
        strLabel = '{0}/{1}'.format(value, self.ui.timeSlider.maximum())
        self.ui.timeLabel.setText(QtCore.QString(strLabel))
        try:
            if self.nextIndex == value - 1:
                self.curImage.setPixmap(self.nextPixmap)
            else:
                self.curImage.setPixmap(QtGui.QPixmap(self.imgSequence[value - 1]))
        except AttributeError:
            pass
        self.loadNextPixmap()
        
    def view_set_frame_label(self, label):
        self.ui.timeLabel.SetText(QtCore.QString(strLabel))
        
    def sliderMovedHandler(self):
        self.stop()
    
    def openHandler(self):
        self.cleanup()
        pass
            
    def view_init_sequence(self, imgSequence):
        pixmap = QtGui.QPixmap(imgSequence)
        self.curImage = QtGui.QGraphicsPixmapItem(pixmap)
        displayWidth = pixmap.width()
        displayHeight = pixmap.height()
        imgScale = 1
        dScreen = QtGui.QDesktopWidget().screenGeometry()
        while(displayWidth > dScreen.width() or
              displayHeight > dScreen.height()):
            displayWidth /= 2
            displayHeight /= 2
            imgScale /= 2
        self.curImage.scale(imgScale, imgScale)
        self.scene.addItem(self.curImage)
        self.ui.graphicsView_2.setFixedSize(displayWidth+5, displayHeight+5)
        self.centerWindow()
        self.ui.timeSlider.setRange(1,len(imgSequence))
        self.ui.timeSlider.setValue(1)
        
    def view_browse_import(self, caption):
        imgFile = str(QtGui.QFileDialog.getOpenFileName(self, QtCore.QString(caption))))
        return imgFile
    
    def view_get_data(self):
        data = {}
        data['recording'] = self.get_button_state(self.ui.recordBtn)
        data['playing'] = self.get_button_state(self.ui.playBtn)
        data['fps_index'] = self.ui.comboBox.index()
        data['cur_frame'] = self.ui.timeSlider.value()
        return data
    
    def view_set_data(self, data):
        self.ui.timeSlider.setValue(data['cur_frame'])
        
        self.set_button_state(self.ui.recordBtn, data['recording'], 'Record')
        self.set_button_state(self.ui.recordBtn, data['playing'], 'Play')
        
    def set_button_state(self, button, state, name):
        if state == self.BUTTON_STATES.ON:
            button.setStyleSheet(BUTTON_ACTIVATE)
            button.setText(QtCore.QString('Stop'))
            button.setEnabled(True)
        elif state == self.BUTTON_STATES.OFF:
            button.setStyleSheet(BUTTON_DEACTIVATE)
            button.setText(QtCore.QString(name))
            button.setEnabled(True)
        elif state == self.BUTTON_STATES.DISABLED
            button.setStyleSheet(BUTTON_DEACTIVATE)
            button.setText(QtCore.QString(name))
            button.setEnabled(False)
            
    def get_button_state(self, button):
        if button.enabled() == False:
            return self.BUTTON_STATES.DISABLED
        if button.text() == 'Stop':
            return self.BUTTON_STATES.ON
        return self.BUTTON_STATES.OFF
    
    def view_query_custom_fps(self):
        fpsData = QtGui.QInputDialog.getInt(
                    self, QtCore.QString('Custom...'),
                    QtCore.QString('Enter Custom Fps'),
                    self.fps, 0 , 1000, 1)
        if fpsData[1]:
            return fpsData[1]
        
    def view_set_fps_options(self, options):
        for i in range(0, len(options)):
            self.ui.comboBox.setItemText(i, QtCore.QString(options[i][0]))
    
    def saveHandler(self):
        pass
    
    def saveAsHandler(self):
        pass
    
    
    
    #keyPressEvents : controller or view?
    def keyPressEvent(self, event):
        if event.key()==QtCore.Qt.Key_Space:
            self.ctl_inc_frame()
        elif event.key()==QtCore.Qt.Key_Backspace:
            self.ctl_goto_frame()
            
    def resizeEvent(self, event):
        self.centerWindow()
            
    def advanceFrame(self):
        nextImage = self.ui.timeSlider.value() + 1
        if nextImage < self.ui.timeSlider.maximum():
            self.ui.timeSlider.setValue(nextImage)
            if self.recording == True:
                self.timingData[self.curFrame] = self.timer.restart()
                self.curFrame = nextImage 
        else:
            self.stop()
            if nextImage == self.ui.timeSlider.maximum():
                self.ui.timeSlider.setValue(nextImage)
                
    def loadNextPixmap(self):
        self.nextIndex = self.ui.timeSlider.value()
        if(self.nextIndex == self.ui.timeSlider.maximum()):
            self.nextPixmap = None
        else:
            self.nextPixmap = self.newPixmap(self.imgSequence[self.nextIndex])
            
    def centerWindow(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
                  (screen.height()-size.height())/2)
        
    def createFramesList(self):
        incFrames = self.timingData[:]
        total = 0
        for i in range(0, len(self.timingData)):
            total = total + self.timingData[i]
            incFrames[i] = int(total * self.fps / 1000)
        fpsFrames = incFrames[:]
        #We can ignore the value at index 0 because it's already the
        #correct value.
        for i in range(1, len(self.timingData)):
            fpsFrames[i] = incFrames[i] - incFrames[i-1]
            if fpsFrames[i] < 1:
                fpsFrames[i] = 1
        return fpsFrames
    
    def cleanup(self):
        try:
            if self.curImage is not None:
                self.scene.removeItem(self.curImage)
        except AttributeError:
            pass
        