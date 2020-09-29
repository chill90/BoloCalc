# Built-in modules
import numpy as np
import functools as ft
import copy as cp


class Sensitivity:
    """
    Sensitivity object takes a simulation object, which has information about
    the experiment, and calculates the sensitivity

    Args:
    sim (src.Simulation): parent Simulation object

    Attributes:
    exp_dir (str): input experiment directory
    senses (list): array of output sensitivities
    opt_pos (list): array of output optical power arrays

    Parents:
    sim (src.Simulation): parent Simulation object
    exp (src.Experiment): parent Experiment object
    """
    def __init__(self, sim):
        # Store passed parameters
        self.exp = sim.exp
        self._log = sim.log
        self._phys = sim.phys
        self._noise = sim.noise
        self._corr = sim.param("corr")
        self._nobs = sim.param("nobs")
        self._ndet = sim.param("ndet")

    # ***** Public methods *****
    def sensitivity(self, exp=None):
        """
        Calculate sensitivity for a given experiment

        Args:
        exp (src.Experiment): Experiment to evaluate. Defaults to None,
        which triggers evaluating the parent Experiment object
        """
        if exp is None:
            exp = self.exp
        return [[[self.ch_sensitivity(ch) for ch in cam.chs.values()]
                for cam in tp.cams.values()]
                for tp in exp.tels.values()]

    def opt_pow(self):
        """ Calculate optical power tables for parent Experiment object """
        return [[[self._opt_pow(ch) for ch in cm.chs.values()]
                for cm in tp.cams.values()]
                for tp in self.exp.tels.values()]

    def ch_sensitivity(self, ch):
        """
        Calculate channel sensitivity of a specific Channel object

        Args:
        ch (src.Channel): Channel object
        """
        # Calculate optical power
        self._calc_popt(ch)
        self._calc_rj_temp(ch)
        # Calculate NEP
        self._calc_photon_NEP(ch)
        self._calc_bolo_NEP(ch)
        self._calc_read_NEP(ch)
        self._calc_tot_NEP(ch)
        # Calculte NET
        self._calc_NET(ch)
        self._calc_NET_RJ(ch)
        # Calculate array NET
        self._calc_NET_arr(ch)
        self._calc_NET_arr_RJ(ch)
        # Calculate correlation degradation
        self._calc_corr_deg(ch)
        # Calculate map depth
        self._calc_map_depth(ch)
        self._calc_map_depth_RJ(ch)

        # Return a list of parameter distributions
        return [self._tel_eff_arr.flatten().tolist(),
                self._popt_arr.flatten().tolist(),
                self._tel_rj_temp.flatten().tolist(),
                self._sky_rj_temp.flatten().tolist(),
                self._NEP_ph_arr.flatten().tolist(),
                self._NEP_bolo_arr.flatten().tolist(),
                self._NEP_read_arr.flatten().tolist(),
                self._NEP.flatten().tolist(),
                self._NET.flatten().tolist(),
                self._NET_RJ.flatten().tolist(),
                self._NET_arr.flatten().tolist(),
                self._NET_arr_RJ.flatten().tolist(),
                self._corr_deg.flatten().tolist(),
                self._map_depth.flatten().tolist(),
                self._map_depth_RJ.flatten().tolist()]

    # *** Helper methods ***
    def _opt_pow(self, ch):
        """ Calculate optical power table for a specific channel """
        # Store passed parameters
        self._pow_sky_side = []
        self._pow_det_side = []
        self._eff_elem = []
        self._eff_det_side = []
        for i in range(len(ch.elem)):  # nobs
            pow_sky_side_1 = []
            pow_det_side_1 = []
            eff_elem_1 = []
            eff_det_side_1 = []
            for j in range(len(ch.elem[i])):  # ndet
                window = np.array(ch.det_arr.dets[j].window)
                bw = ch.det_arr.dets[j].param("bw")
                pows = []
                pow_sky_side_2 = []
                pow_det_side_2 = []
                eff_sky_side_2 = []
                eff_elem_2 = []
                eff_det_side_2 = []
                # Store efficiency towards sky and towards detector
                for k in range(len(ch.elem[i][j])):  # nelem
                    # Store efficiency
                    eff_elem_2.append(ch.tran[i][j][k])
                    # Buffer the efficiency array
                    eff_arr = np.vstack([ch.tran[i][j],
                                         np.array([1. for f in ch.freqs])])
                    # Efficiency towards the detector
                    cum_eff_det = ft.reduce(lambda x, y: x*y, eff_arr[k+1:])
                    eff_det_side_2.append(np.array(cum_eff_det))
                    # Efficiency towards the sky
                    if k == 0:
                        # Zero elements sky side
                        cum_eff_sky = [[0. for f in ch.freqs]]
                    elif k == 1:
                        # One element sky side
                        cum_eff_sky = [[1. for f in ch.freqs],
                                       [0. for f in ch.freqs]]
                    else:
                        cum_eff_sky = [ft.reduce(
                            lambda x, y: x*y, eff_arr[m+1:k])
                            if m < k-2 else eff_arr[m+1]
                            for m in range(k-1)] + [[1. for f in ch.freqs],
                                                    [0. for f in ch.freqs]]
                    eff_sky_side_2.append(cum_eff_sky)
                    pow = self._phys.bb_pow_spec(
                        ch.freqs, ch.temp[i][j][k], ch.emis[i][j][k])
                    pows.append(pow)
                # Store band-averaged power from sky and power on detector
                # and band-average the efficiencies
                for k in range(len(ch.elem[i][j])):
                    pow_out = np.trapz(pows[k] * eff_det_side_2[k], ch.freqs)
                    pow_det_side_2.append(pow_out)
                    if k == len(ch.elem[i][j]) - 1:
                        eff_elem_2[k] = np.trapz(eff_elem_2[k], ch.freqs) / bw
                    else:
                        eff_elem_2[k] = (
                            np.trapz(
                                eff_elem_2[k] * eff_elem_2[-1], ch.freqs) / 
                            np.trapz(eff_elem_2[-1], ch.freqs))
                    eff_det_side_2[k] = (
                        np.trapz(eff_det_side_2[k], ch.freqs) / bw)
                    pow_in = sum([np.trapz(
                        pows[m] * eff_sky_side_2[k][m] *
                        window, ch.freqs)
                        for m in range(k)])
                    pow_sky_side_2.append(pow_in)
                # Force the final efficiency to be 100%
                eff_det_side_2[-1] = 1.
                pow_sky_side_1.append(pow_sky_side_2)
                pow_det_side_1.append(pow_det_side_2)
                eff_elem_1.append(eff_elem_2)
                eff_det_side_1.append(eff_det_side_2)
            self._pow_sky_side.append(pow_sky_side_1)
            self._pow_det_side.append(pow_det_side_1)
            self._eff_elem.append(eff_elem_1)
            self._eff_det_side.append(eff_det_side_1)
        # Build table of optical powers and efficiencies for each element
        return self._opt_table()

    def _calc_popt(self, ch):
        """ Calculate optical power for a specific channel """
        self._popt_arr = np.array([[self._popt(
            ch.elem[i][j], ch.emis[i][j], ch.tran[i][j],
            ch.temp[i][j], ch.freqs)
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        return

    def _calc_rj_temp(self, ch):
        """ Calculate telescope RJ temp for a specific temperature """
        n_sky_elem = self._num_sky_elem(ch)
        # Telescope efficiency
        self._tel_eff_arr = np.array([[self._eff(
            ch.tran[i][j][n_sky_elem-1:],
            ch.freqs, ch.det_arr.dets[j].param("bw"))
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        # Telescope temperature
        self._tel_rj_temp = np.array([[self._rj_temp(
            ch.elem[i][j][n_sky_elem:],
            ch.emis[i][j][n_sky_elem:],
            ch.tran[i][j][n_sky_elem:],
            ch.temp[i][j][n_sky_elem:],
            ch.freqs, self._tel_eff_arr[i][j],
            ch.det_arr.dets[j].param("bw"))
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        # Sky temperature
        self._sky_rj_temp = np.array([[self._rj_temp(
            ch.elem[i][j][:n_sky_elem],
            ch.emis[i][j][:n_sky_elem],
            ch.tran[i][j],
            ch.temp[i][j][:n_sky_elem],
            ch.freqs, self._tel_eff_arr[i][j],
            ch.det_arr.dets[j].param("bw"))
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        return

    def _calc_photon_NEP(self, ch):
        """ Calculate photon NEP for a specific channel """
        if self._corr:
            pass_ch = ch
        else:
            pass_ch = None
        NEP_ph_out = np.array([[self._photon_NEP(
            ch.elem[i][j], ch.emis[i][j], ch.tran[i][j],
            ch.temp[i][j], ch.freqs, pass_ch)
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        # pylint: disable=unbalanced-tuple-unpacking
        NEP_ph_arr, NEP_ph_arr_corr = np.split(NEP_ph_out, 2, axis=2)
        self._NEP_ph_arr = np.reshape(
            NEP_ph_arr, np.shape(NEP_ph_arr)[:2])
        self._NEP_ph_arr_corr = np.reshape(
            NEP_ph_arr_corr, np.shape(NEP_ph_arr_corr)[:2])
        return

    def _calc_bolo_NEP(self, ch):
        """ Calculate bolometer NEP for a specific channel """
        self._NEP_bolo_arr = np.array([[self._bolo_NEP(
            self._popt_arr[i][j], ch.det_arr.dets[j])
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        return

    def _calc_read_NEP(self, ch):
        """ Calculate readout NEP for a specific channel """
        NEP_read_arr = np.array([[self._read_NEP(
            self._popt_arr[i][j], ch.det_arr.dets[j])
            for j in range(self._ndet)]
            for i in range(self._nobs)])

        if np.any(np.isin(NEP_read_arr.astype(str), ['NA'])):
            self._NEP_read_arr = np.array([[np.sqrt(
                (1. + ch.det_arr.dets[j].param("read_frac"))**2 - 1.) *
                np.sqrt(self._NEP_ph_arr[i][j]**2 +
                        self._NEP_bolo_arr[i][j]**2)
                for j in range(self._ndet)]
                for i in range(self._nobs)])
        else:
            self._NEP_read_arr = NEP_read_arr
        return

    def _calc_tot_NEP(self, ch):
        """ Calculate total NEP for a specific channel """
        self._NEP = np.sqrt(self._NEP_ph_arr**2 +
                            self._NEP_bolo_arr**2 +
                            self._NEP_read_arr**2)
        # Total NEP with correlation adjustment
        self._NEP_corr = np.sqrt(self._NEP_ph_arr_corr**2 +
                                 self._NEP_bolo_arr**2 +
                                 self._NEP_read_arr**2)
        return

    def _calc_NET(self, ch):
        """ Calculate NET for a specific channel """
        # Total NET
        self._NET = np.array([[self._noise.NET_from_NEP(
            self._NEP[i][j], ch.freqs, np.prod(ch.tran[i][j], axis=0),
            ch.cam.param("opt_coup"))
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        # Total NET with correlation adjustment
        self._NET_corr = np.array([[self._noise.NET_from_NEP(
            self._NEP_corr[i][j], ch.freqs, np.prod(ch.tran[i][j], axis=0),
            ch.cam.param("opt_coup"))
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        return

    def _calc_NET_RJ(self, ch):
        """ Calculate RJ NET for a specific channel """
        self._NET_RJ = np.array([[self._Trj_over_Tcmb(
            ch.freqs)*self._NET[i][j]
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        self._NET_corr_RJ = np.array([[self._Trj_over_Tcmb(
            ch.freqs)*self._NET_corr[i][j]
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        return

    def _calc_NET_arr(self, ch):
        """ Calcualte array NET for a specific channel """
        self._NET_arr = np.array([[self._noise.NET_arr(
            self._NET_corr[i][j], ch.param("ndet"), ch.param("yield"))
            for j in range(self._ndet)]
            for i in range(self._nobs)]) * (
                ch.cam.tel.param("net_mgn"))
        return

    def _calc_NET_arr_RJ(self, ch):
        """ Calculate array NET RJ for a specific channel """
        self._NET_arr_RJ = np.array([[self._noise.NET_arr(
            self._NET_corr_RJ[i][j], ch.param("ndet"), ch.param("yield"))
            for j in range(self._ndet)]
            for i in range(self._nobs)]) * (
                ch.cam.tel.param("net_mgn"))
        return

    def _calc_corr_deg(self, ch):
        """ Calculate correlation factor for a specific channel """
        self._corr_deg = np.array([[self._NET_corr[i][j] / self._NET[i][j]
                                  for j in range(self._ndet)]
                                  for i in range(self._nobs)])
        return

    def _calc_map_depth(self, ch):
        """ Calculate map depth for a specific channel """
        tel = ch.cam.tel
        self._map_depth = np.array([[self._noise.map_depth(
            self._NET_arr[i][j], tel.param("fsky"),
            tel.param("tobs"), tel.param("obs_eff"))
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        return

    def _calc_map_depth_RJ(self, ch):
        """ Calculate RJ map depth for a specific channel """
        tel = ch.cam.tel
        self._map_depth_RJ = np.array([[self._noise.map_depth(
            self._NET_arr_RJ[i][j], tel.param("fsky"),
            tel.param("tobs"), tel.param("obs_eff"))
            for j in range(self._ndet)]
            for i in range(self._nobs)])
        return

    def _eff(self, tran, freqs, bw):
        """ Calculate cumulative efficiency """
        tot_eff = np.trapz(np.prod(tran, axis=0), freqs) / bw
        return tot_eff

    def _popt(self, elem, emis, tran, temp, freqs):
        """ Calculate optical power """
        buf_tran = self._buffer_tran(tran, freqs)
        tot_pow = np.sum([np.trapz(
            self._phys.bb_pow_spec(
                freqs, temp[i], emis[i] *
                np.prod(buf_tran[i+1:], axis=0)), freqs)
                for i in range(len(elem))])
        return tot_pow

    def _rj_temp(self, elem, emis, tran, temp, freqs, eff, bw):
        """ Calculate RJ temperature """
        opt_pow = self._popt(elem, emis, tran, temp, freqs)
        rj_temp = self._phys.rj_temp(opt_pow, bw, eff)
        return rj_temp

    def _photon_NEP(self, elem, emis, tran, temp, freqs, ch=None):
        """ Calculate photon NEP """
        tran = self._buffer_tran(tran, freqs)
        if ch:
            corrs = True
        else:
            corrs = False
        pow_ints = np.array([self._phys.bb_pow_spec(
            freqs, temp[i], emis[i]*np.prod(tran[i+1:], axis=0))
            for i in range(len(elem))])
        if corrs:
            # Photon NEP both without and with correlations
            NEP_ph, NEP_ph_arr = self._noise.photon_NEP(
                pow_ints, freqs, elem, (
                    ch.param("pix_sz") /
                    float(ch.cam.param("fnum") * self._phys.lamb(
                        ch.param("bc")))))
        else:
            # Both outputs are identical
            NEP_ph, NEP_ph_arr = self._noise.photon_NEP(pow_ints, freqs)
        return NEP_ph, NEP_ph_arr

    def _bolo_NEP(self, opt_pow, det):
        """ Calculate bolometer NEP """
        if 'NA' in str(det.param("g")):
            if 'NA' in str(det.param("psat")):
                g = self._noise.G(
                    det.param("psat_fact") * opt_pow, det.param("n"),
                    det.param("tb"), det.param("tc"))
            else:
                g = self._noise.G(
                    det.param("psat"), det.param("n"),
                    det.param("tb"), det.param("tc"))
        else:
            g = det.param("g")
        if 'NA' in str(det.param("flink")):
            return self._noise.bolo_NEP(
                self._noise.Flink(
                    det.param("n"), det.param("tb"), det.param("tc")),
                g, det.param("tc"))
        else:
            return self._noise.bolo_NEP(
                det.param("flink"), g, det.param("tc"))

    def _read_NEP(self, opt_pow, det):
        """ Calculate readout NEP """
        if 'NA' in str(det.param("nei")):
            return 'NA'
        elif 'NA' in str(det.param("bolo_r")):
            return 'NA'
        elif 'NA' in str(det.param("psat")):
            p_bias = (det.param("psat_fact") - 1.) * opt_pow
        else:
            if opt_pow >= det.param("psat"):
                return 0.
            else:
                p_bias = det.param("psat") - opt_pow

        if 'NA' in str(det.param("sfact")):
            sfact = 1.
        else:
            sfact = det.param("sfact")
        return self._noise.read_NEP(
            p_bias, det.param("bolo_r"),
            det.param("nei"), sfact)

    def _Trj_over_Tcmb(self, freqs):
        """ Convert to RJ temperature from CMB temperature """
        factor_spec = self._phys.Trj_over_Tb(freqs, self._phys.Tcmb)
        bw = freqs[-1] - freqs[0]
        factor = np.trapz(factor_spec, freqs)/bw
        return factor

    def _buffer_tran(self, tran, freqs):
        """ Function to buffer the transmission array with ones """
        out_tran = cp.copy(np.insert(
            tran, len(tran), [1. for f in freqs], axis=0))
        return np.array(out_tran).astype(np.float)

    def _opt_table(self):
        """ Calculate optial power table """
        shape = np.shape(self._pow_sky_side)
        new_shape = (shape[0] * shape[1], shape[2])
        pow_sky_side = np.transpose(np.reshape(self._pow_sky_side, new_shape))
        pow_det_side = np.transpose(np.reshape(self._pow_det_side, new_shape))
        eff_elem = np.transpose(np.reshape(self._eff_elem, new_shape))
        eff_det_side = np.transpose(np.reshape(self._eff_det_side, new_shape))
        return [pow_sky_side,
                pow_det_side,
                eff_elem,
                eff_det_side]

    def _num_sky_elem(self, ch):
        """ Discern the number of sky optical elements """
        site = ch.cam.tel.param("site").upper()
        infg = ch.cam.tel.exp.sim.param("infg")
        if site == "ROOM":
            nelem = 1
        elif site == "SPACE":
            if infg:
                nelem = 3
            else:
                nelem = 1
        else:
            if infg:
                nelem = 4
            else:
                nelem = 2
        return nelem
