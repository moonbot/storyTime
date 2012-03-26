"""
gui.py

Created by Bohdon Sayre on 2012-03-26.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

__all__ = ['run']

from storyTime import model, view, controller
import logging

LOG = logging.getLogger(__name__)

def run(*args, **kwargs):
    LOG.debug('Initializing StoryTime...')
    m = model.StoryTimeModel()
    view.init_app()
    v = view.StoryTimeView()
    c = controller.StoryTimeController(m, m)
    v.show()
    LOG.debug('Running application...')
    return view.app().exec_()

