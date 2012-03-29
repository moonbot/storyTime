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


class AudioRecording(object):
    """
    Represents an audio file that can be recorded to
    and played back. Uses and AudioRecorder and
    AudioPlayer to handle recording and playback.
    """
    def __init__(self):
        self.filename = None
        self.duration = 0
        self._hasRecording = False
        self._tempFile = None
        self._recorder = None
        self._player = None
    
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
    
    def record(self):
        """ Start recording audio """
        if self.isRecording:
            LOG.info('already recording')
            return
        if self.isPlaying:
            self.stop()
        self._recorder = AudioRecorder(self.tempFile)
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


class AudioDevice(threading.Thread):
    def __init__(self, filename=None):
        threading.Thread.__init__(self)
        self.filename = filename
        self.pyaudio = pyaudio.PyAudio()
        self.deviceIndex = self.getDefaultDeviceIndex()
    
    def __del__(self):
        self.pyaudio.terminate()
    
    @property
    def devices(self):
        count = self.pyaudio.get_device_count()
        devices = [self.pyaudio.get_device_info_by_index(i) for i in range(count)]
        return [d for d in devices if self.isValidDevice(d)]

    @property
    def deviceIndeces(self):
        return [d['index'] for d in self.devices]

    @property
    def device(self):
        """The current device info"""
        return self.getDevice(self.deviceIndex)

    @property
    def deviceName(self):
        """The current device's name"""
        return self.getDeviceName(self.deviceIndex)

    def getDeviceIndex(self):
        return self._deviceIndex
    def setDeviceIndex(self, value):
        if self.isValidDeviceIndex(value):
            self._deviceIndex = value
    deviceIndex = property(getDeviceIndex, setDeviceIndex)

    def isValidDeviceIndex(self, index):
        return index in [d['index'] for d in self.devices]
    
    def getDefaultDeviceIndex(self):
        return self.getDefaultDevice()['index']

    def getDevice(self, index):
        for d in self.devices:
            if d['index'] == index:
                return d

    def getDeviceName(self, index):
        d = self.getDevice(index)
        if d is not None:
            return d['name']

    def isValidDevice(self, device):
        raise NotImplementedError

    def getDefaultDevice(self):
        raise NotImplementedError


class AudioRecorder(AudioDevice):
    def __init__(self, filename=None):
        super(AudioRecorder, self).__init__(filename)
        self._isRecording = False
        self.duration = 0
        self.allSound = []
    
    @property
    def isRecording(self):
        return self._isRecording
    
    def isValidDevice(self, device):
        return device['maxInputChannels'] > 0

    def getDefaultDevice(self):
        return self.pyaudio.get_default_input_device_info()
    
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
        LOG.debug('recording audio...')
        self._isRecording = True
        opts = self.getStreamOpts()
        data = self.recordData(opts)
        self.writeData(data, opts)
        LOG.debug('finished recording. {0}'.format(self.filename))
    
    def recordData(self, opts):
        # create stream and start recording
        stream = self.pyaudio.open(**opts)
        self.allSound = []
        while self._isRecording:
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



class AudioPlayer(AudioDevice):    
    def __init__(self, filename=None):
        super(AudioPlayer, self).__init__(filename)
        self._isPlaying = False
    
    @property
    def isPlaying(self):
        return self._isPlaying
    
    def isValidDevice(self, device):
        return device['maxOutputChannels'] > 0

    def getDefaultDevice(self):
        return self.pyaudio.get_default_output_device_info()
        
    def run(self):
        LOG.debug('playing audio {0}'.format(self.filename))
        self._isPlaying = True
        chunk = 1024
        wf = wave.open(self.filename, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                                  channels = wf.getnchannels(),
                                  rate = wf.getframerate(),
                                  output = True)
        data = wf.readframes(chunk)
        while data != '' and self._isPlaying:
            stream.write(data)
            data = wf.readframes(chunk)
        stream.close()
        p.terminate()
        wf.close()
        LOG.debug('audio playback ended')
    
    def stop(self):
        self._isPlaying = False
        self.join()


