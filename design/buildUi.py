"""
	Util for converting Qt .ui files to PyQt4 classes.
	
	Drag a .ui file onto this script to convert it.
"""

import sys, os
from PyQt4 import uic


def convertUiToPy(uiFile):
    print 'In File: {0}'.format(uiFile)
    pyFile = '{0}.py'.format(os.path.splitext(uiFile)[0])
    print 'Out File: {0}'.format(pyFile)
    if os.path.exists(pyFile):
        print '  Out file already exists. Overwrite? (y/n)'
        result = raw_input()
        if result != 'y':
            return
    
    with open(pyFile, 'wb') as fp:
        uic.compileUi(uiFile, fp, True)
    print 'compiled to %s' % pyFile
    

if __name__ == '__main__':
    if len(sys.argv) > 1:
        uiFile = sys.argv[1]
        convertUiToPy(uiFile)
    else:
        print 'No input file given...'
        raw_input()