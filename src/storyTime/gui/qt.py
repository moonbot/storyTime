import sys, os
import StringIO

from PyQt4 import QtCore, QtGui
from PIL import Image

from storyTime import get_log
from storyTime.gui.qt_ui import Ui_MainWindow
from storyTime.gui.fps_ui import Ui_Dialog
from storyTime.gui import StoryTimeControl
from production import sequences

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
            self.ui.recordBtn.setStyleSheet(BUTTON_ACTIVATE)
            self.ui.recordBtn.setText(QtCore.QString('Stop'))
            self.ui.playBtn.setEnabled(False)
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
            self.ui.playBtn.setStyleSheet(BUTTON_ACTIVATE)
            self.ui.playBtn.setText(QtCore.QString('Stop'))
            self.ui.recordBtn.setEnabled(False)
            self.recording = False
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
                self.curImage.setPixmap(self.newPixmap(self.imgSequence[value - 1]))
        except AttributeError:
            pass
        self.loadNextPixmap()
        
    def sliderMovedHandler(self):
        self.stop()
    
    def openHandler(self):
        self.cleanup()
        pass
    
    def importHandler(self):
        self.cleanup()
        imgFile = str(QtGui.QFileDialog.getOpenFileName(
                self, QtCore.QString('Import Image Sequence')))
        if imgFile is not None:
            imgFile = os.path.normpath(imgFile)
            self.imgSequence = sequences.file_sequence(imgFile)
            i = self.imgSequence.index(imgFile)
            pixmap = self.newPixmap(self.imgSequence[i])
            self.curImage = QtGui.QGraphicsPixmapItem(pixmap)
            displayWidth = pixmap.width()
            displayHeight = pixmap.height()
            self.imgScale = 1
            dScreen = QtGui.QDesktopWidget().screenGeometry()
            print str(pixmap.size())
            while (displayWidth > dScreen.width() or
                   displayHeight > dScreen.height()):
                displayWidth = displayWidth / 2;
                displayHeight = displayHeight / 2;
                self.imgScale = self.imgScale / 2;
            
            self.curImage.scale(self.imgScale, self.imgScale)
            self.scene.addItem(self.curImage)
            self.ui.graphicsView_2.setFixedSize(displayWidth+5, displayHeight+5)
            self.centerWindow()
            self.ui.timeSlider.setRange(1,len(self.imgSequence))
            self.ui.timeSlider.setValue(i+1)
            self.timingData = [1000 for x in range(0,self.ui.timeSlider.maximum())]
    
    def saveHandler(self):
        
        pass
    
    def saveAsHandler(self):
        pass
    
    def fpsHandler(self, index):
        if index == 0:
            self.fps = 24
        elif index == 1:
            self.fps = 25
        elif index == 2:
            self.fps = 30
        elif index == 3:
            self.fps = 48
        elif index == 4:
            self.fps = 50
        elif index == 5:
            self.fps = 60
        elif index == 6:
            fpsData = QtGui.QInputDialog.getInt(
                    self, QtCore.QString('Custom...'),
                    QtCore.QString('Enter Custom Fps'),
                    self.fps, 0 , 1000, 1)
            if fpsData[1]:
                self.fps = fpsData[0]
                newString = 'Custom ({0} fps)...'.format(fpsData[0])
                self.ui.comboBox.setItemText(6, QtCore.QString(newString))
        print self.createFramesList()
    
    def keyPressEvent(self, event):
        if event.key()==QtCore.Qt.Key_Space:
            self.advanceFrame()
        elif event.key()==QtCore.Qt.Key_Backspace:
            self.ui.timeSlider.setValue(self.ui.timeSlider.value()-1)
            
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
            
    def newPixmap(self, path):
        return QtGui.QPixmap(path)
                
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
        
    def stop(self):
        if self.recording:
            self.timingData[self.curFrame] = self.timer.elapsed()
        self.ui.recordBtn.setStyleSheet(BUTTON_DEACTIVATE)
        self.ui.playBtn.setStyleSheet(BUTTON_DEACTIVATE)
        self.ui.recordBtn.setText(QtCore.QString('Record'))
        self.ui.playBtn.setText(QtCore.QString('Play'))
        self.ui.recordBtn.setEnabled(True)
        self.ui.playBtn.setEnabled(True)
        self.recording = False
        self.playing = False
        
    def createXml(self):
        xml_str = '<?xml version="1.0" ?>\n<fps>{0}</fps>\n<frames>'.format(self.fps)
        for i in range(0,len(self.imgSequence)):
            xml_str = xml_str + '\n\t<frame>\n\t\t<ms>{0}</ms>\n\t\t<path>{1}</path>\n\t</frame>'.format(self.imgSequence[i], self.timingData[i])
        xml_str = xml_str + '\n</frames>\n'
        return xml_str
            
        
        