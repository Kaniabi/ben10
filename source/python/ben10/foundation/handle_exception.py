'''
This module contains utility functions for dealing with exceptions that should be handled in the
application.
'''

from ben10.foundation import log
from ben10.foundation.callback import Callback



# Callback for clients that want to hear about handled exceptions.
on_exception_handled = Callback()

LOG_ERRORS = True

_ignore_expected_exception = 0

#===================================================================================================
# StartIgnoreHandleException
#===================================================================================================
def StartIgnoreHandleException():
    '''
    Starts ignoring any handled exception (will still call the on_exception_handled(), but
    won't log nor call the excepthook).
    '''
    global _ignore_expected_exception
    _ignore_expected_exception += 1



#===================================================================================================
# EndIgnoreHandleException
#===================================================================================================
def EndIgnoreHandleException():
    '''
    Stops ignoring handled exceptions.
    '''
    global _ignore_expected_exception
    _ignore_expected_exception -= 1


#===================================================================================================
# HandleException
#===================================================================================================
def HandleException(msg):
    '''
    Handles the current exception (in sys.exc_info()) without actually continuing its raise.

    It should be used when for some reason the current exception should not stop the current
    execution flow but should still be shown to the user and reported accordingly.
    '''
    # Let listeners know about the exception (usually the test case)
    on_exception_handled()

    if _ignore_expected_exception > 0:
        return  # Don't log nor call excepthook.

    if LOG_ERRORS:
        # Log it
        log.Exception(msg)

    # And just call the except hook (and keep on going with the calls) -- in the application
    # this should trigger the except dialog.
    import sys
    sys.excepthook(*sys.exc_info())
