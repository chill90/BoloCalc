import numpy            as np
import glob             as gb
import sys              as sy
import collections      as cl
import                     os

import src.parameter    as pr
import src.camera       as cm
import src.units        as un
import src.sky          as sk
import src.scanStrategy as sc

class Telescope:
    def __init__(self, log, dir, fgndDict=None, nrealize=1, nobs=1, clcDet=1, specRes=1.e9, foregrounds=False):
        #Storing passed parameters
        self.log        = log
        self.dir        = dir
        self.fgndDict   = fgndDict
        self.nrealize   = nrealize
        self.nobs       = nobs
        self.clcDet     = clcDet
        self.specRes    = specRes
        self.fgnds      = foregrounds

        #Storing global parameters
        self.configDir  = os.path.join(self.dir, 'config')
        self.name       = os.path.split(self.dir)[-1]

        self.log.log("Instantiating telescope %s" % (self.name), 1)

        #Store the telescope parameters in a dictionary
        paramArr, valArr = np.loadtxt(os.path.join(self.configDir, 'telescope.txt'), unpack=True, usecols=[0,2], dtype=np.str, delimiter='|')
        dict             = cl.OrderedDict({paramArr[i].strip(): valArr[i].strip() for i in range(len(paramArr))})
        self.params = cl.OrderedDict({'Site':                   self.__paramSamp(pr.Parameter(self.log, 'Site',                   dict['Site'])),
                                      'Elevation':              self.__paramSamp(pr.Parameter(self.log, 'Elevation',              dict['Elevation'],                    min=20., max=90.   )),
                                      'PWV':                    self.__paramSamp(pr.Parameter(self.log, 'PWV',                    dict['PWV'],                          min=0.0, max=8.0   )),
                                      'Observation Time':       self.__paramSamp(pr.Parameter(self.log, 'Observation Time',       dict['Observation Time'], un.yrToSec, min=0.0, max=np.inf)),
                                      'Sky Fraction':           self.__paramSamp(pr.Parameter(self.log, 'Sky Fraction',           dict['Sky Fraction'],                 min=0.0, max=1.0   )),
                                      'Observation Efficiency': self.__paramSamp(pr.Parameter(self.log, 'Observation Efficiency', dict['Observation Efficiency'],       min=0.0, max=1.0   )),
                                      'NET Margin':             self.__paramSamp(pr.Parameter(self.log, 'NET Margin',             dict['NET Margin'],                   min=0.0, max=np.inf))})

        #Generate the telescope
        self.generate()

    #***** Public Methods *****
    def generate(self):
        #Store sky and elevation objects
        self.log.log("Generating sky for telescope %s" % (self.name), 1)
        atmFile = sorted(gb.glob(os.path.join(self.configDir, 'atm*.txt')))
        if len(atmFile) == 0:
            self.atmFile = None
            self.log.log("No custom atmosphere provided.", 2)
            #Obtain site
            if self.params['Site'] == 'NA':
                self.log.log("No site provided", 0)
                sy.exit(1)
            #Obtain PWV
            if self.params['PWV'] == 'NA':
                self.params['PWV'] = None
                pwvFile = sorted(gb.glob(os.path.join(self.configDir, 'pwv.txt')))
                if len(pwvFile) == 0:
                    self.log.log("No pwv distribution or value provided for telescope %s" % (self.name), 0)
                    sy.exit(1)
                elif len(pwvFile) > 1:
                    self.log.log('More than one pwv distribution found for telescope %s' % (self.name), 0)
                    sy.exit(1)
                else:
                    pwvFile = pwvFile[0]
                    params, vals = np.loadtxt(pwvFile, unpack=True, usecols=[0,1], dtype=np.str, delimiter='|')
                    self.pwvDict = cl.OrderedDict({params[i].strip(): vals[i].strip() for i in range(2, len(params))})
                    self.log.log("Using pwv distribution defined in %s" % (pwvFile), 2)
            else:
                self.pwvDict = None
            #Obtain elevation
            if self.params['Elevation'] == 'NA':
                self.params['Elevation'] = None
                elvFile = sorted(gb.glob(os.path.join(self.configDir, 'elevation.txt')))
                if len(elvFile) == 0:
                    self.log.log("No elevation distribution or value provided for telescope %s" % (self.name), 0)
                    sy.exit(1)
                elif len(elvFile) > 1:
                    self.log.log('More than one elevation distribution found for telescope %s' % (self.name), 0)
                    sy.exit(1)
                else:
                    elvFile = elvFile[0]
                    params, vals = np.loadtxt(elvFile, unpack=True, usecols=[0,1], dtype=np.str, delimiter='|')
                    self.elvDict = cl.OrderedDict({params[i].strip(): vals[i].strip() for i in range(2, len(params))})
                    self.log.log("Using elevation distribution defined in %s" % (elvFile), 2)
            else:
                self.elvDict = None            
        elif len(atmFile) > 1:                
            self.log.log('More than one atmosphere file found for telescope %s' % (self.name), 0)
            sy.exit(1)
        else:
            self.atmFile = atmFile[0]
            self.params['Site']      = None
            self.params['Elevation'] = None
            self.params['PWV']       = None
            self.elvDict             = None
            self.pwvDict             = None
            self.log.log("Using custom atmosphere defined in %s" % (atmFile), 0)
        #Store sky object
        self.sky = sk.Sky(self.log, nrealize=1, fgndDict=self.fgndDict, atmFile=self.atmFile, site=self.params['Site'], pwv=self.params['PWV'], pwvDict=self.pwvDict, foregrounds=self.fgnds)
        #Store scan strategy object
        self.log.log("Generating scan strategy for telescope %s" % (self.name), 1)
        self.scn = sc.ScanStrategy(self.log, elv=self.params['Elevation'], elvDict=self.elvDict)
        #Store camera objects
        self.log.log("Generating cameras for telescope %s" % (self.name), 1)
        cameraDirs   = sorted(gb.glob(os.path.join(self.dir, '*'+os.sep))); cameraDirs = [x for x in cameraDirs if 'config' not in x]; cameraNames  = [cameraDir.split(os.sep)[-2] for cameraDir in cameraDirs]
        self.cameras = cl.OrderedDict({cameraNames[i]: cm.Camera(self.log, cameraDirs[i], self.sky, self.scn, nrealize=self.nrealize, nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes) for i in range(len(cameraNames))})

    #***** Private Methods *****
    def __paramSamp(self, param):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))): return np.float(param)
        if self.nrealize == 1: return param.getAvg()
        else:                  return param.sample(nsample=1)
