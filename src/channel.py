#Core Python packages
import numpy              as np
import glob               as gb
import collections        as cl
import                       os

#BoloCalc packages
import src.band           as bd
import src.detectorArray  as da
import src.observationSet as ob
import src.parameter      as pr
import src.units          as un

class Channel:
    def __init__(self, log, channelDict, camera, optChain, sky, scn, detBandDict=None, nrealize=1, nobs=1, clcDet=1, specRes=1.e9):
        #Store passed parameters
        self.log         = log
        self.dict        = channelDict
        self.camera      = camera
        self.optChain    = optChain
        self.sky         = sky
        self.scn         = scn
        self.detBandDict = detBandDict
        self.nrealize    = nrealize
        self.nobs        = nobs
        self.clcDet      = clcDet
        self.specRes     = specRes
        
        #Name this channel
        self.bandID    = int(self.dict['Band ID'])
        self.pixelID   = int(self.dict['Pixel ID'])
        self.name      = self.camera.name+str(self.bandID)

        #Check for band file
        if self.detBandDict and self.name in self.detBandDict.keys():
            self.detBandFile = self.detBandDict[self.name]
        else:
            self.detBandFile = None

        self.log.log("Generating channel %s" % (self.name), 1)
        
        #Store the channel parameters in a dictionary
        self.paramsDict = {'Num Det per Wafer': pr.Parameter(self.log, 'Num Det per Wafer', self.dict['Num Det per Wafer'],           min=0.0, max=np.inf),
                           'Num Waf per OT':    pr.Parameter(self.log, 'Num Waf per OT',    self.dict['Num Waf per OT'],              min=0.0, max=np.inf),
                           'Num OT':            pr.Parameter(self.log, 'Num OT',            self.dict['Num OT'],                      min=0.0, max=np.inf),
                           'Yield':             pr.Parameter(self.log, 'Yield',             self.dict['Yield'],                       min=0.0, max=1.0   ),
                           'Pixel Size':        pr.Parameter(self.log, 'Pixel Size',        self.dict['Pixel Size'], un.mmToM,        min=0.0, max=np.inf),
                           'Waist Factor':      pr.Parameter(self.log, 'Waist Factor',      self.dict['Waist Factor'],                min=2.0, max=np.inf),
                           'Band Center':       pr.Parameter(self.log, 'Band Center',       self.dict['Band Center'], un.GHzToHz,     min=0.0, max=np.inf),
                           'Fractional BW':     pr.Parameter(self.log, 'Fractional BW',     self.dict['Fractional BW'],               min=0.0, max=2.0   ),
                           'Det Eff':           pr.Parameter(self.log, 'Det Eff',           self.dict['Det Eff'],                     min=0.0, max=1.0   ),
                           'Psat':              pr.Parameter(self.log, 'Psat',              self.dict['Psat'], un.pWtoW,              min=0.0, max=np.inf),
                           'Psat Factor':       pr.Parameter(self.log, 'Psat Factor',       self.dict['Psat Factor'],                 min=0.0, max=np.inf),
                           'Carrier Index':     pr.Parameter(self.log, 'Carrier Index',     self.dict['Carrier Index'],               min=0.0, max=np.inf),
                           'Tc':                pr.Parameter(self.log, 'Tc',                self.dict['Tc'],                          min=0.0, max=np.inf),
                           'Tc Fraction':       pr.Parameter(self.log, 'Tc Fraction',       self.dict['Tc Fraction'],                 min=0.0, max=np.inf),
                           'SQUID NEI':         pr.Parameter(self.log, 'SQUID NEI',         self.dict['SQUID NEI'], un.pArtHzToArtHz, min=0.0, max=np.inf),
                           'Bolo Resistance':   pr.Parameter(self.log, 'Bolo Resistance',   self.dict['Bolo Resistance'],             min=0.0, max=np.inf),
                           'Read Noise Frac':   pr.Parameter(self.log, 'Read Noise Frac',   self.dict['Read Noise Frac'],             min=0.0, max=1.0   )}
        self.chKeys = ['Num Det per Wafer', 'Num Waf per OT', 'Num OT', 'Yield', 'Pixel Size', 'Waist Factor']

        #Newly added parameters to BoloCalc -- checked separately for backwards compatibility
        if 'Flink' in self.dict.keys():
            self.paramsDict['Flink'] = pr.Parameter(self.log, 'Flink', self.dict['Flink'], min=0.0, max=np.inf)
        else:
            self.paramsDict['Flink'] = pr.Parameter(self.log, 'Flink', 'NA',               min=0.0, max=np.inf)

        if 'G' in self.dict.keys():
            self.paramsDict['G'] = pr.Parameter(self.log, 'G', self.dict['G'], un.pWtoW, min=0.0, max=np.inf)
        else:
            self.paramsDict['G'] = pr.Parameter(self.log, 'G', 'NA',           un.pWtoW, min=0.0, max=np.inf)
        
        #Store the camera parameters
        self.camElv    = camera.params['Boresight Elevation']
        self.optCouple = camera.params['Optical Coupling']
        self.Fnumber   = camera.params['F Number']
        self.Tb        = camera.params['Bath Temp']        

        #Elevation distribution for pixels in the camera
        elvFile = sorted(gb.glob(os.path.join(camera.configDir, 'elevation.txt')))
        if len(elvFile) == 0:
            self.log.log("No elevation distribution for pixels within camera %s" % (camera.name), 2)
            self.elvDict = None
        elif len(elvFile) > 1:
            self.log.log('More than one elevation distribution for pixels within camera %s. Using none of them' % (camera.name), 2)
            self.elvDict = None
        else:
            elvFile = elvFile[0]
            params, vals = np.loadtxt(elvFile, unpack=True, usecols=[0,1], dtype=np.str, delimiter='|')
            self.elvDict = {params[i].strip(): vals[i].strip() for i in range(2, len(params))}
            self.log.log("Using pixel elevation distribution for camera %s defined in %s" % (camera.name, elvFile), 2)
            
        #Generate the channel
        self.generate()

    #***** Public Methods *****
    def generate(self):
        #Generate channel parameters
        self.params = {}; self.detectorDict = {}
        for k in self.paramsDict:
            if k in self.chKeys:
                self.params[k] = self.__paramSamp(self.paramsDict[k], self.bandID)
            else:
                self.detectorDict[k] = self.paramsDict[k]

        #Derived channel parameters
        self.numDet    = int(self.params['Num Det per Wafer']*self.params['Num Waf per OT']*self.params['Num OT'])
        if self.clcDet == None: self.clcDet = self.numDet
        self.numPix    = np.round(self.numDet/2.)

        #Frequencies to integrate over
        self.fres          = self.specRes
        if self.detBandFile is not None:
            #Use defined detector band edges
            band = bd.Band(self.log, self.detBandFile)
            self.loFreq = np.amin(band.freqs)
            self.hiFreq = np.amax(band.freqs)
            #Band mask edges defined using lowest and highest freqiencies in passed detector band file
            self.fLo = self.loFreq
            self.fHi = self.hiFreq
        else:
            #Use wider than nominal band by 30% to cover tolerances/errors
            self.loFreq = self.detectorDict['Band Center'].getAvg()*(1. - 0.65*self.detectorDict['Fractional BW'].getAvg())
            self.hiFreq = self.detectorDict['Band Center'].getAvg()*(1. + 0.65*self.detectorDict['Fractional BW'].getAvg())
            #Band mask edges defined using band center and fractional BW
            self.fLo           = self.detectorDict['Band Center'].getAvg()*(1. - 0.50*self.detectorDict['Fractional BW'].getAvg())
            self.fHi           = self.detectorDict['Band Center'].getAvg()*(1. + 0.50*self.detectorDict['Fractional BW'].getAvg())
        self.freqs         = np.arange(self.loFreq, self.hiFreq+self.fres, self.fres)
        self.nfreq         = len(self.freqs)
        self.deltaF        = self.freqs[-1] - self.freqs[0]
        
        #Band mask
        self.bandMask      = np.array([1. if f >= self.fLo and f <= self.fHi else 0. for f in self.freqs])
        self.bandDeltaF    = self.fHi - self.fLo
        
        #Sample the pixel parameters
        self.apEff      = None #Calculated later
        self.edgeTaper  = None #Calculated later

        #Store the detector array object
        if self.detBandFile is not None: self.detArray = da.DetectorArray(self.log, self, self.detBandFile)
        else:                            self.detArray = da.DetectorArray(self.log, self)

        #Store the observation set object
        self.obsSet = ob.ObservationSet(self.log, self.detArray, self.sky, self.scn, belv=self.camElv, nobs=self.nobs, elvDict=self.elvDict)
        
        #Build the element, emissivity, efficiency, and temperature arrays
        optElem, optEmiss, optEffic, optTemp = self.optChain.generate(self)
        self.log.log("Generating emissitivies, efficiencies, and temperatures for all optical elements seen by channel %s" % (self.name), 1)
        self.elem  = np.array([[obs.elem[i]  + optElem  + self.detArray.detectors[i].elem   for i in range(self.detArray.nDet)] for obs in self.obsSet.observations]).astype(np.str)
        self.emiss = np.array([[obs.emiss[i] + optEmiss + self.detArray.detectors[i].emiss  for i in range(self.detArray.nDet)] for obs in self.obsSet.observations]).astype(np.float)
        self.effic = np.array([[obs.effic[i] + optEffic + self.detArray.detectors[i].effic  for i in range(self.detArray.nDet)] for obs in self.obsSet.observations]).astype(np.float)
        self.temp  = np.array([[obs.temp[i]  + optTemp  + self.detArray.detectors[i].temp   for i in range(self.detArray.nDet)] for obs in self.obsSet.observations]).astype(np.float)

    #***** Private Methods *****
    def __paramSamp(self, param, bandID): 
        if not ('instance' in str(type(param)) or 'class' in str(type(param))): return np.float(param)
        if self.nrealize == 1: return param.getAvg(bandID)
        else:                  return param.sample(bandID=bandID, nsample=1)
