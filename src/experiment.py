# Built-in modules
import glob as gb
import os

# BoloCalc modules
import src.telescope as tp
import src.parameter as pr


class Experiment:
    """
    Experiment object gathers foreground parameters and contains
    a dictionary of telescope objects. It inherits a Simulation
    object.

    Args:
    sim (src.Simulation): parent Simulation object

    Attributes:
    dir (str): the input directory for the experiment

    Parents:
    sim (src.Simulation): Simulation object

    Children:
    tels (dict): dictionary of Telescope objects
    """
    def __init__(self, sim):
        # Store passed classes
        self.sim = sim
        self._log = self.sim.log
        self._load = self.sim.load
        self._std_params = self.sim.std_params
        # Experiment directory
        self.dir = self.sim.exp_dir
        self.name = self.dir.split(os.sep)[-2]

        # Generate the experiment
        self._log.log("Generating expeiment realization from %s" % (self.dir))
        # Check whether experiment and config dirs exist
        self._check_dirs()
        # Store foreground parameter dictionary
        self._store_param_dict()
        # Store telescopes
        self._store_tels()

    # ***** Public Methods *****
    def evaluate(self):
        """ Generate param dict and telescope dict """
        self._log.log("Evaluating experiment %s" % (self.dir))
        # Generate parameter values
        self._store_param_vals()
        # Evaluate telescopes
        self._log.log("Evaluating telescopes in experiment %s" % (self.dir))
        for tel in self.tels.values():
            tel.evaluate()
        return

    def param(self, param):
        """
        Return parameter from param_vals

        Args:
        param (str): parameter name, param_vals key
        """
        return self._param_vals[param]

    def change_param(self, param, new_val):
        """
        Change foreground parameter values

        Args:
        param (str): name of parameter or param dict key
        new_val (float): new value to set the parameter to
        """
        self._log.log(
            "Changing foreground parameter '%s' to new value '%s'"
            % (str(param), str(new_val)))
        # Check that foreground parameters are defined
        if self._param_dict is None:
            self._log.err(
                "Cannot change foreground parameter in %s when foregrounds "
                "are disabled" % (self.dir))
        # Check if the parameter label is by name
        if param not in self._param_dict.keys():
            caps_param = param.replace(" ", "").strip().upper()
            if caps_param in self._param_names.keys():
                return (self._param_dict[
                        self._param_names[caps_param]].change(new_val))
            else:
                self._log.err(
                    "Parameter '%s' not understood by "
                    "Experiment.change_param()"
                    % (str(param)))
        # Check if the parameter label is by dict key
        elif param in self._param_dict.keys():
            return self._param_dict[param].change(new_val)
        # Throw an error if they parameter cannot be identified
        else:
            self._log.err(
                "Parameter '%s' not understood by Experiment.change_param()"
                % (str(param)))
        return

    # ***** Helper Methods *****
    def _param_samp(self, param):
        """ Sample experiment parameter """
        if self.sim.param("nexp"):
            return param.get_med()
        else:
            return param.sample(nsample=1)

    def _store_param(self, name):
        """ Generate src.Parameter object and return it """
        cap_name = name.replace(" ", "").strip().upper()
        if cap_name in self._std_params.keys():
            return pr.Parameter(
                self._log, self._inp_dict[cap_name],
                std_param=self._std_params[cap_name])
        else:
            self._log.err(
                "Passed parameter in foregrounds.txt '%s' not "
                "recognized" % (name))

    def _store_param_dict(self):
        """ Store dictionary of experiment parameters """
        if self.sim.param("infg"):
            # Load foreground file into a dictionary
            fgnd_file = os.path.join(self._config_dir, 'foregrounds.txt')
            self._log.log(
                "Loading foreground file '%s'" % (fgnd_file))
            self._inp_dict = self._load.foregrounds(fgnd_file)

            # Dictionary of the foreground Parameter objects
            self._log.log(
                "Storing foreground parameters for %s" % (self.dir))
            self._param_dict = {
                "dust_temp": self._store_param("Dust Temperature"),
                "dust_ind": self._store_param("Dust Spec Index"),
                "dust_amp": self._store_param("Dust Amplitude"),
                "dust_freq": self._store_param("Dust Scale Frequency"),
                'sync_ind': self._store_param("Synchrotron Spec Index"),
                "sync_amp": self._store_param("Synchrotron Amplitude"),
                "sync_freq": self._store_param("Sync Scale Frequency")}
            # Dictionary for ID-ing parameters for changing
            self._param_names = {
                param.caps_name: pid
                for pid, param in self._param_dict.items()}
        else:
            self._param_dict = None
            self._param_names = None
            self._log.log(
                "Ignoring foregrounds for experiment %s" % (self.dir))
        return

    def _store_param_vals(self):
        """ Sample and store parameter values """
        self._log.log(
            "Evaluating parameters for experiment %s"
            % (self.dir))
        # Store foreground parameters
        self._param_vals = {}
        if self._param_dict is not None:
            for k in self._param_dict.keys():
                self._param_vals[k] = self._param_samp(self._param_dict[k])
        # Store experiment name
        self._param_vals["exp_name"] = os.path.split(self.dir.rstrip('/'))[-1]
        return

    def _store_tels(self):
        """ Store telescopes """
        self._log.log(
            "Storing telescopes in experiment %s"
            % (self.dir))
        # Gather directories in experiment, ignoring 'config' and 'paramVary'
        tel_dirs = sorted(gb.glob(os.path.join(self.dir, '*' + os.sep)))
        tel_dirs = [x for x in tel_dirs
                    if 'config' not in x and 'paramVary' not in x]
        # Check that at least one telescope is present
        if len(tel_dirs) == 0:
            self._log.err(
                "Zero telescopes in '%s'" % (self.dir))
        # Check for duplicate telescope names
        tel_names = [tel_dir.split(os.sep)[-2] for tel_dir in tel_dirs]
        if len(tel_names) != len(set(tel_names)):
            self._log.err("Duplicate telescope name in '%s'" % (self.dir))
        # Store telescope objects
        self.tels = {}
        for i in range(len(tel_names)):
            tel_name_upper = tel_names[i].replace(" ", "").strip().upper()
            self.tels.update({tel_name_upper:
                              tp.Telescope(self, tel_dirs[i])})
        return

    def _check_dirs(self):
        """ Check that passed experiment directory exists with a config dir """
        # Check that experiment directory exists
        if not os.path.isdir(self.dir):
            self._log.err(
                "Experiment dir '%s' does not exist" % (self.dir))
        # Check that experiment config directory exists
        self._config_dir = os.path.join(self.dir, 'config')
        if not os.path.isdir(self._config_dir):
            self._log.err(
                "Experiment config dir '%s' does not exist"
                % (self._config_dir))
