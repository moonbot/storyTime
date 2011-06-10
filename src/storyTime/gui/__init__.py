import os

from production import sequences

import storyTime
from storyTime import get_log
import storyTime.gui
from storyTime.gui.utils import enum, Observable

LOG = get_log(__name__)

def run_gui(**kwargs):
    """Run the Sync Gui"""
    import storyTime.gui.qt
    storyTime.gui.qt.run_gui()
        
    
class StoryTimeControlUI(object):
    
    def ctl_import_sequence(self):
        raise NotImplementedError
    
    def ctl_import_from_sequence(self, path):
        raise NotImplementedError
    
    def ctl_import_from_directory(self, path):
        raise NotImplementedError
    
    def ctl_open_project(self, path):
        raise NotImplementedError
    
    def ctl_save_project(self, path):
        raise NotImplementedError
    
    def ctl_save_as_project(self, path):
        raise NotImplementedError
    
    def ctl_toggle_play(self):
        raise NotImplementedError
    
    def ctl_toggle_record(self):
        raise NotImplementedError
    
    def ctl_set_fps(self, fpsIndex):
        raise NotImplementedError
    
    def ctl_set_custom_fps(self):
        raise NotImplementedError
    
    def ctl_goto_frame(self, frame):
        raise NotImplementedError
    
    def ctl_inc_frame(self):
        """Increment the current frame by 1"""
        raise NotImplementedError
    
    #def ctl_get_frame_str(self):
        #raise NotImplementedError
    
    def ctl_center_window(self):
        raise NotImplementedError
    
    #def build_fps_options(self):
        #raise NotImplementedError
    
    #def create_frames_list(self, fps):
        #raise NotImplementedError
    
    #def cleanup(self):
        #raise NotImplementedError
    
    def to_xml(self):
        """Return the app's data formatted to an XML string"""
        raise NotImplementedError
        
    #View function
    def view_get_data(self):
        raise NotImplementedError
    
    #View function
    def view_set_data(self, data):
        raise NotImplementedError
    
    def view_stop(self):
        """
        Stop recording and/or playback and returns the time elapsed since
        the previous update_timer event.
        """
        raise NotImplementedError
    
    def start_timer(self):
        raise NotImplementedError
    
    def update_timer(self):
        """Refresh the timer and returns the time since the previous call"""
        raise NotImplementedError
    
    def view_init_sequence(self):
        raise NotImplementedError
    
    def view_query_custom_fps(self):
        """Return new custom fps"""
        raise NotImplementedError
    
    def view_browse_import(self):
        """Return the path of the selected file"""
        raise NotImplementedError
        
    def view_set_frame_label(self, label):
        raise NotImplementedError
    
    def load_image(self, path):
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
    
    BUTTON_STATES = enum('ON', 'OFF', 'DISABLED')
    
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
            'fpsIndex':0
        }
        self.add_observables(model)
        
    def add_observables(self, data):
        for key in data.keys():
            data[key] = Observable(data[key])
        self.__dict__.update(data)
    
    
class StoryTimeControl(StoryTimeControlUI):
    
    def ctl_add_model_observers(self):
        self.recording.add_observer(self.ctl_recording_change)
        self.playing.add_observer(self.ctl_playing_change)
        self.curFrame.add_observer(self.ctl_cur_frame_change)
        self.times.add_observer(self.ctl_times_change)
        self.images.add_observer(self.ctl_images_change)
        self.fpsOptions.add_observer(self.ctl_fps_options_change)
        self.fpsIndex.add_observer(self.ctl_fps_index_change)
        
    def ctl_import_from_sequence(self):
        path = self.view_browse_import('Import Image Sequence...')
        if path is not None:
            self.images.set(sequences.file_sequence(path))
            self.ctl_import_sequence()
        
    def ctl_import_from_directory(self):
        path = self.view_browse_import('Import Image Directory...')
        if path is not None:
            ext = os.path.splitext(path)[1]
            dir = os.path.split(path)[0]
            images = []
            for img in os.listdir(dir):
                if os.path.splitext(img)[1] == ext:
                    images.append(img)
            self.images.set(sorted(images))
            self.ctl_import_sequence()
        
    def import_sequence(self):
        self.stdata['times'] = [1000 for x in range(0,len(self.stdata['images']))]
        self.stdata['start_frame'] = 1
        self.stdata['cur_frame'] = 1
        self.ctl_push()
        self.view_init_sequence(self.stdata['images'])
        
    def create_frames_list(self):
        """Return a list of image times converted to the current fps"""
        self.ctl_pull()
        incFrames = self.stdata['times'][:]
        total = 0
        for i in range(0, len(self.stdata['times'])):
            total = total + self.stdata['times'][i]
            incFrames[i] = int(total * self.stdata['fps'] / 1000)
        fpsFrames = incFrames[:]
        #We can ignore the value at index 0 because it's already the
        #correct value.
        for i in range(1, len(self.timingData)):
            fpsFrames[i] = incFrames[i] - incFrames[i-1]
            if fpsFrames[i] < 1:
                fpsFrames[i] = 1
        return fpsFrames
        
    def to_xml(self):
        self.ctl_pull()
        xml_str = '<?xml version="1.0" ?>\n<fps>{0}</fps>\n<frames>'.format(self.stdata['fps'])
        for i in range(0,len(self.stdata['images'])):
            xml_str += '\n\t<frame>\n\t\t<ms>{0}</ms>\n\t\t<path>{1}</path>\n\t</frame>'.format(self.stdata['images'][i], self.stdata['times'][i])
        xml_str += '\n</frames>\n'
        return xml_str
    
    def ctl_stop(self):
        self.ctl_pull()
        if self.stdata['recording'] == self.BUTTON_STATES.ON:
            self.stdata['times'][self.stdata['cur_frame']] = self.update_timer()
        self.stdata['recording'] = self.BUTTON_STATES.OFF
        self.stdata['playing'] = self.BUTTON_STATES.OFF
        self.ctl_push()
        
    def ctl_fps_index_change(self):
        if self.fpsIndex.get() == len(self.fpsOptions.get()) - 1:
            newFps = int(self.view_query_custom_fps())
            self.fpsOptions.get()[-1][0] = 'Custom ({0} fps...'.format(newFps)
            self.fpsOptions.get()[-1][1] = newFps
        self.fps.get() = self.fpsOptions.get()[self.fpsIndex.get()][1]
        
    def ctl_fps_options_change(self):
        self.view_set_fps_options(self.fpsOptions.get())
        
    def ctl_goto_frame(self, frame):
        label = '{0}/{1}'.format(frame, len(self.stdata['images']))
        self.view_set_frame_label(label)
        self.load_image(self.stdata['images'][self.stdata['cur_frame']])
        self.stdata['cur_frame'] = frame
        self.ctl_push()
        
    def ctl_inc_frame(self):
        if self.stdata['cur_frame'] == len(self.stdata['images']):
            self.ctl_stop()
            return
        elif self.stdata['recording']:
            self.stdata['times'][self.stdata['cur_frame']] = self.update_timer()
        ctl_goto_frame(self.stdata['cur_frame'])
        
    def ctl_toggle_record(self):
        pass
        
    def ctl_toggle_play(self):
        pass
    