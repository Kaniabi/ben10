'''
This module tries to import the odict class from the ordereddict shared-resource. If this fails,
returns a less performing version implemented in Python.

This switch is used by some basic class in coilib50 in order to allow Builds to work without any
external dependencies.
'''

from ._odict import PythonOrderedDict

try:
    # Previously this code was:
    #     from odict import odict
    # But cx_freeze seemed to have some trouble finding this module, so we changed to the current
    # code below.
    try:
        # This is the official import, as generated by the ordereddict build system.
        # This is valid only on dist-12.0
        import _ordereddict
        odict = _ordereddict.ordereddict
    except ImportError:
        # This is how the dist-1104 is organized and does not match the default build of ordereddict.
        # Kept for backward compatibility to dist-1104
        import odict._ordereddict
        odict = odict._ordereddict.ordereddict
except ImportError:
    odict = PythonOrderedDict
