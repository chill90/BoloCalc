import numpy         as np
import glob          as gb
import collections   as cl
import                  os
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
        if not os.path.isdir(self.dir): raise Exception('Experiment directory %s does not exist' % (self.dir))

        #Generate global parameters
        self.configDir = os.path.join(self.dir, 'config')
        #Check whether configuration directory exists
        if not os.path.isdir(self.configDir): raise Exception('Experiment configuration directory %s does not exist' % (self.configDir))

        #Name the experiment
        self.name = os.path.split(self.dir.rstrip('/'))[-1]
        self.log.log("Instantiating experiment %s" % (self.name), 1)

        #Store foreground parameters        
        try:
            params, vals  = np.loadtxt(os.path.join(self.configDir, 'foregrounds.txt'), unpack=True, usecols=[0,2], dtype=np.str, delimiter='|')
            self.fgndDict = {params[i].strip(): vals[i].strip() for i in range(len(params))}
            if foregrounds: self.log.log("Using foreground parameters in %s"    % (os.path(self.configDir, 'foregrounds.txt')), 1)
            else:           self.log.log("Ignoring foreground parameters in %s" % (os.path(self.configDir, 'foregrounds.txt')), 1)
        except:
            self.fgndDict = None
            self.log.log("No foregrounds assumed", 1)

        #Generate experiment
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        #Store telescope objects in dictionary
        self.log.log("Generating telescopes for experiment %s" % (self.name), 1)
        telescopeDirs   = sorted(gb.glob(os.path.join(self.dir, '*'+os.sep))); telescopeDirs = [x for x in telescopeDirs if 'config' not in x and 'paramVary' not in x] 
        telescopeNames  = [telescopeDir.split(os.sep)[-2] for telescopeDir in telescopeDirs]
        self.telescopes = cl.OrderedDict({})
        for i in range(len(telescopeNames)):
            if telescopeNames[i] in self.telescopes.keys():
                raise Exception('FATAL: Multiple telescopes with the same name "%s" in experiment "%s"' % (telescopeNames[i], self.name))
            self.telescopes.update({telescopeNames[i]: tp.Telescope(self.log, telescopeDirs[i], fgndDict=self.fgndDict, nrealize=self.nrealize, nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes, foregrounds=self.fgnds)})
