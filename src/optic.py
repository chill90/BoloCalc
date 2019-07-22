# Built-in methods
import numpy as np
import collections as cl

# BoloCalc modules
import src.parameter as pr
import src.physics as ph
import src.units as un
import src.band as bd


class Optic:
    def __init__(self, opt_chn, inp_dict, band_file=None):
        # Store passed parameters
        self.opt_chn = opt_chn
        self.inp_dict = inp_dict
        self.band_file = band_file
        self._ph = ph.Physics()

        # Names for the special optical elements
        self._ap_names = ["APERTURE", "STOP", "LYOT"]
        self._mirr_names = ["MIRROR", "PRIMARY", "SECONDARY"]

        # Store parameter dict
        self._store_param_dict()
        return

    # ***** Public Functions *****
    # Generate element, temperature, emissivity, and efficiency
    def generate(self, ch):
        # Generate optic parameters
        self.param_vals = {}
        for k in self.param_vals_dict.keys():
            self.param_vals[k] = self._param_samp(
                self.param_dict[k], ch.band_id)

        # Name
        elem = self.inp_dict[]

        # Temperature
        temp = np.ones(ch.nfreq)*self.param_vals["temp"]

        # Efficiency and reflection from a band file
        if self.band_file is not None:
            band = bd.Band(self._log(), self.bandFile, ch.freqs)
            eff = band.sample()[0]
            if eff is not None:
                eff = np.array([e if e > 0 else 0. for e in eff])
                eff = np.array([e if e < 1 else 1. for e in eff])
        else:
            eff = None

        # Reflection -- use only if no band file
        if eff is None:
            if not self.param_vals["refl"] == "NA":
                refl = np.ones(ch.nfreq)*self.param_vals["refl"]
            else:
                refl = np.zeros(ch.nfreq)

        # Spillover
        if not self.param_vals["spill"] == 'NA':
            spill = np.ones(ch.nfreq)*self.param_vals["spill"]
        else:
            spill = np.zeros(ch.nfreq)
        if not self.param_vals["spill_temp"] == "NA":
            spillTemp = np.ones(ch.nfreq)*self.param_vals["spill_temp"]
        else:
            spillTemp = np.ones(ch.nfreq)*temp

        # Scattering
        if not self.param_vals["surfr"] == "NA":
            scatt = 1. - self._ph.ruzeEff(ch.freqs, self.param_vals["surfr"])
        elif not self.param_vals["scat_frac"] == "NA":
            scatt = np.ones(ch.nfreq)*self.param_vals["scat_frac"]
        else:
            scatt = np.zeros(ch.nfreq)
        if not self.param_vals["scat_temp"] == 'NA':
            scattTemp = np.ones(ch.nfreq)*self.param_vals["scat_temp"]
        else:
            scattTemp = np.ones(ch.nfreq)*temp

        # Absorption
        if self.elem.strip().upper() in self._ap_names:
            if eff is None:
                if not self.param_vals["abs"] == 'NA':
                    abso = np.ones(ch.nfreq)*self.param_vals["abs"]
                else:
                    abso = 1. - self._ph.spillEff(
                        ch.freqs, ch.params['pix_sz'],
                        ch.Fnumber, ch.params['wf'])
            else:
                abso = 1. - eff
        else:
            if not self.param_vals["abs"] == "NA":
                abso = np.ones(ch.nfreq)*self.param_vals["abs"]
            elif self.elem.strip().upper() in self._mirr_names:
                abso = 1. - self._ph.ohmicEff(
                    ch.freqs, self.param_vals["cond"])
            else:
                try:
                    abso = self._ph.dielectricLoss(
                        ch.freqs, self.param_vals["thick"],
                        self.param_vals["ind"], self.param_vals["ltan"])
                except:
                    abso = np.zeros(ch.nfreq)

        # Reflection
        if eff is not None:
            refl = 1. - eff - abso
            refl = np.where(refl < 0, np.zeros(len(refl)), refl)
            refl = np.where(refl > 1, np.ones(len(refl)), refl)

        # Element, absorption, efficiency, and temperature
        if scatt is not None and spill is not None:
            emiss = (abso + scatt*self._pow_frac(scattTemp, temp, ch.freqs) +
                     spill*self._pow_frac(spillTemp, temp, ch.freqs))
        elif spill is not None:
            emiss = abso + spill*self._pow_frac(spillTemp, temp, ch.freqs)
        elif scatt is not None:
            emiss = abso + scatt*self._pow_frac(scattTemp, temp, ch.freqs)
        else:
            emiss = abso
        if eff is not None:
            effic = eff
        else:
            effic = 1. - refl - abso - spill - scatt

        # Store channel pixel parameters
        if self.elem.strip().upper() in self._ap_names:
            ch.apEff = (np.trapz(effic, ch.freqs) /
                        float(ch.freqs[-1] - ch.freqs[0]))
            ch.edgeTaper = self._ph.edge_taper(ch.ap_eff)

        return [self.elem, emiss, effic, temp]

    # ***** Private Methods *****
    # Ratio of blackbody power between two temperatures
    def _log(self):
        return self.opt_chn.cam.tel.exp.sim.log

    def _pow_frac(self, T1, T2, freqs):
        return (np.trapz(self._ph.bbPowSpec(freqs, T1), freqs) /
                float(np.trapz(self.__ph.bbPowSpec(freqs, T2), freqs)))

    # Sample parameter values
    def _param_samp(self, param, band_id):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self.nrealize == 1:
            return param.get_avg(bandID)
        else:
            return param.sample(band_id=band_id, nsample=1)

    def _store_param_dict(self, params):
        self.param_dict = {
            "elem": pr.Parameter(
                self._log(), "Element", params["Element"])
            "temp": pr.Parameter(
                self._log(), "Temperature", params["Temperature"],
                min=0.0, max=np.inf),
            "abs": pr.Parameter(
                self._log(), "Absorption", params["Absorption"],
                min=0.0, max=1.0),
            "refl": pr.Parameter(
                self._log(), "Reflection", params["Reflection"],
                min=0.0, max=1.0),
            "thick": pr.Parameter(
                self._log(), "Thickness", params["Thickness"],
                un.mmToM, min=0.0, max=np.inf),
            "Index": pr.Parameter(
                self._log(), "Index", params["Index"],
                min=0.0, max=np.inf),
            "ltan": pr.Parameter(
                self._log(), "Loss Tangent", params["Loss Tangent"],
                un.Unit(1.e-04), min=0.0, max=np.inf),
            "cond": pr.Parameter(
                self._log(), "Conductivity", params["Conductivity"],
                un.Unit(1.e+06), min=0.0, max=np.inf),
            "surfr": pr.Parameter(
                self._log(), "Surface Rough", params["Surface Rough"],
                un.Unit("um"), min=0.0, max=np.inf),
            "spill": pr.Parameter(
                self._log(), "Spillover", params["Spillover"],
                min=0.0, max=1.0),
            "spill_temp": pr.Parameter(
                self._log(), "Spillover Temp", params["Spillover Temp"],
                min=0.0, max=np.inf),
            "scat_frac": pr.Parameter(
                self._log(), "Scatter Frac", params["Scatter Frac"],
                min=0.0, max=1.0),
            "scat_temp":   pr.Parameter(
                self._log(), "Scatter Temp", params["Scatter Temp"],
                min=0.0, max=np.inf)}
        return

