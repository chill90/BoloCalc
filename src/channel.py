# Built-in modules
import numpy as np
import glob as gb
import collections as cl
import os

# BoloCalc modules
import src.band as bd
import src.detectorArray as da
import src.observationSet as ob
import src.parameter as pr
import src.unit as un


class Channel:
    """
    Channel object contains the src.DetectorArray object and
    channel-specific parameters

    Args:
    cam (src.Camera): Camera object
    inp_dict (dict): dictionary of channel parameters
    band_file (str): band file for this channel. Defaults to 'None'

    Attributes:
    cam (src.Camera): where the 'cam' arg is stored
    det_arr (src.DetectorArray): the DetectorArray object for this channel
    det_band (src.Band): detector band for this channel
    band_mask (list): frequencies for which the band is defined
    elev_dict (dict): pixel elevation distribution for ObservationSet object
    det_dict (dict): detector-specific parameters for DetectorArray object
    elem (list): sky, optics, and detector element names
    emis (list): sky, optics, and detector element absorbtivities
    tran (list): sky, optics, and detector element tranmissions
    temp (list): sky, optics, and detector element temperatures
    """
    def __init__(self, cam, inp_dict, band_file=None):
        # Store passed parameters
        self.cam = cam
        self._inp_dict = inp_dict
        self._band_file = band_file
        self._name = "%s%d" % (
            self.cam.param("cam_name"), int(self._inp_dict["Band ID"]))
        self._log = self.cam.tel.exp.sim.log
        self._load = self.cam.tel.exp.sim.load
        self._nexp = self.cam.tel.exp.sim.param("nexp")
        self._fres = self.cam.tel.exp.sim.param("fres")
        self._ndet = self.cam.tel.exp.sim.param("ndet")

        self._log.log(
            "Generating realization for channel %s" % (self._name))
        # Store the channel parameters in a dictionary
        self._store_param_dict()
        # Elevation distribution for pixels in the camera
        self._store_elev_dict()
        # Store frequencies to integrate over and detector band
        self._store_band()

        self._log.log(
            "Generating DetectorArray and ObservationSet objects "
            "in channel %s" % (self._name))
        # Store the detector array object
        self.det_arr = da.DetectorArray(self)
        # Store the observation set object
        self._obs_set = ob.ObservationSet(self)

    # ***** Public Methods *****
    def evaluate(self):
        """ Evaluate channel """
        self._log.log(
            "Evaluating channel %s%d"
            % (self._name))
        # Generate parameter values
        self._store_param_vals()
        # Evaluate focal plane
        self.det_arr.evaluate()
        # Evaluate observations
        self._obs_set.evaluate()

        # Build the elem, emis, tran, and temp arrays
        self._calculate()

    def param(self, param):
        """
        Return parameter value for this channel

        Args:
        param (str): parameter name
        """
        if param in self._param_vals.keys():
            return self._param_vals[param]
        else:
            return self._cam_param(param)

    def set_param(self, param, new_val):
        """
        Set parameter value for this channel

        Args:
        param (str): parameter name
        val (str, int, float): new value for parameter
        """
        self._param_vals[param] = new_val
        return

    def change_param(self, param, new_val):
        """
        Change telescope parameter values

        Args:
        param (str): name of parameter or param dict key
        new_val (float): new value to set the parameter to
        """
        self._log.log(
            "Changing channel '%s' parameter '%s' to new value '%s'"
            % (self._name, str(param), str(new_val)))
        # Check if the parameter label is by name
        if (param not in self._param_dict.keys() and
           param not in self.det_dict.keys()):
            if param in self._param_names.keys():
                return (self._param_dict[
                        self._param_names[param]].change(new_val))
            elif param in self._det_param_names.keys():
                return (self.det_dict[
                        self._det_param_names[param]].change(new_val))
            else:
                self._log.err(
                    "Parameter '%s' not understood by Channel.change_param()"
                    % (str(param)))
        # Check if the parameter label is by dict key
        elif param in self._param_dict.keys():
            return self._param_dict[param].change(new_val)
        elif param in self.det_dict.keys():
            return self.det_dict[param].change(new_val)
        # Throw an error if they parameter cannot be identified
        else:
            self._log.err(
                "Parameter '%s' not understood by Channel.change_param()"
                % (str(param)))

    def get_param(self, param):
        """ Return parameter median value """
        return self._param_dict[param].get_med()

    # ***** Helper Methods *****
    def _cam_param(self, param):
        return self.cam.param(param)

    def _param_samp(self, param):
        band_id = self.param("band_id")
        if self._nexp == 1:
            return param.get_avg(band_id)
        else:
            return param.sample(band_id=band_id, nsample=1)

    def _store_param_dict(self):
        """ Store Parameter objects for channel """
        # Dictionary of the channel Parameter objects
        self._param_dict = {
            "det_per_waf": pr.Parameter(
                self._log, "Num Det per Wafer",
                self._inp_dict["Num Det per Wafer"],
                min=0.0, max=np.inf),
            "waf_per_ot": pr.Parameter(
                self._log, "Num Waf per OT",
                self._inp_dict["Num Waf per OT"],
                min=0.0, max=np.inf),
            "ot": pr.Parameter(
                self._log, "Num OT",
                self._inp_dict["Num OT"],
                min=0.0, max=np.inf),
            "yield": pr.Parameter(
                self._log, "Yield",
                self._inp_dict["Yield"],
                min=0.0, max=1.0),
            "pix_sz": pr.Parameter(
                self._log, "Pixel Size",
                self._inp_dict["Pixel Size"],
                min=0.0, max=np.inf),
            "wf": pr.Parameter(
                self._log, "Waist Factor",
                self._inp_dict["Waist Factor"],
                min=2.0, max=np.inf)}

        # Dictionary of the detector Parameter objects
        # These are evaluated at the detector object level
        self.det_dict = {
            "bc": pr.Parameter(
                self._log, "Band Center",
                self._inp_dict["Band Center"],
                min=0.0, max=np.inf),
            "fbw": pr.Parameter(
                self._log, "Fractional BW",
                self._inp_dict["Fractional BW"],
                min=0.0, max=2.0),
            "det_eff": pr.Parameter(
                self._log, "Det Eff",
                self._inp_dict["Det Eff"],
                min=0.0, max=1.0),
            "psat": pr.Parameter(
                self._log, "Psat",
                self._inp_dict["Psat"],
                min=0.0, max=np.inf),
            "psat_fact": pr.Parameter(
                self._log, "Psat Factor",
                self._inp_dict["Psat Factor"],
                min=0.0, max=np.inf),
            "n": pr.Parameter(
                self._log, "Carrier Index",
                self._inp_dict["Carrier Index"],
                min=0.0, max=np.inf),
            "tc": pr.Parameter(
                self._log, "Tc", self._inp_dict["Tc"],
                min=0.0, max=np.inf),
            "tc_frac": pr.Parameter(
                self._log, "Tc Fraction",
                self._inp_dict["Tc Fraction"],
                min=0.0, max=np.inf),
            "nei": pr.Parameter(
                self._log, "SQUID NEI",
                self._inp_dict["SQUID NEI"],
                min=0.0, max=np.inf),
            "bolo_r": pr.Parameter(
                self._log, "Bolo Resistance",
                self._inp_dict["Bolo Resistance"],
                min=0.0, max=np.inf),
            "read_frac": pr.Parameter(
                self._log, "Read Noise Frac",
                self._inp_dict["Read Noise Frac"],
                min=0.0, max=1.0)}

        # Newly added parameters to BoloCalc
        # checked separately for backwards compatibility
        if "Flink" in self._inp_dict.keys():
            self.det_dict["flink"] = pr.Parameter(
                self._log, "Flink", self._inp_dict["Flink"],
                min=0.0, max=np.inf)
        else:
            self.det_dict["flink"] = pr.Parameter(
                self._log, "Flink", "NA",
                min=0.0, max=np.inf)
        if "G" in self._inp_dict.keys():
            self.det_dict["g"] = pr.Parameter(
                self._log, "G", self._inp_dict["G"],
                min=0.0, max=np.inf)
        else:
            self.det_dict["g"] = pr.Parameter(
                self._log, "G", "NA",
                min=0.0, max=np.inf)
        if "Responsivity Factor" in self._inp_dict.keys():
            self.det_dict["sfact"] = pr.Parameter(
                self._log, "Responsivity Factor",
                self._inp_dict["Responsivity Factor"],
                min=0.0, max=np.inf)
        else:
            self.det_dict["sfact"] = pr.Parameter(
                self._log, "Responsivity Factor", "NA",
                min=0.0, max=np.inf)
        # Dictionary for ID-ing parameters for changing
        self._param_names = {
            param.name: pid
            for pid, param in self._param_dict.items()}
        self._det_param_names = {
            param.name: pid
            for pid, param in self.det_dict.items()}
        return

    def _store_param_vals(self):
        """ Evaluate channel parameters """
        self._log.log(
            "Evaluating parameters for channel %s"
            % (self._name))
        self._param_vals = {}
        # Store ID parameters first
        self._param_vals["band_id"] = int(self._inp_dict["Band ID"])
        self._param_vals["pix_id"] = int(self._inp_dict["Pixel ID"])
        self._param_vals["ch_name"] = (self.cam.param("cam_name") +
                                       str(self.param("band_id")))
        # Store channel parameters
        for k in self._param_dict:
            self._param_vals[k] = self._param_samp(
                self._param_dict[k])
        # Store median values for detector-specific parameters
        # Input distributions will be sampled at the detector object level
        for k in self.det_dict:
            self._param_vals[k] = self.det_dict[k].get_med()
        # Derived channel parameters
        self._param_vals["ndet"] = int(self.param("det_per_waf") *
                                       self.param("waf_per_ot") *
                                       self.param("ot"))
        if self.cam.tel.exp.sim.param("ndet") is "NA":
            self._param_vals["cdet"] = self._param_vals["ndet"]
        else:
            self._param_vals["cdet"] = self.cam.tel.exp.sim.param("ndet")
        # To be stored by specific optic
        self._param_vals["ap_eff"] = None
        self._param_vals["edge_tap"] = None
        return

    def _store_elev_dict(self):
        """ Store distribution of pixel elevations w.r.t. boresight """
        # Load possible pixel elevation files
        elev_files = sorted(gb.glob(os.path.join(
            self.cam.config_dir, "elevation.txt")))
        # Ignore pixel elevations if no file is found
        if len(elev_files) == 0:
            self.elev_dict = None
        # Check that only one distribution file exists
        elif len(elev_files) > 1:
            self._log.err(
                "More than one pixel elevation distribution for camera '%s'"
                % (self.cam.name))
        # Load pixel elevation distribution into dictionary
        else:
            self.elev_dict = self._load.elevation(elev_files[0])
            self._log.log(
                "Using pixel elevation distribution '%s' in camera '%s"
                % (elev_files[0], self.cam.param("cam_name")))
        return

    def _store_band(self):
        """ Store detector band """
        self._log.log(
            "Storing detector band for channel %s" % (self._name))
        if self._band_file is not None:
            self._log.log(
                "Using custom band for channel %s" % (self._name))
            # Use defined band
            self.det_band = bd.Band(self._log, self._load, self._band_file)
            # Frequencies to integrate over
            lo_freq = np.amin(self.det_band.freqs)
            hi_freq = np.amax(self.det_band.freqs)
            self.freqs = np.arange(
                lo_freq, hi_freq + self._fres, self._fres)
            # Interpolate band using defined frequencies
            self.det_band.interp_freqs(self.freqs)
        else:
            self.det_band = None
            # Define edges of frequencies to integrate over
            # Use wider than nominal band by 30% to cover tolerances/errors
            lo_freq = (
                self.det_dict["bc"].get_avg() *
                (1. - 0.65 * self.det_dict["fbw"].get_avg()))
            hi_freq = (
                self.det_dict["bc"].get_avg() *
                (1. + 0.65 * self.det_dict["fbw"].get_avg()))
            self.freqs = np.arange(
                lo_freq, hi_freq + self._fres, self._fres)
        return

    def _calculate(self):
        """ Calculate sky + optics + detector emiss/effic/temp arrays """
        # Load the calculated optical parameters
        elem, emis, tran, temp = self.cam.opt_chn.evaluate(self)
        # Concatenate the elem/emiss/effic/temp arrays, sky to det
        self.elem = np.array(
            [[obs.elem[i] + elem + self.det_arr.dets[i].elem
             for i in range(self._ndet)]
             for obs in self._obs_set.obs_arr]).astype(np.str)
        self.emis = np.array(
            [[obs.emis[i] + emis + self.det_arr.dets[i].emis
             for i in range(self._ndet)]
             for obs in self._obs_set.obs_arr]).astype(np.float)
        self.tran = np.array(
            [[obs.tran[i] + tran + self.det_arr.dets[i].tran
             for i in range(self._ndet)]
             for obs in self._obs_set.obs_arr]).astype(np.float)
        self.temp = np.array(
            [[obs.temp[i] + temp + self.det_arr.dets[i].temp
             for i in range(self._ndet)]
             for obs in self._obs_set.obs_arr]).astype(np.float)
        return
