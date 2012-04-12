"""
audio.py

Created by Chris Lewis on 2011-06-16.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

import logging
import os
import pyaudio
import shutil
import tempfile
import threading
import wave

LOG = logging.getLogger('storyTime.audio')

__all__ = [
    'devices',
    'defaultInputDeviceIndex',
    'defaultInputDeviceIndex',
    'inputDevices',
    'outputDevices',
    'isInputDevice',
    'isOutputDevice',
    'getDevice',
    'AudioRecording',
    'AudioHandler',
    'AudioRecorder',
    'AudioPlayer',
]


def devices():
    p = pyaudio.PyAudio()
    count = p.get_device_count()
    devices = [p.get_device_info_by_index(i) for i in range(count)]
    p.terminate()
    return devices

def defaultInputDeviceIndex():
    p = pyaudio.PyAudio()
    try:
        device = p.get_default_input_device_info()
    except IOError:
        device = {'index':-1}
    p.terminate()
    return device['index']

def defaultOutputDeviceIndex():
    p = pyaudio.PyAudio()
    try:
        device = p.get_default_output_device_info()
    except IOError:
        device = {'index':-1}
    p.terminate()
    return device['index']

def inputDevices():
    return [d for d in devices() if isInputDevice(d)]
    
def outputDevices():
    return [d for d in devices() if isOutputDevice(d)]

def isInputDevice(d):
    return d['maxInputChannels'] > 0

def isOutputDevice(d):
    return d['maxOutputChannels'] > 0

def getDevice(index):
    for d in devices():
        if d['index'] == index:
            return d


class AudioRecording(object):
    """
    Represents an audio file that can be recorded to
    and played back. Uses and AudioRecorder and
    AudioPlayer to handle recording and playback.
    """
    
    def __init__(self, filename=None):
        self.filename = None
        self.duration = 0
        self.inputDeviceIndex = defaultInputDeviceIndex()
        self.outputDeviceIndex = defaultOutputDeviceIndex()
        self._hasRecording = False
        self._tempFile = None
        self._recorder = None
        self._player = None
        if filename is not None:
            self.load(filename)
    
    def __del__(self):
        if self.isRecording or self.isPlaying:
            self.stop()
    
    @property
    def tempFile(self):
        if self._tempFile is None:
            fd, self._tempFile = tempfile.mkstemp('_audioRecording.wav')
            os.close(fd)
        return self._tempFile
    
    @property
    def hasRecording(self):
        """ Whether the AudioRecording has an actual recording yet or not"""
        return self._hasRecording
    
    @property
    def isRecording(self):
        return self._recorder is not None and self._recorder.isRecording
    
    @property
    def isPlaying(self):
        return self._player is not None and self._player.isPlaying
    
    @property
    def recorder(self):
        return self._recorder
    
    @property
    def player(self):
        return self._player
    
    def load(self, filename):
        # copy the file to the tmp location
        shutil.copy2(filename, self.tempFile)
        self.filename = filename
        self._hasRecording = True
        LOG.debug('loaded audio file: {0}'.format(filename))
    
    def record(self):
        """ Start recording audio """
        if self.isRecording:
            LOG.info('already recording')
            return
        if self.isPlaying:
            self.stop()
        self._recorder = AudioRecorder(self.tempFile)
        self._recorder.deviceIndex = self.inputDeviceIndex
        self._recorder.start()
    
    def play(self):
        """ Playback the audio file """
        if self.isRecording:
            self.stop()
        if not self.hasRecording:
            LOG.warning('cant playback audio. no recording exists yet')
            return
        if self.isPlaying:
            self.stop()
        self._player = AudioPlayer(self.tempFile)
        self._player.deviceIndex = self.outputDeviceIndex
        self._player.start()
    
    def stop(self):
        """
        Stop recording/playing.
        Recordings in progress will be saved to disk.
        """
        if self.isRecording:
            self.recorder.stop()
            self._hasRecording = True
        elif self.isPlaying:
            self.player.stop()
    
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


class AudioHandler(threading.Thread):
    def __init__(self, filename=None):
        threading.Thread.__init__(self)
        self.filename = filename
        self.pyaudio = pyaudio.PyAudio()
        self.deviceIndex = self.getDefaultDeviceIndex()
    
    def __del__(self):
        self.pyaudio.terminate()
    
    @property
    def devices(self):
        raise NotImplementedError
    
    @property
    def device(self):
        """The current device info"""
        return getDevice(self.deviceIndex)

    @property
    def deviceName(self):
        """The current device's name"""
        d = self.device
        if d is not None:
            return d['name']

    def getDeviceIndex(self):
        return self._deviceIndex
    def setDeviceIndex(self, value):
        if self.isValidDeviceIndex(value):
            self._deviceIndex = value
    deviceIndex = property(getDeviceIndex, setDeviceIndex)

    def isValidDeviceIndex(self, index):
        return index in [d['index'] for d in self.devices]
    
    def getDefaultDeviceIndex(self):
        raise NotImplementedError


class AudioRecorder(AudioHandler):
    def __init__(self, filename=None):
        super(AudioRecorder, self).__init__(filename)
        self._isRecording = False
        self.duration = 0
        self.allSound = []
    
    @property
    def isRecording(self):
        return self._isRecording
    
    @property
    def devices(self):
        return inputDevices()

    def getDefaultDeviceIndex(self):
        return defaultInputDeviceIndex()
    
    def getStreamOpts(self):
        device = self.device
        opts = {
            'input_device_index':device['index'],
            'channels':int(device['maxInputChannels']),
            'rate':int(device['defaultSampleRate']),
            'input':True,
            'format':pyaudio.paInt16,
            'frames_per_buffer':1024,
        }
        return opts
    
    def run(self):
        self._isRecording = True
        opts = self.getStreamOpts()
        data = self.recordData(opts)
        self.writeData(data, opts)
        LOG.debug('recorded audio: {0}'.format(self.filename))
    
    def recordData(self, opts):
        # create stream and start recording
        stream = self.pyaudio.open(**opts)
        self.allSound = []
        while self._isRecording or len(self.allSound) == 0:
            data = stream.read(1024)
            self.allSound.append(data)
        
        stream.close()
        return ''.join(self.allSound)
    
    def writeData(self, data, opts):
        # write out the wave file
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(opts['channels'])
        wf.setsampwidth(self.pyaudio.get_sample_size(opts['format']))
        wf.setframerate(opts['rate'])
        wf.writeframes(data)
        wf.close()
    
    def stop(self):
        """Stop the recording and rejoin the main thread"""
        self._isRecording = False
        self.join()



class AudioPlayer(AudioHandler):    
    def __init__(self, filename=None):
        super(AudioPlayer, self).__init__(filename)
        self._isPlaying = False
    
    @property
    def isPlaying(self):
        return self._isPlaying
    
    @property
    def devices(self):
        return outputDevices()

    def getDefaultDeviceIndex(self):
        return defaultOutputDeviceIndex()
    
    def getStreamOpts(self, wav):
        device = self.device
        opts = {
            'output_device_index':device['index'],
            'channels':wav.getnchannels(),
            'rate':wav.getframerate(),
            'output':True,
            'format':self.pyaudio.get_format_from_width(wav.getsampwidth()),
        }
        return opts
    
    def run(self):
        LOG.debug('playing audio {0}'.format(self.filename))
        self._isPlaying = True
        wav = wave.open(self.filename, 'rb')
        opts = self.getStreamOpts(wav)
        stream = self.pyaudio.open(**opts)
        chunk = 1024
        data = wav.readframes(chunk)
        while data != '' and self._isPlaying:
            stream.write(data)
            data = wav.readframes(chunk)
        stream.close()
        wav.close()
    
    def stop(self):
        self._isPlaying = False
        self.join()


