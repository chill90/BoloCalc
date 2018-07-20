import numpy         as np
import collections   as cl
import src.physics   as ph
import src.units     as un
import src.parameter as pr

class Foregrounds:
    def __init__(self, log, fgndDict=None, nrealize=1):
        #Store passed parameters
        self.log      = log
        self.fgndDict = fgndDict
        self.nrealize = nrealize

        #Create physics object for calculations
        self.ph = ph.Physics()

        #Store foreground parameters
        if self.fgndDict:
            self.params = cl.OrderedDict({'Dust Temperature':       self.__paramSamp(pr.Parameter(self.log, 'Dust Temperature',       self.fgndDict['Dust Temperature'],       min=0.0,     max=np.inf)),
                                          'Dust Spec Index':        self.__paramSamp(pr.Parameter(self.log, 'Dust Spec Index',        self.fgndDict['Dust Spec Index'],        min=-np.inf, max=np.inf)),
                                          'Dust Amplitude':         self.__paramSamp(pr.Parameter(self.log, 'Dust Amplitude',         self.fgndDict['Dust Amplitude'],         min=0.0,     max=np.inf)),
                                          'Dust Scale Frequency':   self.__paramSamp(pr.Parameter(self.log, 'Dust Scale Frequency',   self.fgndDict['Dust Scale Frequency'],   min=0.0,     max=np.inf)),
                                          'Synchrotron Spec Index': self.__paramSamp(pr.Parameter(self.log, 'Synchrotron Spec Index', self.fgndDict['Synchrotron Spec Index'], min=-np.inf, max=np.inf)),
                                          'Synchrotron Amplitude':  self.__paramSamp(pr.Parameter(self.log, 'Synchrotron Amplitude',  self.fgndDict['Synchrotron Amplitude'],  min=0.0,     max=np.inf))})
        else:
            #Default parameters from Planck
            self.params = cl.OrderedDict({'Dust Temperature':       19.7,
                                          'Dust Spec Index':        1.5,
                                          'Dust Amplitude':         2.e-3,
                                          'Dust Scale Frequency':   353.*un.GHzToHz,
                                          'Synchrotron Spec Index': -3.0,
                                          'Synchrotron Amplitude':  6.e3})

        #Dust angular power spectrum constants, taken from Dunkley
        self.dustAngAmp = 8.e-12
        self.dustEll0    = 10.0
        self.dustNu0     = 90.0*un.GHzToHz #[Hz]
        self.dustM       = -0.5

        #Synchrotron angular power spectrum constants, taken from Dunkley
        self.syncAngAmp = 4e-12
        self.syncEll0    = 10.0
        self.syncNu0     = 90.0*un.GHzToHz #[Hz]
        self.syncM       = -0.6

    #***** Public methods *****
    #Polarized galactic dust spectral radiance [W/(m^2-Hz)]
    def dustSpecRad(self, emissivity, freq, dustAmp=None, dustTemp=None, dustSpecIndex=None):
        if dustAmp == None:
            dustAmp = self.params['Dust Amplitude']
        if dustTemp == None:
            dustTemp = self.params['Dust Temperature']
        if dustSpecIndex == None:
            dustSpecIndex = self.params['Dust Spec Index']

        return emissivity*dustAmp*((freq/float(self.params['Dust Scale Frequency']))**dustSpecIndex)*self.ph.bbSpecRad(freq, dustTemp)

    #Polarized galactic dust power spectrum on a diffraction-limited detector [W/Hz]
    def dustPowSpec(self, emissivity, freq, dustAmp=None, dustTemp=None, dustSpecIndex=None):
        if dustAmp == None:
            dustAmp = self.params['Dust Amplitude']
        if dustTemp == None:
            dustTemp = self.params['Dust Temperature']
        if dustSpecIndex == None:
            dustSpecIndex = self.params['Dust Spec Index']

        return 0.5*self.ph.AOmega(freq)*self.dustSpecRad(emissivity, freq, dustAmp, dustTemp, dustSpecIndex) 

    #Polarized galactic dust power on a diffraction-limited detector [W]
    def dustPower(self, emissivity, freq, fbw, dustAmp=None, dustTemp=None, dustSpecIndex=None):
        if dustAmp == None:
            dustAmp = self.params['Dust Amplitude']
        if dustTemp == None:
            dustTemp = self.params['Dust Temperature']
        if dustSpecIndex == None:
            dustSpecIndex = self.params['Dust Spec Index']

        freq1, freq2 = self.ph.bandEdges(freq, fbw)
        if callable(emissivity):
            return itg.quad(self.dustPowSpec(emissivity(x), x, dustAmp, dustTemp, dustSpecIndex), freq1, freq2)[0]
        else:
            return itg.quad(self.dustPowSpec(emissivity,    x, dustAmp, dustTemp, dustSpecIndex), freq1, freq2)[0]
    
    #Polarized galactic dust power dust power equivalent CMB temperature spectrum on a diffraction-limited detector [K/Hz]
    def dustPowTempSpec(self, emissivity, freq, dustAmp=None, dustTemp=None, dustSpecIndex=None):
        if dustAmp == None:
            dustAmp = self.params['Dust Amplitude']
        if dustTemp == None:
            dustTemp = self.params['Dust Temperature']
        if dustSpecIndex == None:
            dustSpecIndex = self.params['Dust Spec Index']

        return self.dustPowSpec(emissivity, freq, dustAmp, dustTemp, dustSpecIndex)/self.ph.aniPowSpec(freq, self.ph.Tcmb, emissivity)

    #Polarized galactic dust power dust power equivalent CMB temperature on a diffraction-limited detector [K]
    def dustPowTemp(self, emissivity, freq, fbw, dustAmp=None, dustTemp=None, dustSpecIndex=None):
        if dustAmp == None:
            dustAmp = self.params['Dust Amplitude']
        if dustTemp == None:
            dustTemp = self.params['Dust Temperature']
        if dustSpecIndex == None:
            dustSpecIndex = self.params['Dust Spec Index']

        freq1, freq2 = self.ph.bandEdges(freq, fbw)
        if callable(emissivity):
            return itg.quad(self.dustPowTempSpec(emissivity(x), x, dustAmp, dustTemp, dustSpecIndex), freq1, freq2)[0]
        else:
            return itg.quad(self.dustPowTempSpec(emissivity   , x, dustAmp, dustTemp, dustSpecIndex), freq1, freq2)[0]    

    #Synchrotron spectral radiance [W/(m^2-Hz)]
    def syncSpecRad(self, emissivity, freq, syncAmp=None, syncSpecIndex=None):
        if syncAmp == None:
            syncAmp = self.params['Synchrotron Amplitude']
        if syncSpecIndex == None:
            syncSpecIndex = self.params['Synchrotron Spec Index']

        return emissivity*syncAmp*(freq**syncSpecIndex)

    #Synchrotron power spectrum on a diffraction-limited detector [W/Hz]
    def syncPowSpec(self, emissivity, freq, syncAmp=None, syncSpecIndex=None):
        if syncAmp == None:
            syncAmp = self.params['Synchrotron Amplitude']
        if syncSpecIndex == None:
            syncSpecIndex = self.params['Synchrotron Spec Index']

        return 0.5*self.ph.AOmega(freq)*self.syncSpecRad(emissivity, freq, syncAmp, syncSpecIndex)

    #Synchrotron power on on diffraction-limited detector [W]
    def syncPower(self, emissivity, freq, fbw, syncAmp=None, syncSpecIndex=None):
        if syncAmp == None:
            syncAmp = self.params['Synchrotron Amplitude']
        if syncSpecIndex == None:
            syncSpecIndex = self.params['Synchrotron Spec Index']

        freq1, freq2 = self.ph.bandEdges(freq, fbw)
        if callable(emissivity):
            return itg.quad(self.syncPowSpec(emissivity(x), x, syncAmp, syncSpecIndex), freq1, freq2)[0]
        else:
            return itg.quad(self.syncPowSpec(emissivity,    x, syncAmp, syncSpecIndex), freq1, freq2)[0]
        
    #Synchrotron power equivalent CMB temperature spectrum on a diffraction-limited detector [K/Hz]
    def syncPowTempSpec(self, emissivity, freq, syncAmp=None, syncSpecIndex=None):
        if syncAmp == None:
            syncAmp = self.params['Synchrotron Amplitude']
        if syncSpecIndex == None:
            syncSpecIndex = self.params['Synchrotron Spec Index']
        
        return self.syncPowSpec(emissivity, freq, syncAmp, syncSpecIndex)/(self.ph.aniPowSpec(freq, self.ph.Tcmb, emissivity))

    #Synchrotron power equivalent CMB temperature on a diffraction-limited detector [K]
    def syncPowTemp(self, emissivity, freq, fbw, syncAmp=None, syncSpecIndex=None):
        if syncAmp == None:
            syncAmp = self.params['Synchrotron Amplitude']
        if syncSpecIndex == None:
            syncSpecIndex = self.params['Synchrotron Spec Index']

        freq1, freq2 = self.ph.bandEdges(freqCent, fracBw)
        if callable(emissivity):
            return itg.quad(self.syncPowTempSpec(emissivity(x), x, syncAmp, syncSpecIndex), freq1, freq2)[0]
        else:
            return itg.quad(self.syncPowTempSpec(emissivity,    x, syncAmp, syncSpecIndex), freq1, freq2)[0]
        
    #Polarized galactic dust angular power spectrum [W/Hz]
    def dustAngPowSpec(self, emissivity, freq, ell, dustAngAmp=None, dustSpecIndex=None, dustEll0=None, dustNu0=None, dustM=None):
        if dustAngAmp == None:
            dustAngAmp = self.dustAngAmp
        if dustSpecIndex == None:
            dustSpecIndex = self.params['Dust Spec Index']
        if dustEll0 == None:
            dustEll0 = self.dustEll0
        if dustNu0 == None:
            dustNu0 = self.dustNu0
        if dustM == None:
            dustM = self.dustM

        return emissivity*((2*self.ph.PI*dustAngAmp)/(ell*(ell + 1.)))*((freq/float(dustNu0))**(2*dustSpecIndex))*((ell/float(dustEll0))**dustM)

    #For calculating the polarized synchrotron radiation angular power spectrum
    def syncAngPowSpec(self, emissivity, freq, ell, syncAngAmp=None, syncSpecIndex=None, syncEll0=None, syncNu0=None, syncM=None):
        if syncAngAmp == None:
            syncAngAmp = self.syncAngAmp
        if syncSpecIndex == None:
            syncSpecIndex = self.params['Synchrotron Spec Index']
        if syncEll0 == None:
            syncEll0 = self.syncEll0
        if syncNu0 == None:
            syncNu0 = self.syncNu0
        if syncM == None:
            syncM = self.syncM

        return emissivity*((2*self.ph.PI*syncAngAmp)/(ell*(ell + 1.)))*((freq/float(syncNu0))**(2*syncSpecIndex))*((ell/float(syncEll0))**syncM)

    #***** Private Methods *****
    def __paramSamp(self, param): 
        if not 'instance' in str(type(param)): return np.float(param)
        if self.nrealize == 1: return param.getAvg()
        else:                  return param.sample(nsample=1)
