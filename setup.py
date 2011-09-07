import sys, os
from distutils.core import setup

cwd = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(cwd, 'src')))
import storyTime


setup(
    name = 'storyTime',
    version = storyTime.__version__,
    author = storyTime.__author__,
    package_dir = {'':'src'},
    packages = ['storyTime', 'storyTime.gui'],
    package_data = {'storyTime': ['images/*', 'test/*']},
    py_modules = ['StoryTime']
)