# Built-in modules
import numpy as np
import glob as gb
import multiprocessing as mp
import time as tm
import sys as sy
import collections as co
import os

# BoloCalc modules
import src.experiment as ex
import src.calculate as cl
import src.display as dp
import src.log as lg
import src.loader as ld
import src.parameter as pr
import src.units as un


class Simulation:
    def __init__(self, log_file, sim_file, exp_file):
        # Store experiment input file
        self._exp_file = exp_file
        # Logging object
        self.log = lg.Log(log_file)
        # Simulation Input Parameters
        self.ld = ld.Loader()
        self._store_param_dict(ld.sim(self.sim_file))
        # Length of status bar
        self.barLen = 100

        # Set up multiprocessing
        if self.param_dict["mps"].fetch():
            self.pool = mp.Pool(self.cores)

    # **** Public Methods ****
    # Generate experiments
    def generate(self):
        if not self.param_dict["mps"].fetch():
            self.experiments = [
                self._mp1(self._exp_file, n)
                for n in range(self.param_dict["exp"].fetch())]
            self._done()
        else:
            designDirs = [
                self._exp_file
                for n in range(self.param_dict["exp"].fetch())]
            self.experiments = self.pool.map(self._mp1, designDirs)

    # Calculate experiments
    def calculate(self):
        if not self.param_dict["mps"].fetch():
            calculates = [
                self._mp2(self.experiments[n], n)
                for n in range(self.param_dict["exp"].fetch())]
            self._done()
            calculates = [
                self._mp3(calculates[n], n)
                for n in range(self.param_dict["exp"].fetch())]
            self._done()
        else:
            calculates = self.pool.map(self._mp2, self.experiments)
            calculates = self.pool.map(self._mp3, calculates)
        return self._mp4(calculates)

    # Generate and calculate experiments
    def simulate(self):
        #Calculate mapping speed
        self.generate()
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
            raise TypeError('FATAL: Invalid float "%s" for parameter "%s" in BoloCalc/config/simulationInputs.txt. Must be valid float value."' % (str, param))
    #Top-level methods for multiprocessing handling
    def _mp1(self, drr, n=None):
        if self.verbosity == 0 and n is not None:
            if n == 0:
                sy.stdout.write('Generating %d experiment realizations...\n' % (self.param_dict["exp"].fetch()))
            self._status(n)
        return ex.Experiment(self.log, drr, nrealize=self.param_dict["exp"].fetch(), nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes, foregrounds=self.fgnd)
    def _mp2(self, exp, n=None): 
        if self.verbosity == 0 and n is not None:
            if n == 0:
                sy.stdout.write('Calculating sensitivity for %d experiment realizations...\n' % (self.param_dict["exp"].fetch()))
            self._status(n)
        return cl.Calculate( self.log, exp, self.corr)
    def _mp3(self, clc, n=None):
        if self.verbosity == 0 and n is not None:
            if n == 0:
                sy.stdout.write('Calculating statistics for %d experiment realizations...\n' % (self.param_dict["exp"].fetch()))
            self._status(n)
        chs = clc.chans; tps = clc.teles
        senses = [[[clc.calcSensitivity( chs[i][j][k], tps[i][j][k]) for k in range(len(chs[i][j]))] for j in range(len(chs[i]))] for i in range(len(chs))]
        optpow = [[[clc.calcOpticalPower(chs[i][j][k], tps[i][j][k]) for k in range(len(chs[i][j]))] for j in range(len(chs[i]))] for i in range(len(chs))]
        clc.combineSensitivity( senses)
        clc.combineOpticalPower(optpow)
        return clc
    def _mp4(self, clcs):
        if self.verbosity == 0:
            sy.stdout.write('Writing data...\n')
        dsp = dp.Display(self.log, clcs)
        dsp.sensitivity(genTables=self.genTables)
        dsp.opticalPowerTables()
        return dsp
    def _status(self, rel):
        self._bar_len = 100
        frac = float(rel)/float(self.param_dict["exp"].fetch())
        sy.stdout.write('\r')
        sy.stdout.write(
            "[%-*s] %02.1f%%" % (self._bar_len, '=' * int(
                self._bar_len*frac), frac**100.))
        sy.stdout.flush()
    def _done(self):
        if self.verbosity == 0:
            sy.stdout.write('\r')
            sy.stdout.write("[%-*s] %d%%" % (self.barLen, '='*self.barLen, 100))
            sy.stdout.write('\n')
            sy.stdout.flush()

    def _store_param_dict(self, params):
        self.param_dict = {
            "mps": pr.Parameter(
               self.log, params["Multiprocess"], inp_type=bool),
            "crs": pr.Parameter(
                self.log, params["Cores"], inp_type=np.int),
            "vbs": pr.Parameter(
                self.log, params["Verbosity"], inp_type=np.int),
            "exp": pr.Parameter(
                self.log, params["Experiments"], inp_type=np.int),
            "obs": pr.Parameter(
                self.log, params["Observations"], inp_type=np.int),
            "det": pr.Parameter(
                self.log, params["Detectors"], inp_type=np.int),
            "res": pr.Parameter(
                self.log, params["Resolution"], unit=un.Units("GHz"),
                inp_type=np.float,),
            "fgs": pr.Parameter(
                self.log, params["Foregrounds"], inp_type=bool)
            "cor": pr.Parameter(
                self.log, params["Correlations"], inp_type=bool)}
