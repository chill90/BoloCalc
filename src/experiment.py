# Built-in modules
import numpy as np
import glob as gb
import collections as cl
import os

# BoloCalc modules
import src.telescope as tp
import src.parameter as pr
import src.loader as ld


class Experiment:
    def __init__(self, log, dir, nrealize=1, nobs=1, clcDet=1,
                 specRes=1.e9, foregrounds=False):
        # Store passed parameters
        self.log = log
        self.dir = str(dir)
        self.nrealize = int(nrealize)
        self.nobs = int(nobs)
        self.clcDet = int(clcDet)
        self.specRes = float(specRes)
        self.fgnds = bool(foregrounds)

        # Check whether experiment exists
        if not os.path.isdir(self.dir):
            raise Exception('BoloCalc FATAL Exception: Experiment directory \
                            %s does not exist' % (self.dir))

        # Generate global parameters
        self.configDir = os.path.join(self.dir, 'config')
        # Check whether configuration directory exists
        if not os.path.isdir(self.configDir):
            raise Exception(
                'BoloCalc FATAL Exception: Experiment configuration directory \
                %s does not exist' % (self.configDir))

        # Name the experiment
        self.name = os.path.split(self.dir.rstrip('/'))[-1]
        self.log.log("Instantiating experiment %s" % (self.name), 1)

        # Store foreground parameters
        self.ld = ld.Loader()
        if self.fgnds:
            self.fgndFile = os.path.join(self.configDir, 'foregrounds.txt')
            if not os.path.isfile(self.fgndFile):
                raise Exception("BoloCalc FATAL Exception: Foreground file '%s' \
                                does not exist" % (self.fgndFile))
            try:
                params, vals = self.ld.foregrounds(self.fgndFile)
                dict = {params[i].strip(): vals[i].strip()
                        for i in range(len(params))}
                self.log.log(
                    "Using foreground parameters in '%s'" % (self.fgndFile), 1)
            except:
                raise Exception("BoloCalc FATAL Exception: Failed to load \
                                parameters in '%s'" % (self.fgndFile))
            try:
                self.paramsDict = {
                    'Dust Temperature': pr.Parameter(
                        self.log, 'Dust Temperature',
                        dict['Dust Temperature'],
                        min=0.0, max=np.inf),
                    'Dust Spec Index': pr.Parameter(
                        self.log, 'Dust Spec Index',
                        dict['Dust Spec Index'],
                        min=-np.inf, max=np.inf),
                    'Dust Amplitude': pr.Parameter(
                        self.log, 'Dust Amplitude',
                        dict['Dust Amplitude'],
                        min=0.0, max=np.inf),
                    'Dust Scale Frequency': pr.Parameter(
                        self.log, 'Dust Scale Frequency',
                        dict['Dust Scale Frequency'],
                        min=0.0, max=np.inf),
                    'Synchrotron Spec Index': pr.Parameter(
                        self.log, 'Synchrotron Spec Index',
                        dict['Synchrotron Spec Index'],
                        min=-np.inf, max=np.inf),
                    'Synchrotron Amplitude': pr.Parameter(
                        self.log, 'Synchrotron Amplitude',
                        dict['Synchrotron Amplitude'],
                        min=0.0, max=np.inf)}
            except KeyError:
                raise Exception(
                    "BoloCalc FATAL Exception: Failed to store \
                    parameters specified in '%s'" % (self.fgndFile))
        else:
            self.paramsDict = None
            self.log.log("Ignoring foregrounds", 1)

        # Generate experiment
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        # Generate foregroun d parameters
        if self.paramsDict is not None:
            self.params = {}
            for k in self.paramsDict:
                self.params[k] = self._param_samp(self.paramsDict[k])
        else:
            self.params = None
        # Store telescope objects in dictionary
        self.log.log(
            "Generating telescopes for experiment %s" % (self.name), 1)
        telescopeDirs = sorted(gb.glob(os.path.join(self.dir, '*'+os.sep)))
        telescopeDirs = [x for x in telescopeDirs
                         if 'config' not in x and 'paramVary' not in x]
        if len(telescopeDirs) == 0:
            raise Exception(
                "BoloCalc FATAL Exception: Zero telescope directories found in \
                experiment directory '%s'" % (self.dir))
        telescopeNames = [telescopeDir.split(os.sep)[-2]
                          for telescopeDir in telescopeDirs]
        self.telescopes = cl.OrderedDict({})
        for i in range(len(telescopeNames)):
            if telescopeNames[i] in self.telescopes.keys():
                raise Exception(
                    "BoloCalc FATAL Exception: Multiple telescope directories \
                    with the same name '%s' in experiment directory '%s'"
                    % (telescopeNames[i], self.dir))
            self.telescopes.update({telescopeNames[i]: tp.Telescope(
                self.log, telescopeDirs[i], fgndDict=self.params,
                nrealize=self.nrealize, nobs=self.nobs, clcDet=self.clcDet,
                specRes=self.specRes, foregrounds=self.fgnds)})

    # ***** Private Methods *****
    def _param_samp(self, param):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self.nrealize == 1:
            return param.getAvg()
        else:
            return param.sample(nsample=1)
