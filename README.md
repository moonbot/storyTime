![Image Alt](https://github.com/moonbot/storyTime/raw/master/storyTime/images/storyTime_small.png)

## Story Time

The goal of the Story Time project is to simplify all of the steps it takes for a story artist to turn their ideas into animatics.
Story Time is in **very early development**, and much of the groundwork is subject to change drastically.

Story Time works just like giving a verbal presentation: you step through story boards and deliver an audio pitch in real-time.
The software records your delivery as timing data and audio recordings. You can then export the pitch as a video, or to an
XML format for use with Premiere or Final Cut Pro, where you can refine timing or tweak the edit. Story Time is not designed to
replace traditional editing software, but rather to bring together key elements that will help you get ideas out fast
and allow you to iterate on them quickly.


## Download

The latest compiled applications can be found here:

Windows:
http://sourceforge.net/projects/mb-storytime/files/StoryTime_Setup_v1.1_win64.exe/download

Mac:
http://sourceforge.net/projects/mb-storytime/files/StoryTime_v1.1_mac.zip/download

## Features

- PySide GUI for viewing and recording storyboard timing
- Preview current and upcoming boards while timing
- Auto-Saves working recordings as they are made
- Record audio simultaneously with board timings
- Record and export multiple sessions
- Export XML files for using in Final Cut Pro and Premiere
- Export Movies with audio and video. These are encoded with h264 and aac using ffmpeg

## Wish List

- Drawing tools - simplified suite of drawing tools for creating storyboards in-app
- Basic movement tools - simplified suite of pan/zoom and other things that can be recorded live
- Sound board - create sounds verbally or load from anywhere to be used on demand
- Custom sorting/re-arranging of boards
- Indicate shot grouping and automatic shot code assignment
- Very basic editing tools to make quick fixes
- Improved timeline UI
- Improved exporting options
- Re-record sections without losing an entire recording
- Combine multiple recordings to export them as one video
- Video recording (started)

## System Requirements
- 64-bit Operating System
- Mac/Windows

## Known Limitations
- Images must have even resolutions. Ex: 1920x1080. 1921x1081 will produce errors when exporting a movie.
- Images work best if they are all the same size.

## Usage

- Create storyboards using your preferred drawing application
- Export storyboards named alphabetically (i.e. mySceneA.001.jpg, mySceneA.002.jpg, mySceneB.001.jpg, etc.)
- Open Story Time and drag the boards into the main window
- When ready, press the record button (or hit R) and then tap through the boards

## Exporting

You can export videos or XML files from Story Time. Story Time stores its own files as xml and they can be reopened
easily if you need to re-export a video or anything else.  When exporting for Premiere or Final Cut, be sure
the images can be accessed at the same path used to import them in Story Time.

## Hotkeys

- Space, period, right arrow, down arrow - Go to next image
- Backspace, comma, left arrow, up arrow - Go to previous image
- R - Start/Stop recording
- P - Playback recording
- B - Go to first frame of recording
- E - Go to last frame of recording
- N - Create new recording
- [ - Show previous image preview
- ] - Show next image preview
- 

## Installer
Windows Installer is built using Inno Setup:

http://www.jrsoftware.org/isinfo.php

You can use the win_installer.iss script to build the installer.


## Building

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


## Changelog
v1.1
- Fixed jpeg imports
