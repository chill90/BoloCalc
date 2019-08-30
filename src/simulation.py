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
import src.display as dp
import src.log as lg
import src.loader as ld
import src.parameter as pr
import src.unit as un
import src.physics as ph
import src.noise as ns
import src.profile as pf
import src.sensitivity as sn
import src.vary as vr


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

        self.log.log(
            "Generating Simulation object")
        # Store parameter values
        self._store_param_dict()
        # Length of status bar
        self._bar_len = 100

        self.log.log(
            "Generating Experiment, Sensitivity, and Display objects")
        # Generate simulation objects
        self.exp = ex.Experiment(self)
        self.sns = sn.Sensitivity(self)
        self.dsp = dp.Display(self)

        # Output arrays
        self.senses = []
        self.opt_pows = []

    # **** Public Methods ****
    # @pf.profiler
    def simulate(self):
        """ Run simulation """
        self._evaluate()
        self._display()
        return

    def vary_simulate(self, param_file, vary_name, vary_tog):
        """
        Run parameter vary simulation
        
        Args:
        param_file (str): file that contains the parameters to be varied
        vary_name (str): name of the vary output directory
        vary_tog(bool): whether or not to vary the parameter arrays together
        """
        vary = vr.Vary(self, param_file, vary_name, vary_tog)
        vary.vary()
        return

    def param(self, param):
        """ Return parameter from param_dict

        Args:
        param (str): name or parameter, param_dict key
        """
        val = self._param_dict[param].get_val()
        if val is None:
            val = self._param_dict[param].get_avg()
        return val

    # **** Helper Methods ****
    def _evaluate(self):
        """ Evaluate experiment """
        tot_sims = self.param("nexp") * self.param("ndet") * self.param("nobs")
        self.log.out((
                "Simulting %d experiment realizations each with "
                "%d detector realizations and %d sky realizations.\n"
                "Total sims = %d"
                % (self.param("nexp"), self.param("ndet"),
                   self.param("nobs"), tot_sims)))
        for n in range(self.param("nexp")):
            self._evaluate_exp(n)
        self._done()
        return
    
    def _display(self):
        """ Display sensitivity output """
        self.dsp.display()
        return
    
    def _evaluate_exp(self, n):
        """ Evaluate and calculate sensitivity for a generated experiment """
        self._status(n)
        self.exp.evaluate()
        self.senses.append(self.sns.sensitivity())
        self.opt_pows.append(self.sns.opt_pow())
        return

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
            "[%-*s] %.1f%%" % (self._bar_len, '='*self._bar_len, 100.))
        sy.stdout.write('\n')
        sy.stdout.flush()
        return

    def _store_param_dict(self):
        """ Store input parameters in dictionary """
        # Check whether the simulation file exists
        if not os.path.isfile(self._sim_file):
            self.log.err(
                "Simulation file '%s' does not exist" % (self._sim_file))
        # Load the simulation file to a parameter dictionary
        params = self.load.sim(self._sim_file)
        # Store dictionary of Parameter objects
        self._param_dict = {
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
                inp_type=float),
            "infg": pr.Parameter(
                self.log, "Foregrounds", params["Foregrounds"],
                inp_type=bool),
            "corr": pr.Parameter(
                self.log, "Correlations", params["Correlations"],
                inp_type=bool),
            "pct": pr.Parameter(
                self.log, "Percentile", params["Percentile"],
                inp_type=list)}
        return
