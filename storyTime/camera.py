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

class VideoRecording(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.isRecording = False
        self.hasRecording = False
        self.fps = 24.0
        self.prevTime = 0
        self.duration = 0
        self.camera = cv.CaptureFromCAM(-1)
            
    def __del__(self):
        if self.isRecording:
            self.stop()
        del(self.camera)
        
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
        index = 0
        while self.isRecording:
            index += 1
            elapsedTime = time.time() - self.prevTime
            self.duration += elapsedTime
            if elapsedTime > 1.0 / self.fps:
                image = cv.QueryFrame(self.camera)
                if image is not None:
                    cv.SaveImage(os.path.join(tempfile.gettempdir(), 'cameraExport.%06d.jpg' % index), image)
                        
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
            '-t', float(self.duration) / self.fps,
            filename,
        ]
        args = [str(a) for a in args]
        LOG.debug('ffmpeg command:\n {0}'.format(' '.join(args)))
        subprocess.Popen(args)
        
v = VideoRecording()
v.record()
pdb.set_trace()
 