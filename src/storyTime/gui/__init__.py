import storyTime
from storyTime import get_log

LOG = get_log(__name__)

def run_gui(**kwargs):
    """Run the Sync Gui"""
    import storyTime.gui.qt
    storyTime.gui.qt.run_gui()