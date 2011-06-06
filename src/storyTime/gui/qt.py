import sys, os

from PyQt4 import QtCore, QtGui

from storyTime import get_log
from storyTime.gui.qt_ui import Ui_MainWindow
from production import sequences
from pickle import FALSE

LOG = get_log(__name__)

FPS = 24

def run_gui(**kwargs):
    """Create an instance of the sync gui and show it."""
    LOG.debug('Initializing StoryTime Gui...')
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Plastique')
    win = StoryView()
    win.show()
    app.exec_()

class StoryView(QtGui.QMainWindow):
    
    recording = False
    playing = FALSE
    startFrame = 0
    curFrame = 0
    timingData = []
    imgSequence = []
    
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        # center on screen
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
        # load ui class
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle('StoryTime')
        
        self.timer = QtCore.QTime()
        self.timer.start()
        
        self.ui.timeSlider.setRange(0,0)
        self.ui.timeSlider.setValue(0)
        self.ui.timeLabel.setText(QtCore.QString('0/0'))
        
        self.connect(self.ui.recordBtn, QtCore.SIGNAL('clicked()'), self.recordHandler)
        self.connect(self.ui.playBtn, QtCore.SIGNAL('clicked()'), self.playHandler)
        self.connect(self.ui.timeSlider, QtCore.SIGNAL('valueChanged(int)'), self.sliderHandler)
        self.connect(self.ui.timeSlider, QtCore.SIGNAL('rangeChanged(int,int)'), self.sliderRangeHandler)
        self.connect(self.ui.timeSlider, QtCore.SIGNAL('sliderMoved(int)'), self.sliderMovedHandler)
        
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
            self.ui.recordBtn.setStyleSheet('QPushButton { background-color: rgb(255,125,125) }')
            self.ui.recordBtn.setText(QtCore.QString('Stop'))
            self.ui.playBtn.setEnabled(False)
            self.playing = False
            self.timer.start()
            self.startFrame = self.ui.timeSlider.value() - 1
            self.curFrame = self.startFrame
            self.ui.recordBtn.clearFocus()
        else:
            print 'recordhandler'
            self.stop()
        pass
    
    def playHandler(self):
        self.playing = not self.playing
        if self.playing:
            self.ui.playBtn.setStyleSheet('QPushButton { background-color: rgb(255,125,125) }')
            self.ui.playBtn.setText(QtCore.QString('Stop'))
            self.ui.recordBtn.setEnabled(False)
            self.recording = False
            self.ui.playBtn.clearFocus()
        else:
            print 'playhandler'
            self.stop()
        pass
    
    def sliderHandler(self, value):
        strLabel = '{0}/{1}'.format(self.ui.timeSlider.value(), self.ui.timeSlider.maximum())
        self.ui.timeLabel.setText(QtCore.QString(strLabel))
        #Switch graphics view to requested image
        #Load next image
        pass
    
    def sliderRangeHandler(self):
        self.ui.timeSlider.setValue(1)
        self.timingData = [24 for x in range(0,self.ui.timeSlider.maximum())]
        
    def sliderMovedHandler(self):
        print 'slidermovedhandler'
        self.stop()
    
    def openHandler(self):
        pass
    
    def importHandler(self):
        imgFile = str(QtGui.QFileDialog.getOpenFileName(self, QtCore.QString('Import Image Sequence')))
        imgFile = os.path.normpath(imgFile)
        print imgFile
        self.imgSequence = sequences.file_sequence(imgFile)
        i = self.imgSequence.index(imgFile)+1
        print i
        self.ui.timeSlider.setRange(1,len(self.imgSequence))
        self.ui.timeSlider.setValue(i)
    
    def saveHandler(self):
        pass
    
    def saveAsHandler(self):
        pass
    
    def keyPressEvent(self, event):
        if event.key()==QtCore.Qt.Key_Space:
            self.advanceFrame()
            
    def advanceFrame(self):
        nextImage = self.ui.timeSlider.value() + 1
        if nextImage < self.ui.timeSlider.maximum():
            self.ui.timeSlider.setValue(nextImage)
            if self.recording == True:
                self.timingData[self.curFrame] = int(self.timer.restart()*FPS/1000.0)
                self.curFrame = nextImage 
        else:
            self.stop()
            if nextImage == self.ui.timeSlider.maximum():
                self.ui.timeSlider.setValue(nextImage)
        
    def stop(self):
        if self.recording:
            self.timingData[self.curFrame] = int(self.timer.elapsed()*FPS/1000.0)
        
        self.ui.recordBtn.setStyleSheet('QPushButton { background-color: rgb(70,70,70) }')
        self.ui.recordBtn.setText(QtCore.QString('Record'))
        
        self.ui.playBtn.setStyleSheet('QPushButton { background-color: rgb(70,70,70) }')
        self.ui.playBtn.setText(QtCore.QString('Play'))
        
        self.ui.recordBtn.setEnabled(True)
        self.ui.playBtn.setEnabled(True)
        
        self.recording = False
        self.playing = False
        
        print self.timingData
        