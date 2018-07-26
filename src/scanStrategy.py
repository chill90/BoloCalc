import numpy     as np
import src.units as un

class ScanStrategy:
    def __init__(self, log, elv=None, elvDict=None):
        #Store passed parameters
        self.log      = log
        self.elv      = elv
        self.elvDict  = elvDict

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
        else:                    return np.random.choice(self.elVals, size=1, p=self.elFrac/float(np.sum(self.elFrac)))[0]
    #Retrieve user-defined elevation
    def getElv(self):
        return self.elv
