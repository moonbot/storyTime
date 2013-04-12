from distutils.core import setup
import py2exe
import os
import sys
import shutil
import fnmatch

pyDir = os.path.dirname(sys.executable)
pysideDir = os.path.join(pyDir, 'Lib/site-packages/PySide')
qtconf = '[PATHS]\nBinaries=.\nPlugins=plugins'

ico = 'storyTime/images/StoryTime.ico'
uiDir = 'storyTime/views'
uiFiles = [os.path.join(uiDir, ui) for ui in os.listdir(uiDir)]
imgDir = 'storyTime/images'
imgFiles = [os.path.join(imgDir, i) for i in os.listdir(imgDir)]

setup(
    options = {'py2exe': {
        'dist_dir':'dist_windows',
        'compressed':1,
        'optimize':2,
        'bundle_files': 3,
        'includes':['PySide.QtXml'],
        },
    },
    data_files = [
        ('views', uiFiles),
        ('images', imgFiles),
        ('bin/windows', ["storyTime/bin/windows/ffmpeg.exe"]),
        ('bin/mac', ["storyTime/bin/mac/ffmpeg"]),
    ],
    windows = [{
        'dest_base':'StoryTime',
        'script':'run.py',
        'icon_resources':[(i, ico) for i in range(2)]
    }],
    zipfile = None,
)


# copy plugins and write qt.conf
if os.path.isdir('dist_windows/plugins'):
    shutil.rmtree('dist_windows/plugins')
shutil.copytree(os.path.abspath('storyTime/bin/windows/plugins'), 'dist_windows/plugins')
with open('dist_windows/qt.conf', 'wb') as fp:
    fp.write(qtconf)
