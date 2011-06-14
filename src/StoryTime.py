"""
Run the StoryTime GUI

Traps stderr into stdout to nullify py2exe error logs window.
"""

# nullify py2exe window error logs
import sys
# sys.stderr = sys.stdout
def run():
    import storytime
    storytime.run()
    
run()