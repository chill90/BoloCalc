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
import src.physics as ph
import src.noise as ns


class Simulation:
    """
    Simulation object generates experiments, calculates their parameters,
    simulates their sensitivies, and displays the outputs

    Args:
    log_file (str): logging file
    sim_file (str): simulation input file
    exp_dir (str): experiment directory

    Attributes:
    log (src.Log): Log object
    load (src.Load): Load object
    phys (src.Physics): Physics object
    noise (src.Noise): Noise object
    """
    def __init__(self, log_file, sim_file, exp_dir):
        # Store experiment input file
        self._exp_dir = exp_dir

        # Build simulation-wide objects
        self.log = lg.Log(log_file)
        self.load = ld.Loader()
        self.phys = ph.Physics()
        self.noise = ns.Noise(self.phys)

        # Store parameter dictionary
        self._store_param_dict(ld.sim(sim_file))

        # Set up multiprocessing
        if self.fetch("mpss"):
            self._pool = mp.Pool(self.fetch("core"))

        # Length of status bar
        self._bar_len = 100.

    # **** Public Methods ****
    def generate(self):
        """ Generate experiments """
        if not self.fetch("mpss"):
            self.experiments = [
                self._mp1(self._exp_dir, n)
                for n in range(self.fetch("nexp"))]
            self._done()
        else:
            designDirs = [
                self._exp_dir
                for n in range(self.fetch("nexp"))]
            self.experiments = self._pool.map(self._mp1, designDirs)

    def calculate(self):
        """ Calculate experiments """
        if not self.fetch("mpps"):
            calculates = [
                self._mp2(self.experiments[n], n)
                for n in range(self.fetch("nexp"))]
            self._done()
            calculates = [
                self._mp3(calculates[n], n)
                for n in range(self.fetch("nexp"))]
            self._done()
        else:
            calculates = self._pool.map(self._mp2, self.experiments)
            calculates = self._pool.map(self._mp3, calculates)
        return self._mp4(calculates)

    def simulate(self):
        """ Generate and calculate experiments """
        self.generate()
        self.calculate()

    def fetch(self, param):
        """ Fetch parameter from param_dict

        Args:
        param (str): name or parameter, param_dict key
        """
        return self._param_dict[param].fetch()

    # **** Helper Methods ****
    # Multiprocessing functions
    def _mp1(self, drr, n=None):
        if n is not None and n == 0:
            self.log.log(
                "Generating %d experiment realizations."
                % (self.fetch("exp")))
        self._status(n)
        return ex.Experiment(self)

    def _mp2(self, exp, n=None):
        if n is not None and n == 0:
            self.log.log(
                "Calculating sensitivity for %d experiment realizations"
                % (self._param_dict["nexp"].fetch()))
        self._status(n)
        return cl.Calculate(self.log, exp, self.corr)

    def _mp3(self, clc, n=None):
        if n is not None and n == 0:
            self.log.log(
                "Calculating statistics for %d experiment realizations"
                % (self.fetch("nexp")))
        self._status(n)
        chs = clc.chans
        tps = clc.teles
        senses = [[[
            clc.calcSensitivity(chs[i][j][k], tps[i][j][k])
            for k in range(len(chs[i][j]))]
            for j in range(len(chs[i]))]
            for i in range(len(chs))]
        optpow = [[[
            clc.calcOpticalPower(chs[i][j][k], tps[i][j][k])
            for k in range(len(chs[i][j]))]
            for j in range(len(chs[i]))]
            for i in range(len(chs))]
        clc.combineSensitivity(senses)
        clc.combineOpticalPower(optpow)
        return clc

    def _mp4(self, clcs):
        dsp = dp.Display(self.log, clcs)
        dsp.sensitivity()
        dsp.opticalPowerTables()
        return dsp

    def _status(self, rel):
        frac = float(rel)/float(self.fetch("nexp"))
        sy.stdout.write('\r')
        sy.stdout.write(
            "[%-*s] %02.1f%%" % (self._bar_len, '=' * int(
                self._bar_len*frac), frac**100.))
        sy.stdout.flush()
        return

    def _done(self):
        if self.verbosity == 0:
            sy.stdout.write('\r')
            sy.stdout.write(
                "[%-*s] %d%%" % (self._bar_len, '='*self._bar_len, 100))
            sy.stdout.write('\n')
            sy.stdout.flush()
        return

    def _store_param_dict(self, params):
        self._param_dict = {
            "mpps": pr.Parameter(
               self.log, params["Multiprocess"], inp_type=bool),
            "core": pr.Parameter(
                self.log, params["Cores"], inp_type=np.int),
            "vrbs": pr.Parameter(
                self.log, params["Verbosity"], inp_type=np.int),
            "nexp": pr.Parameter(
                self.log, params["Experiments"], inp_type=np.int),
            "nobs": pr.Parameter(
                self.log, params["Observations"], inp_type=np.int),
            "ndet": pr.Parameter(
                self.log, params["Detectors"], inp_type=np.int),
            "fres": pr.Parameter(
                self.log, params["Resolution"], unit=un.Units("GHz"),
                inp_type=np.float,),
            "infg": pr.Parameter(
                self.log, params["Foregrounds"], inp_type=bool)
            "corr": pr.Parameter(
                self.log, params["Correlations"], inp_type=bool)}
