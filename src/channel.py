# Built-in modules
import numpy as np
import glob as gb
import os

# BoloCalc modules
import src.band as bd
import src.detectorArray as da
import src.observationSet as ob
import src.parameter as pr


class Channel:
    """
    Channel object contains the src.DetectorArray object and
    channel-specific parameters

    Args:
    cam (src.Camera): Camera object
    inp_dict (dict): dictionary of channel parameters
    band_file (str): band file for this channel. Defaults to 'None'

    Attributes:
    band_mask (list): frequencies for which the band is defined
    elev_dict (dict): pixel elevation distribution for ObservationSet object
    det_dict (dict): detector-specific parameters for DetectorArray object
    elem (list): sky, optics, and detector element names
    emis (list): sky, optics, and detector element absorbtivities
    tran (list): sky, optics, and detector element transmissions
    temp (list): sky, optics, and detector element temperatures

    Parents:
    cam (src.Camera): Camera object

    Children:
    det_arr (src.DetectorArray): the DetectorArray object for this channel
    det_band (src.Band): detector band for this channel
    """
    def __init__(self, cam, inp_dict, band_file=None):
        # Store passed parameters
        self.cam = cam
        self._inp_dict = inp_dict
        self.band_id = "%s" % (self._inp_dict["BANDID"])
        self._store_band_index()
        self._band_file = band_file
        self._log = self.cam.tel.exp.sim.log
        self._load = self.cam.tel.exp.sim.load
        self._phys = self.cam.tel.exp.sim.phys
        self._std_params = self.cam.tel.exp.sim.std_params
        self._nexp = self.cam.tel.exp.sim.param("nexp")
        self._fres = self.cam.tel.exp.sim.param("fres")
        self._ndet = self.cam.tel.exp.sim.param("ndet")

        self._log.log("Generating realization for channel Band_ID '%s'"
                      % (self.band_id))
        # Store the channel parameters in a dictionary
        self._store_param_dict()
        # Elevation distribution for pixels in the camera
        self._store_elev_dict()
        # Store frequencies to integrate over and detector band
        self._store_band()

        # Store the detector array object
        self._log.log("Generating DetectorArray object in channel %s"
                      % (self.band_id))
        self.det_arr = da.DetectorArray(self)
        # Store the observation set object
        self._log.log("Generating ObservationSet object in channel %s"
                      % (self.band_id))
        self._obs_set = ob.ObservationSet(self)

    # ***** Public Methods *****
    def evaluate(self):
        """ Evaluate channel """
        self._log.log("Evaluating channel Band_ID '%s'" % (self.band_id))
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
        Change channel parameter values

        Args:
        param (str): name of parameter or param dict key
        new_val (float): new value to set the parameter to
        """
        self._log.log(
            "Changing channel '%s' parameter '%s' to new value '%s'"
            % (self.param("ch_name"), str(param), str(new_val)))
        # Check if the parameter label is by name
        if (param not in self._param_dict.keys() and
           param not in self.det_dict.keys()):
            caps_param = param.replace(" ", "").strip().upper()
            if caps_param in self._param_names.keys():
                ret_val = (self._param_dict[
                           self._param_names[caps_param]].change(new_val))
            elif caps_param in self._det_param_names.keys():
                ret_val = (self.det_dict[
                           self._det_param_names[caps_param]].change(new_val))
            else:
                self._log.err(
                    "Parameter '%s' not understood by Channel.change_param()"
                    % (str(param)))
        # Check if the parameter label is by dict key
        elif param in self._param_dict.keys():
            ret_val = self._param_dict[param].change(new_val)
        elif param in self.det_dict.keys():
            ret_val = self.det_dict[param].change(new_val)
        # Throw an error if they parameter cannot be identified
        else:
            self._log.err(
                "Parameter '%s' not understood by Channel.change_param()"
                % (str(param)))
        # If the band center or bandwidth is changed, redefine frequencies
        if (param == "bc" or param == "fbw" or
           param == "Band Center" or param == "Fractional BW"):
            self._store_band()
        return ret_val

    def get_param(self, param):
        """ Return parameter median value """
        if param in self._param_dict.keys():
            return self._param_dict[param].get_med()
        elif param in self.det_dict.keys():
            return self.det_dict[param].get_med()
        else:
            self._log.err(
                "Unable to retrieve median value for parameter '%s' "
                "in channel Band_ID = %s" % (str(param), str(self.band_id)))

    # ***** Helper Methods *****
    def _cam_param(self, param):
        """ Return parent camera parameter value """
        return self.cam.param(param)

    def _param_samp(self, param):
        """ Sample channel parameter """
        if self._nexp == 1:
            return param.get_med()
        else:
            return param.sample(nsample=1)

    def _store_param(self, name):
        """ Store src.Parameter objects for this channel """
        cap_name = name.replace(" ", "").strip().upper()
        if cap_name in self._std_params.keys():
            return pr.Parameter(
                self._log, self._inp_dict[cap_name],
                std_param=self._std_params[cap_name])
        else:
            self._log.err(
                "Passed parameter in channel.txt '%s' not "
                "recognized" % (name))

    def _store_param_dict(self):
        """ Store Parameter objects for channel """
        # Dictionary of the channel Parameter objects
        self._param_dict = {
            "det_per_waf": self._store_param("Num Det per Wafer"),
            "waf_per_ot": self._store_param("Num Waf per OT"),
            "ot": self._store_param("Num OT"),
            "yield": self._store_param("Yield"),
            "pix_sz": self._store_param("Pixel Size"),
            "wf": self._store_param("Waist Factor")}

        # Dictionary of the detector Parameter objects
        # These are evaluated at the detector object level
        self.det_dict = {
            "bc": self._store_param("Band Center"),
            "fbw": self._store_param("Fractional BW"),
            "det_eff": self._store_param("Det Eff"),
            "psat": self._store_param("Psat"),
            "psat_fact": self._store_param("Psat Factor"),
            "n": self._store_param("Carrier Index"),
            "tc": self._store_param("Tc"),
            "tc_frac": self._store_param("Tc Fraction"),
            "nei": self._store_param("SQUID NEI"),
            "bolo_r": self._store_param("Bolo Resistance"),
            "read_frac": self._store_param("Read Noise Frac")}

        # Newly added parameters to BoloCalc
        # checked separately for backwards compatibility
        if "FLINK" in self._inp_dict.keys():
            self.det_dict["flink"] = self._store_param("Flink")
        else:
            self.det_dict["flink"] = pr.Parameter(
                self._log, "NA", name="Flink")
        if "G" in self._inp_dict.keys():
            self.det_dict["g"] = self._store_param("G")
        else:
            self.det_dict["g"] = pr.Parameter(
                self._log, "NA", name="G")
        if "RESPFACTOR" in self._inp_dict.keys():
            self.det_dict["sfact"] = self._store_param("Resp Factor")
        else:
            self.det_dict["sfact"] = pr.Parameter(
                self._log, "NA", name="Resp Factor")
        # Dictionary for ID-ing parameters for changing
        self._param_names = {
            param.caps_name: pid
            for pid, param in self._param_dict.items()}
        self._det_param_names = {
            param.caps_name: pid
            for pid, param in self.det_dict.items()}
        return

    def _store_param_vals(self):
        """ Evaluate channel parameters """
        self._log.log(
            "Evaluating parameters for channel Band_ID = '%s'"
            % (self.band_id))
        self._param_vals = {}
        # Store ID parameters first
        self._param_vals["band_id"] = self._inp_dict["BANDID"]
        # self._param_vals["pix_id"] = self._inp_dict["PIXELID"]
        self._param_vals["ch_name"] = (self.cam.param("cam_name") + "_" +
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
        if str(self.cam.tel.exp.sim.param("ndet")) == "NA":
            self._param_vals["cdet"] = self._param_vals["ndet"]
        else:
            self._param_vals["cdet"] = self.cam.tel.exp.sim.param("ndet")
        # Store estimated band center if user-defined band
        if self._band_file is not None and self._bc is not None:
            self._param_vals["bc"] = self._bc
            self._param_vals["cust"] = True
        else:
            self._param_vals["cust"] = False
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
                "** Using pixel elevation distribution '%s'"
                % (elev_files[0]))
        return

    def _store_band(self):
        """ Store detector band """
        self._log.log(
            "Storing detector band for channel Band_ID '%s'"
            % (self.band_id))
        bc = self.det_dict["bc"].get_med()
        fbw = self.det_dict["fbw"].get_med()
        if str(bc).strip().upper() == "BAND" and self._band_file is not None:
            self._log.log(
                "** Using custom band for channel Band_ID '%s'"
                % (self.band_id))
            # Use defined band
            self.det_band = bd.Band(self._log, self._load, self._band_file)
            # Frequencies to integrate over
            lo_freq = np.amin(self.det_band.freqs)
            hi_freq = np.amax(self.det_band.freqs)
            self.freqs = np.arange(
                lo_freq, hi_freq + self._fres, self._fres)
            # Interpolate band using defined frequencies
            self.det_band.interp_freqs(self.freqs)
            # Estimate and store band center
            # Define band "edges" as -3 dB points
            tran = self.det_band.get_avg()[0]
            flo, fhi = self._phys.band_edges(self.freqs, tran)
            self._bc = (fhi + flo) / 2.
        elif isinstance(bc, float) and isinstance(fbw, float):
            self.det_band = None
            # Define edges of frequencies to integrate over
            if fbw < 1.5:
                # Use wider than nominal band by 30% to cover tolerances/errors
                lo_freq = (bc * (1. - 0.65 * fbw))
                hi_freq = (bc * (1. + 0.65 * fbw))
            else:
                lo_freq = 1.
                hi_freq = 2 * bc
            self.freqs = np.arange(
                lo_freq, hi_freq + self._fres, self._fres)
            self._bc = None
        else:
            self._log.err(
                "Problem constructing detector band for channel "
                "Band ID = '%s' using Band Center '%s' and FBW '%s'"
                % (str(self.band_id), str(bc), str(fbw)))
        return

    def _calculate(self):
        """ Calculate sky + optics + detector emiss/effic/temp arrays """
        # Load the calculated optical parameters
        elem, emis, tran, temp = self.cam.opt_chn.evaluate(self)
        # Concatenate the elem/emiss/effic/temp arrays, sky to det
        self.elem = np.array(
            [[obs.elem[i][0] + elem + self.det_arr.dets[i].elem
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

    def _store_band_index(self):
        """ Store band index for this channel """
        self.band_ind = len(self.cam.chs.keys())
        return
