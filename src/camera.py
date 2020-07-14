# Built-in modules
import numpy as np
import glob as gb
import os

# BoloCalc modules
import src.parameter as pr
import src.opticalChain as oc
import src.channel as ch


class Camera:
    """
    Camera object holds the optical chain and channel data for a defined
    camera

    Args:
    tel (src.Telescope): parent Telescope object
    inp_dir (str): camera directory

    Attributes:
    dir (str): where arg 'inp_dir' is stored
    config_dir (str): configuration directory for this camera
    name (str): camera name

    Parents:
    tel (src.Telescope): Telescope object

    Children:
    chs (dict): dictionary of Channel objects
    opt_chn (src.OpticalChain): OpticalChain object
    """
    def __init__(self, tel, inp_dir):
        # Store passed parameters
        self.tel = tel
        self.dir = inp_dir
        self.name = self.dir.split(os.sep)[-2]
        self._log = self.tel.exp.sim.log
        self._load = self.tel.exp.sim.load
        self._std_params = self.tel.exp.sim.std_params
        self._nexp = self.tel.exp.sim.param("nexp")

        self._log.log("Generating camera realization from %s" % (self.dir))
        # Check whether camera and config dir exists
        self._check_dirs()
        # Store camera parameters into a dictionary
        self._store_param_dict()

        self._log.log("Generating OpticalChain object for camera %s"
                      % (self.dir))
        # Generate channels
        self._store_chs()
        # Generate optical chain
        self.opt_chn = oc.OpticalChain(self)

    # ***** Public Methods *****
    def evaluate(self):
        """ Evaluate camera """
        self._log.log("Evaluating camera %s" % (self.dir))
        # Evaluate camera parameters
        self._store_param_vals()
        # Evaluate channels
        self._log.log("Evaluating channels in camera %s" % (self.dir))
        for chan in self.chs.values():
            chan.evaluate()
        return

    def param(self, param):
        """
        Return camera parameter value

        Args:
        param (str): parameter to return
        """
        return self._param_vals[param]

    def change_param(self, param, new_val):
        """
        Change camera parameter values

        Args:
        param (str): name of parameter or param dict key
        new_val (float): new value to set the parameter to
        """
        self._log.log(
            "Changing %s camera parameter '%s' to new value '%s'"
            % (self.dir, str(param), str(new_val)))
        # Check if the parameter label is by name
        if param not in self._param_dict.keys():
            caps_param = param.replace(" ", "").strip().upper()
            if caps_param in self._param_names.keys():
                return (self._param_dict[
                        self._param_names[caps_param]].change(new_val))
            else:
                self._log.err(
                    "Parameter '%s' not understood by Camera.change_param()"
                    % (str(param)))
        # Check if the parameter label is by dict key
        elif param in self._param_dict.keys():
            return self._param_dict[param].change(new_val)
        # Throw an error if they parameter cannot be identified
        else:
            self._log.err(
                    "Parameter '%s' not understood by Camera.change_param()"
                    % (str(param)))
        return

    def get_param(self, param):
        """ Return parameter median value """
        return self._param_dict[param].get_med()

    # ***** Helper Methods *****
    def _check_dirs(self):
        """ Check that passed camera directory exists with a config dir """
        # Check that camera directory exists
        if not os.path.isdir(self.dir):
            self._log.err("Camera dir '%s' does not exist" % (self.dir))
        # Check whether configuration directory exists
        self.config_dir = os.path.join(self.dir, 'config')
        if not os.path.isdir(self.config_dir):
            self._log.err(
                "Camera config dir '%s' does not exist"
                % (self.config_dir))
        return

    def _store_param_dict(self):
        """ Store Parameter objects for camera """
        # Check that the camera parameter file exists
        cam_file = os.path.join(self.config_dir, 'camera.txt')
        if not os.path.isfile(cam_file):
            self._log.err(
                "Camera file '%s' does not exist" % (cam_file))
        # Load camera file into a dictionary
        self._inp_dict = self._load.camera(cam_file)

        # Dictionary of the camera Parameter objects
        self._param_dict = {
            "bore_elev": self._store_param("Boresight Elevation"),
            "opt_coup": self._store_param("Optical Coupling"),
            "fnum": self._store_param("F Number"),
            "tb": self._store_param("Bath Temp")}
        # Dictionary for ID-ing parameters for changing
        self._param_names = {
            param.caps_name: pid
            for pid, param in self._param_dict.items()}
        return

    def _store_param(self, name):
        """ Store src.Parameter objects for this camera """
        cap_name = name.replace(" ", "").strip().upper()
        if cap_name in self._std_params.keys():
            return pr.Parameter(
                self._log, self._inp_dict[cap_name],
                std_param=self._std_params[cap_name])
        else:
            self._log.err(
                "Passed parameter in camera.txt '%s' not "
                "recognized" % (name))

    def _store_chs(self):
        """ Store the channels in this camera """
        # Generate dictionary of channel bands
        self._gen_band_dict(
            os.path.join(self.config_dir, "Bands", "Detectors"))
        # Check that the channels file exists
        chn_file = os.path.join(
            self.config_dir, "channels.txt")
        if not os.path.exists(chn_file):
            self._log.err(
                "Channel file '%s' for camera %s does not exist"
                % (chn_file, self.dir))
        # Generate channel dictionary from channels.txt file
        self._log.log(
            "Generating channel dictionaries from '%s'"
            % (chn_file))
        chan_dicts = self._load.channels(chn_file)
        # Store channel objects
        self._log.log(
            "Generating channel objects for camera %s"
            % (self.dir))
        self.chs = {}
        for chan_dict in chan_dicts.values():
            band_id_upper = (
                chan_dict["BANDID"].replace(" ", "").strip().upper())
            # Check for duplicate band names
            if band_id_upper in self.chs.keys():
                self._log.err(
                    "Multiple bands named '%s' in camera '%s'"
                    % (chan_dict["Band ID"], self.dir))
            # Check for band file for this channel
            cam_name = str(self.dir.rstrip(os.sep).split(os.sep)[-1])
            band_name = (cam_name + "_" + str(band_id_upper)).upper()
            if (self._band_dict is not None and
               band_name in self._band_dict.keys()):
                band_file = self._band_dict[band_name]
            else:
                band_file = None
            # Store the channel object
            self.chs.update(
                {band_id_upper:
                 ch.Channel(self, chan_dict, band_file)})
        return

    def _gen_band_dict(self, band_dir):
        """ Generate a dictionary of band files given an input directory """
        # Gather potential band files in the passed directory
        band_files = sorted(gb.glob(os.path.join(band_dir, '*')))
        band_files = [band_file for band_file in band_files
                      if '~' not in band_file]
        # Check that at least one band file was found
        if len(band_files):
            # Array of potential band names, ignoring temp files
            name_arr = [os.path.split(nm)[-1].split('.')[0]
                        for nm in band_files if "~" not in nm]
            # Create a dictionary of band files, if there are any
            if len(name_arr):
                self._band_dict = {name_arr[i].strip().upper(): band_files[i]
                                   for i in range(len(name_arr))}
            # Otherwise, set the dict variable to None
            else:
                self._band_dict = None
        else:
            self._band_dict = None
        return

    def _store_param_vals(self):
        """ Evaluate camera parameters """
        self._log.log(
            "Evaluating parameters for camera %s"
            % (self.dir))
        # Store camera parameters
        self._param_vals = {}
        for k in self._param_dict:
            self._param_vals[k] = self._param_samp(self._param_dict[k])
        # Generate camera name
        self._param_vals["cam_name"] = (
            self.dir.rstrip(os.sep).split(os.sep)[-1])
        return

    def _param_samp(self, param):
        """ Sample camera parameter """
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self._nexp == 1:
            return param.get_med()
        else:
            return param.sample(nsample=1)
