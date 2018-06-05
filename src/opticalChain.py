#python Version 2.7.2
import numpy as np
import optic as op

class OpticalChain:
    def __init__(self, log, optFile, nrealize=1, optBands=None):
        #Store passed parameters
        self.log      = log
        self.optFile  = optFile
        self.nrealize = nrealize
        self.optBands = optBands

        #Store optic objects
        self.log.log("Storing individual optics in optical chain", 1)
        output      = np.loadtxt(self.optFile, dtype=np.str, delimiter='|'); keyArr  = output[0]; elemArr = output[1:]
        opticDicts  = [{keyArr[i].strip(): elem[i].strip() for i in range(len(keyArr))} for elem in elemArr]
        if self.optBands:
            self.optics = {}
            for opticDict in opticDicts:
                if opticDict['Element'] in self.optBands.keys(): 
                    self.optics[opticDict['Element']] = op.Optic(log, opticDict, nrealize=self.nrealize, bandFile=self.optBands[opticDict['Element']])
                    self.log.log("Using user-input spectra for optic '%s'" % (opticDict['Element']),1)
                else:                                       
                    self.optics[opticDict['Element']] = op.Optic(log, opticDict, nrealize=self.nrealize)
        else:
            self.optics = {opticDict['Element']: op.Optic(log, opticDict, nrealize=self.nrealize) for opticDict in opticDicts}
            
    #***** Public Methods *****
    #Generate element, temperature, emissivity, and efficiency arrays
    def generate(self, ch):
        arr = [optic.generate(ch) for optic in self.optics.values()]
        elem = [a[0] for a in arr]; emiss = [a[1] for a in arr]; effic = [a[2] for a in arr]; temp = [a[3] for a in arr]
        return elem, emiss, effic, temp
