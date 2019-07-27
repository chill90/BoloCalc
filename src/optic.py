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
    def __init__(self, opt_chn, inp_dict, band_file=None):
        # Store passed parameters
        self._opt_chn = opt_chn
        self._inp_dict = inp_dict
        self._band_file = band_file
        self._log = self._opt_chn.cam.tel.exp.sim.log
        self._load = self._opt_chn.cam.tel.exp.sim.load
        self._phys = self._opt_chn.cam.tel.exp.sim.phys
        self._nexp = self._opt_chn.cam.tel.exp.sim.param("nexp")

        # Names for the special optical elements
        self._ap_names = ["APERTURE", "STOP", "LYOT"]
        self._mirr_names = ["MIRROR", "PRIMARY", "SECONDARY"]

        # Store parameter dict
        self._store_param_dict()

    # ***** Public Functions *****
    def generate(self, ch):
        """
        Generate optic element, absorbtivity, transmission, and
        temperature for a given channel

        Args:
        ch (src.Channel): Channel object for which to calculate optic
        parameters
        """
        # Generate the parameter values
        self._store_param_vals(ch)

        # Name
        elem = self._param_vals["elem"]
        self.name = elem
        nfreq = len(ch.freqs)

        # Temperature
        temp = np.ones(nfreq) * self._param_vals["temp"]

        # Efficiency and reflection from a band file
        if self._band_file is not None:
            band = bd.Band(self._log, self._load, self._band_file, ch.freqs)
            eff = band.sample()[0]
            if eff is not None:
                eff = np.array([e if e > 0 else 0. for e in eff])
                eff = np.array([e if e < 1 else 1. for e in eff])
        else:
            eff = None

        # Reflection -- use only if no band file
        if eff is None:
            if not self._param_vals["refl"] == "NA":
                refl = np.ones(nfreq) * self._param_vals["refl"]
            else:
                refl = np.zeros(nfreq)

        # Spillover
        if not self._param_vals["spill"] == 'NA':
            spill = np.ones(nfreq) * self._param_vals["spill"]
        else:
            spill = np.zeros(nfreq)
        if not self._param_vals["spill_temp"] == "NA":
            spill_temp = np.ones(nfreq) * self._param_vals["spill_temp"]
        else:
            spill_temp = np.ones(nfreq) * temp

        # Scattering
        if not self._param_vals["surfr"] == "NA":
            scatt = 1. - self._phys.ruze_eff(
                ch.freqs, self._param_vals["surfr"])
        elif not self._param_vals["scat_frac"] == "NA":
            scatt = np.ones(nfreq) * self._param_vals["scat_frac"]
        else:
            scatt = np.zeros(nfreq)
        if not self._param_vals["scat_temp"] == 'NA':
            scatt_temp = np.ones(nfreq) * self._param_vals["scat_temp"]
        else:
            scatt_temp = np.ones(nfreq) * temp

        # Absorption
        if elem.strip().upper() in self._ap_names:
            if eff is None:
                if not self._param_vals["abs"] == 'NA':
                    abso = np.ones(nfreq)*self._param_vals["abs"]
                else:
                    abso = 1. - self._phys.spill_eff(
                        ch.freqs, ch.param("pix_sz"),
                        ch.param("fnum"), ch.param("wf"))
            else:
                abso = 1. - eff
        else:
            if not self._param_vals["abs"] == "NA":
                abso = np.ones(nfreq) * self._param_vals["abs"]
            elif self.elem.strip().upper() in self._mirr_names:
                abso = 1. - self._phys.ohmic_eff(
                    ch.freqs, self._param_vals["cond"])
            else:
                try:
                    abso = self._phys.dielectric_loss(
                        ch.freqs, self._param_vals["thick"],
                        self._param_vals["ind"], self._param_vals["ltan"])
                except:
                    abso = np.zeros(nfreq)

        # Reflection
        if eff is not None:
            refl = 1. - eff - abso
            refl = np.where(refl < 0, np.zeros(len(refl)), refl)
            refl = np.where(refl > 1, np.ones(len(refl)), refl)

        # Element, absorption, efficiency, and temperature
        if scatt is not None and spill is not None:
            emiss = (abso + scatt *
                     self._pow_frac(scatt_temp, temp, ch.freqs) +
                     spill * self._pow_frac(spill_temp, temp, ch.freqs))
        elif spill is not None:
            emiss = abso + spill * self._pow_frac(spill_temp, temp, ch.freqs)
        elif scatt is not None:
            emiss = abso + scatt * self._pow_frac(scatt_temp, temp, ch.freqs)
        else:
            emiss = abso
        if eff is not None:
            effic = eff
        else:
            effic = 1. - refl - abso - spill - scatt

        # Store channel pixel parameters
        if elem.strip().upper() in self._ap_names:
            ch_eff = (np.trapz(effic, ch.freqs) /
                      float(ch.freqs[-1] - ch.freqs[0]))
            ch_taper = self._phys.edge_taper(ch_eff)
            ch.set_param("ap_eff", ch_eff)
            ch.set_param("edge_tap", ch_taper)

        return (elem, emiss, effic, temp)

    # ***** Helper Methods *****
    # Ratio of blackbody power between two temperatures
    def _pow_frac(self, T1, T2, freqs):
        return (np.trapz(self._phys.bb_pow_spec(freqs, T1), freqs) /
                float(np.trapz(self._phys.bb_pow_spec(freqs, T2), freqs)))

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
                un.Unit("mm"), min=0.0, max=np.inf),
            "Index": pr.Parameter(
                self._log, "Index", self._inp_dict["Index"],
                min=0.0, max=np.inf),
            "ltan": pr.Parameter(
                self._log, "Loss Tangent", self._inp_dict["Loss Tangent"],
                un.Unit(1.e-04), min=0.0, max=np.inf),
            "cond": pr.Parameter(
                self._log, "Conductivity", self._inp_dict["Conductivity"],
                un.Unit(1.e+06), min=0.0, max=np.inf),
            "surfr": pr.Parameter(
                self._log, "Surface Rough", self._inp_dict["Surface Rough"],
                un.Unit("um"), min=0.0, max=np.inf),
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
        return

    def _store_param_vals(self, ch):
        self._param_vals = {}
        for k in self._param_dict.keys():
            self._param_vals[k] = self._param_samp(
                self._param_dict[k], ch.param("band_id"))
