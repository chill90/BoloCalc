#python Version 2.7.2
import numpy        as np
import glob         as gb
import parameter    as pr
import opticalChain as oc
import channel      as ch

class Camera:
    def __init__(self, log, dir, sky, scn, nrealize=1, nobs=1, clcDet=1, specRes=1.e9):
        #Store passed parameters
        self.log      = log
        self.dir      = dir
        self.sky      = sky
        self.scn      = scn
        self.nrealize = nrealize
        self.nobs     = nobs
        self.clcDet   = clcDet
        self.specRes  = specRes

        #Store global parameters
        self.configDir  = self.dir+'/config'
        self.bandDir    = self.configDir+'/Bands'
        self.name       = dir.rstrip('/').split('/')[-1]

        self.log.log("Generating camera %s" % (self.name), 1)

        #Store camera parameters into a dictionary
        paramArr, valArr = np.loadtxt(self.configDir+'/camera.txt', dtype=np.str, unpack=True, usecols=[0,2], delimiter='|')
        dict             = {paramArr[i].strip(): valArr[i].strip() for i in range(len(paramArr))}
        self.params = {'Boresight Elevation': self.__paramSamp(pr.Parameter(self.log, 'Boresight Elevation', dict['Boresight Elevation'], min=-40.0, max=40.0  )),
                       'Optical Coupling':    self.__paramSamp(pr.Parameter(self.log, 'Optical Coupling',    dict['Optical Coupling'],    min=0.0,   max=1.0   )),
                       'F Number':            self.__paramSamp(pr.Parameter(self.log, 'F Number',            dict['F Number'        ],    min=0.0,   max=np.inf)),
                       'Bath Temp':           self.__paramSamp(pr.Parameter(self.log, 'Bath Temp',           dict['Bath Temp'       ],    min=0.0,   max=np.inf))}
        
        #Generate camera
        self.generate()

    #***** Public Methods *****
    def generate(self):
        #Store optical chain object
        self.log.log("Generating optical chain for camera %s" % (self.name), 1)
        self.optBandDict = self.__bandDict(self.bandDir+'/Optics')
        self.optChain    = oc.OpticalChain(self.log, self.configDir+'/optics.txt', nrealize=self.nrealize, optBands=self.optBandDict)
        #Store channel objects
        self.log.log("Generating channels for camera %s" % (self.name), 1)
        self.detBandDict = self.__bandDict(self.bandDir+'/Detectors')
        chans            = np.loadtxt(self.configDir+'/channels.txt', dtype=np.str, delimiter='|'); keyArr  = chans[0]; elemArr = chans[1:]
        self.chanDicts   = [{keyArr[i].strip(): elem[i].strip() for i in range(len(keyArr))} for elem in elemArr]
        self.channels    = {chDict['Band ID']: ch.Channel(self.log, chDict, self, self.optChain, self.sky, self.scn, detBandDict=self.detBandDict, nrealize=self.nrealize, nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes) for chDict in self.chanDicts}
        #Store pixel dictionary
        self.log.log("Generating pixels for camera %s" % (self.name), 2)
        self.pixels   = {}
        for c in self.channels:
            if self.channels[c].pixelID in self.pixels.keys(): self.pixels[self.channels[c].pixelID].append(self.channels[c])
            else:                                              self.pixels[self.channels[c].pixelID] = [self.channels[c]]

    #***** Private Methods *****
    #Collect band files
    def __bandDict(self, dir):
        bandFiles = sorted(gb.glob(dir+'/*'))
        if len(bandFiles):
            nameArr = [nm.split('/')[-1].split('.')[0] for nm in bandFiles if "~" not in nm]
            if len(nameArr): return {nameArr[i]: bandFiles[i] for i in range(len(nameArr))}
            else:            return None
        else:
            return None
    #Sample camera parameters
    def __paramSamp(self, param): 
        if not 'instance' in str(type(param)): return np.float(param)
        if self.nrealize == 1: return param.getAvg()
        else:                  return param.sample(nsample=1)
