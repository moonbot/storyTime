# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\moonbot\dev\storyTime\design\qt_ui.ui'
#
# Created: Thu Mar 22 09:22:30 2012
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(800, 832)
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        MainWindow.setStyleSheet(QtGui.QApplication.translate("MainWindow", "background-color: rgb(50, 50, 50);color: rgb(255, 255, 255);selection-background-color:rgb(140, 140, 140)", None, QtGui.QApplication.UnicodeUTF8))
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.graphicsViewLayout = QtGui.QVBoxLayout()
        self.graphicsViewLayout.setObjectName(_fromUtf8("graphicsViewLayout"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.graphicsView_2 = QtGui.QGraphicsView(self.centralwidget)
        self.graphicsView_2.setObjectName(_fromUtf8("graphicsView_2"))
        self.horizontalLayout_5.addWidget(self.graphicsView_2)
        self.graphicsViewLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 3)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.timeLabel = QtGui.QLabel(self.centralwidget)
        self.timeLabel.setMinimumSize(QtCore.QSize(63, 0))
        self.timeLabel.setMaximumSize(QtCore.QSize(63, 16777215))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Courier"))
        self.timeLabel.setFont(font)
        self.timeLabel.setText(QtGui.QApplication.translate("MainWindow", "9999/9999", None, QtGui.QApplication.UnicodeUTF8))
        self.timeLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.timeLabel.setObjectName(_fromUtf8("timeLabel"))
        self.horizontalLayout_3.addWidget(self.timeLabel)
        self.timeSlider = QtGui.QSlider(self.centralwidget)
        self.timeSlider.setProperty("value", 0)
        self.timeSlider.setSliderPosition(0)
        self.timeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.timeSlider.setObjectName(_fromUtf8("timeSlider"))
        self.horizontalLayout_3.addWidget(self.timeSlider)
        self.filenameText = QtGui.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.filenameText.setFont(font)
        self.filenameText.setText(QtGui.QApplication.translate("MainWindow", "Filename: *.png", None, QtGui.QApplication.UnicodeUTF8))
        self.filenameText.setObjectName(_fromUtf8("filenameText"))
        self.horizontalLayout_3.addWidget(self.filenameText)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.graphicsViewLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.line = QtGui.QFrame(self.centralwidget)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.horizontalLayout_7.addWidget(self.line)
        self.graphicsViewLayout.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.frameLabel = QtGui.QLabel(self.centralwidget)
        self.frameLabel.setMinimumSize(QtCore.QSize(63, 0))
        self.frameLabel.setMaximumSize(QtCore.QSize(63, 10))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Courier"))
        self.frameLabel.setFont(font)
        self.frameLabel.setText(QtGui.QApplication.translate("MainWindow", "9999/9999", None, QtGui.QApplication.UnicodeUTF8))
        self.frameLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.frameLabel.setObjectName(_fromUtf8("frameLabel"))
        self.horizontalLayout_4.addWidget(self.frameLabel)
        self.recSlider = QtGui.QSlider(self.centralwidget)
        self.recSlider.setOrientation(QtCore.Qt.Horizontal)
        self.recSlider.setObjectName(_fromUtf8("recSlider"))
        self.horizontalLayout_4.addWidget(self.recSlider)
        self.curTimeLabel = QtGui.QLabel(self.centralwidget)
        self.curTimeLabel.setMinimumSize(QtCore.QSize(60, 0))
        self.curTimeLabel.setMaximumSize(QtCore.QSize(200, 200))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Courier"))
        self.curTimeLabel.setFont(font)
        self.curTimeLabel.setText(QtGui.QApplication.translate("MainWindow", "00:00:00/00:00:00", None, QtGui.QApplication.UnicodeUTF8))
        self.curTimeLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.curTimeLabel.setObjectName(_fromUtf8("curTimeLabel"))
        self.horizontalLayout_4.addWidget(self.curTimeLabel)
        self.recordBtn = QtGui.QPushButton(self.centralwidget)
        self.recordBtn.setMaximumSize(QtCore.QSize(62, 60))
        self.recordBtn.setStyleSheet(QtGui.QApplication.translate("MainWindow", "background-color: rgb(70, 70, 70);", None, QtGui.QApplication.UnicodeUTF8))
        self.recordBtn.setText(QtGui.QApplication.translate("MainWindow", "Record", None, QtGui.QApplication.UnicodeUTF8))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("images/rec2.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.recordBtn.setIcon(icon)
        self.recordBtn.setObjectName(_fromUtf8("recordBtn"))
        self.horizontalLayout_4.addWidget(self.recordBtn)
        self.playBtn = QtGui.QPushButton(self.centralwidget)
        self.playBtn.setMaximumSize(QtCore.QSize(50, 60))
        self.playBtn.setStyleSheet(QtGui.QApplication.translate("MainWindow", "background-color: rgb(70, 70, 70);", None, QtGui.QApplication.UnicodeUTF8))
        self.playBtn.setText(QtGui.QApplication.translate("MainWindow", "Play", None, QtGui.QApplication.UnicodeUTF8))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("images/play.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.playBtn.setIcon(icon1)
        self.playBtn.setObjectName(_fromUtf8("playBtn"))
        self.horizontalLayout_4.addWidget(self.playBtn)
        self.clearBtn = QtGui.QPushButton(self.centralwidget)
        self.clearBtn.setMaximumSize(QtCore.QSize(50, 60))
        self.clearBtn.setStyleSheet(_fromUtf8("background-color: rgb(70, 70, 70);"))
        self.clearBtn.setText(QtGui.QApplication.translate("MainWindow", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.clearBtn.setObjectName(_fromUtf8("clearBtn"))
        self.horizontalLayout_4.addWidget(self.clearBtn)
        self.graphicsViewLayout.addLayout(self.horizontalLayout_4)
        self.line_2 = QtGui.QFrame(self.centralwidget)
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.graphicsViewLayout.addWidget(self.line_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "Press Space/, to advance frame, Backspace/. to go back a frame", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.loopBox = QtGui.QCheckBox(self.centralwidget)
        self.loopBox.setMaximumSize(QtCore.QSize(45, 16777215))
        self.loopBox.setText(QtGui.QApplication.translate("MainWindow", "Loop", None, QtGui.QApplication.UnicodeUTF8))
        self.loopBox.setChecked(True)
        self.loopBox.setObjectName(_fromUtf8("loopBox"))
        self.horizontalLayout.addWidget(self.loopBox)
        self.timingBox = QtGui.QCheckBox(self.centralwidget)
        self.timingBox.setMinimumSize(QtCore.QSize(0, 0))
        self.timingBox.setMaximumSize(QtCore.QSize(90, 16777215))
        self.timingBox.setText(QtGui.QApplication.translate("MainWindow", "Record Timing", None, QtGui.QApplication.UnicodeUTF8))
        self.timingBox.setChecked(True)
        self.timingBox.setObjectName(_fromUtf8("timingBox"))
        self.horizontalLayout.addWidget(self.timingBox)
        self.audioBox = QtGui.QCheckBox(self.centralwidget)
        self.audioBox.setMaximumSize(QtCore.QSize(82, 16777215))
        self.audioBox.setText(QtGui.QApplication.translate("MainWindow", "Record Audio", None, QtGui.QApplication.UnicodeUTF8))
        self.audioBox.setChecked(True)
        self.audioBox.setObjectName(_fromUtf8("audioBox"))
        self.horizontalLayout.addWidget(self.audioBox)
        self.graphicsViewLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.graphicsViewLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setTitle(QtGui.QApplication.translate("MainWindow", "File", None, QtGui.QApplication.UnicodeUTF8))
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuOptions = QtGui.QMenu(self.menubar)
        self.menuOptions.setTitle(QtGui.QApplication.translate("MainWindow", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.menuOptions.setObjectName(_fromUtf8("menuOptions"))
        self.menuFPS_2 = QtGui.QMenu(self.menuOptions)
        self.menuFPS_2.setTitle(QtGui.QApplication.translate("MainWindow", "FPS", None, QtGui.QApplication.UnicodeUTF8))
        self.menuFPS_2.setObjectName(_fromUtf8("menuFPS_2"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionImport_Image_Sequence = QtGui.QAction(MainWindow)
        self.actionImport_Image_Sequence.setText(QtGui.QApplication.translate("MainWindow", "Import Image Sequence...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionImport_Image_Sequence.setObjectName(_fromUtf8("actionImport_Image_Sequence"))
        self.actionOpen = QtGui.QAction(MainWindow)
        self.actionOpen.setText(QtGui.QApplication.translate("MainWindow", "Open...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionOpen.setObjectName(_fromUtf8("actionOpen"))
        self.actionSave = QtGui.QAction(MainWindow)
        self.actionSave.setText(QtGui.QApplication.translate("MainWindow", "Save", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.actionSave_As = QtGui.QAction(MainWindow)
        self.actionSave_As.setText(QtGui.QApplication.translate("MainWindow", "Save As...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave_As.setObjectName(_fromUtf8("actionSave_As"))
        self.action24 = QtGui.QAction(MainWindow)
        self.action24.setCheckable(True)
        self.action24.setChecked(True)
        self.action24.setText(QtGui.QApplication.translate("MainWindow", "Film (24 fps)", None, QtGui.QApplication.UnicodeUTF8))
        self.action24.setObjectName(_fromUtf8("action24"))
        self.action25 = QtGui.QAction(MainWindow)
        self.action25.setCheckable(True)
        self.action25.setText(QtGui.QApplication.translate("MainWindow", "PAL (25 fps)", None, QtGui.QApplication.UnicodeUTF8))
        self.action25.setObjectName(_fromUtf8("action25"))
        self.action30 = QtGui.QAction(MainWindow)
        self.action30.setCheckable(True)
        self.action30.setText(QtGui.QApplication.translate("MainWindow", "NTSC (30 fps)", None, QtGui.QApplication.UnicodeUTF8))
        self.action30.setObjectName(_fromUtf8("action30"))
        self.action48 = QtGui.QAction(MainWindow)
        self.action48.setCheckable(True)
        self.action48.setText(QtGui.QApplication.translate("MainWindow", "Show (48 fps)", None, QtGui.QApplication.UnicodeUTF8))
        self.action48.setObjectName(_fromUtf8("action48"))
        self.action50 = QtGui.QAction(MainWindow)
        self.action50.setCheckable(True)
        self.action50.setText(QtGui.QApplication.translate("MainWindow", "PAL Field (50 fps)", None, QtGui.QApplication.UnicodeUTF8))
        self.action50.setObjectName(_fromUtf8("action50"))
        self.action60 = QtGui.QAction(MainWindow)
        self.action60.setCheckable(True)
        self.action60.setText(QtGui.QApplication.translate("MainWindow", "NTSC Field (60 fps)", None, QtGui.QApplication.UnicodeUTF8))
        self.action60.setObjectName(_fromUtf8("action60"))
        self.actionCustom = QtGui.QAction(MainWindow)
        self.actionCustom.setCheckable(True)
        self.actionCustom.setText(QtGui.QApplication.translate("MainWindow", "Custom...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCustom.setObjectName(_fromUtf8("actionCustom"))
        self.actionCustom_2 = QtGui.QAction(MainWindow)
        self.actionCustom_2.setText(QtGui.QApplication.translate("MainWindow", "Custom...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCustom_2.setObjectName(_fromUtf8("actionCustom_2"))
        self.actionSet_Recording_Countdown = QtGui.QAction(MainWindow)
        self.actionSet_Recording_Countdown.setText(QtGui.QApplication.translate("MainWindow", "Set Recording Countdown...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSet_Recording_Countdown.setObjectName(_fromUtf8("actionSet_Recording_Countdown"))
        self.actionImport_Directory = QtGui.QAction(MainWindow)
        self.actionImport_Directory.setText(QtGui.QApplication.translate("MainWindow", "Import Directory...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionImport_Directory.setObjectName(_fromUtf8("actionImport_Directory"))
        self.actionOpen_2 = QtGui.QAction(MainWindow)
        self.actionOpen_2.setText(QtGui.QApplication.translate("MainWindow", "Open...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionOpen_2.setObjectName(_fromUtf8("actionOpen_2"))
        self.actionImport_Image_Sequence_2 = QtGui.QAction(MainWindow)
        self.actionImport_Image_Sequence_2.setText(QtGui.QApplication.translate("MainWindow", "Import Image Sequence...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionImport_Image_Sequence_2.setObjectName(_fromUtf8("actionImport_Image_Sequence_2"))
        self.actionImport_Directory_2 = QtGui.QAction(MainWindow)
        self.actionImport_Directory_2.setText(QtGui.QApplication.translate("MainWindow", "Import Directory...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionImport_Directory_2.setObjectName(_fromUtf8("actionImport_Directory_2"))
        self.actionSave_2 = QtGui.QAction(MainWindow)
        self.actionSave_2.setText(QtGui.QApplication.translate("MainWindow", "Save", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave_2.setObjectName(_fromUtf8("actionSave_2"))
        self.actionSave_As_2 = QtGui.QAction(MainWindow)
        self.actionSave_As_2.setText(QtGui.QApplication.translate("MainWindow", "Save As...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave_As_2.setObjectName(_fromUtf8("actionSave_As_2"))
        self.actionExport_to_Final_Cut_Pro = QtGui.QAction(MainWindow)
        self.actionExport_to_Final_Cut_Pro.setText(QtGui.QApplication.translate("MainWindow", "Export to Final Cut Pro...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExport_to_Final_Cut_Pro.setObjectName(_fromUtf8("actionExport_to_Final_Cut_Pro"))
        self.actionExport_to_Premiere = QtGui.QAction(MainWindow)
        self.actionExport_to_Premiere.setText(QtGui.QApplication.translate("MainWindow", "Export to Premiere...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExport_to_Premiere.setObjectName(_fromUtf8("actionExport_to_Premiere"))
        self.menuFile.addAction(self.actionOpen_2)
        self.menuFile.addAction(self.actionImport_Image_Sequence_2)
        self.menuFile.addAction(self.actionImport_Directory_2)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave_2)
        self.menuFile.addAction(self.actionSave_As_2)
        self.menuFile.addAction(self.actionExport_to_Final_Cut_Pro)
        self.menuFile.addAction(self.actionExport_to_Premiere)
        self.menuFPS_2.addAction(self.action24)
        self.menuFPS_2.addAction(self.action25)
        self.menuFPS_2.addAction(self.action48)
        self.menuFPS_2.addAction(self.action30)
        self.menuFPS_2.addAction(self.action50)
        self.menuFPS_2.addAction(self.action60)
        self.menuFPS_2.addAction(self.actionCustom_2)
        self.menuOptions.addAction(self.menuFPS_2.menuAction())
        self.menuOptions.addAction(self.actionSet_Recording_Countdown)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuOptions.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        pass


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

