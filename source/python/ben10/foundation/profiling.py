import cProfile as profile
import pstats
import sys



#=======================================================================================================================
# ObtainStats
#=======================================================================================================================
def ObtainStats(method, *args, **kwargs):
    '''
    Runs the method in profile mode and returns the pstats.Stats method relative to that run.
    
    :param callable method:
        The method that should be profiled.
        
    @param args and kwargs: object
        Parameters to be passed to call the method.
    
    :rtype: pstats.Stats
    :returns:
        The stats that was generated from running the method in profile mode.
    '''
    prof = profile.Profile()
    prof.runcall(method, *args, **kwargs)
    stats = pstats.Stats(prof)
    return stats



#=======================================================================================================================
# ProfileMethod
#=======================================================================================================================
def ProfileMethod(filename, rows=50, sort=(('cumul',), ('time',))):
    '''Decorator to profile the decorated function or method.

    :param filename: 
        Where to save the profiling information. If None, profile information will be printed to the output.

    :param rows:
        If the profile will be printed to the output, how many rows of data to print.

    :type sort: tuple(str, ...), tuple(tuple(str, ...), ...)
    :param sort:
        If the profile will be printed to the output (filename=None), how to sort the stats. 
        It may be a list of strings or a list of lists of strings (in which case it will print
        the result multiple times, one for each inner list. E.g.: (('time',), ('cumul',))
    
    Flags accepted in sort:
        ['tim', 'stdn', 'p', 'ca', 'module', 'pcalls', 'file', 'cumu', 'st', 'cu', 'pcall', 
        'pc', 'na', 'lin', 'cumulative', 'nf', 'nam', 'stdna', 'cumul', 'call', 'time', 'cum', 
        'mod', 'modul', 'fil', 'pcal', 'cumula', 'modu', 'stdnam', 'cumulati', 'fi', 'line', 
        'cumulativ', 'std', 'pca', 'name', 'calls', 'f', 'mo', 'nfl', 'm', 'l', 'stdname', 's', 
        'li', 't', 'cal', 'ti', 'cumulat']
        
        Available from: 
        stats = pstats.Stats(prof)
        print stats.get_sort_arg_defs().keys()
    '''

    def wrapper(method):
        def inner(*args, **kwargs):
            prof = profile.Profile()
            result = prof.runcall(method, *args, **kwargs)

            if filename is None:
                tup_sort = sort
                s = tup_sort[0]
                if isinstance(s, str):
                    tup_sort = [tup_sort]

                stats = pstats.Stats(prof)
                for s in tup_sort:
                    stats.strip_dirs().sort_stats(*s).print_stats(int(rows))
            else:
                prof.dump_stats(filename)

            return result
        return inner
    return wrapper



#=======================================================================================================================
# PrintProfile
#=======================================================================================================================
def PrintProfile(filename, rows=30, sort=('time', 'calls'), streams=None):
    '''
        Prints the profiling info for a given function.
        
        :type filename: the filename with the stats we want to load.
        :param filename:
        :type rows: the number of rows that we want to print.
        :param rows:
        :type sort: list with strings for the way we want to sort the results.
        :param sort:
    '''
    PrintProfileMultiple(filename, rows, [sort], streams)



#=======================================================================================================================
# PrintProfileMultiple
#=======================================================================================================================
def PrintProfileMultiple(filename, rows=30, sort=(('cumulative', 'time'), ('time', 'calls')),
    streams=None):
    '''
        Prints multiple profile outputs at once.
        
        :type filename: the filename with the stats we want to load.
        :param filename:
        :type rows: the number of rows that we want to print.
        :param rows:
        :type sort: list of tuples with the types of sorting for the outputs we want 
        :param sort:
            (see defaults for example)
            
        the available sorting options (from Stats.sort_arg_dict_default)
        calls     cumulative     file        line        module    
        name      nfl            pcalls      stdname     time      
            
        :type streams: if specified, the output will be print to the given streams (otherwise it'll
        :param streams:
            be print to stdout).
    '''
    stats = pstats.Stats(filename)
    stats.strip_dirs()
    if streams is None:
        streams = [sys.stdout]

    initial = sys.stdout
    for s in sort:
        stats.sort_stats(*s)
        for stream in streams:
            sys.stdout = stream
            stats.stream = stream
            try:
                stats.print_stats(int(rows))
            finally:
                sys.stdout = initial
