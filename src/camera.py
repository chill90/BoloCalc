#Core Python packages
import numpy            as np
import glob             as gb
import collections      as cl
import                     os

#BoloCalc packages
import src.parameter    as pr
import src.opticalChain as oc
import src.channel      as ch

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

        #Check whether this camera exists
        if not os.path.isdir(self.dir):       
            raise Exception("BoloCalc FATAL Exception: Camera directory '%s' does not exist" % (self.dir))

        #Store global parameters
        self.configDir  = os.path.join(self.dir, 'config')
        #Check whether configuration directory exists
        if not os.path.isdir(self.configDir):
            raise Exception("BoloCalc FATAL Exception: Camera configuration directory '%s' does not exist" % (self.configDir))
            
        #Name the camera
        self.bandDir    = os.path.join(self.configDir, 'Bands')
        self.name       = self.dir.rstrip(os.sep).split(os.sep)[-1]
        self.telName    = self.dir.rstrip(os.sep).split(os.sep)[-2]
        self.expName    = self.dir.rstrip(os.sep).split(os.sep)[-3]

        self.log.log("Generating camera %s" % (self.name), 1)

        #Store camera parameters into a dictionary
        self.camFile = os.path.join(self.configDir, 'camera.txt')
        if not os.path.isfile(self.camFile): 
            raise Exception("BoloCalc FATAL Exception: Camera file '%s' does not exist" % (self.camFile))
        try:
            paramArr, valArr = np.loadtxt(self.camFile, dtype=np.str, unpack=True, usecols=[0,2], delimiter='|')
            dict             = {paramArr[i].strip(): valArr[i].strip() for i in range(len(paramArr))}
        except:
            raise Exception("BoloCalc FATAL Exception: Failed to load parameters in '%s'. See 'camera.txt' formatting rules in the BoloCalc User Manual" % (self.camFile))
        try:
            self.paramsDict = {'Boresight Elevation': pr.Parameter(self.log, 'Boresight Elevation', dict['Boresight Elevation'], min=-40.0, max=40.0  ),
                               'Optical Coupling':    pr.Parameter(self.log, 'Optical Coupling',    dict['Optical Coupling'],    min=0.0,   max=1.0   ),
                               'F Number':            pr.Parameter(self.log, 'F Number',            dict['F Number'        ],    min=0.0,   max=np.inf),
                               'Bath Temp':           pr.Parameter(self.log, 'Bath Temp',           dict['Bath Temp'       ],    min=0.0,   max=np.inf)}
        except KeyError:
            raise Exception("BoloCalc FATAL Exception: Failed to store parameters specified in '%s'" % (self.camFile))
        
        #Generate camera
        self.generate()

    #***** Public Methods *****
    def generate(self):
        #Generate camera parameters
        self.params = {}
        for k in self.paramsDict:
            self.params[k] = self.__paramSamp(self.paramsDict[k])
        #Store optical chain object
        self.log.log("Generating optical chain for camera %s" % (self.name), 1)
        self.optBandDict = self.__bandDict(os.path.join(self.bandDir, 'Optics'))
        self.optChain    = oc.OpticalChain(self.log, os.path.join(self.configDir, 'optics.txt'), nrealize=self.nrealize, optBands=self.optBandDict)
        #Store channel objects
        self.log.log("Generating channels for camera %s" % (self.name), 1)
        self.detBandDict = self.__bandDict(os.path.join(self.bandDir, 'Detectors'))
        self.chnFile = os.path.join(self.configDir, 'channels.txt')
        if not os.path.isdir(self.configDir): 
            raise Exception("BoloCalc FATAL Exception: Telescope configuration directory '%s' does not exist" % (self.configDir))
        chans            = np.loadtxt(self.chnFile, dtype=np.str, delimiter='|'); keyArr  = chans[0]; elemArr = chans[1:]
        self.chanDicts   = [{keyArr[i].strip(): elem[i].strip() for i in range(len(keyArr))} for elem in elemArr]
        self.channels = cl.OrderedDict({})
        for chDict in self.chanDicts:
            if chDict['Band ID'] in self.channels.keys():
                raise Exception('FATAL: Multiple bands with the same name "%s" defined in camera "%s", telescope "%s", experiment "%s"' % (chDict['Band ID'], self.name, self.telName, self.expName))
            self.channels.update({chDict['Band ID']: ch.Channel(self.log, chDict, self, self.optChain, self.sky, self.scn, detBandDict=self.detBandDict, nrealize=self.nrealize, nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes)})
        #Store pixel dictionary
        self.log.log("Generating pixels for camera %s" % (self.name), 2)
        self.pixels   = cl.OrderedDict({})
        for c in self.channels:
            if self.channels[c].pixelID in self.pixels.keys(): self.pixels[self.channels[c].pixelID].append(self.channels[c])
            else:                                              self.pixels[self.channels[c].pixelID] = [self.channels[c]]

    #***** Private Methods *****
    #Collect band files
    def __bandDict(self, dir):
        bandFiles = sorted(gb.glob(os.path.join(dir, '*')))
        if len(bandFiles):
            nameArr = [os.path.split(nm)[-1].split('.')[0] for nm in bandFiles if "~" not in nm]
            if len(nameArr): return cl.OrderedDict({nameArr[i]: bandFiles[i] for i in range(len(nameArr))})
            else:            return None
        else:
            return None
    #Sample camera parameters
    def __paramSamp(self, param): 
        if not ('instance' in str(type(param)) or 'class' in str(type(param))): return np.float(param)
        if self.nrealize == 1: return param.getAvg()
        else:                  return param.sample(nsample=1)
