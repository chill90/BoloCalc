#python Version 2.7.2
import datetime as dt

class Log:
    def __init__(self, logFile, verbose=1):
        self.__logFile = logFile
        self.__f = open(self.__logFile, 'w')
        if verbose > 2:     self.__verbose = 2
        if verbose < 0:     self.__verbose = 0
        if verbose is None: self.__verbose = 0
        else:               self.__verbose = verbose
    
    def log(self, msg, importance=None):
        now = dt.datetime.now()
        if not importance: importance = self.__verbose
        wrmsg = '[%04d-%02d-%02d %02d:%02d:%02d] %s\n' % (now.year, now.month, now.day, now.hour, now.minute, now.second, msg)
        self.__f.write(wrmsg)
        if importance <= self.__verbose: print wrmsg,
    
        
        
