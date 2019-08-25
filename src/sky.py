# Built-in modules
import numpy as np
import glob as gb
import os
import io
import h5py as hp
import sys as sy

# BoloCalc modules
import src.foregrounds as fg


class Sky:
    """
    Sky object contains the foregrounds and atmosphere
    added line

    Args:
    tel (src.Telescope): Telescope object

    Attributes:
    tel (src.Telescope): there arg 'tel' is stored
    """
    def __init__(self, tel):
        # Store passed parameters
        self.tel = tel
        self._log = self.tel.exp.sim.log
        self._load = self.tel.exp.sim.load
        self._infg = self.tel.exp.sim.param("infg")

        # Initialize foregrounds
        if self._infg:
            self._log.log(
                "Initializing foregrounds in Sky object")
            self._fg = fg.Foregrounds(self)
        else:
            self._fg = None
        # Maximum and minimum allowed PWV
        self._max_pwv = 8.0
        self._min_pwv = 0.0
        # Directory which holds the ATM files
        self._atm_dir = os.path.join(
            os.path.split(__file__)[0], 'atmFiles')

    # ***** Public Methods ******
    def evaluate(self, pwv, elev, freqs):
        """
        Generate the sky elements, absorbtivities, transmissions,
        and temperatures

        Args:
        pwv (float): PWV
        elev (float): elevation
        freqs (float): frequencies [Hz] at which to evlauate the sky
        """
        Ncmb = ['CMB' for f in freqs]
        Tcmb = [2.725 for f in freqs]
        Ecmb = [1. for f in freqs]
        Acmb = [1. for f in freqs]
        if not self.tel.param("site").upper() == 'SPACE':
            Natm = ['ATM' for f in freqs]
            Tatm, Eatm = self._atm_spectrum(pwv, elev, freqs)[1:]
            Aatm = [1. for f in freqs]
        if self._infg:
            Nsyn = ['SYNC' for f in freqs]
            Tsyn = self._syn_spectrum(freqs)
            Esyn = [1. for f in freqs]
            Asyn = [1. for f in freqs]
            Ndst = ['DUST' for f in freqs]
            Tdst = self._dst_spectrum(freqs)
            Edst = [1. for f in freqs]
            Adst = [1. for f in freqs]
            if not self.tel.param("site").upper() == 'SPACE':
                return [[Ncmb, Nsyn, Ndst, Natm],
                        [Acmb, Asyn, Adst, Aatm],
                        [Ecmb, Esyn, Edst, Eatm],
                        [Tcmb, Tsyn, Tdst, Tatm]]
            else:
                return [[Ncmb, Nsyn, Ndst],
                        [Acmb, Asyn, Adst],
                        [Ecmb, Esyn, Edst],
                        [Tcmb, Tsyn, Tdst]]
        else:
            if not self.tel.param("site").upper() == 'SPACE':
                return [[Ncmb, Natm],
                        [Acmb, Aatm],
                        [Ecmb, Eatm],
                        [Tcmb, Tatm]]
            else:
                return [[Ncmb],
                        [Acmb],
                        [Ecmb],
                        [Tcmb]]

    def pwv_sample(self):
        """ Sample the PWV distribution """
        samp = self.tel.pwv_sample()
        # Minimum allowed PWV is 0 mm
        if samp < self._min_pwv:
            self._log.log('Cannot have PWV %.1f < %.1f. Using %.1f instead'
                          % (samp, self._min_pwv, self._min_pwv))
            return self._min_pwv
        # Maximum allowed PWV is 8 mm
        elif samp > self._max_pwv:
            self._log.log('Cannot have PWV %.1f > %.1f. Using %.1f instead'
                          % (samp, self._max_pwv, self._max_pwv))
            return self._max_pwv
        else:
            return samp

    # ***** Helper Methods *****
    def _hdf5_select(self, pwv, elev):
        """ Retrieve ATM spectrum from HDF5 file """
        # Two-level dictionary structure in the HDF5 file
        site = self.tel.param("site").lower().capitalize()
        key = "%d,%d" % (pwv, elev)
        with hp.File("%s/atm.hdf5" % (self._atm_dir), "r") as hf:
            data = hf[site][key]
            freq = data[0]
            temp = data[2]
            tran = data[3]
        return (freq, tran, temp)

    def _atm_spectrum(self, pwv, elev, freqs):
        """ Atmosphere spectrum given a PWV and elevation """
        GHz_to_Hz = 1.e+09
        m_to_mm = 1.e+03
        mm_to_um = 1.e+03
        # Load custom ATM file if present
        if self.tel.param("atm_file") is not None:
            freq, tran, temp = self._load.atm(self.tel.param("atm_file"))
        # Otherwise, select the atmosphere from the HDF5 file
        else:
            freq, tran, temp = self._hdf5_select(
                int(round(pwv * m_to_mm, 1) * mm_to_um),
                int(round(elev, 0)))
        # Massage arrays
        freq = (freq * GHz_to_Hz).flatten().tolist()
        temp = np.interp(freqs, freq, temp).flatten().tolist()
        tran = np.interp(freqs, freq, tran).flatten().tolist()
        return freq, temp, tran

    def _syn_spectrum(self, freqs):
        """ Synchrotron spectrum """
        return self._fg.sync_spec_rad(freqs)

    def _dst_spectrum(self, freqs):
        """ Dust spectrum """
        return self._fg.dust_spec_rad(freqs)

