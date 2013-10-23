from ben10.foundation.decorators import Deprecated, Override
from ben10.foundation.is_frozen import IsFrozen
from ben10.foundation.klass import IsInstance
from ben10.foundation.reraise import Reraise
from ben10.foundation.singleton import Singleton
from ben10.foundation.types_ import Method
from new import classobj
import inspect
import sys
import warnings



#===================================================================================================
# InterfaceError
#===================================================================================================
class InterfaceError(RuntimeError):
    pass



#===================================================================================================
# BadImplementationError
#===================================================================================================
class BadImplementationError(InterfaceError):
    pass



#===================================================================================================
# InterfaceImplementationMetaClass
#===================================================================================================
class InterfaceImplementationMetaClass(type):
    def __new__(cls, name, bases, dct):
        C = type.__new__(cls, name, bases, dct)
        if not IsFrozen():  # Only doing check in dev mode.
            for I in dct.get('__implements__', []):
                # Will do full checking this first time, and also cache the results
                AssertImplements(C, I)
        return C



#===================================================================================================
# InterfaceImplementorStub
#===================================================================================================
class InterfaceImplementorStub(object):
    '''
        A helper for acting as a stub for some object (in this way, we're only able to access
        attributes declared directly in the interface.
    
        It forwards the calls to the actual implementor (the wrapped object)
    '''

    def __init__(self, wrapped, implemented_interface):
        self.__wrapped = wrapped
        self.__implemented_interface = implemented_interface

        self.__interface_methods, self.__attrs = \
            cache_interface_attrs.GetInterfaceMethodsAndAttrs(implemented_interface)


    def GetWrappedFromImplementorStub(self):
        '''
            Really big and awkward name because we don't want name-clashes
        '''
        return self.__wrapped

    def __getattr__(self, attr):
        if attr not in self.__attrs and attr not in self.__interface_methods:
            raise AttributeError("Error. The interface %s does not have the attribute '%s' declared." % (self.__implemented_interface, attr))
        return getattr(self.__wrapped, attr)

    def __getitem__(self, *args, **kwargs):
        if '__getitem__' not in self.__interface_methods:
            raise AttributeError("Error. The interface %s does not have the attribute '%s' declared." % (self.__implemented_interface, '__getitem__'))
        return self.__wrapped.__getitem__(*args, **kwargs)

    def __setitem__(self, *args, **kwargs):
        if '__setitem__' not in self.__interface_methods:
            raise AttributeError("Error. The interface %s does not have the attribute '%s' declared." % (self.__implemented_interface, '__setitem__'))
        return self.__wrapped.__setitem__(*args, **kwargs)

    def __repr__(self):
        return '<InterfaceImplementorStub %s>' % self.__wrapped

    def __call__(self, *args, **kwargs):
        if '__call__' not in self.__interface_methods:
            raise AttributeError("Error. The interface %s does not have the attribute '%s' declared." % (self.__implemented_interface, '__call__'))
        return self.__wrapped.__call__(*args, **kwargs)



#===================================================================================================
# Interface
#===================================================================================================
class Interface(object):
    '''Base class for interfaces.
    
    A interface describes a behavior that some objects must implement.
    '''

    # : instance to check if we are receiving an argument during __new__
    _SENTINEL = []

    def __new__(cls, class_=_SENTINEL):
        # if no class is given, raise InterfaceError('trying to instantiate interface')
        # check if class_or_object implements this interface
        from _adaptable_interface import IAdaptable

        if class_ is cls._SENTINEL:
            raise InterfaceError('Can\'t instantiate Interface.')
        else:
            if isinstance(class_, type):
                # We're doing something as Interface(InterfaceImpl) -- not instancing
                _AssertImplementsFullChecking(class_, cls, check_attr=False)
                return class_
            elif isinstance(class_, InterfaceImplementorStub):
                return class_
            else:
                implemented_interfaces = GetImplementedInterfaces(class_)

                if cls in implemented_interfaces:
                    return InterfaceImplementorStub(class_, cls)

                elif IAdaptable in implemented_interfaces:
                    adapter = class_.GetAdapter(cls)
                    if adapter is not None:
                        return InterfaceImplementorStub(adapter, cls)

                # We're doing something as Interface(InterfaceImpl()) -- instancing
                _AssertImplementsFullChecking(class_, cls, check_attr=True)
                return InterfaceImplementorStub(class_, cls)



#===================================================================================================
# _GetClassForInterfaceChecking
#===================================================================================================
def _GetClassForInterfaceChecking(class_or_instance):
    if isinstance(class_or_instance, (type, classobj)):
        return class_or_instance  # is class
    elif isinstance(class_or_instance, InterfaceImplementorStub):
        return _GetClassForInterfaceChecking(class_or_instance.GetWrappedFromImplementorStub())

    return class_or_instance.__class__  # is instance



#===================================================================================================
# IsImplementation
#===================================================================================================
def IsImplementation(class_or_instance, interface):
    '''    
    :type class_or_instance: type or classobj or object

    :type interface: Interface

    :rtype: bool

    :see: :py:func:`.AssertImplements`
    '''
    try:
        is_interface = issubclass(interface, Interface)
    except TypeError, e:
        Reraise(e, "interface=%s (type %s)" % (interface, type(interface)))

    if not is_interface:
        raise InterfaceError(
            'To check against an interface, an interface is required (received: %s -- mro:%s)' %
            (interface, interface.__mro__)
        )

    class_ = _GetClassForInterfaceChecking(class_or_instance)

    is_implementation, _reason = _CheckIfClassImplements(class_, interface)
#    # DEBUG CODE (will be removed after refactory)
#
#    print 'class:', class_
#    print 'interface:', interface
#    print 'is_implementation:', is_implementation
#    if _reason:
#        print 'reason:', _reason
#    print
#
#    # END OF DEBUG CODE
    if is_implementation:
        return True

    return False



#===================================================================================================
# IsImplementationOfAny
#===================================================================================================
def IsImplementationOfAny(class_or_instance, interfaces):
    '''
    Check if the class or instance implements any of the given interfaces
     
    :type class_or_instance: type or classobj or object
    
    :type interfaces: list(Interface)
    
    :rtype: bool
    
    :see: :py:func:`.IsImplementation`
    '''
    for interface in interfaces:
        if IsImplementation(class_or_instance, interface):
            return True

    return False



#===================================================================================================
# AssertImplements
#===================================================================================================
def AssertImplements(class_or_instance, interface):
    '''
    If given a class, will try to match the class against a given interface. If given an object
    (instance), will try to match the class of the given object.
    
    NOTE: The Interface must have been explicitly declared through :py:func:`interface.Implements`.

    :type class_or_instance: type or classobj or object

    :type interface: Interface
    
    :raises BadImplementationError:
        If the object's class does not implement the given :arg interface:.
        
    :raises InterfaceError:
        In case the :arg interface: object is not really an interface.

    .. attention:: Caching
        Will do a full checking only once, and then cache the result for the given class.

    .. attention:: Runtime modifications
        Runtime modifications in the instances (appending methods or attributed) won't affect
        implementation checking (after the first check), because what is really being tested is the
        class.
    '''
    class_ = _GetClassForInterfaceChecking(class_or_instance)

    is_implementation, reason = _CheckIfClassImplements(class_, interface)

    if not is_implementation:
        raise AssertionError(reason)



#===================================================================================================
# __ResultsCache
#===================================================================================================
class __ResultsCache(object):

    def __init__(self):
        self._cache = {}

    def SetResult(self, args, result):
        self._cache[args] = result

    def GetResult(self, args):
        return self._cache.get(args, None)

    def ForgetResult(self, args):
        self._cache.pop(args, None)



#===================================================================================================
# __ImplementsCache
#===================================================================================================
class __ImplementsCache(__ResultsCache, Singleton):
    pass



#===================================================================================================
# __ImplementedInterfacesCache
#===================================================================================================
class __ImplementedInterfacesCache(__ResultsCache, Singleton):
    pass



#===================================================================================================
# _CheckIfClassImplements
#===================================================================================================
def _CheckIfClassImplements(class_, interface):
    '''
    :type class_: type or classobj
    :param class_: 
        A class type (NOT an instance of the class).
        
    :type interface: Interface
    
    :rtype: (bool, str) or (bool, None)
    :returns:
        (is_implementation, reason)
        If the class doesn't implement the given interface, will return False, and a message stating
        the reason (missing methods, etc.). The message may be None.
    '''
    assert isinstance(class_, (type, classobj))

    # Using explicit memoization, because we need to forget some values at some times
    cache = __ImplementsCache().GetSingleton()

    cached_result = cache.GetResult((class_, interface))
    if cached_result is not None:
        return cached_result

    is_implementation = True
    reason = None

    # Exception: Null implements every Interface (useful for Null Object Pattern and for testing)
    from ben10.foundation.types_ import Null

    if not issubclass(class_, Null):
        if _IsInterfaceDeclared(class_, interface):
            # It is required to explicitly declare that the class implements the interface.

            # Since this will only run *once*, a full check is also done here to ensure it is really
            # implementing.
            try:
                _AssertImplementsFullChecking(class_, interface, check_attr=False)
            except BadImplementationError, e:
                is_implementation = False
                reason = e.message
        else:
            is_implementation = False
            reason = 'The class %s does not declare that it implements the interface %s.' % (
                class_, interface)

    result = (is_implementation, reason)
    cache.SetResult((class_, interface), result)
    return result



#===================================================================================================
# IsImplementationFullChecking
#===================================================================================================
@Deprecated(IsImplementation)
def IsImplementationFullChecking(class_or_instance, interface):
    return IsImplementation(class_or_instance, interface)



#===================================================================================================
# _IsImplementationFullChecking
#===================================================================================================
def _IsImplementationFullChecking(class_or_instance, interface):
    '''
    Used internally by Attribute.
    
    :see: :py:func:`._AssertImplementsFullChecking`
    :type class_or_instance: type or instance
    :param class_or_instance:
        Class or instance to check
    
    :param interface.Interface interface:
        Interface to check
    
    :rtype: bool
    :returns:
        If it implements the interface
    '''
    try:
        _AssertImplementsFullChecking(class_or_instance, interface)
    except BadImplementationError:
        return False
    else:
        return True



#===================================================================================================
# CacheInterfaceAttrs
#===================================================================================================
class CacheInterfaceAttrs(object):
    '''
    Cache for holding the attrs for a given interface (separated by attrs and methods).
    '''

    def __GetInterfaceMethodsAndAttrs(self, interface):
        '''
            :type interface: the interface from where the methods and attributes should be gotten.
            :param interface:
            :rtype: the interface methods and attributes available in a given interface.
        '''
        all_attrs = dir(interface)

        interface_methods = dict()
        interface_attrs = dict()

        for attr in all_attrs:
            val = getattr(interface, attr)
            if type(val) in (Attribute, ReadOnlyAttribute, ScalarAttribute):
                interface_attrs[attr] = val

            if _IsMethod(val, False):
                interface_methods[attr] = val

        return interface_methods, interface_attrs

    def GetInterfaceMethodsAndAttrs(self, interface):
        '''
            We have to make the creation of the ImmutableParamsCacheManager lazy because
            otherwise we'd enter a cyclic import.
            
            :type interface: the interface from where the methods and attributes should be gotten
            :param interface:
                (used as the cache-key)
            :rtype: @see: CacheInterfaceAttrs.__GetInterfaceMethodsAndAttrs
        '''
        try:
            cache = self.cache
        except AttributeError:
            # create it on the 1st access
            from _cached_method import ImmutableParamsCachedMethod
            cache = self.cache = ImmutableParamsCachedMethod(self.__GetInterfaceMethodsAndAttrs)
        return cache(interface)



# cache for the interface attrs (for Methods and Attrs).
cache_interface_attrs = CacheInterfaceAttrs()


#===================================================================================================
# _IsMethod
#===================================================================================================
def _IsMethod(member, include_functions):
    '''
        Consider method the following:
            1) Methods
            2) Functions (if include_functions is True)
            3) instances of Method (should it be implementors of "IMethod"?)
            
        USER: cache mechanism for coilib50.basic.process
    '''
    if include_functions and inspect.isfunction(member):
        return True
    elif inspect.ismethod(member):
        return True
    elif isinstance(member, Method):
        return True
    return False



#===================================================================================================
# AssertImplementsFullChecking
#===================================================================================================
@Deprecated(AssertImplements)
def AssertImplementsFullChecking(class_or_instance, interface, check_attr=True):
    return AssertImplements(class_or_instance, interface)



#===================================================================================================
# _AssertImplementsFullChecking
#===================================================================================================
def _AssertImplementsFullChecking(class_or_instance, interface, check_attr=True):
    '''
    Used internally.
    
    This method will check each member of the given instance (or class) comparing them against the
    ones declared in the interface, making sure that it actually implements it even if it does not
    declare it so using interface.Implements.
    
    .. note:: Slow
        This method is *slow*, so make sure to never use it in hot-spots.
    
    :raises BadImplementationError:
        If :arg class_or_instance: doesn't implement this interface.
    '''
    # Moved from the file to avoid cyclic import:
    from ben10.foundation.types_ import Null

    try:
        is_interface = issubclass(interface, Interface)
    except TypeError, e:
        Reraise(e, "interface=%s (type %s)" % (interface, type(interface)))

    if not is_interface:
        raise InterfaceError(
            'To check against an interface, an interface is required (received: %s -- mro:%s)' %
            (interface, interface.__mro__)
        )

    if isinstance(class_or_instance, Null):
        return True

    try:
        classname = class_or_instance.__name__
    except:
        classname = class_or_instance.__class__.__name__


    if classname == 'InterfaceImplementorStub':
        return _AssertImplementsFullChecking(class_or_instance.GetWrappedFromImplementorStub(), interface, check_attr)

    interface_methods, interface_attrs = cache_interface_attrs.GetInterfaceMethodsAndAttrs(interface)
    if check_attr:
        for attr_name, val in interface_attrs.iteritems():
            if hasattr(class_or_instance, attr_name):
                attr = getattr(class_or_instance, attr_name)
                match, match_msg = val.Match(attr)
                if not match:
                    msg = 'Attribute %r for class %s does not match the interface %s'
                    msg = msg % (attr_name, class_or_instance, interface)
                    if match_msg:
                        msg += ': ' + match_msg
                    raise BadImplementationError(msg)
            else:
                msg = 'Attribute %r is missing in class %s and it is required by interface %s'
                msg = msg % (attr_name, class_or_instance, interface)
                raise BadImplementationError(msg)


    def GetArgSpec(method):
        '''
            Get the arguments for the method, considering the possibility of instances of Method,
            in which case, we must obtain the arguments of the instance "__call__" method.
            
            USER: cache mechanism for coilib50.basic.process
        '''
        if isinstance(method, Method):
            return inspect.getargspec(method.__call__)
        else:
            return inspect.getargspec(method)


    for name in interface_methods:
        # only check the interface methods (because trying to get all the instance methods is
        # too slow).
        try:
            cls_method = getattr(class_or_instance, name)
            if not _IsMethod(cls_method, True):
                raise AttributeError

        except AttributeError:
            msg = 'Method %r is missing in class %r (required by interface %r)'
            raise BadImplementationError(msg % (name, classname, interface.__name__))
        else:
            interface_method = interface_methods[name]

            c_args, c_varargs, c_varkw, c_defaults = GetArgSpec(cls_method)

            if c_varargs is not None and c_varkw is not None:
                if not c_args or c_args == ['self'] or c_args == ['cls']:
                    # Accept the implementor if it matches the signature: (*args, **kwargs)
                    # Accept the implementor if it matches the signature: (self, *args, **kwargs)
                    # Accept the implementor if it matches the signature: (cls, *args, **kwargs)
                    continue

            i_args, i_varargs, i_varkw, i_defaults = inspect.getargspec(interface_method)

            # Rules:
            #
            #   1. Variable arguments or keyword arguments: if present
            #      in interface, then it MUST be present in class too
            #
            #   2. Arguments: names must be the same
            #
            #   3. Defaults: for now we assume that default values
            #      must be the same too
            mismatch_varargs = i_varargs is not None and c_varargs is None
            mismatch_varkw = i_varkw is not None and c_varkw is None
            mismatch_args = i_args != c_args
            mismatch_defaults = i_defaults != c_defaults
            if mismatch_varargs or mismatch_varkw or mismatch_args or mismatch_defaults:
                class_sign = inspect.formatargspec(c_args, c_varargs, c_varkw, c_defaults)
                interface_sign = inspect.formatargspec(i_args, i_varargs, i_varkw, i_defaults)
                msg = '\nMethod %s.%s signature:\n  %s\ndiffers from defined in interface %s\n  %s'
                msg = msg % (classname, name, class_sign, interface.__name__, interface_sign)
                raise BadImplementationError(msg)



#===================================================================================================
# PROFILING FOR ASSERT IMPLEMENTS

# NOTE: There was code here for profiling AssertImplements in revisions prior to 2013-03-19.
#       That code can be useful for seeing where exactly it is being slow.
#===================================================================================================



#===================================================================================================
# Implements
#===================================================================================================
def Implements(*interfaces, **kwargs):
    '''
    Make sure a class implements the given interfaces. Must be used in the class scope during class
    creation:
        
        class Foo(object):
            Implements(IFoo)
        
    For old-style classes, use:
        
        class Foo(QWidget): 
            Implements(IFoo, old_style=True)
        
    For not having it checked on its creation -- may happen for performance reasons -- use:
        
        class Foo(object): 
            Implements(IFoo, no_init_check=True)
    '''
    # Just get the previous frame
    frame = sys._getframe().f_back
    try:
        namespace = frame.f_locals
        curr = namespace.get('__implements__', None)
        if curr is not None:
            namespace['__implements__'] = curr + interfaces
        else:
            namespace['__implements__'] = interfaces

        old_style = kwargs.pop('old_style', False)
        no_init_check = kwargs.pop('no_init_check', False)

        # only put the metaclass on new-style classes (which want to be checked)
        if not old_style and not no_init_check:
            namespace['__metaclass__'] = InterfaceImplementationMetaClass
        else:
            if old_style:
                if kwargs.get('old_style', False):
                    warnings.warn(
                        'DEPRECATED: Interface is deprecated for old-style classes. Use new style.',
                        stacklevel=1,
                    )

        assert len(kwargs) == 0, \
            'Expected only no_init_check or old_style as kwargs. Found: %s' % (kwargs,)

    finally:
        del frame


# TODO: Replace by ImplementsInterface permanently.
ImplementsInterface = Implements



#===================================================================================================
# DeclareClassImplements
#===================================================================================================
def DeclareClassImplements(class_, *interfaces):
    '''
    This is a way to tell, from outside of the class, that a given :arg class_: implements the
    given :arg interfaces:.
    
    .. attention:: Use Implements whenever possible
        This method should be used only when you can't use :py:func:`Implements`, or when you can't
        change the code of the class being declared, i.e., when you:
        * Can't add metaclass because the class already has one
        * Class can't depend on the library where the interface is defined
        * Class is defined from bindings
        * Class is defined in an external library
        * Class is defined by generated code
        
    :type interfaces: list(Interface)
    :type class_: type
    
    :raises BadImplementationError:
        If, after checking the methods, :arg class_: doesn't really implement the :arg interface:.
        
    .. note:: Inheritance
        When you use this method to declare that a base class implements a given interface, you
        should *also* use this in the derived classes, it does not propagate automatically to
        the derived classes. See testDeclareClassImplements.
    '''
    assert isinstance(class_, (type, classobj))

    from itertools import chain

    old_implements = getattr(class_, '__implements__', [])
    class_.__implements__ = list(chain(old_implements, interfaces))

    # This check must be done *after* adding the interfaces to __implements__, because it will
    # also check that the interfaces are declared there.
    try:
        for interface in interfaces:
            # Forget any previous checks
            __ImplementsCache().GetSingleton().ForgetResult((class_, interface))
            __ImplementedInterfacesCache.GetSingleton().ForgetResult(class_)

            AssertImplements(class_, interface)
    except:
        # Roll back...
        class_.__implements__ = old_implements
        raise



#===================================================================================================
# _GetMROForOldStyleClass
#===================================================================================================
def _GetMROForOldStyleClass(class_):
    '''
    :type class_: classobj
    :param class_:
        An old-style class
        
    :rtype: list(classobj)
    :return:
        A list with all the bases in the older MRO (method resolution order)
    '''
    def _CalculateMro(class_, mro):
        for base in class_.__bases__:
            if base not in mro:
                mro.append(base)
                _CalculateMro(base, mro)

    mro = [class_]
    _CalculateMro(class_, mro)
    return mro



#===================================================================================================
# _GetMROForClass
#===================================================================================================
def _GetMROForClass(class_):
    '''
    :param classobj class_:
        A class
        
    :rtype: list(classobj)
    :return:
        A list with all the bases in the older MRO (method resolution order)
    '''
    if hasattr(class_, '__mro__'):
        mro = class_.__mro__
    else:
        mro = _GetMROForOldStyleClass(class_)
    return mro



#===================================================================================================
# _GetClassImplementedInterfaces
#===================================================================================================
def _GetClassImplementedInterfaces(class_):
    cache = __ImplementedInterfacesCache.GetSingleton()
    result = cache.GetResult(class_)
    if result is not None:
        return result

    result = set()

    mro = _GetMROForClass(class_)

    for c in mro:
        interfaces = getattr(c, '__implements__', ())
        for interface in interfaces:
            interface_mro = _GetMROForClass(interface)

            for interface_type in interface_mro:
                if interface_type in [Interface, object]:
                    # Ignore basic types
                    continue
                result.add(interface_type)

    result = frozenset(result)

    cache.SetResult(class_, result)
    return result



#===================================================================================================
# GetImplementedInterfaces
#===================================================================================================
def GetImplementedInterfaces(class_or_object):
    '''
   :rtype: frozenset([interfaces]) 
       The interfaces implemented by the object or class passed.
    '''
    class_ = _GetClassForInterfaceChecking(class_or_object)

    # we have to build the cache attribute given the name of the class, otherwise setting in a base
    # class before a subclass may give errors.
    return _GetClassImplementedInterfaces(class_)



#===================================================================================================
# IsInterfaceDeclared
#===================================================================================================
@Deprecated('IsImplementation')
def IsInterfaceDeclared(class_or_instance, interface_or_interfaces):
    if isinstance(interface_or_interfaces, (set, list, tuple)):
        interfaces = interface_or_interfaces
    else:
        interfaces = [interface_or_interfaces]

    for interface in interfaces:
        if IsImplementation(class_or_instance, interface):
            return True

    return False



#===================================================================================================
# _IsInterfaceDeclared
#===================================================================================================
def _IsInterfaceDeclared(class_, interface):
    '''
        :type interface: Interface or iterable(Interface)
        :param interface:
            The target interface(s). If multitple interfaces are passed the method will return True
            if the given class or instance implements any of the given interfaces.
            
        :rtype: True if the object declares the interface passed and False otherwise. Note that
        to declare an interface, the class MUST have declared 
        
            >>> interface.Implements(Class) 
    '''
    if class_ is None:
        return False

    is_collection = False
    if isinstance(interface, (set, list, tuple)):
        is_collection = True
        for i in interface:
            if not issubclass(i, Interface):
                raise InterfaceError('To check against an interface, an interface is required (received: %s -- mro:%s)' %
                                     (interface, interface.__mro__))
    elif not issubclass(interface, Interface):
        raise InterfaceError('To check against an interface, an interface is required (received: %s -- mro:%s)' %
                             (interface, interface.__mro__))

    declared_interfaces = GetImplementedInterfaces(class_)

    # This set will include all interfaces (and its subclasses) declared for the given objec
    declared_and_subclasses = set()
    for implemented in declared_interfaces:
        declared_and_subclasses.update(implemented.__mro__)

    # Discarding object (it will always be returned in the mro collection)
    declared_and_subclasses.discard(object)

    if not is_collection:
        return interface in declared_and_subclasses
    else:
        return bool(set(interface).intersection(declared_and_subclasses))



#===================================================================================================
# PROFILING FOR IsInterfaceDeclared

# NOTE: There was code here for profiling IsInterfaceDeclared in revisions prior to 2013-03-19.
#       That code can be useful for seeing where exactly it is being called.
#===================================================================================================



#===================================================================================================
# AssertDeclaresInterface
#===================================================================================================
@Deprecated(AssertImplements)
def AssertDeclaresInterface(class_or_instance, interface):
    return AssertImplements(class_or_instance, interface)



#===================================================================================================
# Attribute
#===================================================================================================
class Attribute(object):
    '''
    '''
    _do_not_check_instance = object()

    def __init__(self, attribute_type, instance=_do_not_check_instance):
        '''
        :param type attribute_type:
            Will check the attribute type in the implementation against this type.
            Checks if the attribute is a direct instance of attribute_type, or of it implements it.
            
        :param object instance:
            If passed, will check for *equality* against this instance. The default is to not check
            for equality.
        '''
        self.attribute_type = attribute_type
        self.instance = instance


    def Match(self, attribute):
        '''
        :param object attribute:
            Object that will be compared to see if it matches the expected interface.
            
        :rtype: (bool, str)
        :returns:
            If the given object implements or inherits from the interface expected by this
            attribute, will return (True, None), otherwise will return (False, message), where
            message is an error message of why there was a mismatch (may be None also).
        '''
        msg = None

        if isinstance(attribute, self.attribute_type):
            return (True, None)

        if self.instance is not self._do_not_check_instance:
            if self.instance == attribute:
                return (True, None)
            else:
                return (
                    False,
                    'The instance (%s) does not match the expected one (%s).' % (
                        self.instance, attribute)
                )

        try:
            if _IsImplementationFullChecking(attribute, self.attribute_type):
                return (True, msg)
        except InterfaceError, exception_msg:
            # Necessary because whenever a value is compared to an interface it does not inherits
            # from, IsImplementation raises an InterfaceError. In this context, an error like that
            # will mean that our candidate attribute is in fact not matching the interface, so we
            # capture this error and return False.
            msg = exception_msg

        return (False, None)



#===================================================================================================
# ReadOnlyAttribute
#===================================================================================================
class ReadOnlyAttribute(Attribute):
    '''
    This is an attribute that should be treated as read-only (note that usually this means that
    the related property should be also declared as read-only).
    '''


#===================================================================================================
# ScalarAttribute
#===================================================================================================
class ScalarAttribute(Attribute):
    '''
    '''

    def __init__(self, category):
        '''
        :param str quantity_type:
            String with the category of the Scalar.
        '''
        self.category = category


    @Override(Attribute.Match)
    def Match(self, attribute):
        if not IsInstance(attribute, 'Scalar'):
            return (False, 'The attribute is not a Scalar instance.')
        elif attribute.GetCategory() != self.category:
            return (
                False,
                'The Scalar category (%s) does not match the expected category of the'
                ' interface (%s).' % (attribute.GetCategory(), self.category)
            )

        return (True, None)
