from distutils.core import setup
import py2exe
import os

ico = 'storyTime/images/StoryTime.ico'
uiDir = 'storyTime/views'
uiFiles = [os.path.join(uiDir, ui) for ui in os.listdir(uiDir)]

setup(
    options = {'py2exe': {
        'compressed':1,
        'optimize':2,
        'bundle_files': 3,
        'includes':['PySide.QtXml'],
        },
    },
    data_files = [
        ('views', uiFiles),
    ],
    windows = [{
        'dest_base':'StoryTime',
        'script':'storyTime',
        'icon_resources':[(i, ico) for i in range(2)]
    }],
    zipfile = None,
)
