

import os
import sys
import subprocess

UIC = 'C:/Python27/Scripts/pyside-uic'
DIR = 'views'

def main():
    dir_ = os.path.abspath(DIR)
    if not os.path.isdir(dir_):
        raise ValueError('directory does not exist: {0}'.format(dir_))
    print('checking for uis in {0}...'.format(dir_))
    uis = [i for i in os.listdir(dir_) if os.path.splitext(i)[-1] == '.ui']
    for ui in uis:
        py = ui.replace('.', '_') + '.py'
        print('{0} -> {1}'.format(ui, py))
        args = [UIC, '-o', os.path.join(dir_, py), os.path.join(dir_, ui)]
        subprocess.Popen(args)


if __name__ == '__main__':
    main()