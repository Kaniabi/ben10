import pytest

from etk11.memoize import Memoize
from etk11.weak_ref import GetWeakRef



#=======================================================================================================================
# _Countcalls
#=======================================================================================================================
def _Countcalls(counts):
    '''
    Decorator to count calls to a function
    '''
    def decorate(func):
        func_name = func.func_name
        counts[func_name] = 0
        def call(*args, **kwds):
            counts[func_name] += 1
            return func(*args, **kwds)
        call.func_name = func_name
        return call
    return decorate



#=======================================================================================================================
# Test
#=======================================================================================================================
class Test:

    def testMemoizeAndClassmethod(self):
        self._calls = 0
        class F(object):
            NAME = 'F'

            @classmethod
            @Memoize(3)  # Note: cls will be part of the cache-key in the Memoize.
            def GetName(cls, param):
                self._calls += 1
                return cls.NAME + param

        class G(F):
            NAME = 'G'

        assert 'F1' == F.GetName('1')
        assert 'F2' == F.GetName('2')
        assert 'G2' == G.GetName('2')
        assert 3 == self._calls

        assert 'F1' == F.GetName('1')
        assert 3 == self._calls

        assert 'G3' == G.GetName('3')
        assert 4 == self._calls
        assert 'F1' == F.GetName('1')
        assert 5 == self._calls


    def testMemoizeAndMethod(self):
        _calls = []

        class F(object):

            def __init__(self, name):
                self.name = name

            @Memoize(2)
            def GetName(self, param):
                result = self.name + param
                _calls.append(result)
                return result

        f = F('F')
        g = F('G')

        f.GetName('1')
        assert _calls == ['F1']
        f.GetName('2')
        assert _calls == ['F1', 'F2']
        f.GetName('1')
        assert _calls == ['F1', 'F2']  # Cache HIT

        f.GetName('3')
        assert _calls == ['F1', 'F2', 'F3']

        f.GetName('1')
        assert _calls == ['F1', 'F2', 'F3', 'F1']  # Cache miss because F1 was removed

        g.GetName('1')
        g.GetName('2')
        assert _calls == ['F1', 'F2', 'F3', 'F1', 'G1', 'G2']

        g.GetName('2')
        assert _calls == ['F1', 'F2', 'F3', 'F1', 'G1', 'G2']  # Cache HIT because F and G have a separated cache.


    def testMemoizeBoundMethod(self):
        _calls = []

        class F(object):

            def __init__(self, name):
                self.name = name

            @Memoize(2)
            def GetName(self, param):
                result = self.name + param
                _calls.append(result)
                return result

        # Testing memozoize in a bound method
        f = F('F')
        m = Memoize(2)
        m(f.GetName)

        f.GetName('1')
        f.GetName('1')
        f.GetName('2')
        f.GetName('2')
        f.GetName('3')
        f.GetName('3')
        f.GetName('1')
        assert _calls == ['F1', 'F2', 'F3', 'F1']


    def testMemoizeErrors(self):
        with pytest.raises(TypeError):
            class MyClass(object):

                @Memoize(2)
                @classmethod
                def MyMethod(self):
                    'Not called'

        with pytest.raises(TypeError) as exception:
            number = 999
            Memoize(2)(number)

            assert str(exception) == 'Expecting a function/method/classmethod for Memoize.'

        with pytest.raises(AssertionError) as exception:
            @Memoize(2, 'INVALID')
            def MyFunction():
                'Not called!'

            assert str(exception) == 'Memoize prune method not supported: INVALID'


    def testMemoizeLRU(self):
        counts = {}

        @Memoize(2, Memoize.LRU)  # Just 2 values kept
        @_Countcalls(counts)
        def Double(x):
            return x * 2
        assert Double.func_name == 'Double'

        assert counts == dict(Double=0)

        # Only the first call with a given argument bumps the call count:
        #
        assert Double(2) == 4
        assert counts['Double'] == 1
        assert Double(2) == 4
        assert counts['Double'] == 1
        assert Double(3) == 6
        assert counts['Double'] == 2

        # Unhashable keys: an error is raised!
        with pytest.raises(TypeError):
            Double([10])

        # Now, let's see if values are discarded when more than 2 are used...
        assert Double(2) == 4
        assert counts['Double'] == 2
        Double(4)  # Now, we have 2 and 4 in the cache
        assert counts['Double'] == 3
        Double(3)  # It has discarded this one, so, it has to be added again!
        assert counts['Double'] == 4


    def testMemoize(self):
        counts = {}

        @Memoize(2, Memoize.FIFO)  # Just 2 values kept
        @_Countcalls(counts)
        def Double(x):
            return x * 2
        assert Double.func_name == 'Double'

        assert counts == dict(Double=0)

        # Only the first call with a given argument bumps the call count:
        #
        assert Double(2) == 4
        assert counts['Double'] == 1
        assert Double(2) == 4
        assert counts['Double'] == 1
        assert Double(3) == 6
        assert counts['Double'] == 2

        # Unhashable keys: an error is raised!
        with pytest.raises(TypeError):
            Double([10])

        # Now, let's see if values are discarded when more than 2 are used...
        assert Double(2) == 4
        assert counts['Double'] == 2
        Double(4)
        assert counts['Double'] == 3
        Double(2)  # It has discarded this one, so, it has to be added again!
        assert counts['Double'] == 4


        # Check if it works without any arguments.
        @Memoize
        @_Countcalls(counts)
        def NoArgs():
            return 1
        NoArgs()
        NoArgs()
        NoArgs()
        assert counts['NoArgs'] == 1


        #--- Check if the cache is cleared when the instance is removed.
        class Stub(object):
            pass

        self._stub = Stub()
        def _GetRet():
            return self._stub

        class Foo(object):

            def __init__(self):
                self.called = False

            @Memoize(2)
            def m1(self):
                assert not self.called
                self.called = True
                return _GetRet()

        f = Foo()
        assert f.m1() is self._stub

        self._stub = GetWeakRef(self._stub)
        assert f.m1() is self._stub()
        assert f.called

        f2 = Foo()
        assert not f2.called
        f2.m1()
        assert f2.called

        del f
        del f2
        assert self._stub() is None  # Should be garbage-collected at this point!


    def testClearMemo(self):
        self._called = 0
        @Memoize
        def Method(p):
            self._called += 1
            return p

        Method(1)
        Method(1)

        assert self._called == 1
        Method.ClearCache()

        Method(1)
        Method(1)
        assert self._called == 2


    def testClearMemoOnInstance(self):
        self._called = 0
        outer_self = self
        class Bar(object):
            @Memoize
            def m1(self, p):
                outer_self._called += 1
                return p

        b = Bar()
        b.m1(1)
        b.m1(1)
        assert self._called == 1

        b.m1.ClearCache(b)
        b.m1(1)
        assert self._called == 2
        b.m1(1)
        assert self._called == 2
