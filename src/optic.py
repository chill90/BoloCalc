import numpy         as np
import collections   as cl
import src.parameter as pr
import src.physics   as ph
import src.units     as un
import src.band      as bd

class Optic:
    def __init__(self, log, dict, nrealize=1, bandFile=None):
        self.__ph = ph.Physics()
        self.log      = log
        self.bandFile = bandFile
        self.nrealize = nrealize

        #Store optic parameters
        self.elem       = dict['Element']
        self.paramsDict = cl.OrderedDict({'Temperature':    pr.Parameter(self.log, 'Temperature',    dict['Temperature'],             min=0.0, max=np.inf),
                                          'Absorption':     pr.Parameter(self.log, 'Absorption',     dict['Absorption'],              min=0.0, max=1.0   ),
                                          'Reflection':     pr.Parameter(self.log, 'Reflection',     dict['Reflection'],              min=0.0, max=1.0   ),
                                          'Thickness':      pr.Parameter(self.log, 'Thickness',      dict['Thickness'],     un.mmToM, min=0.0, max=np.inf),
                                          'Index':          pr.Parameter(self.log, 'Index',          dict['Index'],                   min=0.0, max=np.inf),
                                          'Loss Tangent':   pr.Parameter(self.log, 'Loss Tangent',   dict['Loss Tangent'],  1.e-04,   min=0.0, max=np.inf),
                                          'Conductivity':   pr.Parameter(self.log, 'Conductivity',   dict['Conductivity'],  1.e+06,   min=0.0, max=np.inf),
                                          'Surface Rough':  pr.Parameter(self.log, 'Surface Rough',  dict['Surface Rough'], un.umToM, min=0.0, max=np.inf),
                                          'Spillover':      pr.Parameter(self.log, 'Spillover',      dict['Spillover'],               min=0.0, max=1.0   ),
                                          'Spillover Temp': pr.Parameter(self.log, 'Spillover Temp', dict['Spillover Temp'],          min=0.0, max=np.inf),
                                          'Scatter Frac':   pr.Parameter(self.log, 'Scatter Frac',   dict['Scatter Frac'],            min=0.0, max=1.0   ),
                                          'Scatter Temp':   pr.Parameter(self.log, 'Scatter Temp',   dict['Scatter Temp'],            min=0.0, max=np.inf)})

    #***** Public Functions *****
    #Generate element, temperature, emissivity, and efficiency
    def generate(self, ch):
        #Generate optic parameters
        self.params = {}
        for k in self.paramsDict:
            self.params[k] = self.__paramSamp(self.paramsDict[k], ch.bandID)

        #Temperature
        temp  = np.ones(ch.nfreq)*self.params['Temperature']

        #Efficiency from a band file?
        if self.bandFile is not None:
            band = bd.Band(self.log, self.bandFile, ch.freqs)
            eff  = band.sample()[0]
            if eff is not None:
                eff = np.array([e if e > 0 else 0. for e in eff])
                eff = np.array([e if e < 1 else 1. for e in eff])
        else: 
            eff = None

        #Reflection -- use only if no band file
        if eff is None:
            if not self.params['Reflection'] == 'NA': refl = np.ones(ch.nfreq)*self.params['Reflection']
            else:                                     refl = np.zeros(ch.nfreq)

        #Spillover
        if not self.params['Spillover'] == 'NA': spill = np.ones(ch.nfreq)*self.params['Spillover']
        else:                                    spill = np.zeros(ch.nfreq)
        if not self.params['Spillover Temp'] == 'NA': spillTemp = np.ones(ch.nfreq)*self.params['Spillover Temp']
        else:                                         spillTemp = np.ones(ch.nfreq)*temp

        #Scattering
        if   not self.params['Surface Rough'] == 'NA': scatt     = 1. - self.__ph.ruzeEff(ch.freqs, self.params['Surface Rough'])
        elif not self.params['Scatter Frac'] == 'NA':  scatt     = scatt = np.ones(ch.nfreq)*self.params['Scatter Frac']
        else:                                          scatt     = np.zeros(ch.nfreq)
        if not self.params['Scatter Temp'] == 'NA':    scattTemp = scattTemp = np.ones(ch.nfreq)*self.params['Scatter Temp']
        else:                                          scattTemp = np.ones(ch.nfreq)*temp

        #Absorption
        if 'APERTURE' in self.elem.upper() or 'STOP' in self.elem.upper() or 'LYOT' in self.elem.upper():
            if not eff:
                if not self.params['Absorption'] == 'NA': abso = np.ones(ch.nfreq)*self.params['Absorption']
                else:                                     abso = 1. - self.__ph.spillEff(ch.freqs, ch.params['Pixel Size'], ch.Fnumber, ch.params['Waist Factor'])
            else:       
                abso = 1. - eff
        else:
            if not self.params['Absorption'] == 'NA':                             abso = np.ones(ch.nfreq)*self.params['Absorption']
            elif 'MIRROR' in self.elem.upper() or 'PRIMARY' in self.elem.upper(): abso = 1. - self.__ph.ohmicEff(ch.freqs, self.params['Conductivity'])
            else:                                                                           
                try:                                                              abso = self.__ph.dielectricLoss(ch.freqs, self.params['Thickness'], self.params['Index'], self.params['Loss Tangent'])
                except:                                                           abso = np.zeros(ch.nfreq)
        
        #Reflection from band file?
        if eff is not None: 
            refl = 1. - eff - abso
            for r in refl:
                if r > 1: r = 1.
                if r < 0: r = 0.
        
        #Element, absorption, efficiency, and temperature
        if not scatt is None and not spill is None: emiss = abso + scatt*self.__powFrac(scattTemp, temp, ch.freqs) + spill*self.__powFrac(spillTemp, temp, ch.freqs)
        elif not spill is None:                     emiss = abso + spill*self.__powFrac(spillTemp, temp, ch.freqs) 
        elif not scatt is None:                     emiss = abso + scatt*self.__powFrac(scattTemp, temp, ch.freqs)
        else:                                       emiss = abso
        if not eff is None: effic = eff
        else:               effic = 1. - refl - abso - spill - scatt

        #Store channel pixel parameters
        if self.elem.upper() == 'APERTURE' or self.elem.upper() == 'LYOT' or self.elem.upper() == 'STOP':
            ch.apEff     = np.trapz(effic, ch.freqs)/float(ch.freqs[-1] - ch.freqs[0])
            ch.edgeTaper = self.__ph.edgeTaper(ch.apEff)

        return [self.elem, emiss, effic, temp]

    #***** Private Methods *****
    #Ratio of blackbody power between two temperatures
    def __powFrac(self, T1, T2, freqs):
        return np.trapz(self.__ph.bbPowSpec(freqs, T1), freqs)/float(np.trapz(self.__ph.bbPowSpec(freqs, T2), freqs))

    #Sample parameter values
    def __paramSamp(self, param, bandID):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))): return np.float(param)
        if self.nrealize == 1: return param.getAvg(bandID)
        else:                  return param.sample(bandID=bandID, nsample=1)
