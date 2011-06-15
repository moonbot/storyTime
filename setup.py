import sys, os
from distutils.core import setup

cwd = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(cwd, 'src')))
import storytime


setup(
    name = 'storytime',
    version = storytime.__version__,
    author = storytime.__author__,
    package_dir = {'':'src'},
    packages = ['storytime', 'storytime.gui'],
    package_data = {'storytime': ['images/*', 'test/*']},
    py_modules = ['StoryTime']
)