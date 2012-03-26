

from storyTime import utils
import logging

LOG = logging.getLogger('storyTime.model')


class StoryTimeModel(object):
    
    BUTTON_STATES = utils.enum('OFF', 'ON', 'DISABLED')
    
    def __init__(self):
        pass
    
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
