'''
    @author
        ama@esss.com.br
        fabioz@esss.com.br
'''

# Custom cache for optimization purposes.
__bases_cache = {}
__hierarchy_cache = {}

#===================================================================================================
# AllBasesNames
#===================================================================================================
def AllBasesNames(p_class):
    '''
        :rtype: set with all the names of the bases classes of the given class.
    '''
    try:
        return __bases_cache[p_class]
    except KeyError:
        result = set()
        for i_base in p_class.__bases__:
            result.add(i_base.__name__)
            result.update(AllBasesNames(i_base))
        return __bases_cache.setdefault(p_class, result)



#===================================================================================================
# IsInstance
#===================================================================================================
def IsInstance(p_object, p_class_name):
    '''
    :param object p_object:
        The object we would like to test for.

    :param str p_class_name:
        Name or class to test if the object is an instance of.

    Like the built-in isinstance, but also accepts a class name as parameter.
    '''
    try:
        # obtain the type of the class; using only type() is not enough, because some built-in
        # types don't respond to type() correctly (vtk objects for instance always return the
        # same type object)
        class_ = p_object.__class__
    except AttributeError:
        # some built-in objects don't have a __class__ attribute, but return its type correctly
        # from type()
        class_ = type(p_object)
    return IsSubclass(class_, p_class_name)


#===================================================================================================
# IsSubclass
#===================================================================================================
def IsSubclass(p_class, p_class_name):
    '''
    Like the built-in issubclass, but also accepts a class name as parameter.
    '''
    isins = isinstance  # put it in locals

    if isins(p_class_name, str):
        if p_class_name == p_class.__name__:
            return True

        try:
            names = __bases_cache[p_class]
        except KeyError:
            return p_class_name in AllBasesNames(p_class)
        else:
            return p_class_name in names


    elif isins(p_class_name, tuple) and len(p_class_name) > 0 and isins(p_class_name[0], str) :

        names = None

        for c in p_class_name:
            if c == p_class.__name__:
                return True

            if names is None:
                try:
                    names = __bases_cache[p_class]
                except KeyError:
                    names = AllBasesNames(p_class)

            if c in names:
                return True


        return False

    else:
        return issubclass(p_class, p_class_name)


#===================================================================================================
# _IterClassHierarchy
#===================================================================================================
def _IterClassHierarchy(class_):
    '''
        Iterates through the whole hierarchy of a given class (including the class itself)
    '''
    yield class_

    iter = _IterClassHierarchy
    for c in class_.__bases__:
        for c in iter(c):
            yield c


#===================================================================================================
# GetClassHierarchy
#===================================================================================================
def GetClassHierarchy(class_):
    '''
        :rtype: the class hierarchy for a given class in a flattened way as a set.
    '''
    try:
        return __hierarchy_cache[class_]
    except:
        return __hierarchy_cache.setdefault(class_, set(_IterClassHierarchy(class_)))


