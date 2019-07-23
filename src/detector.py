# Built-in modules
import numpy as np

# BoloCalc modules
import src.parameter as pr
import src.units as un


class Detector:
    def __init__(self, det_arr, band=None):
        self.det_arr = det_arr

        # Store detector parameters
        self._store_param_dict()
        self._store_param_vals()

        # Store efficiency
        self._store_eff()

        # Store detector optical parameters
        self.elem = ["Detector"]
        self.emiss = [[0.000 for f in self.det_arr.ch.freqs]]
        self.eff = [self._eff]
        self.temp = [[self._tb() for f in self.det_arr.ch.freqs]]

    def fetch(self, param):
        return self._param_vals[param]

    # ***** Private Methods *****
    def _param_samp(self, param):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self._ndet() == 1:
            return param.getAvg(band_id=self._band_id())
        else:
            return param.sample(band_id=self._band_id(), nsample=1)

    def _store_param_dict(self):
        self._param_dict = self.det_arr.ch.det_dict
        return

    def _store_param_vals(self):
        self._param_vals = {}
        for k in self.param_dict.keys():
            self._param_vals[k] = self._param_samp(self._param_dict[k])
        # Calculate bath temperature if not explicitly defined
        if "NA" in self._param_vals["tc"]:
            if "NA" in self._param_vals["tc_frac"]:
                self._log().err("Both 'Tc' and 'Tc Frac' undefined for channel \
                                '%s'" % (self.det_arr.ch.name))
            else:
                self._params_vals["tc"] = (
                    self._tb() *
                    self._param_vals["tc_frac"])
        # Calculte lo and hi frequency
        self._param_vals["flo"], self_param_vals["fhi"] = (
            self._phys(self._param_vals["bc"] * self._param_vals["fbw"]))
        return

    def _store_eff(self):
        # Load band
        if band is not None:
            self._eff = band
            if self._eff is not None:
                self._eff = np.where(eff < 1, eff, 1.)
                self._eff = np.where(eff > 0, eff, 0.)
        else:
            # Default to top hat band
            self._eff = [self.fetch("det_eff")
                         if f > self.fetch("flo") and f < self.fetch("fhi")
                         else 0. for f in self.det_arr.ch.freqs]
        return

    def _log(self):
        return self.det_arr.ch.cam.tel.exp.sim.log

    def _band_id(self):
        return self.det_arr.ch.band_id

    def _ndet(self):
        return self.det_arr.ch.cam.tel.exp.sim.fetch("ndet")

    def _phys(self):
        return self.det_arr.ch.cam.tel.exp.sim.phys

    def _tb(self):
        return self.det_arr.ch.cam.fetch("bath_temp")
