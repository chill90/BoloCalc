#Core Python packages
import numpy         as np
import glob          as gb
import collections   as cl
import                  os

#BoloCalc packages
import src.telescope as tp

class Experiment:
    def __init__(self, log, dir, nrealize=1, nobs=1, clcDet=1, specRes=1.e9, foregrounds=False):
        #Store passed parameters
        self.log       = log
        self.dir       = str(dir)
        self.nrealize  = int(nrealize)
        self.nobs      = int(nobs)
        self.clcDet    = int(clcDet)
        self.specRes   = float(specRes)
        self.fgnds     = bool(foregrounds)

        #Check whether experiment exists
        if not os.path.isdir(self.dir): raise Exception('BoloCalc FATAL Exception: Experiment directory %s does not exist' % (self.dir))

        #Generate global parameters
        self.configDir = os.path.join(self.dir, 'config')
        #Check whether configuration directory exists
        if not os.path.isdir( self.configDir): raise Exception('BoloCalc FATAL Exception: Experiment configuration directory %s does not exist' % (self.configDir))

        #Name the experiment
        self.name = os.path.split(self.dir.rstrip('/'))[-1]
        self.log.log("Instantiating experiment %s" % (self.name), 1)

        #Store foreground parameters
        if self.fgnds:
            self.fgndFile = os.path.join(self.configDir, 'foregrounds.txt')
            if not os.path.isfile(self.fgndFile): raise Exception("BoloCalc FATAL Exception: Foreground file '%s' does not exist" % (self.fgndFile))
            try:
                params, vals  = np.loadtxt(self.fgndFile, unpack=True, usecols=[0,2], dtype=np.str, delimiter='|')
                self.fgndDict = {params[i].strip(): vals[i].strip() for i in range(len(params))}
                self.log.log("Using foreground parameters in '%s'"    % (self.fgndFile), 1)            
            except:
                raise Exception("BoloCalc FATAL Exception: Failed to load parameters in '%s'. See 'foreground.txt' formatting rules in the BoloCalc User Manual" % (self.fgndFile))
        else:
            self.fgndDict = None
            self.log.log("Ignoring foregrounds", 1)

        #Generate experiment
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        #Store telescope objects in dictionary
        self.log.log("Generating telescopes for experiment %s" % (self.name), 1)
        telescopeDirs   = sorted(gb.glob(os.path.join(self.dir, '*'+os.sep))); telescopeDirs = [x for x in telescopeDirs if 'config' not in x and 'paramVary' not in x] 
        if len(telescopeDirs) == 0: 
            raise Exception("BoloCalc FATAL Exception: Zero telescope directories found in experiment directory '%s'" % (self.dir))
        telescopeNames  = [telescopeDir.split(os.sep)[-2] for telescopeDir in telescopeDirs]
        self.telescopes = cl.OrderedDict({})
        for i in range(len(telescopeNames)):
            if telescopeNames[i] in self.telescopes.keys():
                raise Exception("BoloCalc FATAL Exception: Multiple telescope directories with the same name '%s' in experiment directory '%s'" % (telescopeNames[i], self.dir))
            self.telescopes.update({telescopeNames[i]: tp.Telescope(self.log, telescopeDirs[i], fgndDict=self.fgndDict, nrealize=self.nrealize, nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes, foregrounds=self.fgnds)})
