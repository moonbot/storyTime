import os

from production import sequences

import storyTime
from storyTime import get_log

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
    
    #def to_xml(self):
        #raise NotImplementedError
        
    #View function
    def view_get_data(self):
        raise NotImplementedError
    
    #View function
    def view_set_data(self, data):
        raise NotImplementedError

class StoryTimeControl(StoryTimeControlUI):
    
    stdata = {}
    
    FPS_OPTIONS = [
        ['Film (24 fps)', 24],
        ['PAL (25 fps)', 25],
        ['NTSC (30 fps)', 30],
        ['Show (48 fps)', 48],
        ['PAL Field (50 fps)', 50],
        ['NTSC Field (60 fps)', 60],
        ['Customize...', 12]
    ]
    
    def init_model(self):
        self.stdata = {
            'recording':False,
            'playing':False,
            'start_frame':0,
            'cur_frame':0,
            'times':[],
            'images':[],
            'fps':24,
            'fps_opts':self.FPS_OPTIONS
        }
            
    def ctl_pull(self):
        """Pulls data from the view"""
        data = self.view_get_data()
        if data is None:
            return
        self.stdata = data
        
    def ctl_push(self):
        """Pushes data to the view"""
        self.view_set_data(self.stdata)
        
    def ctl_import_from_sequence(self, path):
        self.stdata['images'] = sequences.file_sequence(path)
        self.ctl_import_sequence()
        
    def ctl_import_from_directory(self, path):
        ext = os.path.splitext(path)[1]
        dir = os.path.split(path)[0]
        images = []
        for img in os.listdir(dir):
            if os.path.splitext(img)[1] == ext:
                images.append(img)
        self.stdata['images'] = sorted(images)
        self.ctl_import_sequence()
        
    def import_sequence(self):
        self.stdata['times'] = [1000 for x in range(0,len(self.stdata['images']))]
        self.stdata['start_frame'] = 1
        self.stdata['cur_frame'] = 1
        self.ctl_push()
        
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
        
    
        
    