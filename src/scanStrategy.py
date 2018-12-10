import numpy     as np
import src.units as un

class ScanStrategy:
    def __init__(self, log, elv=None, elvDict=None):
        #Store passed parameters
        self.log      = log
        self.elv      = elv
        self.elvDict  = elvDict
        
        #Mininum and maximum allowed elevations
        self.minElv = 20
        self.maxElv = 90

        if elvDict is not None:
            self.elVals = np.fromiter(elvDict.keys()  , dtype=np.float)
            self.elFrac = np.fromiter(elvDict.values(), dtype=np.float)
        else:
            self.elVals = None
            self.elFrac = None
        
    #***** Public Methods *****
    #Sample elevation distribution
    def elvSample(self):
        if self.elv is not None: return self.elv
        if self.elvDict is None: return None
        else:                    samp = np.random.choice(self.elVals, size=1, p=self.elFrac/float(np.sum(self.elFrac)))[0]
        if   samp < self.minElv:
            self.log.log("Cannot have elevation %.1f < %.1f. Using %.1f instead" % (samp, self.minElv, self.minElv), 2)
            return self.minElv
        elif samp > self.maxElv:
            self.log.log("Cannot have elevation %.1f > %.1f. Using %.1f instead"  % (samp, self.maxElv, self.maxElv), 2)
            return self.maxElv
        else:
            return samp
            
    #Retrieve user-defined elevation
    def getElv(self):
        return self.elv
