# Built-in modules
import numpy as np
import glob as gb
import collections as cl
import os
import io

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
    elem (list): list of sky element names
    abso (list): list of sky element absorbtivities
    tran (list): list of sky element transmissions
    temp (list): list of sky element temperatures
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
        # Initialize the atmosphere
        if not self.tel.param("site").upper() == 'SPACE':
            self._init_atm(create=False)

    # ***** Public Methods ******
    # Generate the sky
    def generate(self, pwv, elev, freqs):
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
    def _atm_spectrum(self, pwv, elev, freqs):
        GHz_to_Hz = 1.e+09
        if self.tel.param("atm_file") is not None:
            freq, tran, temp = self._load.atm(self.tel.param("atm_file"))
        else:
            freq, temp, tran = self._atm_dict[
                (int(round(elev, 0)), round(pwv, 1))]
        freq = (freq * GHz_to_Hz).flatten().tolist()
        temp = np.interp(freqs, freq, temp).flatten().tolist()
        tran = np.interp(freqs, freq, tran).flatten().tolist()
        return freq, temp, tran

    def _syn_spectrum(self, freqs):
        return self._fg.sync_spec_rad(freqs)

    def _dst_spectrum(self, freqs):
        return self._fg.dust_spec_rad(freqs)

    def _init_atm(self, create=False):
        um_to_mm = 1.e-3
        n_files = 20  # Number of files to break .pkl file into
        if create:
            atm_file_arrs = {site: np.array(sorted(gb.glob(os.path.join(
                self._site_dirs[site], 'TXT', 'atm*.txt'))))
                for site in self._site_names}
            elev_arrs = {site: np.array([float(
                os.path.split(atm_file)[-1].split('_')[1][:2])
                for atm_file in atm_file_arrs[site]])
                for site in self._site_names}
            pwv_arrs = {site: np.array([float(
                os.path.split(atm_file)[-1].split('_')[2][:4]) *
                um_to_mm
                for atm_file in atm_file_arrs[site]])
                for site in self._site_names}
            atm_dicts = cl.OrderedDict({})
            for site in self._site_names:
                freq_arr, temp_arr, tran_arr = np.hsplit(np.array(
                    [np.loadtxt(atm_file, usecols=[0, 2, 3], unpack=True)
                     for atm_file in atm_file_arrs[site]]), 3)
                atm_dicts[site] = {
                    (int(round(elev_arrs[site][i])),
                     round(pwv_arrs[site][i], 1)): (
                         freq_arr[i][0], temp_arr[i][0], tran_arr[i][0])
                    for i in range(len(atm_file_arrs[site]))}
                for i in range(n_files):
                    sub_dict = atm_dicts[site].items()[i::n_files]
                    pk.dump(sub_dict, open(os.path.join(
                        self._site_dirs[site], 'PKL',
                        ('atmDict_%d.pkl' % (i))), 'wb'))
            self._atm_dict = atm_dicts[self.site]
        else:
            site = self.tel.param("site").upper()
            self._atm_dict = {}
            for i in range(n_files):
                if comp.PY2:
                    sub_dict = pk.load(open(os.path.join(
                        self._site_dirs[site], 'PKL',
                        ('atmDict_%d.pkl' % (i))), 'rb'))
                else:
                    sub_dict = pk.load(io.open(os.path.join(
                        self._site_dirs[site], 'PKL',
                        ('atmDict_%d.pkl' % (i))), 'rb'), encoding='latin1')
                self._atm_dict.update(sub_dict)

    def _store_private_params(self):
        self._max_pwv = 8.0
        self._min_pwv = 0.0
        self._atm_dir = os.path.join(
            os.path.split(__file__)[0], 'atmFiles')
        self._site_dirs = sorted(gb.glob(os.path.join(
            self._atm_dir, '*' + os.sep)))
        self._site_names = np.array(
            [site_dir.split(os.sep)[-2] for site_dir in self._site_dirs])
        self._site_dirs = {self._site_names[i].upper(): self._site_dirs[i]
                           for i in range(len(self._site_names))}
        return
