## Story Time

Story Time is a tool that allows you to quickly time out story board animatics.
The tool also allows you to record audio and video, making it easy to move from boards to
a presentable pitch quickly.


## Download

The latest compiled applications can be found here:

Windows:
http://sourceforge.net/projects/mb-storytime/files/StoryTime_Setup_v1.0.exe/download

Mac:
http://sourceforge.net/projects/mb-storytime/files/StoryTime_v1.0.zip/download


## Features

- PySide GUI for viewing and recording Story Board timing
- Record audio and video simultaneously with board timings
- Record, manage, and export multiple sessions
- Export XML files for using in Final Cut Pro and Premiere
- Export Movies with audio and video. These are encoded with h264 and aac using ffmpeg.
- Auto-Saves working recordings as they are made
- Preview current and upcoming boards while timing

## System Requirements
- 64-bit Operating System
- Mac/Windows

## Known Limitations
- Images must have even resolutions. Ex: 1920x1080. 1921x1081 will produce errors when exporting a movie.
- Images work best if they are all the same size.

## Usage

To build Story Time simply use the setup_app or setup_exe scripts:

```
: python setup_app.py py2app
```

```
: python setup_exe.py py2exe
```

Story Time also provides commandline usage:

```
: storyTime.exe /path/to/my/storyBoards
```

## Installer
Windows Installer is built using Inno Setup:

http://www.jrsoftware.org/isinfo.php

You can use the win_installer.iss script to build the installer.
