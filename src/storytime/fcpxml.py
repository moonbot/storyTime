'''
Created on Jun 13, 2011

@author: clewis

fcpxml - Provides an easy interface to working with Final Cut Pro XML files

NOTICE: Files should be referenced from the network instead of local paths
'''
import os
import re
import xml.dom.minidom as minidom

from PIL import Image
import hourglass


#Ugly, ugly, lazy hack to format XML correctly
def fixed_writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" {0}=\"".format(a_name))
        minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        if len(self.childNodes) == 1 and self.childNodes[0].nodeType == minidom.Node.TEXT_NODE:
            writer.write(">")
            self.childNodes[0].writexml(writer, "", "", "")
            writer.write("</{0}>{1}".format(self.tagName, newl))
            return
        writer.write(">{0}".format(newl))
        for node in self.childNodes:
            node.writexml(writer,indent+addindent,addindent,newl)
        writer.write("{0}</{1}>{2}".format(indent,self.tagName,newl))
    else:
        writer.write("/>{0}".format(newl))


class FcpXmlError(Exception):
    pass


class FcpXml(object):
    
    xml = None
    images = []
    audioPath = ''
    curId = 1
    curIdSeq = 1
    settings = {
        'name':'',
        'ntsc':'TRUE',
        'fps':'30',
        'displayformat':'NDF',
        'width':'0',
        'height':'0',
        'os':'win',
        'videowidthFCP':'1280',
        'videoheightFCP':'720',
        'videowidthPremiere':'720',
        'videoheightPremiere':'480'
    }
    
    def __init__(self, name = '', images = [], audioPath = '', fps=30, ntsc=True, OS='win'):
        """
        TODO:
        -Turn this class into a function with child functions instead
        
        `xmlFilePath` -- the path of the xml file to be saved
        `images` -- a zipped list of image paths and frame counts
        `fps` -- the frame rate
        `ntsc` -- wether the frame rate has ntsc frame reduction
        """
        minidom.Element.writexml = fixed_writexml
        
        imp = minidom.DOMImplementation()
        doctype = imp.createDocumentType('xmeml', '', '')
        self.xml = imp.createDocument(None, 'xmeml', doctype)
        self.images = images
        self.audioPath = audioPath
        self.includeAudio = os.path.exists(audioPath)
        self.settings['name'] = name
        self.settings['fps'] = str(fps)
        self.settings['os'] = OS
        if ntsc:
            self.settings['ntsc'] = 'TRUE'
        else:
            self.settings['ntsc'] = 'FALSE'
        if fps == 30:
            self.settings['displayformat'] = 'DF'
        else:
            self.settings['displayformat'] = 'NDF'
        size = self.getImageSize(images[0][0])
        self.settings['width'] = str(size[0])
        self.settings['height'] = str(size[1])
        self.build()
        
    def getStr(self):
        return self.xml.toprettyxml()
            
    def build(self):
        self.xml.removeChild(self.xml.childNodes[1])
        xmeml = self.addChild('xmeml', self.xml, version=4)
        project = self.addChild('project', xmeml)
        self.addChild('name', project, self.settings['name'])
        self.children = self.addChild('children', project)
        for image in self.images:
            self.addClip(image[0])
        self.curId = 1
        if self.includeAudio:
            self.addSoundClip()
        self.addSequence()
        start = 0
        for image in self.images:
            end = start + image[1]
            self.addClipitem(start, end)
            start += image[1]
        if self.includeAudio:
            self.addSoundClipitem(end)
        
    def addClip(self, path):
        """Add an image clip to the default sequence"""
        mastercliptext = 'masterclip-{0}'.format(self.curId)
        filetext = 'file-{0}'.format(self.curId)
        clipitemtext = 'clipitem-{0}'.format(self.curId)
        nametext = os.path.split(path)[1]
        pathurltext = self.convertPath(path)
        clip = self.addChild('clip', self.children, '', id=mastercliptext)
        self.addChild('masterclipid', clip, mastercliptext)
        self.addChild('ismasterclip', clip, 'TRUE')
        self.addChild('name', clip, nametext)
        self.addChild('duration', clip, '150')
        self.addRate(clip)
        media = self.addChild('media', clip)
        video = self.addChild('video', media)
        track = self.addChild('track', video)
        clipitem = self.addChild('clipitem', track, '', id=clipitemtext)
        self.addChild('masterclipid', clipitem, mastercliptext)
        fileE = self.addChild('file', clipitem, '', id=filetext)
        self.addChild('name', fileE, nametext)
        self.addChild('pathurl', fileE, pathurltext)
        self.addRate(fileE)
        self.addTimecode(0, fileE)
        media = self.addChild('media', fileE)
        video = self.addChild('video', media)
        self.addChild('duration', video, '18000')
        sc = self.addChild('samplecharacteristics', video)
        self.addRate(sc)
        self.addChild('width', sc, self.settings['width'])
        self.addChild('height', sc, self.settings['height'])
        self.addChild('anamorphic', sc, 'FALSE')
        self.addChild('pixelaspectratio', sc, 'square')
        self.addChild('fielddominance', sc, 'none')
        self.curId += 1
        
    def addSequence(self):
        sequence = self.addChild('sequence', self.children, '', id='sequence-1')
        self.addChild('name', sequence, 'Sequence 01')
        self.addChild('duration', sequence, '150')
        self.addRate(sequence)
        media = self.addChild('media', sequence)
        video = self.addChild('video', media)
        format = self.addChild('format', video)
        sc = self.addChild('samplecharacteristics', format)
        self.addRate(sc)
        if self.settings['os'] == 'win':
            self.addChild('width', sc, self.settings['videowidthPremiere'])
            self.addChild('height', sc, self.settings['videoheightPremiere'])
        elif self.settings['os'] == 'mac':
            self.addChild('width', sc, self.settings['videowidthFCP'])
            self.addChild('height', sc, self.settings['videoheightFCP'])
        else:
            raise FcpXmlError('Not a valid os')
        self.addChild('anamorphic', sc, 'FALSE')
        self.addChild('pixelaspectratio', sc, 'NTSC-601')
        self.addChild('fielddominance', sc, 'none')
        self.addChild('colordepth', sc, '24')
        self.track = self.addChild('track', video)
        self.addChild('enabled', self.track, 'TRUE')
        self.addChild('locked', self.track, 'FALSE')
        audio = self.addChild('audio', media)
        audioformat = self.addChild('format', audio)
        sc = self.addChild('samplecharacteristics', audioformat)
        self.addChild('depth', sc, '16')
        self.addChild('samplerate', sc, '48000')
        self.audiotrack = self.addChild('track', audio)
        self.addChild('enabled', self.audiotrack, 'TRUE')
        self.addChild('locked', self.audiotrack, 'FALSE')
        self.addTimecode(0, sequence)
        
    def addSoundClip(self):
        mastercliptext = 'masterclip-{0}'.format(len(self.images) * 2 + 1)
        filetext = 'file-{0}'.format(len(self.images) * 2 + 1)
        clipitemtext = 'clipitem-{0}'.format(len(self.images) * 2 + 1)
        nametext = os.path.split(self.audioPath)[1]
        pathurltext = self.convertPath(self.audioPath)
        clip = self.addChild('clip', self.children, '', id=mastercliptext)
        self.addChild('masterclipid', clip, mastercliptext)
        self.addChild('ismasterclip', clip, 'TRUE')
        self.addChild('name', clip, nametext)
        self.addChild('duration', clip, '150')
        self.addRate(clip)
        media = self.addChild('media', clip)
        audio = self.addChild('audio', media)
        track = self.addChild('track', audio)
        clipitem = self.addChild('clipitem', track, '', id=clipitemtext)
        self.addChild('masterclipid', clipitem, mastercliptext)
        fileE = self.addChild('file', clipitem, '', id=filetext)
        self.addChild('name', fileE, nametext)
        self.addChild('pathurl', fileE, pathurltext)
        self.addRate(fileE)
        self.addChild('duration', fileE, '150')
        self.addTimecode(0, fileE)
        media = self.addChild('media', fileE)
        audio = self.addChild('audio', media)
        sc = self.addChild('samplecharacteristics', audio)
        self.addChild('depth', sc, '16')
        self.addChild('samplerate', sc, '44100')
        self.addChild('channelcount', audio, '1')
        self.addChild('layout', audio, 'mono')
        ac = self.addChild('audiochannel', audio)
        self.addChild('sourcechannel', ac, '1')
        self.addChild('channellabel', ac, 'discrete')
        st = self.addChild('sourcetrack', clipitem)
        self.addChild('mediatype', st, 'audio')
        self.addChild('trackindex', st, '1')
        
    def addSoundClipitem(self, end):
        mastercliptext = 'masterclip-{0}'.format(len(self.images) * 2 + 1)
        filetext = 'file-{0}'.format(len(self.images) * 2 + 1)
        clipitemtext = 'clipitem-{0}'.format(len(self.images) * 2 + 2)
        clipitem = self.addChild('clipitem', self.audiotrack, '', id=clipitemtext)
        self.addChild('masterclipid', clipitem, mastercliptext)
        self.addChild('enabled', clipitem, 'TRUE')
        self.addChild('duration', clipitem, '100')
        self.addChild('duration', clipitem, '150')
        self.addChild('start', clipitem, '0')
        self.addChild('end', clipitem, str(end))
        self.addChild('file', clipitem, '', id=filetext)
        st = self.addChild('sourcetrack', clipitem)
        self.addChild('mediatype', st, 'audio')
        self.addChild('trackindex', st, '1')
        
    def addClipitem(self, start, end):
        clipitemtext = 'clipitem-{0}'.format(self.curId + len(self.images))
        mastercliptext = 'masterclip-{0}'.format(self.curId)
        filetext = 'file-{0}'.format(self.curId)
        clipitem = self.addChild('clipitem', self.track, '', id=clipitemtext)
        self.addChild('masterclipid', clipitem, mastercliptext)
        self.addChild('enabled', clipitem, 'TRUE')
        self.addChild('duration', clipitem, '150')
        self.addChild('start', clipitem, str(start))
        self.addChild('end', clipitem, str(end))
        self.addChild('file', clipitem, '', id=filetext)
        self.curId += 1
        
    def addChild(self, childName, parent, text='', **kwargs):
        child = self.xml.createElement(childName)
        parent.appendChild(child)
        if text != '':
            textChild = self.xml.createTextNode(str(text))
            child.appendChild(textChild)
        for key in kwargs.keys():
            attr = self.xml.createAttribute(key)
            attr.value = str(kwargs[key])
            child.attributes.setNamedItem(attr)
        return child
        
    def addTimecode(self, frame, parent):
        
        timecode = self.addChild('timecode', parent)
        self.addRate(timecode)
        self.addChild('frame', timecode, str(frame))
        self.addChild('displayformat', timecode, self.settings['displayformat'])
        self.addChild('source', timecode, 'source')
        
    def addRate(self, parent):
        rateNode = self.addChild('rate', parent)
        self.addChild('timebase', rateNode, self.settings['fps'])
        self.addChild('ntsc', rateNode, self.settings['ntsc'])
    
    def getImageSize(self, path):
        img = Image.open(path)
        if img is not None:
            return img.size
        
    def convertPath(self, path):
        if self.settings['os'] == 'win':
            return self.convertPathWin(path)
        elif self.settings['os'] == 'mac':
            return self.convertPathMac(path)
        else:
            raise FcpXmlError('Not a valid os')
        
    def convertPathWin(self, path):
        return 'file://localhost/' + path.replace(':', '%3a').replace(' ', '%20').replace('\\', '/')
    
    def convertPathMac(self, path):
        drive = os.path.splitdrive(path)[0] + '\\'
        mapping = ''
        for project in hourglass.all_projects():
            if project['paths'].has_key('network'):
                if project['paths']['network'] == drive:
                    mapping = project['mappings']['network']
        if mapping != '':
            path = path.replace(os.path.splitdrive(path)[0], mapping[mapping.index('/projects/'):])
            path = path.replace(':', '%3a').replace(' ', '%20').replace('\\', '/')
            path = 'file://localhost/Volumes/HOME' + path
        else:
            path = path.replace(':', '%3a').replace(' ', '%20').replace('\\', '/')
            path = 'file://localhost/Volumes/HOME' + os.path.splitdrive(path)[1]
        return path
    