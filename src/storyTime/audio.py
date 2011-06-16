'''
Created on Jun 16, 2011

@author: clewis
'''

import sys
import os
import threading

import pyaudio
import wave
from production import sequences

class AudioRecorder(threading.Thread):
    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    filename = ''
    allSound = []
    recording = False
    p = None
    stream = None
    
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename
        
    def run(self):
        self.recording = True
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format = self.FORMAT,
                                  channels = self.CHANNELS,
                                  rate = self.RATE,
                                  input = True,
                                  frames_per_buffer = self.chunk)
        while self.recording:
            data = self.stream.read(self.chunk)
            self.allSound.append(data)
        self.stream.close()
        self.p.terminate()
        data = ''.join(self.allSound)
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(data)
            
    def join(self, timeout=None):
        self.recording = False
        threading.Thread.join(self, timeout)
        
        
class AudioPlayer(threading.Thread):
    
    chunk = 1024
    filename = ''
    wf = None
    p = None
    stream = None
    playing = False
    
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename
        
    def run(self):
        self.playing = True
        try:
            self.wf = wave.open(self.filename, 'rb')
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format = self.p.get_format_from_width(self.wf.getsampwidth()),
                                      channels = self.wf.getnchannels(),
                                      rate = self.wf.getframerate(),
                                      output = True)
            data = self.wf.readframes(self.chunk)
            while data != '' and self.playing:
                self.stream.write(data)
                data = self.wf.readframes(self.chunk)
            self.stream.close()
            self.p.terminate()
            self.wf.close()
        except:
            pass
            
    def join(self, timeout=None):
        self.playing = False
        threading.Thread.join(self, timeout)
        
        
class AudioHandler(object):
    
    filename = ''
    _recorder = None
    _player = None
    
    def __init__(self, imageFileName):
        dirname = os.path.dirname(imageFileName)
        dirname = dirname + '\\audio\\'
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        filename = sequences.base_num_ext(os.path.split(imageFileName)[1])[0]
        filename = filename.replace('.', '') + '_audio.wav'
        self.filename = dirname + filename
        
    def start_recording(self):
        self.stop_recording()
        self.stop_playing()
        try:
            self._recorder = AudioRecorder(self.filename)
        except IOError:
            return
        self._recorder.start()
        
    def stop_recording(self):
        if self._recorder is not None:
            if self._recorder.isAlive():
                self._recorder.join()
                
    def start_playing(self):
        self.stop_recording()
        self.stop_playing()
        try:
            self._player = AudioPlayer(self.filename)
        except IOError:
            return
        self._player.start()
        
    def stop_playing(self):
        if self._player is not None:
            if self._player.isAlive():
                self._player.join()  