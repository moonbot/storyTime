from distutils.core import setup
import py2exe
import os
import sys
import shutil

pyDir = os.path.dirname(sys.executable)
pysideDir = os.path.join(pyDir, 'Lib/site-packages/PySide')
qtconf = '[PATHS]\nBinaries=.\nPlugins=plugins'

ico = 'storyTime/images/StoryTime.ico'
uiDir = 'storyTime/views'
uiFiles = [os.path.join(uiDir, ui) for ui in os.listdir(uiDir)]
imgDir = 'storyTime/images'
imgFiles = [os.path.join(imgDir, i) for i in os.listdir(imgDir)]

ffmpeg = 'M:/software/portable/ffmpeg/bin/ffmpeg.exe'

setup(
    options = {'py2exe': {
        'compressed':1,
        'optimize':2,
        'bundle_files': 3,
        'includes':['PySide.QtXml'],
        },
    },
    data_files = [
        ('', [ffmpeg]),
        ('views', uiFiles),
        ('images', imgFiles),
    ],
    windows = [{
        'dest_base':'StoryTime',
        'script':'run.py',
        'icon_resources':[(i, ico) for i in range(2)]
    }],
    zipfile = None,
)


# copy plugins and write qt.conf
if os.path.isdir('dist/plugins'):
    shutil.rmtree('dist/plugins')
shutil.copytree(os.path.join(pysideDir, 'plugins'), 'dist/plugins')
with open('dist/qt.conf', 'wb') as fp:
    fp.write(qtconf)
