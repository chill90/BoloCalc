# Built-in modules
import numpy as np
import os

# BoloCalc modules
import src.parameter as pr
import src.band as bd


class Optic:
    """
    Optic object holds the name, absorbtivity, transmission, and
    temperature for a given optic in a given optic chain

    Args:
    opt_chn (src.OpticalChain): parent OpticalChain object
    inp_dict (dict): dictionary of optic properties
    band_file (str): input band file. Defaults to 'None.'

    Attributes:
    name (str): optical element name

    Parents:
    opt_chn (src.OpticalChain): OpticalChain object
    """
    def __init__(self, opt_chn, inp_dict, band_files=None):
        # Store passed parameters
        self._opt_chn = opt_chn
        self._inp_dict = inp_dict
        self._band_files = band_files
        self._cam = self._opt_chn.cam
        self._log = self._cam.tel.exp.sim.log
        self._load = self._cam.tel.exp.sim.load
        self._phys = self._cam.tel.exp.sim.phys
        self._std_params = self._cam.tel.exp.sim.std_params
        self._nexp = self._cam.tel.exp.sim.param("nexp")
        self._nchs = len(self._cam.chs)

        # Names for the special optical elements
        self._ap_names = ["APERTURE", "STOP", "LYOT"]
        self._mirr_names = ["MIRROR", "PRIMARY", "SECONDARY"]

        # Allowed band names
        self._band_names = ["REFLECTION",
                            "ABSORPTION",
                            "SPILLOVER",
                            "SCATTERFRAC"]

        # Store parameter dict
        self._store_param_dict()
        # Store bands
        self._store_bands()

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

        # Name, which comes from a tuple ('elem', None)
        self._elem = self._param_vals["elem"]
        self.name = self._elem
        self._nfreq = len(self._ch.freqs)

        self._store_temp()
        self._store_refl()
        self._store_spill()
        self._store_spill_temp()
        self._store_scatt()
        self._store_scatt_temp()
        self._store_abso()
        self._calculate()

        return (self._elem, self._emiss, self._effic, self._temp)

    def get_param(self, param, band_ind=None):
        """ Return parameter median value """
        return self._param_dict[param].get_med(band_ind=band_ind)

    def change_param(self, param, new_val, band_ind=None, num_bands=None):
        """
        Change optic parameter value to new value

        Args:
        param (str): parameter name
        new_val (float): new parameter value
        band_ind (int): band number for this parameter
        num_bands (int): number of bands for this optic
        """
        if param not in self._param_dict.keys():
            caps_param = param.replace(" ", "").strip().upper()
            if caps_param in self._param_names.keys():
                if band_ind is not None:
                    ret_val = (
                        self._param_dict[
                            self._param_names[caps_param]].change(
                            new_val, band_ind=band_ind, num_bands=num_bands))
                else:
                    rets = []
                    for i in range(num_bands):
                        ret = (
                            self._param_dict[
                                self._param_names[caps_param]].change(
                                new_val, band_ind=i, num_bands=num_bands))
                        rets.append(ret)
                    ret_val = (np.any(rets))
                return ret_val
            else:
                self._log.err(
                    "Parameter '%s' not understood by Optic.change_param()"
                    % (str(param)))
        elif param in self._param_dict.keys():
            return (self._param_dict[param].change(
                    new_val, band_ind=band_ind, num_bands=num_bands))
        else:
            self._log.err(
                "Parameter '%s' not understood by Optic.change_param()"
                % (str(param)))

    # ***** Helper Methods *****
    def _pow_frac(self, T1, T2, freqs):
        """ Fractional power between two physical temperatures """
        return (self._phys.bb_pow_spec(freqs, T1) /
                self._phys.bb_pow_spec(freqs, T2))

    def _param_samp(self, param, band_ind):
        """ Sample optic parameter for given band """
        if self._nexp == 1:
            return param.get_med(band_ind=band_ind)
        else:
            return param.sample(band_ind=band_ind, nsample=1)

    def _store_param(self, name):
        """ Store Parameter objects for this optic """
        cap_name = name.replace(" ", "").strip().upper()
        if cap_name in self._std_params.keys():
            param = pr.Parameter(
                self._log, self._inp_dict[cap_name],
                std_param=self._std_params[cap_name],
                band_ids=self._band_ids)
            # Check that the number of bands is either equal
            # to the number of channels or a single value
            data = param.fetch(band_ind=None)
            for dat in data:
                corr_len = self._check_param_len(dat)
                if not corr_len:
                    self._log.err(
                        "Wrong parameter list length for input '%s' "
                        "for optic parameter '%s'" % (str(dat), param.name))
                else:
                    continue
            return param
        else:
            self._log.err(
                "Passed parameter in optics.txt '%s' not "
                "recognized" % (name))

    def _store_param_dict(self):
        """ Store optic parameter dictionary """
        # To label optic parameters for each band, also pass the band IDs
        self._band_ids = list(self._cam.chs.keys())
        self._param_dict = {
            "elem": self._store_param("Element"),
            "temp": self._store_param("Temperature"),
            "abs": self._store_param("Absorption"),
            "refl": self._store_param("Reflection"),
            "thick": self._store_param("Thickness"),
            "ind": self._store_param("Index"),
            "ltan": self._store_param("Loss Tangent"),
            "cond": self._store_param("Conductivity"),
            "surfr": self._store_param("Surface Rough"),
            "spill": self._store_param("Spillover"),
            "spillt": self._store_param("Spillover Temp"),
            "scatf": self._store_param("Scatter Frac"),
            "scatt": self._store_param("Scatter Temp")}
        self._param_names = {
            param.caps_name: pid for pid, param in self._param_dict.items()}
        return

    def _store_param_vals(self, ch):
        """ Sampe and store parameter values """
        self._param_vals = {}
        for k in self._param_dict.keys():
            self._param_vals[k] = self._param_samp(
                self._param_dict[k], ch.band_ind)
        return

    def _store_bands(self):
        """ Store bands for this optic """
        # Store the band files in a dictionary
        self._band_dict = {}
        if self._band_files is None:
            return
        # Store the IDs for the band files, which need to be one IDs
        # listed in self._band_names
        b_ids = ['_'.join(
            os.path.split(f)[1].split('.')[0].split('_')[1:]).upper()
            for f in self._band_files]
        # Loop over possible band names
        for b_name in self._band_names:
            # Note where the band IDs match the band name
            args = np.argwhere(np.array(b_ids) == b_name).flatten()
            # Can only have one match
            if len(args) > 1:
                self._log.err(
                    "More than one band file tagged '%s' for optic '%s': %s"
                    % (b_name, self._param_dict['elem'].get_val(),
                       np.array(self._band_names)[args]))
            elif len(args) == 1:
                # Store the full band file path keyed by the band ID
                self._band_dict[b_name] = np.array(
                    self._band_files)[args][0]
            else:
                continue
        # Log the band files being used
        if len(self._band_dict.keys()):
            self._log.log(
                "** Using band files %s for optic '%s' parameters %s"
                % (list(self._band_dict.values()),
                   self._param_dict['elem'].get_val(),
                   list(self._band_dict.keys())))
        return

    def _store_temp(self):
        """ Store temperature for this optic """
        self._temp = np.ones(self._nfreq) * self._param_vals["temp"]
        return

    def _store_refl(self):
        """ Store reflection for this optic """
        # Reflection from a band file?
        if str(self._param_dict["refl"].get_avg()).upper() == "BAND":
            self._refl = self._band_samp("REFLECTION")
        # Store reflection as a flat spectrum
        elif not self._param_vals["refl"] == "NA":
            self._refl = np.ones(self._nfreq) * self._param_vals["refl"]
        # Otherwise store zeros if reflection is 'NA'
        else:
            self._refl = np.zeros(self._nfreq)
        return

    def _store_spill(self):
        """ Store spillover for this optic """
        # Spillover from a band file?
        if str(self._param_dict["spill"].get_avg()).upper() == "BAND":
            self._spill = self._band_samp("SPILLOVER")
        # Store flat spill vs frequency
        elif not self._param_vals["spill"] == 'NA':
            self._spill = np.ones(self._nfreq) * self._param_vals["spill"]
        # Otherwise store zeros if spill is 'NA'
        else:
            self._spill = np.zeros(self._nfreq)
        return

    def _store_spill_temp(self):
        """ Store spillover temperature for this optic """
        if not self._param_vals["spillt"] == "NA":
            self._spill_temp = (np.ones(self._nfreq) *
                                self._param_vals["spillt"])
        else:
            self._spill_temp = np.ones(self._nfreq) * self._temp
        return

    def _store_scatt(self):
        """ Store scattering for this optic """
        # Scattering from a band file?
        if str(self._param_dict["scatf"].get_avg()).upper() == "BAND":
            self._scatt = self._band_samp("SCATTERFRAC")
        # Otherwise calculate using other input parameters
        elif not self._param_vals["scatf"] == "NA":
            self._scatt = np.ones(self._nfreq) * self._param_vals["scatf"]
        # Try using Ruze efficiency
        elif not self._param_vals["surfr"] == "NA":
            self._scatt = 1. - self._phys.ruze_eff(
                self._ch.freqs, self._param_vals["surfr"])
        else:
            self._scatt = np.zeros(self._nfreq)
        return

    def _store_scatt_temp(self):
        """ Store scattering temperature for this optic """
        if not self._param_vals["scatt"] == 'NA':
            self._scatt_temp = np.ones(self._nfreq) * self._param_vals["scatt"]
        else:
            self._scatt_temp = np.ones(self._nfreq) * self._temp
        return

    def _store_abso(self):
        """ Store absorption for this optic """
        elem = str(self._elem).replace(" ", "").upper()
        # Absorption from a band file?
        if str(self._param_dict["abs"].get_avg()).upper() == "BAND":
            self._abso = self._band_samp("ABSORPTION")
        # Otherwise calculate from other parameters
        # Treat the case of the aperture stop
        elif elem in self._ap_names:
            # Flat spectrum using input
            if not str(self._param_vals["abs"]) == 'NA':
                self._abso = (
                    np.ones(self._nfreq) * self._param_vals["abs"])
            else:
                # Analytic spill efficiency
                self._abso = 1. - self._phys.spill_eff(
                    self._ch.freqs, self._ch.param("pix_sz"),
                    self._ch.param("fnum"), self._ch.param("wf"))
        # Treat all other optics
        else:
            # Flat spectrum
            if not self._param_vals["abs"] == "NA":
                self._abso = np.ones(self._nfreq) * self._param_vals["abs"]
            # Ohmic efficiency if the optic is a mirror
            elif self._elem.strip().upper() in self._mirr_names:
                self._abso = 1. - self._phys.ohmic_eff(
                    self._ch.freqs, self._param_vals["cond"])
            else:
                # Dielectric loss
                if (not self._param_vals["thick"] == "NA" and
                   not self._param_vals["ind"] == "NA" and
                   not self._param_vals["ltan"] == "NA"):
                    self._abso = self._phys.dielectric_loss(
                        self._ch.freqs, self._param_vals["thick"],
                        self._param_vals["ind"], self._param_vals["ltan"])
                # Otherwise store zeros if absorption is 'NA'
                else:
                    self._abso = np.zeros(self._nfreq)
        return

    def _calculate(self):
        """ Calculate emission, efficiency and temperature for this optic """
        # Absorption array
        self._emiss = (
            self._abso +
            self._spill * self._pow_frac(
                self._spill_temp, self._temp, self._ch.freqs) +
            self._scatt * self._pow_frac(
                self._scatt_temp, self._temp, self._ch.freqs))

        # Efficiency array
        self._effic = ((1 - self._refl) * (1 - self._abso) *
                       (1 - self._spill) * (1 - self._scatt))

        # Store channel beam coupling efficiency if this is the aperture
        if self._elem.strip().upper() in self._ap_names:
            ch_eff = (np.trapz(self._effic, self._ch.freqs) /
                      float(self._ch.freqs[-1] - self._ch.freqs[0]))
            ch_taper = self._phys.edge_taper(ch_eff)
            self._ch.set_param("ap_eff", ch_eff)
            self._ch.set_param("edge_tap", ch_taper)
        return

    def _phys_lims(self, band):
        """ Forcibly set physical limits of 0 and 1 on input array """
        if band is not None:
            band = np.array([x if x > 0. else 0. for x in band])
            band = np.array([x if x < 1. else 1. for x in band])
        return band

    def _band_samp(self, key):
        """ Sample optic band """
        elem = self._param_vals["elem"]
        if key in self._band_dict.keys():
            band_f = self._band_dict[key]
            load_band = bd.Band(self._log, self._load,
                                band_f, self._ch.freqs)
            # Sample the band if number of experiment realizations
            # is greater than one; otherwise, get the average band
            if self._nexp == 1:
                samp_band = load_band.get_avg()[0]
            else:
                samp_band = load_band.sample()[0]
            # Enforce physical limits
            samp_band = self._phys_lims(samp_band)
        else:
            self._log.err(
                "'BAND' defined for parameter '%s' for optic '%s' but "
                "band file found" % (key, elem))
        return samp_band

    def _check_param_len(self, param):
        """ Check that parameter has same length as number of channels """
        if isinstance(param, list) or isinstance(param, np.ndarray):
            if not len(param) == self._nchs:
                return False
            else:
                return True
        else:
            return True
