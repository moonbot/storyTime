
import math
import os
import re


def enum(*args):
    enums = dict(zip(args, range(len(args))))
    enums['names'] = args
    return type('enum', (), enums)

def listdir(path):
    """
    Return a sorted list of the full paths of the entries in the 
    current directory.
    
    `path` -- path of directory or filename in directory to list
    """
    if os.path.isfile(path):
        path = os.path.split(path)[0]
    return sorted([os.path.join(path, x) for x in os.listdir(path)])

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


# time based media functions
TIMECODE_FMT = '{hr:02}:{min:02}:{sec:02}:{frame:02}'
FPS = 24

def get_timecode(frame, fps=FPS, percentage=False, timeCodeFmt=TIMECODE_FMT):
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


