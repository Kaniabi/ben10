from ben10.foundation import callback, interface
from ben10.foundation.decorators import Implements
from ben10.foundation.interface import (AssertImplementsFullChecking, AttributeBasedCachedMethod,
    BadImplementationError, CachedMethod, IAdaptable, InterfaceError, InterfaceImplementorStub,
    LastResultCachedMethod, Method)
from ben10.foundation.types_ import Null
import pytest



#===================================================================================================
# Test Classes
#===================================================================================================
class _InterfM1(interface.Interface):
    def m1(self):
        ''

class _InterfM2(interface.Interface):
    def m2(self):
        ''

class _InterfM3(interface.Interface):
    def m3(self, arg1, arg2):
        ''

class _InterfM4(_InterfM3):
    def m4(self):
        ''


@pytest.fixture
def _cached_obj():
    '''
    A test_object common to many cached_method tests.
    '''

    class TestObj:
        def __init__(self):
            self.method_count = 0

        def CachedMethod(self, *args, **kwargs):
            self.method_count += 1
            return self.method_count

        def CheckCounts(self, cache, method=0, miss=0, hit=0):

            if not hasattr(cache, 'check_counts'):
                cache.check_counts = dict(method=0, miss=0, hit=0, call=0)

            cache.check_counts['method'] += method
            cache.check_counts['miss'] += miss
            cache.check_counts['hit'] += hit
            cache.check_counts['call'] += (miss + hit)

            assert self.method_count == cache.check_counts['method']
            assert cache.miss_count == cache.check_counts['miss']
            assert cache.hit_count == cache.check_counts['hit']
            assert cache.call_count == cache.check_counts['call']

    return TestObj()


#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testBasics(self):
        class I(interface.Interface):

            def foo(self, a, b=None):
                ''

            def bar(self):
                ''

        class C(object):
            interface.Implements(I)

            def foo(self, a, b=None):
                ''

            def bar(self):
                ''


        class C2(object):

            def foo(self, a, b=None):
                ''

            def bar(self):
                ''


        class D(object):
            pass

        assert interface.IsImplementationFullChecking(I(C()), I)  # OK

        assert interface.IsImplementationFullChecking(C, I)  # OK
        assert interface.IsImplementationFullChecking(C2, I)  # OK
        assert not interface.IsImplementationFullChecking(D, I)  # nope

        assert I(C) is C
        assert I(C2) is C2
        with pytest.raises(interface.InterfaceError):
            I()
        with pytest.raises(interface.BadImplementationError):
            I(D)


    def testMissingMethod(self):
        class I(interface.Interface):

            def foo(self, a, b=None):
                ''


        def TestMissingMethod():
            class C(object):
                interface.Implements(I)

        with pytest.raises(BadImplementationError):
            TestMissingMethod()

        def TestMissingSignature():
            class C(object):
                interface.Implements(I)

                def foo(self, a):
                    ''


        with pytest.raises(interface.BadImplementationError):
            TestMissingSignature()

        def TestMissingSignatureOptional():
            class C(object):
                interface.Implements(I)

                def foo(self, a, b):
                    ''


        with pytest.raises(interface.BadImplementationError):
            TestMissingSignatureOptional()


        def TestWrongParameterName():
            class C(object):
                interface.Implements(I)

                def foo(self, a, c):
                    ''

        with pytest.raises(interface.BadImplementationError):
            TestWrongParameterName()


    def testSubclasses(self):
        class I(interface.Interface):

            def foo(self, a, b=None):
                ''

        class C(object):
            interface.Implements(I)
            def foo(self, a, b=None):
                ''

        class D(C):
            pass


    def testSubclasses2(self):
        class I(interface.Interface):
            def foo(self):
                ''

        class I2(interface.Interface):
            def bar(self):
                ''

        class C(object):
            interface.Implements(I)
            def foo(self):
                ''

        class D(C):
            interface.Implements(I2)
            def bar(self):
                ''

        class E(D):
            pass

        assert interface.GetImplementedInterfaces(C) == set([I])
        assert interface.GetImplementedInterfaces(D) == set([I2, I])
        assert interface.GetImplementedInterfaces(E) == set([I2, I])



    def testNoName(self):
        class I(interface.Interface):
            def MyMethod(self, foo):
                ''

        class C(object):
            def MyMethod(self, bar):
                ''

        with pytest.raises(BadImplementationError):
            interface.AssertImplementsFullChecking(C(), I)

    def testAttributes(self):

        class IZoo(interface.Interface):
            zoo = interface.Attribute(int)

        class I(interface.Interface):

            foo = interface.Attribute(int)
            bar = interface.Attribute(str)
            foobar = interface.Attribute(int, None)
            a_zoo = interface.Attribute(IZoo)


        class Zoo(object):
            interface.Implements(IZoo)

        class C(object):
            interface.Implements(I)

        c1 = C()
        c1.foo = 10
        c1.bar = 'hello'
        c1.foobar = 20

        a_zoo = Zoo()
        a_zoo.zoo = 99
        c1.a_zoo = a_zoo

        c2 = C()

        assert not interface.IsImplementationFullChecking(C, I)  # only works with instances
        assert interface.IsImplementationFullChecking(c1, I)  # OK, has attributes
        assert not interface.IsImplementationFullChecking(c2, I)  # not all the attributes necessary

        # must not be true if including an object that doesn't implement IZoo interface expected for
        # a_zoo attribute
        c1.a_zoo = 'wrong'
        assert not interface.IsImplementationFullChecking(c1, I)  # failed, invalid attr type
        c1.a_zoo = a_zoo

        # test if we can set foobar to None
        c1.foobar = None
        assert interface.IsImplementationFullChecking(c1, I)  # OK

        c1.foobar = 'hello'
        assert not interface.IsImplementationFullChecking(c1, I)  # failed, invalid attr type




    def testPassNoneInAssertImplementsFullChecking(self):
        with pytest.raises(BadImplementationError):
            interface.AssertImplementsFullChecking(None, _InterfM1)
        with pytest.raises(BadImplementationError):
            interface.AssertImplementsFullChecking(10, _InterfM1)

    def testOldStyle(self):
        class Old:
            interface.Implements(_InterfM1, old_style=True)

            def m1(self):
                ''

        class Old2:
            interface.Implements(_InterfM1, old_style=True)


        # self.assertNotRaises(BadImplementationError,
        interface.AssertImplementsFullChecking(Old, _InterfM1)
        with pytest.raises(BadImplementationError):
            interface.AssertImplementsFullChecking(Old2, _InterfM1)



    def testNoInitCheck(self):
        class NoCheck(object):
            interface.Implements(_InterfM1, no_init_check=True)


        no_check = NoCheck()
        with pytest.raises(BadImplementationError):
            interface.AssertImplementsFullChecking(no_check, _InterfM1)


    def testCallbackAndInterfaces(self):
        '''
            Tests if the interface "AssertImplements" works with "callbacked" methods.
        '''
        class My(object):
            interface.Implements(_InterfM1)

            def m1(self):
                ''

        def MyCallback():
            ''

        o = My()
        interface.AssertImplementsFullChecking(o, _InterfM1)

        callback.After(o.m1, MyCallback)

        interface.AssertImplementsFullChecking(o, _InterfM1)

        # self.assertNotRaises( interface.BadImplementationError,
        interface.AssertImplementsFullChecking(o, _InterfM1)


    def testInterfaceStub(self):
        class My(object):
            interface.Implements(_InterfM1)

            def m1(self):
                return 'm1'
            def m2(self):
                ''

        m0 = My()
        m1 = _InterfM1(m0)  # will make sure that we only access the attributes/methods declared in the interface
        assert m1.m1() == 'm1'
        # self.assertNotRaises(AttributeError,
        getattr(m0, 'm2')
        with pytest.raises(AttributeError):
            getattr(m1, 'm2')

        # self.assertNotRaises(interface.BadImplementationError,
        _InterfM1(m1)


    def testHasDeclaredInterface(self):
        class My(object):
            interface.Implements(_InterfM1)

            def m1(self):
                ''

        class My2(object):

            def m1(self):
                ''

        m1 = My()
        m2 = My2()
        assert interface.IsImplementationFullChecking(m1, _InterfM1)
        assert interface.IsImplementationFullChecking(m2, _InterfM1)

        assert interface.IsInterfaceDeclared(My, _InterfM1)
        assert interface.IsInterfaceDeclared(m1, _InterfM1)
        assert not interface.IsInterfaceDeclared(m2, _InterfM1)


        m1Stub = _InterfM1(m1)
        assert interface.IsInterfaceDeclared(m1Stub, _InterfM1)
        m1Stub2 = _InterfM1(_InterfM1(m1Stub))
        assert interface.IsInterfaceDeclared(m1Stub2, _InterfM1)

        assert interface.IsInterfaceDeclared(m1Stub2, set([_InterfM1, _InterfM2]))
        assert not interface.IsInterfaceDeclared(m1Stub2, set([_InterfM2]))


    def testIsInterfaceDeclaredWithSubclasses(self):
        '''
        Checks if the IsInterfaceDeclared method works with subclasses interfaces.
        
        Given that an interface I2 inherits from I1 of a given object declared that it implements I2
        then it is implicitly declaring that implements I1.
        '''

        class My2(object):
            interface.Implements(_InterfM2)

            def m2(self):
                ''

        class My3(object):
            interface.Implements(_InterfM3)

            def m3(self, arg1, arg2):
                ''

        class My4(object):
            interface.Implements(_InterfM4)

            def m3(self, arg1, arg2):
                ''

            def m4(self):
                ''

        m2 = My2()
        m3 = My3()
        m4 = My4()

        # My2
        assert not interface.IsInterfaceDeclared(m2, _InterfM3)

        # My3
        assert interface.IsInterfaceDeclared(m3, _InterfM3)
        assert not interface.IsInterfaceDeclared(m3, _InterfM4)

        # My4
        assert interface.IsInterfaceDeclared(m4, _InterfM4)
        assert interface.IsInterfaceDeclared(m4, _InterfM3)
        assert interface.IsInterfaceDeclared(m4, [_InterfM3, _InterfM4])

        # If any of the given interfaces is an accepted subclass, return True
        assert interface.IsInterfaceDeclared(m4, [_InterfM3, _InterfM2])

        # When wrapped in an m4 interface it should still accept m3 as a declared interface
        wrapped_intef_m4 = _InterfM4(m4)
        assert interface.IsInterfaceDeclared(wrapped_intef_m4, _InterfM4)
        assert interface.IsInterfaceDeclared(wrapped_intef_m4, _InterfM3)


    def testIsInterfaceDeclaredWithBuiltInObjects(self):
        my_number = 10
        assert not interface.IsInterfaceDeclared(my_number, _InterfM1)


    def testClassImplementMethod(self):
        '''
            Tests replacing a method that implements an interface with a class.
            
            The class must be derived from "interface.Method" in order to be accepted as a valid
            implementation.
        '''

        class My(object):
            interface.Implements(_InterfM1)

            def m1(self):
                ''

        class MyRightMethod(interface.Method):

            def __call__(self):
                ''

        class MyWrongMethod(object):

            def __call__(self):
                ''

        m = My()
        m.m1 = MyWrongMethod()
        assert not interface.IsImplementationFullChecking(m, _InterfM1)

        m.m1 = MyRightMethod()
        assert interface.IsImplementationFullChecking(m, _InterfM1)

    def testGetImplementedInterfaces(self):

        class A(object):
            interface.Implements(_InterfM1)
            def m1(self):
                ''

        class B(A):
            pass

        assert len(interface.GetImplementedInterfaces(B())) == 1

    def testGetImplementedInterfaces2(self):

        class A(object):
            interface.Implements(_InterfM1)
            def m1(self):
                ''

        class B(A):
            interface.Implements(_InterfM2)
            def m2(self):
                ''

        assert len(interface.GetImplementedInterfaces(B())) == 2
        with pytest.raises(AssertionError):
            interface.AssertDeclaresInterface(A(), _InterfM2)
        interface.AssertDeclaresInterface(B(), _InterfM2)


    def testAdaptableInterface(self):

        class A(object):
            interface.Implements(IAdaptable)

            def GetAdapter(self, interface_class):
                if interface_class == _InterfM1:
                    return B()

        class B(object):
            interface.Implements(_InterfM1)

            def m1(self):
                pass

        a = A()
        b = _InterfM1(a)  # will try to adapt, as it does not directly implements m1
        assert b is not None
        b.m1()  # has m1
        with pytest.raises(AttributeError):
            getattr(b, 'non_existent')
        assert isinstance(b, InterfaceImplementorStub)


    def testNull(self):
        # assert not raises
        interface.AssertImplementsFullChecking(Null(), _InterfM2)


    def testSetItem(self):

        class InterfSetItem(interface.Interface):
            def __setitem__(self, id, subject):
                ''

            def __getitem__(self, id):
                ''

        class A(object):
            interface.Implements(InterfSetItem)

            def __setitem__(self, id, subject):
                self.set = (id, subject)

            def __getitem__(self, id):
                return self.set

        a = InterfSetItem(A())
        a['10'] = 1
        assert ('10', 1) == a['10']


    def testAssertImplementsDoesNotDirObject(self):

        class M1(object):

            def __getattr__(self, attr):
                if attr == 'm1':
                    class MyMethod(Method):
                        def __call__(self):
                            pass
                    return MyMethod()
                else:
                    raise AttributeError

        m1 = M1()
        m1.m1()
        interface.AssertImplementsFullChecking(m1, _InterfM1)

    def testImplementorWithAny(self):

        class M3(object):

            def m3(self, *args, **kwargs):
                ''

        AssertImplementsFullChecking(M3(), _InterfM3)

    def testInterfaceCheckRequiresInterface(self):
        class M3(object):

            def m3(self, *args, **kwargs):
                ''

        with pytest.raises(InterfaceError):
            AssertImplementsFullChecking(M3(), M3)
        with pytest.raises(InterfaceError):
            interface.IsInterfaceDeclared(M3(), M3)


    def testReadOnlyAttribute(self):
        class IZoo(interface.Interface):
            zoo = interface.ReadOnlyAttribute(int)


        class Zoo(object):
            interface.Implements(IZoo)

            def __init__(self, value):
                self.zoo = value


        a_zoo = Zoo(value=99)
        AssertImplementsFullChecking(a_zoo, IZoo)


    def testReadOnlyAttributeMissingImplementation(self):
        '''
        First implementation of changes in interfaces to support read-only attributes was not 
        including read-only attributes when AssertImplements was called. 
        
        This caused missing read-only attributes to go unnoticed and sometimes false positives, 
        recognizing objects as valid implementations when in fact they weren't.
        '''
        class IZoo(interface.Interface):
            zoo = interface.ReadOnlyAttribute(int)

        # Doesn't have necessary 'zoo' attribute, should raise a bad implementation error
        class FlawedZoo(object):
            interface.Implements(IZoo)

            def __init__(self, value):
                pass

        a_flawed_zoo = FlawedZoo(value=101)
        with pytest.raises(BadImplementationError):
            AssertImplementsFullChecking(a_flawed_zoo, IZoo)


# TODO: interface vs scalar!
#     def testScalarAttribute(self):
#         from coilib50.units import Scalar
#
#         class IFluid(interface.Interface):
#             plastic_viscosity = interface.ScalarAttribute('dynamic viscosity')
#             yield_point = interface.ScalarAttribute('pressure')
#             density = interface.ScalarAttribute('density')
#
#
#         class MyFluid(object):
#             interface.Implements(IFluid)
#
#             def __init__(self, plastic_viscosity, yield_point, density):
#                 self.plastic_viscosity = Scalar('dynamic viscosity', *plastic_viscosity)
#                 self.yield_point = Scalar('pressure', *yield_point)
#                 self.density = Scalar('density', *density)
#
#         fluid = MyFluid(
#             plastic_viscosity=(2.0, 'Pa.s'),
#             yield_point=(4.0, 'lbf/100ft2'),
#             density=(1.2, 'kg/m3'),
#         )
#
#         AssertImplementsFullChecking(fluid, IFluid)
#
#         class OtherFluid(object):
#             interface.Implements(IFluid)
#
#             def __init__(self, plastic_viscosity, yield_point, density):
#                 self.plastic_viscosity = Scalar('kinematic viscosity', *plastic_viscosity)  # Oops
#                 self.yield_point = Scalar('pressure', *yield_point)
#                 self.density = Scalar('density', *density)
#
#         other_fluid = OtherFluid(
#             plastic_viscosity=(1.0, 'm2/s'),  # Wrong!
#             yield_point=(4.0, 'lbf/100ft2'),
#             density=(1.2, 'kg/m3'),
#         )
#
#         try:
#             AssertImplementsFullChecking(other_fluid, IFluid)
#         except BadImplementationError, error:
#             self.assertContains(
#                 'The Scalar category (kinematic viscosity) does not match the expected category'
#                 ' of the interface (dynamic viscosity)',
#                 str(error),
#             )
#         else:
#             self.fail('Expected BadImplementationError.')
#
#
#
#     def testScalarAttributeWithBaseSubjectProperty(self):
#         from coilib50.units import Scalar
#         from coilib50.subject import BaseSubject
#         from coilib50.basic.xfield import XFactory
#
#         class IFluid(interface.Interface):
#             plastic_viscosity = interface.ScalarAttribute('dynamic viscosity')
#             yield_point = interface.ScalarAttribute('pressure')
#             density = interface.ScalarAttribute('density')
#
#
#         class MyFluid(BaseSubject):
#             interface.Implements(IFluid)
#
#             BaseSubject.Properties(
#                 plastic_viscosity=XFactory(Scalar, category='dynamic viscosity'),
#                 yield_point=XFactory(Scalar, category='pressure'),
#                 density=XFactory(Scalar, category='density'),
#             )
#
#             def __init__(self, plastic_viscosity, yield_point, density, **kwargs):
#                 BaseSubject.__init__(self, **kwargs)
#                 self.plastic_viscosity.SetValueAndUnit(plastic_viscosity)
#                 self.yield_point.SetValueAndUnit(yield_point)
#                 self.density.SetValueAndUnit(density)
#
#         fluid = MyFluid(
#             plastic_viscosity=(2.0, 'Pa.s'),
#             yield_point=(4.0, 'lbf/100ft2'),
#             density=(1.2, 'kg/m3'),
#         )
#
#         AssertImplementsFullChecking(fluid, IFluid)


    def testImplementsTwice(self):
        class I1(interface.Interface):
            def Method1(self):
                ''

        class I2(interface.Interface):
            def Method2(self):
                ''

        def Create():

            class Foo(object):
                interface.Implements(I1)
                interface.Implements(I2)

                def Method2(self):
                    ''

        # Error because I1 is not implemented.
        with pytest.raises(BadImplementationError):
            Create()


    def testCallableInterfaceStub(self):
        '''
        Validates that is possible to create stubs for interfaces of callables (i.e. declaring
        __call__ method in interface). 
        
        If a stub for a interface not declared as callable is tried to be executed as callable it 
        raises an error. 
        '''
        # ok, calling a stub for a callable interface.
        class IFoo(interface.Interface):
            def __call__(self, bar):
                ''

        class Foo(object):
            interface.Implements(IFoo)

            def __call__(self, bar):
                ''

        foo = Foo()
        stub = IFoo(foo)
        # self.assertNotRaises(TypeError
        stub(bar=None)

        # wrong, calling a stub for a non-callable interface.
        class IBar(interface.Interface):
            def something(self, stuff):
                ''

        class Bar(object):
            interface.Implements(IBar)

            def something(self, stuff):
                ''

        bar = Bar()
        stub = IBar(bar)
        with pytest.raises(AttributeError):
            stub(stuff=None)


    def testErrorDifferentFunction(self):
        with pytest.raises(AssertionError):
            self.CreateClass()


        class IFoo(interface.Interface):
            def Foo(self):
                '''
                docstring
                '''

        class Impl(object):

            @Implements(IFoo.Foo)
            def Foo(self):
                pass

        assert IFoo.Foo.__doc__ == Impl.Foo.__doc__
        Impl().Foo()  # Coverage!


    def CreateClass(self):

        class IFoo(interface.Interface):

            def DoIt(self):
                ''

        class Implementation(object):

            @Implements(IFoo.DoIt)
            def DoNotDoIt(self):
                ''


    def testCacheMethod(self, _cached_obj):
        cache = MyMethod = CachedMethod(_cached_obj.CachedMethod)

        MyMethod(1)
        _cached_obj.CheckCounts(cache, method=1, miss=1)

        MyMethod(1)
        _cached_obj.CheckCounts(cache, hit=1)

        MyMethod(2)
        _cached_obj.CheckCounts(cache, method=1, miss=1)

        MyMethod(2)
        _cached_obj.CheckCounts(cache, hit=1)

        # ALL results are stored, so these calls are HITs
        MyMethod(1)
        _cached_obj.CheckCounts(cache, hit=1)

        MyMethod(2)
        _cached_obj.CheckCounts(cache, hit=1)


    def testCacheMethodEnabled(self, _cached_obj):
        cache = MyMethod = CachedMethod(_cached_obj.CachedMethod)

        MyMethod(1)
        _cached_obj.CheckCounts(cache, method=1, miss=1)

        MyMethod(1)
        _cached_obj.CheckCounts(cache, hit=1)

        MyMethod.enabled = False

        MyMethod(1)
        _cached_obj.CheckCounts(cache, method=1, miss=1)

        MyMethod.enabled = True

        MyMethod(1)
        _cached_obj.CheckCounts(cache, hit=1)


    def testCacheMethodLastResultCachedMethod(self, _cached_obj):
        cache = MyMethod = LastResultCachedMethod(_cached_obj.CachedMethod)

        MyMethod(1)
        _cached_obj.CheckCounts(cache, method=1, miss=1)

        MyMethod(1)
        _cached_obj.CheckCounts(cache, hit=1)

        MyMethod(2)
        _cached_obj.CheckCounts(cache, method=1, miss=1)

        MyMethod(2)
        _cached_obj.CheckCounts(cache, hit=1)

        # Only the LAST result is stored, so this call is a MISS.
        MyMethod(1)
        _cached_obj.CheckCounts(cache, method=1, miss=1)


    def testCacheMethodObjectInKey(self, _cached_obj):
        cache = MyMethod = CachedMethod(_cached_obj.CachedMethod)

        class MyObject(object):

            def __init__(self):
                self.name = 'alpha'
                self.id = 1

            def __str__(self):
                return '%s %d' % (self.name, self.id)

        alpha = MyObject()

        MyMethod(alpha)
        _cached_obj.CheckCounts(cache, method=1, miss=1)

        MyMethod(alpha)
        _cached_obj.CheckCounts(cache, hit=1)

        alpha.name = 'bravo'
        alpha.id = 2

        MyMethod(alpha)
        _cached_obj.CheckCounts(cache, method=1, miss=1)


    def testCacheMethodAttributeBasedCachedMethod(self):

        class TestObject(object):

            def __init__(self):
                self.name = 'alpha'
                self.id = 1
                self.n_calls = 0

# TODO: Not covered
#             def __str__(self):
#                 return '%s %d' % (self.name, self.id)

            def Foo(self, par):
                self.n_calls += 1
                return '%s %d' % (par, self.id)

        alpha = TestObject()
        alpha.Foo = AttributeBasedCachedMethod(alpha.Foo, 'id', cache_size=3)
        alpha.Foo('test1')
        alpha.Foo('test1')

        assert alpha.n_calls == 1

        alpha.Foo('test2')
        assert alpha.n_calls == 2
        assert len(alpha.Foo._results) == 2

        alpha.id = 3
        alpha.Foo('test2')
        assert alpha.n_calls == 3

        assert len(alpha.Foo._results) == 3

        alpha.Foo('test3')
        assert alpha.n_calls == 4
        assert len(alpha.Foo._results) == 3
