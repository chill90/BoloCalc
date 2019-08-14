# Built-in modules
import numpy as np
import glob as gb
import collections as cl
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
    tel (src.Telescope): Telescope object
    inp_dir (str): camera directory

    Attributes:
    tel (src.Telescope): where arg 'tel' is stored
    dir (str): where arg 'inp_dir' is stored
    name (str): camera name
    opt_chn (src.OpticalChain): OpticalChain object
    chs (dict): dictionary of Channel objects
    pixs (dict): dictionary of Channel objects grouped by pixel
    config_dir (str): configuration directory for this camera
    """
    def __init__(self, tel, inp_dir):
        # Store passed parameters
        self.tel = tel
        self.dir = inp_dir
        self._log = self.tel.exp.sim.log
        self._load = self.tel.exp.sim.load
        self._nexp = self.tel.exp.sim.param("nexp")

        # Check whether this camera exists
        self._check_dirs()

        # Store camera parameters into a dictionary
        self._store_param_dict()
        # Generate optical chain
        self.opt_chn = oc.OpticalChain(self)
        # Generate channels
        self._store_chs()

    # ***** Public Methods *****
    def evaluate(self):
        # Evaluate camera parameters
        self._store_param_vals()
        # Evaluate channels, which also evaluate the optical chain
        for ch in self.chs.values():
            ch.evaluate()
        return

    def param(self, param):
        """
        Return camera parameter value

        Args:
        param (str): parameter to return
        """
        return self._param_vals[param]

    def change_param(self, param, new_val):
        self._param_dict[param].change(new_val)
        return

    def get_param(self, param):
        return self._param_dict[param].get_avg()

    # ***** Helper Methods *****
    def _gen_band_dict(self, band_dir):
        band_files = sorted(gb.glob(os.path.join(band_dir, '*')))
        if len(band_files):
            name_arr = [os.path.split(nm)[-1].split('.')[0]
                        for nm in band_files if "~" not in nm]
            if len(name_arr):
                self._band_dict = {name_arr[i].strip(): band_files[i]
                                   for i in range(len(name_arr))}
            else:
                self._band_dict = None
        else:
            self._band_dict = None
        return

    def _param_samp(self, param):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self._nexp == 1:
            return param.get_avg()
        else:
            return param.sample(nsample=1)

    def _store_param_dict(self):
        cam_file = os.path.join(self.config_dir, 'camera.txt')
        if not os.path.isfile(cam_file):
            self._log.err(
                "Camera file '%s' does not exist" % (cam_file))
        else:
            params = self._load.camera(cam_file)
            self._param_dict = {
                "bore_elev": pr.Parameter(
                    self._log, "Boresight Elevation",
                    params["Boresight Elevation"], min=-40.0, max=40.0),
                "opt_coup": pr.Parameter(
                    self._log, "Optical Coupling",
                    params["Optical Coupling"], min=0.0, max=1.0),
                "fnum": pr.Parameter(
                    self._log, "F Number",
                    params["F Number"], min=0.0, max=np.inf),
                "tb": pr.Parameter(
                    self._log, "Bath Temp",
                    params["Bath Temp"], min=0.0, max=np.inf)}
        return

    def _store_param_vals(self):
        self._param_vals = {}
        for k in self._param_dict:
            self._param_vals[k] = self._param_samp(self._param_dict[k])
        # Generate additional camera parameters
        self._param_vals["cam_name"] = (
            self.dir.rstrip(os.sep).split(os.sep)[-1])
        return

    def _check_dirs(self):
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

    def _store_chs(self):
        self._gen_band_dict(
            os.path.join(self.config_dir, "Bands", "Detectors"))
        chn_file = os.path.join(
            self.config_dir, "channels.txt")
        chan_dicts = self._load.channel(chn_file)
        self.chs = cl.OrderedDict({})
        for chan_dict in chan_dicts:
            if chan_dict["Band ID"] in self.chs.keys():
                self._log.err(
                    "Multiple bands named '%s' in camera '%s'"
                    % (chan_dict["Band ID"], self.dir))
            cam_name = str(self.dir.rstrip(os.sep).split(os.sep)[-1])
            band_name = (cam_name + str(chan_dict["Band ID"]))
            if band_name in self._band_dict.keys():
                band_file = self._band_dict[band_name]
            else:
                band_file = None
            self.chs.update(
                {chan_dict["Band ID"].strip():
                 ch.Channel(self, chan_dict, band_file)})
