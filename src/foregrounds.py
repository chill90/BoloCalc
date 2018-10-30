#Core Python packages
import numpy         as np
import collections   as cl

#BoloCalc packages
import src.physics   as ph
import src.units     as un

class Foregrounds:
    def __init__(self, log, fgndDict=None, nrealize=1):
        #Store passed parameters
        self.log      = log
        self.fgndDict = fgndDict
        self.nrealize = nrealize

        #Create physics object for calculations
        self.ph = ph.Physics()

        #Store foreground parameters
        if self.fgndDict is None:
            self.fgndDict = cl.OrderedDict({'Dust Temperature':       19.7,
                                            'Dust Spec Index':        1.5,
                                            'Dust Amplitude':         2.e-3,
                                            'Dust Scale Frequency':   353.*un.GHzToHz,
                                            'Synchrotron Spec Index': -3.0,
                                            'Synchrotron Amplitude':  6.e3})

    #***** Public methods *****
    #Polarized galactic dust spectral radiance [W/(m^2-Hz)]
    def dustSpecRad(self, freq, emissivity=1.0):
        return emissivity*self.fgndDict['Dust Amplitude']*((freq/float(self.fgndDict['Dust Scale Frequency']))**self.fgndDict['Dust Spec Index'])*self.ph.bbSpecRad(freq, self.fgndDict['Dust Temperature'])

    #Synchrotron spectral radiance [W/(m^2-Hz)]
    def syncSpecRad(self, freq, emissivity=1.0):
        return emissivity*self.fgndDict['Synchrotron Amplitude']*(freq**self.fgndDict['Synchrotron Spec Index'])

    #***** Private Methods *****
    def __paramSamp(self, param): 
        if not ('instance' in str(type(param)) or 'class' in str(type(param))): return np.float(param)
        if self.nrealize == 1: return param.getAvg()
        else:                  return param.sample(nsample=1)
