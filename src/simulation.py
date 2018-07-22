import numpy               as np
import glob                as gb
import multiprocessing     as mp
import time                as tm
import sys                 as sy
import collections         as co
import exception           as ex
import                        os
import src.experiment      as ex
import src.calculate       as cl
import src.display         as dp
import src.log             as lg

class Simulation:
    def __init__(self, expFile, simFile, logFile, verbosity=0, genTables=True):
        #Store passed parameters
        self.expFile   = expFile
        self.simFile   = simFile
        self.logFile   = logFile
        self.verbosity = verbosity
        self.genTables = genTables
        
        #Simulation Input Parameters
        params, vals   = np.loadtxt(simFile, unpack=True, skiprows=1, usecols=[0,1], dtype=np.str, delimiter='|')
        self.inputDict = co.OrderedDict({params[i].strip(): vals[i].strip() for i in range(len(params))})
        self.mp        = self.__bool( 'Multiprocess', self.inputDict['Multiprocess'])
        self.cores     = self.__int(  'Cores',        self.inputDict['Cores'])      
        self.verbose   = self.__int(  'Verbosity',    self.inputDict['Verbosity'])  
        self.nrel      = self.__int(  'Experiments',  self.inputDict['Experiments'])
        self.nobs      = self.__int(  'Observations', self.inputDict['Observations'])
        self.clcDet    = self.__int(  'Detectors',    self.inputDict['Detectors'])  
        self.specRes   = self.__float('Resolution',   self.inputDict['Resolution'])*1.e9 #Hz
        self.fgnd      = self.__bool( 'Foregrounds',  self.inputDict['Foregrounds'])
        self.corr      = self.__bool( 'Correlations', self.inputDict['Correlations'])

        #Logging
        self.log = lg.Log(self.logFile, self.verbosity)
        if verbosity is not None: self.log.log('Logging to file "%s," printing with verbosity = %d' % (logFile, self.verbosity), 1)
        else:                     self.log.log('Logging to file "%s,"' % (logFile), 1)

        #Length of status bar
        self.barLen = 100

        #Set up multiprocessing
        if self.mp: self.p = mp.Pool(self.cores)

    #**** Public Methods ****
    #Generate experiments
    def generateExps(self):
        if not self.mp:
            self.experiments = [self.__mp1(self.expFile, n  ) for n in range(self.nrel)]; self.__done()
        else:
            designDirs = [self.expFile for n in range(self.nrel)]
            self.experiments = self.p.map(self.__mp1, designDirs)            
    def calculate(self):
        if not self.mp:
            calculates  = [self.__mp2(self.experiments[n], n) for n in range(self.nrel)]; self.__done()
            calculates  = [self.__mp3(calculates[n], n ) for n in range(self.nrel)]; self.__done()
        else:
            calculates       = self.p.map(self.__mp2, self.experiments)
            calculates       = self.p.map(self.__mp3, calculates)
        return self.__mp4(calculates)

    #Simulate sensitivity
    def simulate(self):
        #Calculate mapping speed
        self.generateExps()
        self.calculate()

    #**** Private methods ****
    #Convert string to bool
    def __bool(self, param, str): 
        if str.upper() == 'TRUE':    return True
        elif str.upper() == 'FALSE': return False
        else: raise TypeError('FATAL: Invalid boolean "%s" for parameter "%s" in BoloCalc/config/simulationInputs.txt. Must be "True" or "False."' % (str, param))
    def __int(self, param, str):
        try:
            return int(str)
        except:
            raise TypeError('FATAL: Invalid integer "%s" for parameter "%s" in BoloCalc/config/simulationInputs.txt. Must be valid integer value."' % (str, param))
    def __float(self, param, str):
        try:
            return float(str)
        except:
            raise TypeError(('FATAL: Invalid float "%s" for parameter "%s" in BoloCalc/config/simulationInputs.txt. Must be valid float value."' % (str, param))
    #Top-level methods for multiprocessing handling
    def __mp1(self, drr, n=None):
        if self.verbosity == 0 and n is not None:
            if n == 0:
                sy.stdout.write('Generating %d experiment realizations...\n' % (self.nrel))
            self.__status(n)
        return ex.Experiment(self.log, drr, nrealize=self.nrel, nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes, foregrounds=self.fgnd)
    def __mp2(self, exp, n=None): 
        if self.verbosity == 0 and n is not None:
            if n == 0:
                sy.stdout.write('Calculating sensitivity for %d experiment realizations...\n' % (self.nrel))
            self.__status(n)
        return cl.Calculate( self.log, exp, self.corr)
    def __mp3(self, clc, n=None):
        if self.verbosity == 0 and n is not None:
            if n == 0:
                sy.stdout.write('Calculating statistics for %d experiment realizations...\n' % (self.nrel))
            self.__status(n)
        chs = clc.chans; tps = clc.teles
        senses = [[[clc.calcSensitivity( chs[i][j][k], tps[i][j][k]) for k in range(len(chs[i][j]))] for j in range(len(chs[i]))] for i in range(len(chs))]
        optpow = [[[clc.calcOpticalPower(chs[i][j][k], tps[i][j][k]) for k in range(len(chs[i][j]))] for j in range(len(chs[i]))] for i in range(len(chs))]
        clc.combineSensitivity( senses)
        clc.combineOpticalPower(optpow)
        return clc
    def __mp4(self, clcs):
        if self.verbosity == 0:
            sy.stdout.write('Writing data...\n')
        dsp = dp.Display(self.log, clcs)
        dsp.sensitivity(genTables=self.genTables)
        dsp.opticalPowerTables()
        return dsp
    def __status(self, rel):
        frac = float(rel)/float(self.nrel)
        sy.stdout.write('\r')
        sy.stdout.write("[%-*s] %02.1f%%" % (self.barLen, '='*int(self.barLen*frac), frac*100.))
        sy.stdout.flush()
    def __done(self):
        if self.verbosity == 0:
            sy.stdout.write('\r')
            sy.stdout.write("[%-*s] %d%%" % (self.barLen, '='*self.barLen, 100))
            sy.stdout.write('\n')
            sy.stdout.flush()
