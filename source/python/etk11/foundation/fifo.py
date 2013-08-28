from etk11.foundation.odict import odict



#=======================================================================================================================
# FIFO
#=======================================================================================================================
class FIFO(odict):
    '''
    This is a "First In, First Out" queue, so, when the queue size is reached, the first item added is removed.
    '''

    def __init__(self, maxsize):
        '''
        :param int maxsize:
            The maximum size of this cache.
        '''
        odict.__init__(self)
        self._maxsize = maxsize


    def __setitem__(self, key, value):
        '''
        Sets an item in the cache. Pops items as needed so that the max size is never passed.
        
        :param object key:
            Key to be set
            
        :param object value:
            Corresponding value to be set for the given key
        '''
        l = len(self)

        # Note, we must pop items before adding the new one to the cache so that
        # the size does not exceed the maximum at any time.
        while l >= self._maxsize:
            l -= 1
            # Pop the first item created
            self.popitem(0)

        odict.__setitem__(self, key, value)

