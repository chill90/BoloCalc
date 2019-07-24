# Built-in modules
import numpy as np


class Detector:
    """
    Detector object samples and holds the detector parameters

    Args:
    det_arr (src.DetectorArray): DetectorArray object
    band (list): band transmission. Defaults to None.

    Attributes:
    elem (list): detector name of optical element 'Detector'
    emis (list): detector emissivity vs frequency
    tran (list): detector transmission vs frequency
    temp (list): detector temperatrue
    """
    def __init__(self, det_arr, band=None):
        # Store passed parameters
        self._det_arr = det_arr
        self._band = band
        self._log = self.det_arr.ch.cam.tel.exp.sim.log
        self._phys = self.det_arr.ch.cam.tel.exp.sim.phys
        self._ndet = self.det_arr.ch.cam.tel.exp.sim.param("ndet")
        self._tb = self.det_arr.ch.cam.param("tb")

        # Store detector parameters
        self._store_param_dict()
        self._store_param_vals()

        # Store efficiency
        self._store_eff()

        # Store detector optical parameters
        self.elem = ["Detector"]
        self.emis = [[0.000 for f in self._det_arr.ch.freqs]]
        self.tran = [self._eff]
        self.temp = [[self._tb for f in self._det_arr.ch.freqs]]

    # ***** Public Methods *****
    def param(self, param):
        return self._param_vals[param]

    # ***** Helper Methods *****
    def _param_samp(self, param):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self._ndet == 1:
            return param.getAvg(band_id=self._band_id)
        else:
            return param.sample(band_id=self._band_id, nsample=1)

    def _store_param_dict(self):
        self._param_dict = self._det_arr.ch.det_dict
        return

    def _store_param_vals(self):
        self._param_vals = {}
        for k in self._param_dict.keys():
            self._param_vals[k] = self._param_samp(self._param_dict[k])
        # Calculate bath temperature if not explicitly defined
        if "NA" in self._param_vals["tc"]:
            if "NA" in self._param_vals["tc_frac"]:
                self._log.err("Both 'Tc' and 'Tc Frac' undefined for channel \
                               '%s' in camera '%s'" % (
                                   self.det_arr.ch.name,
                                   self.det_arr.ch.cam.dir))
            else:
                self._params_vals["tc"] = (
                    self._tb *
                    self._param_vals["tc_frac"])
        # Calculte lo and hi frequency
        self._param_vals["flo"], self._param_vals["fhi"] = (
            self._phys.band_edges(
                self._param_vals["bc"], self._param_vals["fbw"]))
        return

    def _store_eff(self):
        # Load band
        if self._band is not None:
            self._tran = self._band
            if self._tran is not None:
                self._tran = np.where(self._tran < 1, self._tran, 1.)
                self._tran = np.where(self._tran > 0, self._tran, 0.)
        else:
            # Default to top hat band
            self._tran = [self.param("det_eff")
                          if f > self.param("flo") and f < self.param("fhi")
                          else 0. for f in self.det_arr.ch.freqs]
        return
