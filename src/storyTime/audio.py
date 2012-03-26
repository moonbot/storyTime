"""
audio.py

Created by Chris Lewis on 2011-06-16.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

import threading
import wave
import pyaudio

class AudioRecorder(threading.Thread):
    filename = ''
    recording = False
    
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename
        
    def run(self):
        self.recording = True
        chunk = 1024
        allSound = []
        params = {
            'format':pyaudio.paInt16,
            'channels':1,
            'rate':44100,
            'input':True,
            'frames_per_buffer':chunk
        }
        try:
            p = pyaudio.PyAudio()
            stream = p.open(**params)
            while self.recording:
                data = stream.read(chunk)
                allSound.append(data)
            stream.close()
            p.terminate()
            data = ''.join(allSound)
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(params['channels'])
            wf.setsampwidth(p.get_sample_size(params['format']))
            wf.setframerate(params['rate'])
            wf.writeframes(data)
        except:
            pass
            
    def join(self, timeout=None):
        self.recording = False
        threading.Thread.join(self, timeout)
        
        
class AudioPlayer(threading.Thread):
    filename = ''
    playing = False
    
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename
        
    def run(self):
        chunk = 1024
        self.playing = True
        try:
            wf = wave.open(self.filename, 'rb')
            p = pyaudio.PyAudio()
            stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                                      channels = wf.getnchannels(),
                                      rate = wf.getframerate(),
                                      output = True)
            data = wf.readframes(chunk)
            while data != '' and self.playing:
                stream.write(data)
                data = wf.readframes(chunk)
            stream.close()
            p.terminate()
            wf.close()
        except:
            pass
            
    def join(self, timeout=None):
        self.playing = False
        threading.Thread.join(self, timeout)
        
        
class AudioHandler(object):
    
    filename = ''
    _recorder = None
    _player = None
        
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