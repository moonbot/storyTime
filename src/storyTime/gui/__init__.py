
import sys
import os
import xml.dom.minidom

from production import sequences

from storytime.utils import enum, Observable


def run_gui(**kwargs):
    import qt
    """Run the Sync Gui"""
    qt.run_gui()
    
    
class StoryTimeControlUI(object):
    
    def view_browse_open(self, caption):
        """Return the path of the selected file"""
        raise NotImplementedError
    
    def view_browse_save_as(self):
        """Return the path of the selected file"""
        raise NotImplementedError
    
    def view_update_timer(self):
        """Refresh the timer and returns the time since the previous call"""
        raise NotImplementedError
    
    def view_start_timer(self, ms):
        """Start a timer to call an event in ms milliseconds"""
        raise NotImplementedError
    
    def view_query_custom_fps(self):
        """Query the user for a custom fps and return the value"""
        raise NotImplementedError
    
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
    
    FPS_OPTIONS = [
        ['Film (24 fps)', 24],
        ['PAL (25 fps)', 25],
        ['NTSC (30 fps)', 30],
        ['Show (48 fps)', 48],
        ['PAL Field (50 fps)', 50],
        ['NTSC Field (60 fps)', 60],
        ['Custom...', 12]
    ]
    
    BUTTON_STATES = enum('OFF', 'ON', 'DISABLED')
    
    def init_model(self):
        model = {
            'recording':self.BUTTON_STATES.OFF,
            'playing':self.BUTTON_STATES.OFF,
            'startFrame':0,
            'curFrame':0,
            'times':[],
            'images':[],
            'fps':24,
            'fpsOptions':self.FPS_OPTIONS,
            'fpsIndex':0,
            'savePath':''
        }
        self.add_observables(model)
        
    def add_observables(self, data):
        for key in data.keys():
            data[key] = Observable(data[key])
        self.__dict__.update(data)
        
        
class StoryTimeControl(StoryTimeControlUI, StoryTimeModel):
        
    def create_frames_list(self):
        """Return a list of image times converted to the current fps"""
        incFrames = self.times.get()[:]
        total = 0
        for i in range(0, len(self.times.get())):
            total = total + self.times.get()[i]
            incFrames[i] = int(total * self.fps.get() / 1000)
        fpsFrames = incFrames[:]
        #We can ignore the value at index 0 because it's already the
        #correct value.
        for i in range(1, len(self.times.get())):
            fpsFrames[i] = incFrames[i] - incFrames[i-1]
            if fpsFrames[i] < 1:
                fpsFrames[i] = 1
        return fpsFrames
    
    def from_xml(self, xmlStr):
        xmlStr = xmlStr.replace('\n', '')
        xmlStr = xmlStr.replace('\t', '')
        xmlDoc = xml.dom.minidom.parseString(xmlStr)
        mainElement = xmlDoc.getElementsByTagName('storyTime')[0]
        fps = mainElement.getElementsByTagName('fps')[0].childNodes[0].nodeValue
        framesElement = mainElement.getElementsByTagName('frames')[0]
        images = []
        times = []
        for frameElement in framesElement.childNodes:
            images.append(frameElement.childNodes[0].childNodes[0].nodeValue)
            times.append(int(frameElement.childNodes[1].childNodes[0].nodeValue))
        self.fps.set(fps)
        self.images.set(images)
        self.times.set(times)
        
    def to_xml(self):
        xmlDoc = xml.dom.minidom.Document()
        stElement = xmlDoc.createElement('storyTime')
        xmlDoc.appendChild(stElement)
        fpsElement = xmlDoc.createElement('fps')
        stElement.appendChild(fpsElement)
        fpsText = xmlDoc.createTextNode(str(self.fps.get()))
        fpsElement.appendChild(fpsText)
        framesElement = xmlDoc.createElement('frames')
        stElement.appendChild(framesElement)
        for i in range(0, len(self.images.get())):
            frameElement = xmlDoc.createElement('frame')
            framesElement.appendChild(frameElement)
            pathElement = xmlDoc.createElement('path')
            frameElement.appendChild(pathElement)
            pathText = xmlDoc.createTextNode(self.images.get()[i])
            pathElement.appendChild(pathText)
            msElement = xmlDoc.createElement('ms')
            frameElement.appendChild(msElement)
            msText = xmlDoc.createTextNode(str(self.times.get()[i]))
            msElement.appendChild(msText)
        return xmlDoc.toprettyxml('\t', '\n')
    
    def ctl_open(self):
        path = self.view_browse_open('Open...')
        if path is not None and path != '':
            with open(path, 'r') as openFile:
                self.from_xml(openFile.read())
            self.savePath.set(path)
    
    def ctl_import_from_sequence(self):
        path = self.view_browse_open('Import Image Sequence...')
        if path is not None and path != '':
            self.images.set(sequences.file_sequence(path))
            self.times.set([1000 for x in range(0,len(self.images.get()))])
            self.startFrame.set(1)
            self.curFrame.set(1)
            
    def ctl_import_directory(self):
        raise NotImplementedError
    
    def ctl_export_fcp(self):
        path = self.view_browse_save_as()
        if path is not None and path != '':
            print 'yay!'
            
    def ctl_save(self):
        if self.savePath.get() == '':
            self.ctl_save_as()
            return
        with open(self.savePath.get(), 'w') as saveFile:
            saveFile.write(self.to_xml())
            
    def ctl_save_as(self):
        path = self.view_browse_save_as()
        if path is not None and path != '':
            with open(path, 'w') as saveFile:
                saveFile.write(self.to_xml())
            self.savePath.set(path)
            
    def ctl_stop(self):
        if self.recording.get() == self.BUTTON_STATES.ON:
            self.times.get()[self.curFrame.get() - 1] = self.view_update_timer()
        self.recording.set(self.BUTTON_STATES.OFF)
        self.playing.set(self.BUTTON_STATES.OFF)
        
    def ctl_goto_frame(self, frame):
        self.curFrame.set(frame)
            
    def ctl_inc_frame(self):
        if self.curFrame.get() == len(self.images.get()):
            self.ctl_stop()
            return
        elif self.recording.get() == self.BUTTON_STATES.ON:
            self.times.get()[self.curFrame.get() - 1] = self.view_update_timer()
        self.curFrame.set(self.curFrame.get() + 1)
        
    def ctl_dec_frame(self):
        self.ctl_stop()
        self.curFrame.set(self.curFrame.get() - 1)
            
    def ctl_ob_cur_frame(self):
        if self.curFrame.get() < 1:
            self.curFrame.set(1)
        elif self.curFrame.get() > len(self.images.get()):
            self.curFrame.set(len(self.images.get()))
            
    def ctl_change_fps(self, index):
        self.fpsIndex.set(index)
        if self.fpsIndex.get() == len(self.fpsOptions.get()) - 1:
            newFps = self.view_query_custom_fps()
            self.fpsOptions.get()[-1][0] = 'Custom ({0}) fps...'.format(newFps)
            self.fpsOptions.get()[-1][1] = newFps
            self.fpsOptions.set(self.fpsOptions.get())
        self.fps.set(self.fpsOptions.get()[self.fpsIndex.get()][1])
        
    def ctl_update_playback(self):
        if self.curFrame.get() == len(self.images.get()):
            self.ctl_stop()
            return
        elif self.playing.get() == self.BUTTON_STATES.ON:
            self.curFrame.set(self.curFrame.get() + 1)
            self.view_start_timer(self.times.get()[self.curFrame.get() - 1])
        
    def ctl_toggle_record(self):
        if not (self.recording.get() == self.BUTTON_STATES.DISABLED):
            self.recording.set(not self.recording.get())
            if self.recording.get() == self.BUTTON_STATES.ON:
                if self.curFrame.get() == len(self.images.get()):
                    self.curFrame.set(1)
                self.view_update_timer()
                self.startFrame.set(self.curFrame.get())
                self.playing.set(self.BUTTON_STATES.DISABLED)
            else:
                self.ctl_stop()
    
    def ctl_toggle_play(self):
        if not (self.playing.get() == self.BUTTON_STATES.DISABLED):
            self.playing.set(not self.playing.get())
            if self.playing.get() == self.BUTTON_STATES.ON:
                if self.curFrame.get() == len(self.images.get()):
                    self.curFrame.set(1)
                self.view_start_timer(self.times.get()[self.curFrame.get() - 1])
                self.startFrame.set(self.curFrame.get())
                self.recording.set(self.BUTTON_STATES.DISABLED)
            else:
                self.ctl_stop()
    