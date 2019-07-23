# Built-in modules
import numpy as np
import glob as gb
import sys as sy
import collections as cl
import os

# BoloCalc modules
import src.parameter as pr
import src.camera as cm
import src.sky as sk
import src.scanStrategy as sc
import src.units as un


class Telescope:
    """
    Telescope object contains a Sky object, a ScanStrategy object,
    and a dictionary of Camera objects

    Args:
    exp (src.Experiment): Experiment object
    inp_dir (str): directory for this telescope

    Attributes:
    exp (src.Experiment): where arg 'exp' is stored
    dir (str): where arg 'inp_dir' is stored
    name (str): name of this telescope
    sky (src.Sky): Sky object
    scn (src.ScanStrategy): ScanStrategy object
    cams (dict): dictionary of Camera objects
    """
    def __init__(self, exp, inp_dir):
        # Passed parameters
        self.exp = exp
        self.dir = inp_dir

        # Check whether telescope and config dir exists
        if not os.path.isdir(self.dir):
            self._log().err("Telescope dir '%s' does not exist" % (self.dir))
        self._config_dir = os.path.join(self.dir, 'config')
        if not os.path.isdir(self._config_dir):
            self._log().err(
                "Telescope config dir '%s' does not exist"
                % (self._config_dir))

        # Name the telescope
        self.name = self.dir.rstrip(os.sep).split(os.sep)[-1]

        # Store the telescope parameters
        self._tel_file = os.path.join(self._config_dir, 'telescope.txt')
        if not os.path.isfile(self._tel_file):
            self._log().err(
                "Telescope file '%s' does not exist" % (self.telFile))
        self._store_param_dict(self._load().telescope(self.telFile))

        # Generate the telescope
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        """ Generate camera """
        # Generate parameter values
        self._store_param_vals(self)

        # Handle custom atmospheres
        self._handle_custom_atm()
        self._handle_special_atm()

        # Store sky object
        self.sky = sk.Sky(self)
        # Store scan strategy object
        self.scn = sc.ScanStrategy(self)
        # Store cameras
        self._gen_cams()

    def fetch(self, param):
        """
        Fetch telescope parameter values

        Args:
        param (str): name of parameter, param dict key
        """
        return self._param_vals[param]

    # ***** Helper Methods *****
    def _log(self):
        return self.exp.sim.log

    def _load(self):
        return self.exp.sim.load

    def _param_samp(self, param):
        if self.exp.sim.fetch("nexp") == 1:
            return param.getAvg()
        else:
            return param.sample(nsample=1)

    def _store_param_dict(self, params):
        self._param_dict = {
            "site": pr.Parameter(
                self._log(), 'Site', params['Site']),
            "elev": pr.Parameter(
                self._log(), 'Elevation', params['Elevation'],
                min=20., max=90.),
            "pwv": pr.Parameter(
                self._log(), 'PWV', params['PWV'],
                min=0.0, max=8.0),
            "obs_tm": pr.Parameter(
                self._log(), 'Observation Time', params['Observation Time'],
                un.Unit("year"), min=0.0, max=np.inf),
            "sky_frac": pr.Parameter(
                self._log(), 'Sky Fraction', params['Sky Fraction'],
                min=0.0, max=1.0),
            "obs_eff": pr.Parameter(
                self._log(), 'Observation Efficiency',
                params['Observation Efficiency'],
                min=0.0, max=1.0),
            "net_mgn": pr.Parameter(
                self._log(), 'NET Margin', params['NET Margin'],
                min=0.0, max=np.inf)}
        return

    def _store_param_vals(self):
        self._param_vals = {}
        for k in self._param_dict:
            self._param_vals[k] = self._param_samp(self._param_dict[k])
        return

    def _handle_custom_atm(self):
        if self._param_vals['Site'] is 'NA':
            atm_files = sorted(gb.glob(
                os.path.join(self._config_dir, 'atm*.txt')))
            if len(atm_files) == 0:
                self._log().err(
                    "'Site' parameter in '%s' is 'NA', but no custom \
                    atmosphere file  in '%s'"
                    % (self._tel_file, self._config_dir))
            elif len(atm_files) > 1:
                self._log().err(
                    "'Site' parameter in '%s' is 'NA', but more than one custom \
                    atmosphere file was found in '%s'"
                    % (self._tel_file, self._config_dir))
            else:
                self._param_vals['File'] = atm_files[0]
                self._param_vals['Site'] = None
                self._param_vals['Elevation'] = None
                self._param_vals['PWV'] = None
                self._log().log("Using custom atmosphere defined in '%s'"
                                % (self.atm_file), 0)

    def _handle_special_atm(self):
        if self._param_vals['Site'] is not 'NA':
            self._param_vals['File'] = None
            # Force PWV and elevation for balloon and space missions
            if self._param_vals['Site'].upper() == 'MCMURDO':
                self._param_vals['PWV'] = 0
            elif self._param_vals['Site'].upper() == 'SPACE':
                self._param_vals['PWV'] = None
                self._param_vals['Elevation'] = None

    def _gen_cams(self):
        cam_dirs = sorted(gb.glob(os.path.join(self.dir, '*'+os.sep)))
        cam_dirs = [x for x in cam_dirs if 'config' not in x]
        if len(cam_dirs) == 0:
            self._log().err("Zero cameras in '%s'" % (self.dir))
        cam_names = [cam_dir.split(os.sep)[-2] for cam_dir in cam_dirs]
        if len(cam_names) != len(set(cam_names)):
            self._log().err("Duplicate camera name in '%s'" % (self.dir))
        self.cams = cl.OrderedDict({})
        for i in range(len(cam_names)):
            self.cams.update({cam_names[i]: cm.Camera(self, cam_dirs[i])})
        return
