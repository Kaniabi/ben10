import warnings

import pytest

from etk11 import is_frozen
from etk11.decorators import Implements, Override, Deprecated


#=======================================================================================================================
# Test
#=======================================================================================================================
class Test():

    def testImplements(self):
        with pytest.raises(AssertionError):
            self.CreateClass()

        class IFoo(object):
            def Foo(self):
                '''
                docstring
                '''

        class Impl(object):

            @Implements(IFoo.Foo)
            def Foo(self):
                return self.__class__.__name__

        assert IFoo.Foo.__doc__ == Impl.Foo.__doc__

        # Just for 100% coverage.
        assert Impl().Foo() == 'Impl'


    def CreateClass(self):

        class IFoo(object):

            def DoIt(self):
                ''

        class Implementation(object):

            @Implements(IFoo.DoIt)
            def DoNotDoIt(self):
                ''


    def testOverride(self):

        def TestOK():

            class A(object):

                def Method(self):
                    '''
                    docstring
                    '''


            class B(A):

                @Override(A.Method)
                def Method(self):
                    return 2

            b = B()
            assert b.Method() == 2
            assert A.Method.__doc__ == B.Method.__doc__


        def TestERROR():

            class A(object):

                def MyMethod(self):
                    ''


            class B(A):

                @Override(A.Method)  # it will raise an error at this point
                def Method(self):
                    ''

        def TestNoMatch():

            class A(object):

                def Method(self):
                    ''


            class B(A):

                @Override(A.Method)
                def MethodNoMatch(self):
                    ''


        TestOK()
        with pytest.raises(AttributeError):
            TestERROR()

        with pytest.raises(AssertionError):
            TestNoMatch()


#     def setUp(self):
#         unittest.TestCase.setUp(self)
#         unittest.installMocks(warnings, warn=self._warn)
#
#     def tearDown(self):
#         unittest.TestCase.tearDown(self)
#         unittest.uninstallMocks(warnings)

    def testDeprecated(self, monkeypatch):

        def MyWarn(*args, **kwargs):
            warn_params.append((args, kwargs))

        monkeypatch.setattr(warnings, 'warn', MyWarn)

        old_is_frozen = is_frozen.SetIsFrozen(False)
        try:
            # Emit messages when in development (not frozen)
            warn_params = []

            # ... deprecation with alternative
            @Deprecated('OtherMethod')
            def Method1():
                pass

            # ... deprecation without alternative
            @Deprecated()
            def Method2():
                pass

            Method1()
            Method2()
            assert warn_params == [
                (("DEPRECATED: 'Method1' is deprecated, use 'OtherMethod' instead",), {'stacklevel': 2}),
                (("DEPRECATED: 'Method2' is deprecated",), {'stacklevel': 2})
            ]

            # No messages on release code (frozen)
            is_frozen.SetIsFrozen(True)

            warn_params = []

            @Deprecated()
            def FrozenMethod():
                pass

            FrozenMethod()
            assert warn_params == []
        finally:
            is_frozen.SetIsFrozen(old_is_frozen)


