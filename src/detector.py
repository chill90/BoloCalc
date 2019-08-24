# Built-in modules
import numpy as np


class Detector:
    """
    Detector object samples and holds the detector parameters

    Args:
    det_arr (src.DetectorArray): DetectorArray object
    band (list): band transmission. Defaults to None.

    Attributes:
    det_arr (src.DetectorArray): where 'det_arr' arg is stored
    elem (list): detector name of optical element 'Detector'
    emis (list): detector emissivity vs frequency
    tran (list): detector transmission vs frequency
    temp (list): detector temperatrue
    """
    def __init__(self, det_arr):
        # Store passed parameters
        self.det_arr = det_arr
        self._ch = self.det_arr.ch
        self._log = self._ch.cam.tel.exp.sim.log
        self._phys = self._ch.cam.tel.exp.sim.phys
        self._ndet = self._ch.cam.tel.exp.sim.param("ndet")

        # Generate detector parameters
        self._store_param_dict()

        # Minimum allowed Tc - Tb [K]
        self._min_tc_tb_diff = 0.010

        # Store static arrays
        self.elem = ["Detector"]
        self.emis = [[0.000 for f in self._ch.freqs]]
        return

    # ***** Public Methods *****
    def evaluate(self, band=None):
        # Band ID
        self._band_id = self._ch.param("band_id")
        # Re-store dictionary to reflect ch and cam changes
        self._store_param_dict()
        # Evaluate detector parameters
        self._store_param_vals()
        # Evaluate bandwidth
        self._store_bw(band)
        # Evaluate transmission
        self._store_band(band)
        # Store transmission and temperature
        self.tran = [self.band]
        self.temp = [[self.param("tb") for f in self._ch.freqs]]
        return

    def param(self, param):
        return self._param_vals[param]

    # ***** Helper Methods *****
    def _param_samp(self, param):
        if self._ndet == 1:
            return param.get_avg(band_id=self._band_id)
        else:
            return param.sample(band_id=self._band_id, nsample=1)

    def _store_param_dict(self):
        self._param_dict = self._ch.det_dict
        return

    def _store_param_vals(self):
        # Sample detector parameters
        self._param_vals = {}
        for k in self._param_dict.keys():
            self._param_vals[k] = self._param_samp(self._param_dict[k])

        # Store bath and transition temperature
        self._param_vals["tb"] = self._ch.cam.param("tb")
        if "NA" in str(self.param("tc")):
            if "NA" in str(self.param("tc_frac")):
                self._log.err(
                    "Both 'Tc' and 'Tc Frac' undefined for channel "
                    "'%s' in camera '%s'"
                    % (self._ch.name, self._ch.cam.dir))
            else:
                self._param_vals["tc"] = (
                    self._tb *
                    self._param_vals("tc_frac"))
        else:
            tc_tb_diff = self._param_vals["tc"] - self._param_vals["tb"]
            if tc_tb_diff < self._min_tc_tb_diff:
                self._log.wrn(
                    "Tc - Tb < %d mK for a sampled detector in channel "
                    "'%s' in camera '%s'. Setting Tc = Tb + %d mK for this "
                    "detector sample"
                    % (self._min_tc_tb_diff, self._ch.name, self._ch.cam.dir,
                       self._min_tc_tb_diff))
                self._param_vals["tc"] = (
                    self._param_vals["tb"] + self._min_tc_tb_diff)

        return

    def _store_band(self, band=None):
        freqs = self._ch.freqs
        # Define top-hat band
        if self.param("det_eff") is not "NA":
            top_hat = [
                self.param("det_eff")
                if (f >= self.param("flo") and f < self.param("fhi"))
                else 0. for f in freqs]
        else:
            top_hat = None

        # Scale and store the input band transmission
        if band is not None:
            if top_hat is not None:
                # Scale the band transmission to the sampled det_eff value
                scale_fact = (
                    np.trapz(top_hat, freqs) / np.trapz(band, freqs))
            else:
                scale_fact = 1.
            self.band = scale_fact * band
            # Maximum allowed transmission is 1
            self.band = np.where(self.band < 1, self.band, 1.)
            self.band = np.where(self.band > 0, self.band, 0.)
        # Or store a top-hat band
        else:
            if top_hat is None:
                self._log.err(
                    "Neither 'Detector Eff' nor detector band defined for "
                    "channel '%s' in camera '%s'"
                    % (self._ch.name, self._ch.cam.dir))
            else:
                # Default to top hat band
                self.band = top_hat

    def _store_bw(self, band=None):
        freqs = self._ch.freqs
        if band is not None:
            # Define band edges to be -3 dB point
            tran = band
            max_tran = np.amax(tran)
            lo_point = np.argmin(
                abs(tran[:len(tran)//2] - 0.5 * max_tran))
            hi_point = np.argmin(
                abs(tran[len(tran)//2:] - 0.5 * max_tran)) + len(tran)//2
            self._param_vals["flo"] = freqs[lo_point]
            self._param_vals["fhi"] = freqs[hi_point]
        else:
            # Define band edges using band center and fractional BW
            self._param_vals["flo"] = (
                self.param("bc") * (1. - 0.5 * self.param("fbw")))
            self._param_vals["fhi"] = (
                self.param("bc") * (1. + 0.5 * self.param("fbw")))

        # Store bandwidth
        self._param_vals["bw"] = self.param("fhi") - self.param("flo")
        self._param_vals["bc"] = (self.param("fhi") + self.param("flo")) / 2.
        self.band_mask = [
            1. if f >= self.param("flo") and f < self.param("fhi")
            else 0. for f in freqs]

        return
