'''
Created on Jun 13, 2011

@author: clewis

fcpxml - Provides an easy interface to working with Final Cut Pro XML files
'''

import xml.dom.minidom as minidom

class FcpXml(object):
    xml = None
    def __init__(self, xmlFilePath = ''):
        if xmlFilePath is not None and xmlFilePath != '':
            with open(xmlFilePath, 'r') as xmlFile:
                xmlStr = xmlFile.read()
                xmlStr = xmlStr.replace('\n', '')
                xmlStr = xmlStr.replace('\t', '')
                self.xml = minidom.parseString(xmlFile.read())
        else:
            self.xml = minidom.Document()
            
    def build_basic_structure(self, name):
        xmeml = self.addChild('xmeml', self.xml)
        self.addAttr('version', '4', xmeml)
        project = self.addChild('project', xmeml)
        nameE = self.addChild('name', project)
        self.addText(name, nameE)
        self.children = self.addChild('children', project)
        self.sequence = self.addChild('sequence', self.children)
        self.addAttr('id', 'sequence-1', self.sequence)
        media = self.addChild('media', self.sequence)
        video = self.addChild('video', media)
        self.track = self.addChild('track', video)
        enabled = self.addChild('enabled', self.track)
        self.addText('TRUE', enabled)
        locked = self.addChild('locked', self.track)
        
    def addChild(self, childName, parent):
        child = self.xml.createElement(childName)
        parent.appendChild(child)
        
    def addText(self, text, parent):
        child = self.xml.createTextNode(text)
        parent.appendChild(child)
        
    def addAttr(self, key, value, parent):
        attr = self.xml.createAttribute(key)
        attr.value = value
        parent.attributes.setNamedItem(attr)

    def add_image(self, path, start, end):
        """Adds an image clipitem to the default sequence"""
        pass