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

LOG = logging.getLogger('storyTime.camera')

class VideoRecording(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.isRecording = False
        self.hasRecording = False
        self._camera = None
        self._writer = None
        self._tempFile = None
        self.fps = 24.0
        self.prevTime = 0
        self.duration = 0
            
    def __del__(self):
        if self.isRecording:
            self.stop()
        del(self._camera)

    @property
    def tempFile(self):
        if self._tempFile is None:
            fd, self._tempFile = tempfile.mkstemp('_cameraCapture.mov')
            LOG.debug(self._tempFile)
            os.close(fd)
        return self._tempFile
       
    @property
    def camera(self):
        if self._camera is None:
            self._camera = cv.CaptureFromCAM(-1)
        return self._camera
                
    @property
    def writer(self):
        if self._writer is None:
            self._writer = 1#cv.CreateVideoWriter(self.tempFile, cv.CV_FOURCC('H','2','6','4'), self.fps, (480,320), 1)
        return self._writer
        
    def record(self):
        if self.isRecording:
            return
        self.hasRecording = True
        self.isRecording = True
        self.startTime = time.time()
        self.start()
        
    def stop(self):
        print("stopping")
        if not self.isRecording:
            return
        self.isRecording = False
            
    def run(self):
        # thread function called by self.start()
        while self.isRecording:
            elapsedTime = time.time() - self.prevTime
            self.duration += elapsedTime
            if elapsedTime > 1.0 / self.fps:
                image = cv.RetrieveFrame(self.camera)
                if image is not None:
                    print("my")
                    # cv.WriteFrame(self.writer, image)
                print("done")
        
    def save(self, filename):
        if not self.hasRecording:
            LOG.warning('Nothing to save. No recording has been created yet')
            return
        filename = '{0}.wav'.format(os.path.splitext(filename)[0])
        self.filename = filename
        dir_ = os.path.dirname(filename)
        if not os.path.isdir(dir_):
            try:
                os.makedirs(dir_)
            except OSError as e:
                LOG.warning('Could not save to file, cannot create directory: {0}'.format(dir_))
                return
        shutil.copy2(self.tempFile, filename)
        return self.filename


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        