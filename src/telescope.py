# Built-in modules
import glob as gb
import os

# BoloCalc modules
import src.parameter as pr
import src.camera as cm
import src.sky as sk
import src.scanStrategy as sc


class Telescope:
    """
    Telescope object contains a Sky object, a ScanStrategy object,
    and a dictionary of Camera objects

    Args:
    exp (src.Experiment): parent Experiment object
    inp_dir (str): directory for this telescope

    Attributes:
    dir (str): where arg 'inp_dir' is stored

    Parents:
    exp (src.Experiment): Experiment object

    Children:
    cams (dict): dictionary of Camera objects
    sky (src.Sky): Sky object
    scn (src.ScanStrategy): ScanStrategy object
    """
    def __init__(self, exp, inp_dir):
        # Passed parameters
        self.exp = exp
        self.dir = inp_dir
        self.name = self.dir.split(os.sep)[-2]
        self._log = self.exp.sim.log
        self._load = self.exp.sim.load
        self._std_params = self.exp.sim.std_params

        self._log.log("Generating telescope realization from %s" % (self.dir))
        # Check whether telescope and config dir exists
        self._check_dirs()
        # Store the telescope parameters
        self._store_param_dict()

        self._log.log("Generating Sky object for Telescope %s" % (self.dir))
        # Store sky object
        self.sky = sk.Sky(self)
        # Store scan strategy object
        self._log.log("Generating ScanStrategy object for Telescope %s"
                      % (self.dir))
        self.scn = sc.ScanStrategy(self)
        # Store cameras
        self._log.log("Generating Camera objects for Telescope %s"
                      % (self.dir))
        self._store_cams()

    # ***** Public Methods *****
    def evaluate(self):
        """ Evaluate telescope """
        self._log.log(
            "Evaluating telescope %s" % (self.dir))
        # Evaluate parameter values
        self._store_param_vals()
        # Handle the atmosphere
        self._handle_atm()
        # Evaluate cameras
        self._log.log(
            "Evaluating cameras in telescope %s"
            % (self.dir))
        for cam in self.cams.values():
            cam.evaluate()
        return

    def param(self, param):
        """
        Return telescope parameter value

        Args:
        param (str): name of parameter, param dict key
        """
        return self._param_vals[param]

    def change_param(self, param, new_val):
        """
        Change telescope parameter value

        Args:
        param (str): name of parameter or param dict key
        new_val (float): new value to set the parameter to
        """
        self._log.log(
            "Changing telescope parameter '%s' to new value '%s'"
            % (str(param), str(new_val)))
        # Check if the parameter label is by name
        if param not in self._param_dict.keys():
            caps_param = param.replace(" ", "").strip().upper()
            if caps_param in self._param_names.keys():
                return (self._param_dict[
                        self._param_names[caps_param]].change(new_val))
            else:
                self._log.err(
                    "Parameter '%s' not understood by Telescope.change_param()"
                    % (str(param)))
        # Check if the parameter label is by dict key
        elif param in self._param_dict.keys():
            return self._param_dict[param].change(new_val)
        # Throw an error if they parameter cannot be identified
        else:
            self._log.err(
                    "Parameter '%s' not understood by Telescope.change_param()"
                    % (str(param)))

    def sky_temp_sample(self):
        """ Sample sky temperature for this telescope """
        if self.exp.sim.param("nobs") == 1:
            return self._param_dict["sky_temp"].get_med()
        else:
            return self._param_dict["sky_temp"].sample(nsample=1)

    def pwv_sample(self):
        """ Sample PWV for this telescope """
        if self.exp.sim.param("nobs") == 1:
            return self._param_dict["pwv"].get_med()
        else:
            return self._param_dict["pwv"].sample(nsample=1)

    def elev_sample(self):
        """ Sample elevation for this telescope """
        if self.exp.sim.param("nobs") == 1:
            return self._param_dict["elev"].get_med()
        else:
            return self._param_dict["elev"].sample(nsample=1)

    # ***** Helper Methods *****
    def _check_dirs(self):
        """ Check that passed telescope directory exists with a config dir """
        if not os.path.isdir(self.dir):
            self._log.err("Telescope '%s' does not exist" % (self.dir))
        self._config_dir = os.path.join(self.dir, 'config')
        if not os.path.isdir(self._config_dir):
            self._log.err(
                "Telescope config dir '%s' does not exist"
                % (self._config_dir))
        return

    def _store_param_dict(self):
        """ Store Parameter objects for telescope """
        # Check that the telescope parameter file exists
        self._tel_file = os.path.join(self._config_dir, 'telescope.txt')
        if not os.path.isfile(self._tel_file):
            self._log.err(
                "Telescope file '%s' does not exist" % (self._tel_file))
        # Load telescope file into a dictionary
        self._inp_dict = self._load.telescope(self._tel_file)
        # Dictionary of the telescope Parameter objects
        self._log.log(
                "Storing telescope parameters for %s" % (self.dir))
        self._param_dict = {
            "site": self._store_param("Site"),
            "elev": self._store_param("Elevation"),
            "pwv": self._store_param("PWV"),
            "tobs": self._store_param("Observation Time"),
            "fsky": self._store_param("Sky Fraction"),
            "obs_eff": self._store_param("Observation Efficiency"),
            "net_mgn": self._store_param("NET Margin")}
        # New parameters, added separately for backwards compatibility
        if "SKYTEMPERATURE" in self._inp_dict.keys():
            self._param_dict["sky_temp"] = self._store_param("Sky Temperature")
        else:
            self._param_dict["sky_temp"] = pr.Parameter(
                self._log, "NA", name="Sky Temperature")
        # Dictionary for ID-ing parameters for changing
        self._param_names = {
            param.caps_name: pid
            for pid, param in self._param_dict.items()}
        return

    def _store_param(self, name):
        """ Store src.Parameter objects for this telescope """
        cap_name = name.replace(" ", "").strip().upper()
        if cap_name in self._std_params.keys():
            return pr.Parameter(
                self._log, self._inp_dict[cap_name],
                std_param=self._std_params[cap_name])
        else:
            self._log.err(
                "Passed parameter in telescope.txt '%s' not "
                "recognized" % (name))

    def _store_param_vals(self):
        """ Evaluate telescope parameters """
        self._log.log(
            "Evaluating parameters for telescope %s"
            % (self.dir))
        # Store telescope parameters
        self._param_vals = {}
        for k in self._param_dict:
            self._param_vals[k] = self._param_samp(self._param_dict[k])
        # Store telescope name
        self._param_vals["tel_name"] = (
            self.dir.rstrip(os.sep).split(os.sep)[-1])
        return

    def _store_cams(self):
        """ Store cameras """
        self._log.log(
            "Storing cameras in telescope %s"
            % (self.dir))
        # Gather directories in telescope, ignoring 'config' and 'paramVary'
        cam_dirs = sorted(gb.glob(os.path.join(self.dir, '*'+os.sep)))
        cam_dirs = [x for x in cam_dirs
                    if 'config' not in x and 'paramVary' not in x]
        # Check that at least one camera is present
        if len(cam_dirs) == 0:
            self._log.err("Zero cameras in '%s'" % (self.dir))
        cam_names = [cam_dir.split(os.sep)[-2] for cam_dir in cam_dirs]
        # Check for duplicate camera names
        if len(cam_names) != len(set(cam_names)):
            self._log.err("Duplicate camera name in '%s'" % (self.dir))
        # Store camera objects
        self.cams = {}
        for i in range(len(cam_names)):
            cam_name_upper = cam_names[i].replace(" ", "").strip().upper()
            self.cams.update({cam_name_upper:
                              cm.Camera(self, cam_dirs[i])})
        return

    def _param_samp(self, param):
        """ Sample telescope parameter """
        if self.exp.sim.param("nexp") == 1:
            return param.get_med()
        else:
            return param.sample(nsample=1)

    def _handle_atm(self):
        """ Handle the atmosphere for balloons and space """
        # Store custom atmosphere
        if 'CUST' in self.param('site').upper():
            self._custom_atm()
        else:
            self._param_vals['atm_file'] = None
            # Force PWV and elevation for balloon and space missions
            if self.param('site').upper() == 'MCMURDO':
                self._param_vals['pwv'] = 0
            elif self.param('site').upper() == 'SPACE':
                self._param_vals['pwv'] = None
                self._param_vals['elev'] = None
        return

    def _custom_atm(self):
        """ Load a custom atmosphere spectrum """
        # Load potential ATM files
        atm_files = sorted(gb.glob(
            os.path.join(self._config_dir, 'atm*.txt')))
        # Check that at least one ATM file exists
        if len(atm_files) == 0:
            self._log.err(
                "'Site' parameter in '%s' is 'CUST', but no custom \
                atmosphere file  in '%s'"
                % (self._tel_file, self._config_dir))
        # Check for more than one ATM files
        elif len(atm_files) > 1:
            self._log.err(
                "'Site' parameter in '%s' is 'CUST', but more than one custom \
                atmosphere file was found in '%s'"
                % (self._tel_file, self._config_dir))
        # Store the atm file for use within the Sky object
        else:
            self._log.log(
                "** Using custom ATM file '%s' for telescope %s"
                % (atm_files[0], self.dir))
            self._param_vals['atm_file'] = atm_files[0]
            self._param_vals['site'] = "CUST"
            self._param_vals['elev'] = None
            self._param_vals['pwv'] = None
        return
