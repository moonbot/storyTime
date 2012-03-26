"""
gui.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

from storyTime import model, view, controller
import logging
import sys

LOG = logging.getLogger('storyTime.gui')

def run_gui(**kwargs):
    LOG.debug('Initializing StoryTime...')
    m = model.StoryTimeModel()
    v = view.StoryTimeView()
    c = controller.StoryTimeController()
    return c.run()

