import numpy       as np
import collections as cl
import                os
import src.optic   as op

class OpticalChain:
    def __init__(self, log, optFile, nrealize=1, optBands=None):
        #Store passed parameters
        self.log      = log
        self.optFile  = optFile
        self.nrealize = nrealize
        self.optBands = optBands
        self.camName  = self.optFile.rstrip(os.sep).split(os.sep)[-3]
        self.telName  = self.optFile.rstrip(os.sep).split(os.sep)[-4]
        self.expName  = self.optFile.rstrip(os.sep).split(os.sep)[-5]

        #Store optic objects
        self.log.log("Storing individual optics in optical chain", 1)
        output      = np.loadtxt(self.optFile, dtype=np.str, delimiter='|'); keyArr  = output[0]; elemArr = output[1:]
        opticDicts  = [{keyArr[i].strip(): elem[i].strip() for i in range(len(keyArr))} for elem in elemArr]
        self.optics = cl.OrderedDict({})
        for opticDict in opticDicts:
            if opticDict['Element'] in self.optics.keys():
                raise Exception('FATAL: Multiple optical elements with the same name "%s" defined in camera "%s", telescope "%s", experiment "%s"' % (opticDict['Element'], self.camName, self.telName, self.expName))
            if self.optBands is not None and opticDict['Element'] in self.optBands.keys(): 
                self.optics.update({opticDict['Element']: op.Optic(log, opticDict, nrealize=self.nrealize, bandFile=self.optBands[opticDict['Element']])})
                self.log.log("Using user-input spectra for optic '%s'" % (opticDict['Element']),1)
            else:                                       
                self.optics.update({opticDict['Element']: op.Optic(log, opticDict, nrealize=self.nrealize)})
            
    #***** Public Methods *****
    #Generate element, temperature, emissivity, and efficiency arrays
    def generate(self, ch):
        arr = [optic.generate(ch) for optic in list(self.optics.values())]
        elem = [a[0] for a in arr]; emiss = [a[1] for a in arr]; effic = [a[2] for a in arr]; temp = [a[3] for a in arr]
        return elem, emiss, effic, temp
