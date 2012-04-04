"""
camera.py

Created by Nolan Baker on 2012-04-03.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

import cv
import logging
import os
import shutil
import tempfile
import threading
import time
import pdb
import sys
import subprocess

LOG = logging.getLogger('storyTime.camera')

CAM = cv.CaptureFromCAM(-1)

class CameraRecording(object):
    def __init__(self):
        self.hasRecording = False
        self.fps = 24.0
        self._recorder = None
       
    @property
    def isRecording(self):
        return self._recorder is not None and self._recorder.isRecording
   
    def save(self, filename):
        FFMPEG = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'
        args = [
            FFMPEG,
            '-y',
            '-f', 'image2',
            '-i', os.path.join(tempfile.gettempdir(), 'cameraExport.%06d.jpg'),
            '-r', self.fps,
            '-vcodec', 'libx264',
            '-g', '12',
            '-t', self._recorder.duration,
            filename,
        ]
        args = [str(a) for a in args]
        LOG.debug('\n\nffmpeg command:\n {0}\n\n'.format(' '.join(args)))
        subprocess.Popen(args)
 
    def record(self):
        """ Start recording camera """
        if self.isRecording:
            LOG.info('already recording')
            return

        self._recorder = CameraRecorder()
        self._recorder.recording = self
        self._recorder.start()

    def stop(self):
        self._recorder.join()
        self.hasRecording = True
 
class CameraRecorder(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopEvent = threading.Event()
        self.isRecording = False
        self.recording = None
        self.duration = 0.0
        
    def join(self,timeout=None):
        """
        Stop the thread
        """
        self.stopEvent.set()
        threading.Thread.join(self, timeout)

    def run(self):
        if CAM is None: return
        LOG.debug("{0}".format(tempfile.gettempdir()))

        index = 0
        self.isRecording = True
        startTime = time.time()        
        
        while not self.stopEvent.isSet():
            index += 1
            image = cv.QueryFrame(CAM)
            if image is not None:
                cv.SaveImage(os.path.join(tempfile.gettempdir(), 'cameraExport.%06d.jpg' % index), image)
            self.stopEvent.wait(1.0 / self.recording.fps)
               
        self.duration = time.time() - startTime
        self.isRecording = False
    
        