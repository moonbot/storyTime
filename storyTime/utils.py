
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import QUiLoader
from datetime import datetime
import logging
import math
import os
import re
import string
import subprocess
import sys
import unicodedata
import tempfile
import stat

LOG = logging.getLogger('storyTime.utils')


def isFrozen():
    """
    Return whether we are frozen via py2exe.
    This will affect how we find out where we are located.
    """
    return hasattr(sys, 'frozen')

def modulePath(withinPackage=False):
    """ Return the program's directory, even when frozen via py2exe. """
    if isFrozen():
        return os.path.dirname(sys.executable)
    else:
        dir_ = os.path.dirname(__file__)
        if withinPackage:
            return dir_
        else:
            return os.path.dirname(dir_)


def loadUi(path, parent):
    """ Load the given ui file relative to this package """
    fullPath = os.path.join(modulePath(True), path)
    LOG.debug(fullPath)
    if not os.path.isfile(fullPath):
        raise ValueError('ui file not found: {0}'.format(fullPath))
    loader = QUiLoader()
    file_ = QFile(fullPath)
    file_.open(QFile.ReadOnly)
    widget = loader.load(file_, parent)
    attachUi(widget, parent)
    file_.close()
    return widget


def attachUi(widget, parent):
    if parent is None:
        return
    if parent.layout() is None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        parent.setLayout(layout)
    LOG.debug('adding {0} to {1}'.format(widget, parent))
    parent.layout().addWidget(widget)


def enum(*args):
    enums = dict(zip(args, range(len(args))))
    enums['names'] = args
    return type('enum', (), enums)

def openDir(dir_):
    """
    Open the given directory using the platform appropriate file browser
    """
    dir_ = os.path.expanduser(dir_)
    if os.path.isfile(dir_):
        dir_ = os.path.dirname(dir_)
    if os.path.isdir(dir_):
        if sys.platform == 'win32':
            dir_ = os.path.normpath(dir_)
            subprocess.Popen(['explorer.exe', dir_])
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', dir_])
        elif sys.platform == 'linux2':
            pass

def get_latest_version(dirname):
    """Return the latest version of the given filename"""
    VERS_RE = re.compile('(?P<vers>[v|V]\d+)')
    try:
        filename = os.path.join(dirname, os.listdir(dirname)[0])
        dir_, base = os.path.split(filename)
        pat = VERS_RE.sub('[v|V]\d{3}', base.replace('.', '\.'))
        matches = [x for x in os.listdir(dir_) if re.match(pat, x) and os.path.isfile(os.path.join(dir_, x))]
        return sorted(matches)[-1]
    except:
        return None

def timeString():
    d = datetime.now()
    return d.strftime('%Y%m%d_%H%M%S')


def normalizeFilename(filename):
    validChars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    clean = unicodedata.normalize('NFKD', unicode(filename)).encode('ASCII', 'ignore')
    return ''.join(c for c in clean if c in validChars).replace(' ', '_')


# time based media functions
TIMECODE_FMT = '{hr:02}:{min:02}:{sec:02}:{frame:02}'
FPS = 24

def getTimecode(frame, fps=FPS, percentage=False, timeCodeFmt=TIMECODE_FMT):
    """
    Convert a frame number to a timecode starting at 00:00:00:00
    ``frame`` -- the frame to convert to a time code
    ``fps`` -- the frame rate to use for converting
    ``percentage`` -- if True, will calculate frame digit as a percentage of the fps
    ``timeCodeFmt`` -- a string representing how to format the timecode.
                       should have the keys 'hr', 'min', 'sec', 'frame'
    """
    decimal = frame % fps
    if percentage:
        decimal = decimal / fps * 100.0
    seconds = float(frame) / fps
    minutes = seconds / 60.0
    hours = int(math.floor(minutes / 60.0))
    minutes = int(math.floor(minutes - hours * 60))
    seconds = int(math.floor(seconds - minutes * 60))
    decimal = int(decimal)
    return timeCodeFmt.format(hr=hours, min=minutes, sec=seconds, frame=decimal)


def launchSubprocess(cmd, win_showWindow=False, **kwargs):
    '''
    Helper function for launching subprocesses between mac and windows
    Returns the proc
    '''

    platform = getOS()
    if platform == "windows":
        LOG.debug("Subprocess Command: {0}".format(cmd))
        if not win_showWindow:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs['startupinfo'] = startupinfo
        proc = subprocess.Popen(cmd, **kwargs)
    elif platform in ['mac', 'linux']:
        LOG.debug("Subprocess Command: {0}".format(cmd))
        proc = subprocess.Popen(cmd, shell=True, **kwargs)
    return proc

def getTmpPath(suffix=""):
    '''
    Get a temp file name using tempfile.
    We only want the filename, so we'll remove the file tempfile creates.
    '''
    tmpFile = tempfile.mkstemp(suffix=suffix, text=True)[1]
    try:
        os.remove(tmpFile)
    except:
        pass
    return tmpFile


def launchSubprocessInShell(cmd, keepOpen=False):
    '''
    Launch the supplied command in a shell window for any OS
    '''
    platform = getOS()
    if platform == 'mac':
        ext = ".command"
        path = getTmpPath(ext)
        content = "{0}".format(cmd, path)
        if not keepOpen:
            content += "\nexit"
        f = open(path, 'w')
        f.write(content)
        f.close()
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)
        cmd = "open \"{0}\"".format(path)
        launchSubprocess(cmd)
        LOG.debug("Subprocess Temp File: {0}".format(path))
    if platform == 'windows':
        ext = ".bat"
        path = getTmpPath(ext)
        path = os.path.normpath(path)
        content = "{0}".format(cmd, path)
        if not keepOpen:
            content += "\nexit"
        f = open(path, 'w')
        f.write(content)
        f.close()
        cmd = "start {0}".format(path)
        launchSubprocess(cmd, shell=True)
        LOG.debug("Subprocess Temp File: {0}".format(path))

def getOS():
    '''
    Get the os of the current system in a standard format
    '''
    if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):
        return "windows"
    elif (sys.platform.lower() == "darwin"):
        return "mac"
    else:
        return "linux"