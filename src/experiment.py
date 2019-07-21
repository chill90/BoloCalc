# Built-in modules
import numpy as np
import glob as gb
import collections as cl
import os

# BoloCalc modules
import src.telescope as tp
import src.parameter as pr


class Experiment:
    def __init__(self, sim):
        # Passed classes
        self.sim = sim
        # Experiment directory
        self.dir = self.sim.exp_dir

        # Check whether experiment exists
        if not os.path.isdir(self.dir):
            self._log().err(
                "Experiment dir '%s' does not exist" % (self.dir))

        # Generate global parameters
        self.config_dir = os.path.join(self.dir, 'config')
        # Check whether configuration directory exists
        if not os.path.isdir(self.config_dir):
            self._log().err(
                "Experiment config dir '%s' does not exist" 
                % (self.config_dir))

        # Name the experiment
        self.name = os.path.split(self.dir.rstrip('/'))[-1]
        self._log.()log(
            "Instantiating experiment %s"
            % (self.name), self.log.level["MODERATE"])

        # Store foreground parameter dictionary
        if self.sim.fetch("fgs"):
            self.fgnd_file = os.path.join(self.config_dir, 'foregrounds.txt')
            self._store_param_dict(self._load().foregrounds(self.fgnd_file))
        else:
            self.param_dict = None
            self.log.log("Ignoring foregrounds", self.log.level["MODERATE"])

        # Generate experiment
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        # Generate foreground parameter values
        self._gen_fg()
        # Store telescope objects in dictionary
        self._gen_tels()
        return

    # Fetch parameters from Simulation object
    def fetch(self, param):
        return self.param_dict[param]

    # ***** Private Methods *****
    def _param_samp(self, param):
        if self.sim.fetch("nexp"):
            return param.getAvg()
        else:
            return param.sample(nsample=1)

    # Pass preferred log object
    def _log(self):
        return self.sim.log

    def _load(self):
        return self.sim.ld

    def _store_param_dict(self, params):
        self.param_dict = {
            "dust_temp": pr.Parameter(
                self._log(), "Dust Temperature",
                params["Dust Temperature"],
                min=0.0, max=np.inf),
            "dust_ind": pr.Parameter(
                self._log(), "Dust Spec Index",
                params["Dust Spec Index"],
                min=-np.inf, max=np.inf),
            "dust_amp": pr.Parameter(
                self._log(), "Dust Amplitude",
                params["Dust Amplitude"],
                min=0.0, max=np.inf),
            "dust_frq": pr.Parameter(
                self._log(), "Dust Scale Frequency",
                params["Dust Scale Frequency"],
                min=0.0, max=np.inf),
            'sync_ind': pr.Parameter(
                self._log(), 'Synchrotron Spec Index',
                params['Synchrotron Spec Index'],
                min=-np.inf, max=np.inf),
            "sync_amp": pr.Parameter(
                self._log(), 'Synchrotron Amplitude',
                params['Synchrotron Amplitude'],
                min=0.0, max=np.inf)}
        return

    def _gen_fg(self):
        if self.param_dict is not None:
            self.param_vals = {}
            for k in self.param_dict.keys():
                self.param_vals[k] = self._param_samp(self.param_dict[k])
        return

    def _gen_tels(self):
        tel_dirs = sorted(gb.glob(os.path.join(self.dir, '*'+os.sep)))
        tel_dirs = [x for x in tel_dirs
                    if 'config' not in x and 'paramVary' not in x]
        if len(tel_dirs) == 0:
            self.log.err(
                "Zero telescopes in '%s'" % (self.dir))
        tel_names = [tel_dir.split(os.sep)[-2] for tel_dir in tel_dirs]
        if len(tel_names) != len(set(tel_names)):
            self.log.err("Duplicate telescope name in '%s'" % (self.dir))
        self.tels = cl.OrderedDict({})
        for i in range(len(tel_names)):
            self.tels.update({tel_names[i]: tp.Telescope(self, tel_dirs[i])})
        return
