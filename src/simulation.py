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
import src.unit as un
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
    exp_dir (str): experiment directory
    log (src.Log): Log object
    load (src.Load): Load object
    phys (src.Physics): Physics object
    noise (src.Noise): Noise object
    self.exps (list): list of src.Experiment objects
    """
    def __init__(self, log_file, sim_file, exp_dir):
        # Store experiment input file
        self.exp_dir = exp_dir
        self._sim_file = sim_file

        # Build simulation-wide objects
        self.log = lg.Log(log_file)
        self.load = ld.Loader(self.log)
        self.phys = ph.Physics()
        self.noise = ns.Noise(self.phys)

        # Store parameter values
        self._store_param_dict()

        # Set up multiprocessing
        if self.param("mpps"):
            self._pool = mp.Pool(self.param("core"))

        # Length of status bar
        self._bar_len = 100

    # **** Public Methods ****
    def generate(self):
        """ Generate experiments """
        if not self.param("mpps"):
            self.exps = [
                self._mp1(n)
                for n in range(self.param("nexp"))]
            self._done()
        else:
            iters = [n for n in range(self.param("nexp"))]
            self.exps = self._pool.map(self._mp1, iters)

    def calculate(self):
        """ Calculate experiments """
        if not self.param("mpps"):
            self.calcs = [
                self._mp2(self.exps[n], n)
                for n in range(self.param("nexp"))]
            self._done()
            self.calcs = [
                self._mp3(self.calcs[n], n)
                for n in range(self.param("nexp"))]
            self._done()
        else:
            self.calcs = self._pool.map(self._mp2, self.exps)
            self.calcs = self._pool.map(self._mp3, self.calcs)
        return self._mp4()

    def simulate(self):
        """ Generate and calculate experiments """
        self.generate()
        self.calculate()

    def param(self, param):
        """ Return parameter from param_dict

        Args:
        param (str): name or parameter, param_dict key
        """
        return self._param_dict[param].get_val()

    # **** Helper Methods ****
    def _mp1(self, n=None):
        """ Multiprocessing #1 -- generate experiments """
        if n is not None and n == 0:
            self.log.log(
                "Generating %d experiment realizations."
                % (self.param("nexp")))
        self._status(n)
        return ex.Experiment(self)

    def _mp2(self, exp, n=None):
        """ Multiprocessing #2 -- calculate experiments """
        if n is not None and n == 0:
            self.log.log(
                "Calculating sensitivity for %d experiment realizations"
                % (self.param("nexp")),
                self.log.level["MODERATE"])
        self._status(n)
        return cl.Calculate(exp)

    def _mp3(self, clc, n=None):
        """ Multiprocessing #3 -- generate channel sensitivities """
        if n is not None and n == 0:
            self.log.log(
                "Calculating statistics for %d experiment realizations"
                % (self.param("nexp")), self.log.level["MODERATE"])
        self._status(n)
        chs = clc.chs
        self.senses = [[[
            clc.calc_sens(chs[i][j][k])
            for k in range(len(chs[i][j]))]
            for j in range(len(chs[i]))]
            for i in range(len(chs))]
        self.opt_pows = [[[
            clc.calc_opt_pow(chs[i][j][k])
            for k in range(len(chs[i][j]))]
            for j in range(len(chs[i]))]
            for i in range(len(chs))]
        return clc

    def _mp4(self):
        """ Multiprocessing #4 -- generate output tables """
        dsp = dp.Display(self)
        dsp.sensitivity()
        dsp.opt_pow_tables()
        return dsp

    def _status(self, rel):
        """ Print status bar for realization 'rel' """
        frac = float(rel) / float(self.param("nexp"))
        sy.stdout.write('\r')
        sy.stdout.write(
            "[%-*s] %02.1f%%" % (int(self._bar_len), '=' * int(
                self._bar_len * frac), frac * 100.))
        sy.stdout.flush()
        return

    def _done(self):
        """ Print filled status bar """
        sy.stdout.write('\r')
        sy.stdout.write(
            "[%-*s] %d%%" % (self._bar_len, '='*self._bar_len, 100))
        sy.stdout.write('\n')
        sy.stdout.flush()
        return

    def _store_param_dict(self):
        """ Store input parameters in dictionary """
        if not os.path.isfile(self._sim_file):
            self._log.err(
                "Simulation file '%s' does not exist" % (self._sim_file))
        params = self.load.sim(self._sim_file)
        self._param_dict = {
            "mpps": pr.Parameter(
               self.log, "Multiprocess", params["Multiprocess"],
               inp_type=bool),
            "core": pr.Parameter(
                self.log, "Cores", params["Cores"],
                inp_type=int),
            "vrbs": pr.Parameter(
                self.log, "Verbosity", params["Verbosity"],
                inp_type=int),
            "nexp": pr.Parameter(
                self.log, "Experiments", params["Experiments"],
                inp_type=int),
            "nobs": pr.Parameter(
                self.log, "Observations", params["Observations"],
                inp_type=int),
            "ndet": pr.Parameter(
                self.log, "Detectors", params["Detectors"],
                inp_type=int),
            "fres": pr.Parameter(
                self.log, "Resolution", params["Resolution"],
                unit=un.Unit("GHz"), inp_type=float),
            "infg": pr.Parameter(
                self.log, "Foregrounds", params["Foregrounds"],
                inp_type=bool),
            "corr": pr.Parameter(
                self.log, "Correlations", params["Correlations"],
                inp_type=bool)}
        return
