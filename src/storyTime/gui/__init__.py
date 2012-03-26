
import logging
import sys
import os
import re
import xml.dom.minidom

from storyTime import utils
from storyTime.audio import AudioHandler
from storyTime.fcpxml import FcpXml

LOG = logging.getLogger('storyTime.gui')


def run_gui(**kwargs):
    import qt
    """Run the Sync Gui"""
    qt.run_gui()
    
class StoryTimeControlUI(object):
    
    # Main View Functions
    # -------------------
    
    def view_browse_open(self, caption):
        """Return the path of the selected file"""
        raise NotImplementedError
    
    def view_browse_open_dir(self, caption):
        """Return the path of the selected directory"""
        raise NotImplementedError
    
    def view_browse_save_as(self, caption):
        """Return the path of the selected file"""
        raise NotImplementedError
    
    def view_update_timer(self):
        """Refresh the timer and returns the time since the previous call"""
        raise NotImplementedError
    
    def view_start_timer(self, ms):
        """Start a timer to call an event in ms milliseconds"""
        raise NotImplementedError
    
    def view_start_disp_timer(self):
        """Start the timer used for the UI's timecode"""
        raise NotImplementedError
    
    def view_stop_disp_timer(self):
        """Stop the timer used for the UI's timecode"""
        raise NotImplementedError
    
    def view_query_custom_fps(self):
        """Query the user for a custom fps and return the value"""
        raise NotImplementedError
    
    def view_query_countdown_time(self):
        """Query the user for a countdown time and return the value"""
        raise NotImplementedError
    
    def view_get_image_formats(self):
        """Return a list of valid image formats"""
        raise NotImplementedError
    
    # Observer View Functions
    # -----------------------
    
    def ob_recording(self):
        raise NotImplementedError
    
    def ob_playing(self):
        raise NotImplementedError
    
    def ob_cur_frame(self):
        raise NotImplementedError
    
    def ob_images(self):
        raise NotImplementedError
    
    def ob_fps_options(self):
        raise NotImplementedError
    
    
class StoryTimeModel(object):
    
    BUTTON_STATES = utils.enum('OFF', 'ON', 'DISABLED')
    
    def init_model(self):
        FPS_OPTIONS = [
            ['Film (24 fps)', 24],
            ['PAL (25 fps)', 25],
            ['NTSC (30 fps)', 30],
            ['Show (48 fps)', 48],
            ['PAL Field (50 fps)', 50],
            ['NTSC Field (60 fps)', 60],
            ['Custom...', 12]
        ]
        # TODO: replace the `times` list with a `data` list that will hold
        #	image/time data not associated with the images list
        model = {
            'recording':self.BUTTON_STATES.OFF,
            'playing':self.BUTTON_STATES.OFF,
            'startFrame':0,
            'curFrame':0,
            'curImgFrame':1,
            'timing_data':[],
            'images':[],
            'fps':24,
            'fpsOptions':FPS_OPTIONS,
            'fpsIndex':0,
            'savePath':'',
            'audioPath':'',
            'recordTiming':True,
            'recordAudio':True,
            'loop':True,
            'timecode':0,
            'countdown':None,
            'countdownms':0
        }
        self.add_observables(model)
        
    def add_observables(self, data):
        for key in data.keys():
            data[key] = utils.Observable(data[key])
        self.__dict__.update(data)
        
class StoryTimeControl(StoryTimeControlUI, StoryTimeModel):
    
    audioHandler = AudioHandler()
    UPDATE_INTERVAL = 500
    
    def observe_model(self):
        """Add necessary observer functions to observable objects"""
        self.audioPath.add_observer(self.ctl_ob_audio_path)
        self.countdown.add_observer(self.ctl_ob_countdown)
        self.curFrame.add_observer(self.ctl_ob_cur_frame)
        self.curFrame.add_observer(self.ob_cur_frame)
        self.curImgFrame.add_observer(self.ctl_ob_cur_frame)
        self.curImgFrame.add_observer(self.ob_cur_frame)
        self.fpsOptions.add_observer(self.ob_fps_options)
        self.images.add_observer(self.ob_images)
        self.playing.add_observer(self.ob_playing)
        
        self.recording.add_observer(self.ob_recording)
        self.timecode.add_observer(self.ob_timecode)
        
    # File Handling Functions
    # -----------------------
    
    def ctl_process_dropped_paths(self, paths):
        """
        Decides what to do with paths dropped onto the file.  Possible options:
        
        Single file:
        .xml: open
        anything else: import sequence
        
        Directory:
        import directory
        
        Multiple files:
        import files as sequence
        """
        
        if len(paths) > 1:
            paths = self.filter_image_paths(paths)
            self.ctl_process_import(paths)
        else:
            ext = os.path.splitext(paths[0])[1]
            if ext == '.xml':
                with open(paths[0], 'r') as openFile:
                    self.from_xml(openFile.read())
                self.savePath.set(paths[0])
                self.audioHandler = AudioHandler(self.images.get()[0])
            elif os.path.isdir(paths[0]):
                self.ctl_process_import(utils.listdir(paths[0]))
            else:
                for imageformat in self.view_get_image_formats():
                    if imageformat == ext:
                        # TODO: implement internal version of sequences
                        LOG.warning('Import Image Sequence not yet implemented...')
                        self.ctl_process_import(paths)
    
    def ctl_open(self):
        """Browse for and open a StoryTime XML file"""
        path = self.view_browse_open('Open...')
        if path is not None and path != '':
            with open(path, 'r') as openFile:
                self.from_xml(openFile.read())
            self.savePath.set(path)
            self.audioHandler = AudioHandler(self.images.get()[0])
    
    def ctl_import_from_sequence(self):
        """Browse for and import an image sequence"""
        path = self.view_browse_open('Import Image Sequence...')
        if path is not None and path != '':
            LOG.warning('Import Image Sequence not yet implemented...')
            self.ctl_process_import(path)
            
    def ctl_import_directory(self):
        """Browse for and import an image directory"""
        path = self.view_browse_open_dir('Import Image Directory...')
        if path is not None and path != '':
            self.ctl_process_import(utils.listdir(path))
        
                
    def ctl_process_import(self, paths):
        """Update the current application state from the list of image files."""
        paths = self.filter_image_paths(paths)
        paths.sort()
        if len(paths) > 0:
            #self.times.set([1000 for x in range(0,len(self.images.get()))])
            n = 1
            for i in paths:
                self.timing_data.get().append({'timing':1000,'image':i, 'imageNum':n})
                n += 1
            self.images.set(paths)
            self.startFrame.set(1)
            self.curFrame.set(1)
            self.curImgFrame.set(1)
            self.ctl_make_audio_path()
    
    def ctl_export_premiere(self):
        """
        Export the current application state to a Final Cut Pro XML file
        formatted for Premiere.
        """
        self.ctl_process_export('Export to Premiere...', 'win')
                
    def ctl_export_fcp(self):
        """
        Export the current application state to a Final Cut Pro XML file
        formatted for Final Cut Pro
        """
        self.ctl_process_export('Export to Final Cut Pro...', 'mac')
                    
    def ctl_process_export(self, caption, operatingSystem):
        """
        Export the current application state to a Final Cut Pro XML file.
        
        `caption` -- the caption of the file browsing dialog
        `operatingSystem` -- the operating system to export the file to
        """
        if len(self.images.get()) > 0:
            path = self.view_browse_save_as(caption)
            if path is not None and path != '':
                fcpkw = {
                    'name':os.path.splitext(os.path.split(path)[1])[0],
                    'images':zip(self.images.get(), self.create_frames_list()),
                    'audioPath':self.audioPath.get(),
                    'fps':self.fps.get(),
                    'ntsc':(self.fps.get() % 30 == 0),
                    'OS':operatingSystem
                }
                with open(path, 'w') as exportFile:
                    exportFile.write(FcpXml(**fcpkw).getStr())
                self.ctl_make_audio_path()
            
    def ctl_save(self):
        """Save the current application state to a StoryTime XML file"""
        if self.savePath.get() == '':
            self.ctl_save_as()
            return
        self.ctl_make_audio_path()
        with open(self.savePath.get(), 'w') as saveFile:
            saveFile.write(self.to_xml())
            
    def ctl_save_as(self):
        """Browse and save the current application state to a StoryTime XML file"""
        if len(self.images.get()) > 0:
            path = self.view_browse_save_as('Save As...')
            if path is not None and path != '':
                with open(path, 'w') as saveFile:
                    saveFile.write(self.to_xml())
                self.savePath.set(path)
                self.ctl_make_audio_path()
                
    def ctl_make_audio_path(self):
        """Set the audio path for a new file"""
        imagePath = self.images.get()[0]
        dirname = os.path.dirname(imagePath) + '/'
        dirname = os.path.join(dirname, 'audio')
        if os.path.exists(dirname):
            #filename = utils.get_latest_version(dirname)
            filename = dirname
            if not filename:
                filename = self.ctl_get_audio_path_name(filename)
        else:
            os.mkdir(dirname)
            filename = self.ctl_get_audio_path_name(filename)
        self.audioPath.set(filename)
        
    def ctl_get_audio_path_name(self, path):
        """Return the base audio filename corresponding to the given path"""
        fullbase = os.path.basename(path)
        base = fullbase.split('.')[0]
        path = '{0}Audio.wav'.format(base)
        return path
    
    # Playback and Recording Functions
    # --------------------------------
    
    def ctl_toggle_record(self):
        if len(self.images.get()) > 0:
            if not (self.recording.get() == self.BUTTON_STATES.DISABLED):
                self.recording.set(not self.recording.get())
                if self.recording.get() == self.BUTTON_STATES.ON:
                    self.timecode.set(self.countdownms.get())
                    self.view_start_disp_timer()
                    if self.recordAudio.get():
                        self.audioHandler.start_recording()
                    self.curFrame.set(1)
                    self.curImgFrame.set(1)
                    self.timing_data.set([])
                    if self.recordTiming.get():
                        self.view_update_timer()
                    else:
                    	# changed to timing_data, starts at first     
                    	self.view_start_timer(self.timing_data.get()[self.curFrame.get() - 1]['timing'])
                    self.startFrame.set(self.curFrame.get())
                    self.playing.set(self.BUTTON_STATES.DISABLED)
                else:
                    self.ctl_stop()
    
    def ctl_toggle_play(self):
        if len(self.images.get()) > 0:
            if not (self.playing.get() == self.BUTTON_STATES.DISABLED):
                self.playing.set(not self.playing.get())
                if self.playing.get() == self.BUTTON_STATES.ON:
                    self.timecode.set(0)
                    self.view_start_disp_timer()
                    self.audioHandler.start_playing()
                    self.curFrame.set(1)
                    self.curImgFrame.set(1)
                    self.view_start_timer(self.timing_data.get()[self.curFrame.get() - 1]['timing'])
                    self.startFrame.set(self.curFrame.get())
                    self.recording.set(self.BUTTON_STATES.DISABLED)
                else:
                    self.ctl_stop()
        
    def ctl_goto_recframe(self, frame):
        """Go to the given frame in timing_data"""
        if len(self.timing_data.get()) > 0:
            self.curFrame.set(frame)
            self.curImgFrame.set(self.timing_data.get()[frame-1]['imageNum'])
    
    def ctl_goto_imgframe(self, frame):
        """Go to the given frame from images"""
        if len(self.images.get()) > 0:
            self.curImgFrame.set(frame)
    
    def ctl_inc_frame(self):
        """Increment the current frame"""
        if not len(self.images.get()) > 0 :
            return
        if self.curFrame.get() == len(self.timing_data.get()) and self.recording.get() != self.BUTTON_STATES.ON:
            self.ctl_stop()
        elif self.recording.get() == self.BUTTON_STATES.ON and self.recordTiming.get():
            self.ctl_record_frame()
        if self.loop.get() and self.curImgFrame.get() == len(self.images.get()):
            self.curImgFrame.set(1)
            return
        self.curImgFrame.set(self.curImgFrame.get() + 1)
    
    def ctl_dec_frame(self):
        """Decrement the current frame"""
        if not len(self.images.get()) > 0 :
            return
        if self.recording.get() == self.BUTTON_STATES.ON and self.recordTiming.get():
            self.ctl_record_frame()
        if self.loop.get() and self.curImgFrame.get() == 1:
            self.curImgFrame.set(len(self.images.get()))
            return
        self.curImgFrame.set(self.curImgFrame.get() - 1)
    
    def ctl_record_frame(self):
    	"""
    	Record the current frame with the current time.
    	Gets called on inc and dec when recording.
    	Adds a dict object to the data list
    	eg. [{'image':'currentImage.jpg', 'time':<currentTime>}, ...]
    	"""
    	self.timing_data.get().append({'image':self.images.get()[self.curImgFrame.get() - 1],
    	   'timing':self.view_update_timer(), 'imageNum':(self.curImgFrame.get() -1)})
        
    def ctl_stop(self):
        """Stop playback and recording"""
        if self.recording.get() == self.BUTTON_STATES.ON:
            self.ctl_record_frame()
            self.ui.recSlider.setRange(1,len(self.timing_data.get()))
        self.recording.set(self.BUTTON_STATES.OFF)
        self.playing.set(self.BUTTON_STATES.OFF)
        self.audioHandler.stop_recording()
        self.audioHandler.stop_playing()
        self.view_stop_disp_timer()
        
    def ctl_update_playback(self):
        """Whilst playing, increment the frame """
        if self.curFrame.get() == len(self.timing_data.get()):
            self.ctl_stop()
            return
        elif (self.playing.get() == self.BUTTON_STATES.ON) or (self.recording.get() == self.BUTTON_STATES.ON and not self.recordTiming.get()):
            self.curFrame.set(self.curFrame.get() + 1)
            #self.curImgFrame.set(self.images.get().index(self.timing_data.get()[self.curFrame.get() - 1]['image']))
            self.view_start_timer(self.timing_data.get()[self.curFrame.get() - 1]['timing'])
            
    def ctl_update_timecode(self, value):
        if self.countdownms.get() > 0 and self.recording.get() == self.BUTTON_STATES.ON:
            countdownTime = self.countdownms.get() - value
            if countdownTime < 0:
                countdownTime = 0
            self.timecode.set(countdownTime)
        else:
            self.timecode.set(value)
                
    # Options Functions
    # -----------------
    
    def ctl_change_fps(self, index):
        self.fpsIndex.set(index)
        if self.fpsIndex.get() == len(self.fpsOptions.get()) - 1:
            newFps = self.view_query_custom_fps()
            self.fpsOptions.get()[-1][0] = 'Custom ({0} fps)...'.format(newFps)
            self.fpsOptions.get()[-1][1] = newFps
            self.fpsOptions.set(self.fpsOptions.get())
        self.fps.set(self.fpsOptions.get()[self.fpsIndex.get()][1])
                
    def ctl_toggle_record_timing(self, value):
        self.recordTiming.set(value)
        if not self.recordTiming.get() and not self.recordAudio.get():
            self.recording.set(self.BUTTON_STATES.DISABLED)
        else:
            self.recording.set(self.BUTTON_STATES.OFF)
    
    def ctl_toggle_loop(self, value):
        self.loop.set(value)
    
    def ctl_toggle_record_audio(self, value):
        self.recordAudio.set(value)
        if not self.recordTiming.get() and not self.recordAudio.get():
            self.recording.set(self.BUTTON_STATES.DISABLED)
        else:
            self.recording.set(self.BUTTON_STATES.OFF)
            
    def ctl_set_recording_countdown(self):
        countdownTime = self.view_query_countdown_time()
        if countdownTime is not None:
            self.countdown.set(countdownTime)
            self.timecode.set(self.countdownms.get())
            
            
    # Specialty Functions
    # -------------------
    
    def create_frames_list(self):
        """Return a list of image times converted to the current fps"""
        incFrames = self.timing_data.get()[:]
        total = 0
        for i in range(0, len(self.timing_data.get())):
            total = total + self.timing_data.get()[i]['timing']
            incFrames[i] = int(total * self.fps.get() / 1000)
        fpsFrames = incFrames[:]
        #We can ignore the value at index 0 because it's already the
        #correct value.
        for i in range(1, len(self.timing_data.get())):
            fpsFrames[i] = incFrames[i] - incFrames[i-1]
            if fpsFrames[i] < 1:
                fpsFrames[i] = 1
        return fpsFrames
    
    def filter_image_paths(self, paths):
        """
        Remove paths with invalid file extensions and return the
        resulting list.
        """
        return [path for path in paths if os.path.splitext(path)[1] in self.view_get_image_formats()]
    
    def to_xml(self):
        """Create a StoryTime XML string from the current application state"""
        xmlDoc = xml.dom.minidom.Document()
        stElement = xmlDoc.createElement('storyTime')
        xmlDoc.appendChild(stElement)
        fpsElement = xmlDoc.createElement('fps')
        stElement.appendChild(fpsElement)
        fpsText = xmlDoc.createTextNode(str(self.fps.get()))
        fpsElement.appendChild(fpsText)
        audioElement = xmlDoc.createElement('audio')
        stElement.appendChild(audioElement)
        audioText = xmlDoc.createTextNode(self.audioPath.get())
        audioElement.appendChild(audioText)
        framesElement = xmlDoc.createElement('frames')
        stElement.appendChild(framesElement)
        for i in range(0, len(self.timing_data.get())):
            frameElement = xmlDoc.createElement('frame')
            framesElement.appendChild(frameElement)
            pathElement = xmlDoc.createElement('path')
            frameElement.appendChild(pathElement)
            pathText = xmlDoc.createTextNode(self.timing_data.get()[i]['image'])
            pathElement.appendChild(pathText)
            msElement = xmlDoc.createElement('ms')
            frameElement.appendChild(msElement)
            msText = xmlDoc.createTextNode(str(self.timing_data.get()[i]['timing']))
            msElement.appendChild(msText)
        return xmlDoc.toprettyxml('\t', '\n')
    
    def from_xml(self, xmlStr):
        """Update the application state based on a StoryTime XML string"""
        xmlStr = xmlStr.replace('\n', '')
        xmlStr = xmlStr.replace('\t', '')
        xmlDoc = xml.dom.minidom.parseString(xmlStr)
        mainElement = xmlDoc.getElementsByTagName('storyTime')[0]
        fps = int(mainElement.getElementsByTagName('fps')[0].childNodes[0].nodeValue)
        audioPath = mainElement.getElementsByTagName('audio')[0].childNodes[0].nodeValue
        framesElement = mainElement.getElementsByTagName('frames')[0]
        images = []
        times = []
        for frameElement in framesElement.childNodes:
            images.append(frameElement.childNodes[0].childNodes[0].nodeValue)
            times.append(int(frameElement.childNodes[1].childNodes[0].nodeValue))
        self.fps.set(fps)
        self.images.set(images)
        self.times.set(times)
        self.audioPath.set(audioPath)
            
    # Observer Functions
    # -----------------
        
    def ctl_ob_audio_path(self):
        self.audioHandler.filename = self.audioPath.get()
        
    def ctl_ob_countdown(self):
        cd = self.countdown.get()
        if cd is None:
            return
        hoursMs = cd['hours'] * 60 * 60 * 1000
        minutesMs = cd['minutes'] * 60 * 1000
        secondsMs = cd['seconds'] * 1000
        self.countdownms.set(hoursMs + minutesMs + secondsMs)
        
    def ctl_ob_cur_frame(self):
        if self.curFrame.get() < 1:
            #if len(self.timing_data.get()) > 0:
            self.curFrame.set(1)
        if self.curImgFrame.get() < 1:
            #if len(self.images.get()) > 0: 
            self.curImgFrame.set(1)
        if self.curFrame.get() > len(self.timing_data.get()):
            self.curFrame.set(len(self.timing_data.get()))
        if self.curImgFrame.get() > len(self.images.get()):
            self.curImgFrame.set(len(self.images.get()))         