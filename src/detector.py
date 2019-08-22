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

        # Store static arrays
        self.elem = ["Detector"]
        self.emis = [[0.000 for f in self._ch.freqs]]
        return

    # ***** Public Methods *****
    def evaluate(self, band=None):
        self._band_id = self._ch.param("band_id")
        self._tb = self._ch.cam.param("tb")
        # Re-store dictionary
        self._store_param_dict()
        # Evaluate detector parameters
        self._store_param_vals()
        # Evaluate transmission
        if band is not None:
            self._tran = band
            self._tran = np.where(self._tran < 1, self._tran, 1.)
            self._tran = np.where(self._tran > 0, self._tran, 0.)
        else:
            # Default to top hat band
            self._tran = [self.param("det_eff")
                          if f > self.param("flo") and f < self.param("fhi")
                          else 0. for f in self._ch.freqs]
        # Store bandwidth
        self._store_bw(band)

        # Store transmission and temperature
        self.tran = [self._tran]
        self.temp = [[self._tb for f in self._ch.freqs]]
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
        self._param_vals = {}
        for k in self._param_dict.keys():
            self._param_vals[k] = self._param_samp(self._param_dict[k])
        self._param_vals["tb"] = self._ch.cam.param("tb")
        # Calculate bath temperature if not explicitly defined
        if "NA" in str(self.param("tc")):
            if "NA" in str(self.param("tc_frac")):
                self._log.err("Both 'Tc' and 'Tc Frac' undefined for channel \
                               '%s' in camera '%s'" % (
                                   self._ch.name,
                                   self._ch.cam.dir))
            else:
                self._param_vals["tc"] = (
                    self._tb *
                    self._param_vals("tc_frac"))
        # Calculte bandwidth
        self._param_vals["flo"], self._param_vals["fhi"] = (
            self._phys.band_edges(
                self.param("bc"), self.param("fbw")))
        return

    def _store_bw(self, band=None):
        if band is not None:
            # Define band edges to be -3 dB point
            tran = self._tran
            max_tran = np.amax(tran)
            lo_point = np.argmin(
                abs(tran[:len(tran)//2] - 0.5 * max_tran))
            hi_point = np.argmin(
                abs(tran[len(tran)//2:] - 0.5 * max_tran)) + len(tran)//2
            f_lo = self._ch.freqs[lo_point]
            f_hi = self._ch.freqs[hi_point]
        else:
            # Define band edges
            # Band mask edges defined using band center and fractional BW
            f_lo = self.param("bc") * (1. - 0.50 * self.param("fbw"))
            f_hi = self.param("bc") * (1. + 0.50 * self.param("fbw"))
        self._param_vals["bw"] = f_hi - f_lo
        self.band_mask = (self._ch.freqs > f_lo) * (self._ch.freqs < f_hi)
        return
