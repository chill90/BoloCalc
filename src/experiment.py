# Built-in modules
import numpy as np
import glob as gb
import collections as cl
import os

# BoloCalc modules
import src.telescope as tp
import src.parameter as pr


class Experiment:
    """
    Experiment object gathers foreground parameters and contains
    a dictionary of telescope objects

    Args:
    sim (src.Simulation): Simulation object

    Attributes:
    sim (src.Simulation): where the 'sim' arg is stored
    dir (str): the input directory for the experiment
    name (str): name of the experiment
    tels (dict): dictionary of src.Telescope objects
    """
    def __init__(self, sim):
        # Passed classes
        self.sim = sim
        # Experiment directory
        self.dir = self.sim.exp_dir

        # Check whether experiment and config dir exists
        if not os.path.isdir(self.dir):
            self._log().err(
                "Experiment dir '%s' does not exist" % (self.dir))
        config_dir = os.path.join(self.dir, 'config')
        if not os.path.isdir(config_dir):
            self._log().err(
                "Experiment config dir '%s' does not exist"
                % (config_dir))

        # Name the experiment
        self.name = os.path.split(self.dir.rstrip('/'))[-1]

        # Store foreground parameter dictionary
        if self.sim.fetch("fgs"):
            fgnd_file = os.path.join(config_dir, 'foregrounds.txt')
            self._store_param_dict(self._load().foregrounds(fgnd_file))
        else:
            self._param_dict = None
            self._log().log("Ignoring foregrounds", self.log.level["MODERATE"])

        # Generate experiment
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        """ Generate param dict and telescope dict"""
        # Generate parameter values
        self._store_param_vals()
        # Store telescope objects in dictionary
        self._gen_tels()
        return

    # Fetch parameters from Simulation object
    def fetch(self, param):
        """
        Fetch experiment parameter values

        Args:
        param (str): parameter name, param_vals key
        """
        return self._param_vals[param]

    # ***** Helper Methods *****
    def _param_samp(self, param):
        if self.sim.fetch("nexp"):
            return param.getAvg()
        else:
            return param.sample(nsample=1)

    def _log(self):
        return self.sim.log

    def _load(self):
        return self.sim.ld

    def _store_param_dict(self, params):
        self._param_dict = {
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

    def _store_param_vals(self):
        if self._param_dict is not None:
            self._param_vals = {}
            for k in self._param_dict.keys():
                self._param_vals[k] = self._param_samp(self._param_dict[k])
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
