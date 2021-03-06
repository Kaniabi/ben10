from __future__ import unicode_literals
from ben10.bytes_only_environ_wrapper import ReplaceEnvironWithWrapper
#===================================================================================================
# Placeholder for the "tr" function
# The "tr" function is implemented by xgui20.translate
# BEN10 should not depend on Qt, but regarding translation, it depends indirectly because of the use
# of Qt translation mechanism.
#
# The "tr" function must be defined and used solely as a builtin symbol and *never* as a direct
# import. Failing to do so will break the transation mechanism.
#===================================================================================================
def _tr(text, context=None):
    return text

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

if not hasattr(builtins, 'tr'):
    builtins.tr = _tr



# Adding an alias to `open`: since use of bare `open` is deprecated since we ported to unicode-only
# strings, this alias exists so code that can't work with io.open (usually because it passes the file
# object to C++, which won't work with the wrapper object returned by io.open) use this to
# communicate this intention
builtins.builtin_open = open

ReplaceEnvironWithWrapper()
