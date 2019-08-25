# Built-in modules
import numpy as np

# BoloCalc modules
import src.parameter as pr
import src.unit as un
import src.band as bd


class Optic:
    """
    Optic object holds the name, absorbtivity, transmission, and
    temperature for a given optic in a given optic chain

    Args:
    opt_chn (src.OpticalChain): OpticalChain object
    inp_dict (dict): dictionary of optic properties
    band_file (str): input band file. Defaults to 'None.'

    Attributes:
    name (str): optical element name
    """
    def __init__(self, opt_chn, inp_dict, band_files=None):
        # Store passed parameters
        self._opt_chn = opt_chn
        self._inp_dict = inp_dict
        self._band_files = band_files
        self._log = self._opt_chn.cam.tel.exp.sim.log
        self._load = self._opt_chn.cam.tel.exp.sim.load
        self._phys = self._opt_chn.cam.tel.exp.sim.phys
        self._nexp = self._opt_chn.cam.tel.exp.sim.param("nexp")

        # Names for the special optical elements
        self._ap_names = ["APERTURE", "STOP", "LYOT"]
        self._mirr_names = ["MIRROR", "PRIMARY", "SECONDARY"]

        # Allowed band names
        self._band_names = ["REFL", "TRAN", "ABSO", "SPILL", "SCAT"]

        # Store parameter dict
        self._store_param_dict()

    # ***** Public Functions *****
    def evaluate(self, ch):
        """
        Generate optic element, absorbtivity, transmission, and
        temperature for a given channel

        Args:
        ch (src.Channel): Channel object for which to calculate optic
        parameters
        """
        # Generate the parameter values
        self._ch = ch
        self._store_param_vals(self._ch)

        # Name
        self._elem = self._param_vals["elem"]
        self.name = self._elem
        self._nfreq = len(self._ch.freqs)

        self._store_temp()
        self._store_tran()
        self._store_refl()
        self._store_spill()
        self._store_spill_temp()
        self._store_scatt()
        self._store_scatt_temp()
        self._store_abso()

        return (self._elem, self._emiss, self._effic, self._temp)

    def change_param(self, param, new_val, band_id=None):
        if param not in self._param_dict.keys():
            if param in self._param_names.keys():
                return (self._param_dict[self._param_names[param]].change(
                        new_val, band_id=band_id))
            else:
                self._log.err(
                    "Parameter '%s' not understood by Optic.change_param()"
                    % (str(param)))
        elif param in self._param_dict.keys():
            return self._param_dict[param].change(new_val, band_id=band_id)
        else:
            self._log.err(
                "Parameter '%s' not understood by Optic.change_param()"
                % (str(param)))

    # ***** Helper Methods *****
    # Ratio of blackbody power between two temperatures
    def _pow_frac(self, T1, T2, freqs):
        return (self._phys.bb_pow_spec(freqs, T1) /
                self._phys.bb_pow_spec(freqs, T2))

    def _param_samp(self, param, band_id):
        if self._nexp == 1:
            return param.get_avg(band_id)
        else:
            return param.sample(band_id=band_id, nsample=1)

    def _store_param_dict(self):
        self._param_dict = {
            "elem": pr.Parameter(
                self._log, "Element", self._inp_dict["Element"]),
            "temp": pr.Parameter(
                self._log, "Temperature", self._inp_dict["Temperature"],
                min=0.0, max=np.inf),
            "abs": pr.Parameter(
                self._log, "Absorption", self._inp_dict["Absorption"],
                min=0.0, max=1.0),
            "refl": pr.Parameter(
                self._log, "Reflection", self._inp_dict["Reflection"],
                min=0.0, max=1.0),
            "thick": pr.Parameter(
                self._log, "Thickness", self._inp_dict["Thickness"],
                min=0.0, max=np.inf),
            "Index": pr.Parameter(
                self._log, "Index", self._inp_dict["Index"],
                min=0.0, max=np.inf),
            "ltan": pr.Parameter(
                self._log, "Loss Tangent", self._inp_dict["Loss Tangent"],
                min=0.0, max=np.inf),
            "cond": pr.Parameter(
                self._log, "Conductivity", self._inp_dict["Conductivity"],
                min=0.0, max=np.inf),
            "surfr": pr.Parameter(
                self._log, "Surface Rough", self._inp_dict["Surface Rough"],
                min=0.0, max=np.inf),
            "spill": pr.Parameter(
                self._log, "Spillover", self._inp_dict["Spillover"],
                min=0.0, max=1.0),
            "spill_temp": pr.Parameter(
                self._log, "Spillover Temp",
                self._inp_dict["Spillover Temp"],
                min=0.0, max=np.inf),
            "scat_frac": pr.Parameter(
                self._log, "Scatter Frac", self._inp_dict["Scatter Frac"],
                min=0.0, max=1.0),
            "scat_temp":   pr.Parameter(
                self._log, "Scatter Temp", self._inp_dict["Scatter Temp"],
                min=0.0, max=np.inf)}
        self._param_names = {param.name: pid
                             for pid, param in self._param_dict.items()}
        return

    def _store_param_vals(self, ch):
        self._param_vals = {}
        for k in self._param_dict.keys():
            self._param_vals[k] = self._param_samp(
                self._param_dict[k], ch.param("band_id"))

    def _store_bands(self):
        self._band_dict = {}
        b_ids = ['_'.join(f.split('_')[1:]).upper() for f in self._band_files]
        for b_name in self._band_names:
            args = np.argwhere(b_name in np.array(b_ids)).flatten()
            if len(args) > 1:
                self._log.err(
                    "More than one band file tagged '%s' for optic '%s' "
                    "in camera '%s': %s"
                    % (b_name, self._param_dict['elem'].get_val(),
                       self._opt_chn.cam.param('cam_name'),
                       np.array(self._band_names)[args]))
            else:
                self._band_dict[b_name] = self._band_files[args]
        return

    def _store_temp(self):
        self._temp = np.ones(self._nfreq) * self._param_vals["temp"]
        return

    def _store_tran(self):
        # Efficiency from a band file?
        if "TRAN" in self._band_dict.keys():
            tran_band = bd.Band(self._log, self._load,
                                self._band_dict["TRAN"], self._ch.freqs)
            self._tran = self._phys_lims(tran_band.sample()[0])
        else:
            self._tran = None  # for now
        return
    
    def _store_refl(self):
        # Reflection from a band file?
        if "REFL" in self._band_dict.keys():
            refl_band = bd.Band(self._log, self._load,
                                self._band_dict["REFL"], self._ch.freqs)
            self._refl = refl_band.sample()[0]
            # Maximum reflection is 1, minimum is 0
            if self._refl is not None:
                self._refl = np.array([r if r > 0 else 0. for r in self._refl])
                self._refl = np.array([r if r < 1 else 1. for r in self._refl])
        # Otherwise store reflection only if transmission is known yet
        elif self._tran is None:
            if not self._param_vals["refl"] == "NA":
                self._refl = np.ones(self._nfreq) * self._param_vals["refl"]
            else:
                self._refl = np.zeros(self._nfreq)
        else:
            self._refl = None  # for now
        return
    
    def _store_spill(self):
        # Spillover from a band file?
        if "SPILL" in self._band_dict.keys():
            spill_band = bd.Band(self._log, self._load,
                                self._band_dict["SPILL"], self._ch.freqs)
            self._spill = spill_band.sample()[0]
            # Maximum spill is 1, minimum is 0
            if self._spill is not None:
                self._spill = np.array([s if s > 0 else 0.
                                        for s in self._spill])
                self._spill = np.array([s if s < 1 else 1.
                                        for s in self._spill])
        # Otherwise assume flat spill vs frequency
        elif not self._param_vals["spill"] == 'NA':
            self._spill = np.ones(self._nfreq) * self._param_vals["spill"]
        else:
            self._spill = np.zeros(self._nfreq)
        return
    
    def _store_spill_temp(self):
        if not self._param_vals["spill_temp"] == "NA":
            self._spill_temp = np.ones(self._nfreq) * self._param_vals["spill_temp"]
        else:
            self._spill_temp = np.ones(self._nfreq) * self._temp
        return
    
    def _store_scatt(self):
        # Scattering from a band file?
        if "SCAT" in self._band_dict.keys():
            scatt_band = bd.Band(self._log, self._load,
                                self._band_dict["SCAT"], self._ch.freqs)
            self._scatt = self._phys_lims(scatt_band.sample()[0])
        # Otherwise calculate using other input parameters
        elif not self._param_vals["scat_frac"] == "NA":
            self._scatt = np.ones(self._nfreq) * self._param_vals["scat_frac"]
        elif not self._param_vals["surfr"] == "NA":
            self._scatt = 1. - self._phys.ruze_eff(
                self._ch.freqs, self._param_vals["surfr"])
        else:
            self._scatt = np.zeros(self._nfreq)
        return
    
    def _store_scatt_temp(self):
        if not self._param_vals["scat_temp"] == 'NA':
            self._scatt_temp = np.ones(self._nfreq) * self._param_vals["scat_temp"]
        else:
            self._scatt_temp = np.ones(self._nfreq) * self._temp
        return

    def _store_abso(self):
        # Absorption from a band file?
        if "ABSO" in self._band_dict.keys():
            abso_band = bd.Band(self._log, self._load,
                                self._band_dict["ABSO"], self._ch.freqs)
            self._abso = self._phys_lims(abso_band.sample()[0])
        # Otherwise calculate from other parameters
        # Treat the case of the aperture stop
        elif self._elem.strip().upper() in self._ap_names:
            if self._tran is None:
                if not self._param_vals["abs"] == 'NA':
                    self._abso = np.ones(self._nfreq)*self._param_vals["abs"]
                else:
                    self._abso = 1. - self._phys.spill_eff(
                        self._ch.freqs, self._ch.param("pix_sz"),
                        self._ch.param("fnum"), self._ch.param("wf"))
            else:
                self._abso = 1. - self._tran
        # Treat all other optics
        else:
            if not self._param_vals["abs"] == "NA":
                self._abso = np.ones(self._nfreq) * self._param_vals["abs"]
            elif self._elem.strip().upper() in self._mirr_names:
                self._abso = 1. - self._phys.ohmic_eff(
                    self._ch.freqs, self._param_vals["cond"])
            else:
                if (not self._param_vals["thick"] == "NA" and
                   not self._param_vals["ind"] == "NA" and
                   not self._param_vals["ltan"] == "NA"):
                    self._abso = self._phys.dielectric_loss(
                        self._ch.freqs, self._param_vals["thick"],
                        self._param_vals["ind"], self._param_vals["ltan"])
                else:
                    self._abso = np.zeros(self._nfreq)
        return

    def _calculate(self):
        # Store reflection if it hasn't already
        if self._refl is None and self._tran is not None:
            self._refl = self._phys_lims(1. - self._tran - self._abso)

        # Absorption array
        self._emiss = (
            self._abso +
            self._spill * self._pow_frac(
                self._spill_temp, self._temp, self._ch.freqs) +
            self._scatt * self._pow_frac(
                self._scatt_temp, self._temp, self._ch.freqs))
        
        # Efficiency array
        if self._tran is not None:
            self._effic = self._tran
        else:
            self._effic = (
                1. - self._refl - self._abso - self._spill - self._scatt)

        # Store channel beam coupling efficiency if this is the aperture
        if self._elem.strip().upper() in self._ap_names:
            ch_eff = (np.trapz(self._effic, self._ch.freqs) /
                      float(self._ch.freqs[-1] - self._ch.freqs[0]))
            ch_taper = self._phys.edge_taper(ch_eff)
            self._ch.set_param("ap_eff", ch_eff)
            self._ch.set_param("edge_tap", ch_taper)
        return
    
    def _phys_lims(self, band):
        if band is not None:
            band = np.array([x if x > 0 else 0. for x in band])
            band = np.array([x if x < 1 else 1. for x in band])
        return band