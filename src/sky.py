# Built-in modules
import numpy as np
import glob as gb
import collections as cl
import os
import io
import h5py as hp
import sys as sy

# BoloCalc modules
import src.foregrounds as fg
import src.compatible as cm
# Choose fastest pickling module
comp = cm.Compatible()
if comp.PY2:
    import cPickle as pk
else:
    import pickle as pk


class Sky:
    """
    Sky object contains the foregrounds and atmosphere

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

        # Initialize foregrounds
        self._fg = fg.Foregrounds(self)
        # Store some internal parameters
        self._store_private_params()

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
            freq, Tatm, Eatm = self._atm_spectrum(pwv, elev, freqs)
            Aatm = [1. for f in freqs]
        if self.tel.exp.sim.param("infg"):
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
        if samp < self._min_pwv:
            self._log.log('Cannot have PWV %.1f < %.1f. Using %.1f instead'
                          % (samp, self._min_pwv, self._min_pwv),
                          self._log.level["NOTIFY"])
            return self._min_pwv
        elif samp > self._max_pwv:
            self._log.log('Cannot have PWV %.1f > %.1f. Using %.1f instead'
                          % (samp, self._max_pwv, self._max_pwv),
                          self._log.level["NOTIFY"])
            return self._max_pwv
        else:
            return samp

    # ***** Helper Methods *****
    def _hdf5_select(self, pwv, elev):
        site = self.tel.param("site").lower().capitalize()
        key = "%d,%d" % (pwv, elev)
        with hp.File("%s/atm.hdf5" % (self._atm_dir), "r") as hf:
            freq, depth, temp, tran = hf[site][key]
        return (freq, tran, temp)

    def _atm_spectrum(self, pwv, elev, freqs):
        GHz_to_Hz = 1.e+09
        if self.tel.param("atm_file") is not None:
            freq, tran, temp = self._load.atm(self.tel.param("atm_file"))
        else:
            freq, tran, temp = self._hdf5_select(
                int(round(pwv, 1)*1000), int(round(elev, 0)))
        freq = (freq * GHz_to_Hz).flatten().tolist()
        temp = np.interp(freqs, freq, temp).flatten().tolist()
        tran = np.interp(freqs, freq, tran).flatten().tolist()
        return freq, temp, tran

    def _syn_spectrum(self, freqs):
        return self._fg.sync_spec_rad(freqs)

    def _dst_spectrum(self, freqs):
        return self._fg.dust_spec_rad(freqs)

    def _store_private_params(self):
        self._max_pwv = 8.0
        self._min_pwv = 0.0
        self._atm_dir = os.path.join(
            os.path.split(__file__)[0], 'atmFiles')
        return
