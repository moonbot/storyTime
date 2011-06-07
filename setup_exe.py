from distutils.core import setup
import py2exe

setup(
    options = {'py2exe': {'compressed':1, 'optimize':2, 'bundle_files': 1, 'includes':['sip'], 'packages':['PyQt4']}},
    windows = [{'script':'src/StoryTime.py', 'icon_resources':[(0,'src/StoryTime.ico'), (1,'src/StoryTime.ico'), (2,'src/StoryTime.ico'), (3,'src/StoryTime.ico')] }],
    zipfile = None,
)
