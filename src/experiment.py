#python Version 2.7.2
import numpy     as np
import glob      as gb
import telescope as tp

class Experiment:
    def __init__(self, log, dir, nrealize=1, nobs=1, clcDet=1, specRes=1.e9, foregrounds=False):
        #Store passed parameters
        self.log       = log
        self.dir       = dir
        self.nrealize  = nrealize
        self.nobs      = nobs
        self.clcDet    = clcDet
        self.specRes   = specRes
        self.fgnds     = foregrounds

        #Generate global parameters
        self.configDir = self.dir+'/config'
        self.name      = self.dir.rstrip('/').split('/')[-1]

        self.log.log("Instantiating experiment %s" % (self.name), 1)

        #Store foreground parameters
        try:
            params, vals  = np.loadtxt(self.configDir+'/foregrounds.txt', unpack=True, usecols=[0,2], dtype=np.str, delimiter='|')
            self.fgndDict = {params[i].strip(): vals[i].strip() for i in range(len(params))}
            if foregrounds: self.log.log("Using foreground parameters in %s"    % (self.configDir+'/foregrounds.txt'), 1)
            else:           self.log.log("Ignoring foreground parameters in %s" % (self.configDir+'/foregrounds.txt'), 1)
        except:
            self.fgndDict = None
            self.log.log("No foregrounds assumed", 1)

        #Generate experiment
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        #Store telescope objects in dictionary
        self.log.log("Generating telescopes for experiment %s" % (self.name), 1)
        telescopeDirs   = sorted(gb.glob(self.dir+'/*/')); telescopeDirs = [x for x in telescopeDirs if 'config' not in x and 'paramVary' not in x] 
        telescopeNames  = [telescopeDir.split('/')[-2] for telescopeDir in telescopeDirs]
        self.telescopes = {telescopeNames[i]: tp.Telescope(self.log, telescopeDirs[i], fgndDict=self.fgndDict, nrealize=self.nrealize, nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes, foregrounds=self.fgnds) for i in range(len(telescopeNames))}
