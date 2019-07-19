# Built-in modules
import numpy as np
import glob as gb
import sys as sy
import collections as cl
import os

# BoloCalc packages
import src.parameter as pr
import src.camera as cm
import src.units as un
import src.sky as sk
import src.scanStrategy as sc
import src.loader as ld


class Telescope:
    def __init__(self, log, dir, fgndDict=None, nrealize=1, nobs=1,
                 clcDet=1, specRes=1.e9, foregrounds=False):
        # Storing passed parameters
        self.log = log
        self.dir = dir
        self.fgndDict = fgndDict
        self.nrealize = nrealize
        self.nobs = nobs
        self.clcDet = clcDet
        self.specRes = specRes
        self.fgnds = foregrounds
        self.ld = ld.Loader()

        # Check whether telescope exists
        if not os.path.isdir(self.dir):
            self.log.err(
                "Telescope dir '%s' does not exist" % (self.dir))

        # Generate global parameters
        self.configDir = os.path.join(self.dir, 'config')
        # Check whether configuration directory exists
        if not os.path.isdir(self.configDir):
            self.log.err(
                "Telescope config dir'%s' does not exist" % (self.configDir))

        # Name the telescope
        self.name = self.dir.rstrip(os.sep).split(os.sep)[-1]
        self.log.log("Instantiating telescope %s" % (self.name), 1)
        self.expName = self.dir.rstrip(os.sep).split(os.sep)[-2]

        # Store the telescope parameters in a dictionary
        self.telFile = os.path.join(self.configDir, 'telescope.txt')
        if not os.path.isfile(self.telFile):
            self.log.err(
                "Telescope file '%s' does not exist" % (self.telFile))
        try:
            paramArr, valArr = self.ld.telescope(self.telFile)
            dict = {paramArr[i].strip(): valArr[i].strip()
                    for i in range(len(paramArr))}
        except:
            self.log.err(
                "Failed to load parameters in '%s'" % (self.telFile))
        try:
            self.paramsDict = {
                'Site': pr.Parameter(
                    self.log, 'Site', dict['Site']),
                'Elevation': pr.Parameter(
                    self.log, 'Elevation', dict['Elevation'],
                    min=20., max=90.),
                'PWV': pr.Parameter(
                    self.log, 'PWV', dict['PWV'], 
                    min=0.0, max=8.0),
                'Observation Time': pr.Parameter(
                    self.log, 'Observation Time', dict['Observation Time'],
                    un.Unit("year"), min=0.0, max=np.inf),
                'Sky Fraction': pr.Parameter(
                    self.log, 'Sky Fraction', dict['Sky Fraction'],
                    min=0.0, max=1.0),
                'Observation Efficiency': pr.Parameter(
                    self.log, 'Observation Efficiency',
                    dict['Observation Efficiency'],
                    min=0.0, max=1.0),
                'NET Margin': pr.Parameter(
                    self.log, 'NET Margin', dict['NET Margin'],
                    min=0.0, max=np.inf)}
        except KeyError:
            raise Exception("BoloCalc FATAL Exception: Failed to store \
                            parameters specified in '%s'" % (self.telFile))

        # Generate the telescope
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        # Generate telescope parameters
        self.params = {}
        for k in self.paramsDict:
            self.params[k] = self._param_samp(self.paramsDict[k])
        # Store sky and elevation objects
        self.log.log("Generating sky for telescope %s" % (self.name), 1)
        atmFile = sorted(gb.glob(os.path.join(self.configDir, 'atm*.txt')))
        if self.params['Site'] == 'NA':
            if len(atmFile) == 0:
                raise Exception("BoloCalc FATAL Exception: 'Site' parameter in \
                                '%s' is 'NA', but no custom atmosphere file \
                                provided in '%s'"
                                % (self.telFile, self.configDir))
            elif len(atmFile) > 1:
                raise Exception("BoloCalc FATAL Exception: 'Site' parameter in \
                                '%s' is 'NA', but more than one custom \
                                atmosphere file was found in '%s'"
                                % (self.telFile, self.configDir))
            else:
                self.atmFile = atmFile[0]
                self.params['Site'] = None
                self.params['Elevation'] = None
                self.params['PWV'] = None
                self.elvDict = None
                self.pwvDict = None
                self.log.log("Using custom atmosphere defined in '%s'"
                             % (atmFile), 0)
        else:
            self.atmFile = None
            # Obtain site
            if self.params['Site'].upper() not in sk.siteOpts:
                raise Exception("BoloCalc FATAL Exception: 'Site' parameter \
                                in '%s' not understood. Options '%s'"
                                % (self.telFile, ",' ".join(sk.siteOpts)))
            # Obtain PWV
            if self.params['Site'].upper() == 'MCMURDO':
                self.params['PWV'] = 0
                self.pwvDict = None
            elif self.params['Site'].upper() == 'SPACE':
                self.params['PWV'] = None
                self.pwvDict = None
            else:
                if self.params['PWV'] == 'NA':
                    self.params['PWV'] = None
                    pwvFile = sorted(gb.glob(os.path.join(
                        self.configDir, 'pwv.txt')))
                    if len(pwvFile) == 0:
                        raise Exception(
                            "BoloCalc FATAL Exception: 'PWV' parameter in '%s' is \
                            'NA' and no PWV distribution '%s' for site '%s' \
                            provided"
                            % (self.telFile, pwvFile, self.params['Site']))
                    elif len(pwvFile) > 1:
                        raise Exception(
                            "BoloCalc FATAL Exception: More than \
                            one PWV distribution found in '%s' -- '%s'"
                            % (self.configDir, ",' ".join(pwvFile)))
                    else:
                        pwvFile = pwvFile[0]
                        try:
                            params, vals = np.loadtxt(
                                pwvFile, unpack=True, usecols=[0, 1],
                                dtype=np.str, delimiter='|')
                            self.pwvDict = {params[i].strip(): vals[i].strip()
                                            for i in range(2, len(params))}
                        except:
                            raise Exception(
                                "BoloCalc FATAL Exception: Failed to load \
                                parameters in '%s'. See 'pwv.txt' formatting \
                                rules in the BoloCalc User Manual" % (pwvFile))
                        self.log.log("Using pwv distribution defined in %s"
                                     % (pwvFile), 2)
                else:
                    self.pwvDict = None
            # Obtain elevation
            if self.params['Site'].upper() == 'SPACE':
                self.params['Elevation'] = None
                self.elvDict = None
            else:
                if self.params['Elevation'] == 'NA':
                    self.params['Elevation'] = None
                    elvFile = sorted(gb.glob(os.path.join(
                        self.configDir, 'elevation.txt')))
                    if len(elvFile) == 0:
                        raise Exception(
                            "BoloCalc FATAL Exception: 'Elevation' parameter \
                            in '%s' is 'NA' *and* no elevation distribution \
                            '%s' for site '%s' provided"
                            % (self.telFile, elvFile, self.params['Site']))
                    elif len(elvFile) > 1:
                        raise Exception(
                            "BoloCalc FATAL Exception: More than one elevation \
                            distribution found in '%s' -- '%s'"
                            % (self.configDir, ",' ".join(elvFile)))
                    else:
                        elvFile = elvFile[0]
                        try:
                            params, vals = np.loadtxt(
                                elvFile, unpack=True, usecols=[0, 1],
                                dtype=np.str, delimiter='|')
                            self.elvDict = {
                                params[i].strip(): vals[i].strip()
                                for i in range(2, len(params))}
                        except:
                            raise Exception(
                                "BoloCalc FATAL Exception: Failed to load \
                                parameters in '%s'. See 'elevation.txt' \
                                formatting rules in the BoloCalc User Manual"
                                % (pwvFile))
                        self.log.log(
                            "Using elevation distribution defined in %s"
                            % (elvFile), 2)
                else:
                    self.elvDict = None
        # Store sky object
        self.sky = sk.Sky(
            self.log, nrealize=1, fgndDict=self.fgndDict, atmFile=self.atmFile,
            site=self.params['Site'], pwv=self.params['PWV'],
            pwvDict=self.pwvDict, foregrounds=self.fgnds)
        # Store scan strategy object
        self.log.log("Generating scan strategy for telescope %s"
                     % (self.name), 1)
        self.scn = sc.ScanStrategy(
            self.log, elv=self.params['Elevation'], elvDict=self.elvDict)
        # Store camera objects
        self.log.log("Generating cameras for telescope %s" % (self.name), 1)
        cameraDirs = sorted(gb.glob(os.path.join(self.dir, '*'+os.sep)))
        cameraDirs = [x for x in cameraDirs if 'config' not in x]
        if len(cameraDirs) == 0:
            raise Exception(
                "BoloCalc FATAL Exception: Zero camera directories found in \
                telescope directory '%s'" % (self.dir))
        cameraNames = [cameraDir.split(os.sep)[-2] for cameraDir in cameraDirs]
        self.cameras = cl.OrderedDict({})
        for i in range(len(cameraNames)):
            if cameraNames[i] in self.cameras.keys():
                raise Exception(
                    "BoloCalc FATAL Exception: Multiple cameras with the same \
                    name '%s' defined in telescope '%s', experiment '%s'"
                    % (cameraNames[i], self.name, self.expName))
            self.cameras.update({cameraNames[i]: cm.Camera(
                self.log, cameraDirs[i], self.sky, self.scn,
                nrealize=self.nrealize, nobs=self.nobs, clcDet=self.clcDet,
                specRes=self.specRes)})

    # ***** Private Methods *****
    def _param_samp(self, param):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self.nrealize == 1:
            return param.getAvg()
        else:
            return param.sample(nsample=1)
