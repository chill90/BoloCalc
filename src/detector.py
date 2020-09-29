# built-in modules
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

        # Minimum allowed Tc minus Tb [K]
        self._min_tc_tb_diff = 0.010
        # Generate detector parameters
        self._store_param_dict()

        # Store static arrays
        self.elem = ["Detector"]
        # On-chip absorption isn't differentiated from on-chip reflection
        self.emis = [[0.000 for f in self._ch.freqs]]
        return

    # ***** Public Methods *****
    def evaluate(self, band=None):
        # Re-store dictionary to reflect ch and cam changes
        self._store_param_dict()
        # Evaluate detector parameters
        self._store_param_vals()
        # Evaluate bandwidth
        self._store_bw_bc(band)
        # Evaluate transmission
        self._store_band(band)
        # Store emissivity, transmission, and temperature
        self.emis = [[0.000 for f in self._ch.freqs]]
        self.tran = [self.band]
        self.temp = [[self.param("tb") for f in self._ch.freqs]]
        return

    def param(self, param):
        return self._param_vals[param]

    # ***** Helper Methods *****
    def _param_samp(self, param):
        """ Sample detector parameter """
        if self._ndet == 1:
            return param.get_med()
        else:
            return param.sample(nsample=1)

    def _store_param_dict(self):
        """ Store the paramter dictionary, which is defined at the channel """
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
                    self.param("tb") *
                    self.param("tc_frac"))
        else:
            tc_tb_diff = self._param_vals["tc"] - self._param_vals["tb"]
            if tc_tb_diff < self._min_tc_tb_diff:
                self._log.wrn(
                    "Tc - Tb < %d mK for a sampled detector in Band ID "
                    "'%s' in camera '%s'. Setting Tc = Tb + %d mK for this "
                    "detector sample"
                    % (self._min_tc_tb_diff, self._ch.band_id,
                       self._ch.cam.dir, self._min_tc_tb_diff))
                self._param_vals["tc"] = (
                    self._param_vals["tb"] + self._min_tc_tb_diff)

        return

    def _store_band(self, band=None):
        """ Store the detector band """
        freqs = self._ch.freqs
        # Define top-hat band
        if str(self.param("det_eff")) != "NA":
            top_hat = [
                self.param("det_eff")
                if (f >= self.param("flo") and f < self.param("fhi"))
                else 0. for f in freqs]
        else:
            top_hat = None
        # Use a custom band if "BAND" is passed for band center
        if self._ch.param("cust"):
            if band is None:
                self._log.err(
                    "Band Center for channel '%s' defined as 'BAND' "
                    "but no fand file found" % (self._ch.param("ch_name")))
            # Scale and store the input band transmission
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
            # Treat the special case of band center shifting
            bc_param = self._param_dict["bc"]
            bc_std = bc_param.get_std()
            if isinstance(bc_std, float) or isinstance(bc_std, np.float):
                self._param_vals["bshift"] = bc_param.sample(
                    max=np.inf, min=-np.inf, null=True)
                delta_f = self._param_vals["bshift"]
                delta_ind = int(np.round(delta_f / np.diff(freqs)[0]))
                if delta_ind != 0:
                    self.band = self._shift_band(self.band, delta_ind)
                    # Use the edge value to fill the edge of the array
                    if delta_ind > 0:
                        self.band[:delta_ind] = self.band[delta_ind]
                    else:
                        self.band[delta_ind:] = self.band[delta_ind]
            # Define a top-hat window function for optical power caclulations
            flo, fhi = self._phys.band_edges(freqs, self.band)
            # Define top-hat window for optical-power calculations
            self.window = np.array([
                1. if (f >= flo and f < fhi) else 0. for f in freqs])
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
                # Define top-hat window for optical-power calculations
                self.window = np.array([
                    1. if b else 0. for b in self.band])
        return

    def _store_bw_bc(self, band=None):
        """ Store the bandwidth for this detector """
        freqs = self._ch.freqs
        if band is not None:
            # Define band edges to be -3 dB point
            flo, fhi = self._phys.band_edges(freqs, band)
            self._param_vals["flo"] = flo
            self._param_vals["fhi"] = fhi
        else:
            # Define band edges using band center and fractional BW
            self._param_vals["flo"] = (
                self.param("bc") * (1. - 0.5 * self.param("fbw")))
            self._param_vals["fhi"] = (
                self.param("bc") * (1. + 0.5 * self.param("fbw")))

        # Store bandwidth and band center
        self._param_vals["bc"] = (
            self._param_vals["fhi"] + self._param_vals["flo"]) / 2.
        self._param_vals["bw"] = (
            self._param_vals["fhi"] - self._param_vals["flo"])
        # self.band_mask = [
        #    1. if f >= self.param("flo") and f < self.param("fhi")
        #    else 0. for f in freqs]
        return

    def _shift_band(self, band, delta_ind):
        if delta_ind == 0:
            ret_band = band
        elif delta_ind < 0:
            ret_band = np.concatenate(
                [np.roll(band, delta_ind)[:delta_ind],
                 [band[-1]] * int(abs(delta_ind))])
        else:
            ret_band = np.concatenate(
                [[band[0]] * int(abs(delta_ind)),
                 np.roll(band, delta_ind)[delta_ind:]])
        return ret_band
