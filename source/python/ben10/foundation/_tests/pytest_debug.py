from ben10.foundation.debug import IsPythonDebug



#===================================================================================================
# Test
#===================================================================================================
class Test():

    def testIsPythonDebug(self):
        assert IsPythonDebug() in (True, False)
