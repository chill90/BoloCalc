#python Version 2.7.2
import numpy as np
import sys   as sy

class Parameter:
    def __init__(self, log, name, input, unit=1.0, min=None, max=None, type=np.float):
        #The string that delimits the mean value from the spread
        self.__spreadDelim = '+/-'
        
        #Store passed parameters
        self.log  = log
        self.name = name
        self.inst = input
        self.unit = unit
        self.min  = self.__float(min)
        self.max  = self.__float(max)
        self.type = type

        if self.__spreadDelim in input:
            vals     = input.split(self.__spreadDelim)
            self.avg = self.__float(vals[0], self.unit)
            self.std = self.__float(vals[1], self.unit)
        else:
            self.avg = self.__float(input,   self.unit)
            self.std = self.__zero(self.avg)
            
        #Check that the value is within the allowed range. If not, terminate the program
        if not isinstance(self.avg, str):
            if np.any(self.avg < self.min):
                print self.avg
                self.log.log("Passed value %f for parameter %s lower than the mininum allowed value %f" % (self.avg, self.name, self.min), 0)
                sy.exit(1)
            elif np.any(self.avg > self.max):
                self.log.log("Passed value %f for parameter %s greater than the maximum allowed value %f" % (self.avg, self.name, self.max), 0)
                sy.exit(1)

    #***** Public Methods *****
    def isEmpty(self):
        if 'NA' in str(self.avg): return True
        else:                     return False

    def convolve(self, param):
        if not self.isEmpty() and not param.isEmpty():
            self.avg = self.avg*param.avg
            self.std = np.sqrt(self.std**2 + param.std**2)

    def multiply(self, factor):
        if not self.isEmpty():
            self.avg = self.avg*factor
            self.std = self.std*factor
    
    def fetch(self, bandID=1):
        if self.isEmpty():
            return ('NA', 'NA')
        else:
            if 'array' in str(type(self.avg)): return (self.avg[bandID-1], self.std[bandID-1])
            else:                              return (self.avg,           self.std          )

    def change(self, newAvg, newStd=None, bandID=1):
        if 'array' in str(type(self.avg)): 
            self.avg[bandID-1] = newAvg
            if not newStd == None: self.std[bandID-1] = newStd
        else:
            self.avg = newAvg
            if not newStd == None: self.std = newStd

    def getAvg(self, bandID=1):
        return self.fetch(bandID)[0]
    
    def getStd(self, bandID=1):
        return self.fetch(bandID)[1]

    def sample(self, bandID=1, nsample=1, min=None, max=None):
        if self.isEmpty(): 
            return 'NA'
        else:
            avg, std = self.fetch(bandID)
            if np.any(std <= 0.): return avg
            else:         
                if nsample == 1: samp = np.random.normal(avg, std, nsample)[0]
                else:            samp = np.random.normal(avg, std, nsample)
                
            if min is not None: 
                if samp < min: return min
            if max is not None:
                if samp > max: return max
            return samp

    #***** Private Methods *****
    def __float(self, val, unit=1.0):
        try:
            return unit*float(val)
        except:
            try:
                return unit*np.array(eval(val)).astype(np.float)
            except:
                return str(val)

    def __zero(self, val):
        try:
            return np.zeros(len(val))
        except:
            return 0.
