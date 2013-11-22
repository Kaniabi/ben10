from ben10.foundation import is_frozen
from ben10.foundation.platform_ import Platform
from ben10.foundation.pushpop import PushPop
from ben10.foundation.uname import GetApplicationDir, GetUserHomeDir, IsRunningOn64BitMachine
import os
import sys



#===================================================================================================
# Test
#===================================================================================================
class Test():

    def testIsRunningOn64BitMachine(self, monkeypatch):
        monkeypatch.setattr(Platform, 'GetCurrentPlatform', classmethod(lambda x:'win64'))
        assert IsRunningOn64BitMachine()

#        TODO: In this case it checks using IsWow64Process... shoudn't be better/easier to check for PROGRAMFILES(x86)
#              environment variable?
#        monkeypatch.setattr(Platform, 'GetCurrentPlatform', classmethod(lambda x:'win32'))
#        assert not IsRunningOn64BitMachine()


    def testGetUserHomeDir(self):
        with PushPop(os, 'environ', dict(HOMEDRIVE='C:/',HOMEPATH='Users/ama',HOME='/home/users/ama')):
            with PushPop(sys, 'platform', 'win32'):
                assert GetUserHomeDir() == '%(HOMEDRIVE)s%(HOMEPATH)s' % os.environ
            with PushPop(sys, 'platform', 'linux2'):
                assert GetUserHomeDir() == '%(HOME)s' % os.environ


    def testGetApplicationDir(self):
        is_frozen_ = is_frozen.SetIsFrozen(False)
        try:
            assert GetApplicationDir() == sys.path[0]

            # When in a executable...
            is_frozen.SetIsFrozen(True)
            assert GetApplicationDir() == os.path.dirname(os.path.dirname(sys.executable))
        finally:
            is_frozen.SetIsFrozen(is_frozen_)
