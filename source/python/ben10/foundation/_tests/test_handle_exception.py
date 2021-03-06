from __future__ import unicode_literals
from ben10.foundation import handle_exception
from ben10.foundation.string import Dedent
import pytest
import sys



#===================================================================================================
# exception_handler
#===================================================================================================
@pytest.fixture
def exception_handler(request):
    '''
    Captures the exceptions using handle_exception module.

    This code was in coilib50's base TestCase.
    '''

    class Handler():

        def __init__(self):
            self.exceptions = []
            handle_exception.on_exception_handled.Register(self._OnHandledException)

        def Finalizer(self):
            self.exceptions = []
            handle_exception.on_exception_handled.Unregister(self._OnHandledException)

        def _OnHandledException(self):
            info = sys.exc_info()
            self.exceptions.append(info)

    result = Handler()
    request.addfinalizer(result.Finalizer)
    return result



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testHandleException(self, exception_handler, capfd, handled_exceptions):
        try:
            raise RuntimeError()
        except:
            handle_exception.HandleException('Test')
        assert len(exception_handler.exceptions) == 1

        obtained = capfd.readouterr()
        assert tuple(obtained) == (
            '',
            Dedent(
                '''
                Traceback (most recent call last):
                  File "%s", line 47, in testHandleException
                    raise RuntimeError()
                RuntimeError

                ''' % __file__,
            )
        )
        handled_exceptions.ClearHandledExceptions()


    def testIgnoreHandleException(self, exception_handler, capfd, handled_exceptions):
        handle_exception.StartIgnoreHandleException()
        try:
            try:
                raise RuntimeError()
            except:
                handle_exception.HandleException('Test')
            assert len(exception_handler.exceptions) == 1
        finally:
            handle_exception.EndIgnoreHandleException()

        obtained = capfd.readouterr()
        assert tuple(obtained) == (u'', u'')
        handled_exceptions.ClearHandledExceptions()
