# Built-in modules
import numpy as np
import glob as gb
import collections as cl
import sys as sy
import os
import io

# BoloCalc modules
import src.foregrounds as fg
import src.compatible as cm
# Choose fastest pickling module
if cm.Compatible().PY2:
    import cPickle as pk
else:
    import pickle as pk


class Sky:
    def __init__(self, tel):
        # Store passed parameters
        self.tel = tel

        self.fg = fg.Foregrounds(self)
        self.nfiles = 20  # Number of files to break .pkl file into
        self.medianPwv = 0.934  # Atacama, as defined by the MERRA-2 dataset
        self.maxPWV = 8.0
        self.minPWV = 0.0
        self.atmDir = os.path.join(
            os.path.split(__file__)[0], 'atmFiles')
        self.siteDirs = sorted(gb.glob(os.path.join(
            self.atmDir, '*' + os.sep)))
        self.siteNames = np.array(
            [siteDir.split(os.sep)[-2] for siteDir in self.siteDirs])
        self.siteDirs = {self.siteNames[i]: self.siteDirs[i]
                         for i in range(len(self.siteNames))}

        if not self.site.upper() == 'SPACE':
            self._init_atm(create=False)

    # ***** Public methods ******
    # Sample PWV distribution
    def pwv_sample(self):
        samp = tel.fetch("pwv").sample()
        if samp < self.minPWV:
            self.log.log('Cannot have PWV %.1f < %.1f. Using %.1f instead'
                         % (samp, self.minPWV, self.minPWV), 2)
            return self.minPWV
        elif samp > self.maxPWV:
            self.log.log('Cannot have PWV %.1f > %.1f. Using %.1f instead'
                         % (samp, self.maxPWV, self.maxPWV), 2)
            return self.maxPWV
        else:
            return samp

    # Retrieve user-defined PWV value
    def get_pwv(self):
        return self.pwv

    # Retrieve ATM spectrum given some PWV, elevation, and array of frequencies
    def atm_spectrum(self, pwv, elev, freqs):
        self._GHz_to_Hz = 1.e+09
        if self.tel.atmFile is not None
            freq, tran, temp = self._load().atm(self.tel.atmFile)
        else:
            freq, temp, tran = self.atm_dict[
                (int(round(elev, 0)), round(pwv, 1))]
        freq = freq*self._GHz_to_Hz.flatten().tolist()
        temp = np.interp(freqs, freq, temp).flatten().tolist()
        tran = np.interp(freqs, freq, tran).flatten().tolist()
        return freq, temp, tran

    # Retrieve synchrotron spectrum given some array of frequencies
    def syn_spectrum(self, freqs):
        return self.fg.sync_spec_rad(freqs)

    # Retrieve dust spectrum given some array of frequencies
    def dst_spectrum(self, freqs):
        return self.fg.dust_spec_rad(freqs)

    # Generate the sky
    def generate(self, pwv, elev, freqs):
        self.Ncmb = ['CMB' for f in freqs]
        self.Tcmb = [2.725 for f in freqs]
        self.Ecmb = [1. for f in freqs]
        self.Acmb = [1. for f in freqs]
        if not self.site.upper() == 'SPACE':
            self.Natm = ['ATM' for f in freqs]
            freq, self.Tatm, self.Eatm = self.atmSpectrum(pwv, elev, freqs)
            self.Aatm = [1. for f in freqs]
        if self.inclF:
            self.Nsyn = ['SYNC' for f in freqs]
            self.Tsyn = self.synSpectrum(freqs)
            self.Esyn = [1. for f in freqs]
            self.Asyn = [1. for f in freqs]
            self.Ndst = ['DUST' for f in freqs]
            self.Tdst = self.dstSpectrum(freqs)
            self.Edst = [1. for f in freqs]
            self.Adst = [1. for f in freqs]
            if not self.site.upper() == 'SPACE':
                return ([self.Ncmb, self.Nsyn, self.Ndst, self.Natm],
                        [self.Acmb, self.Asyn, self.Adst, self.Aatm],
                        [self.Ecmb, self.Esyn, self.Edst, self.Eatm],
                        [self.Tcmb, self.Tsyn, self.Tdst, self.Tatm])
            else:
                return ([self.Ncmb, self.Nsyn, self.Ndst],
                        [self.Acmb, self.Asyn, self.Adst],
                        [self.Ecmb, self.Esyn, self.Edst],
                        [self.Tcmb, self.Tsyn, self.Tdst])
        else:
            if not self.site.upper() == 'SPACE':
                return ([self.Ncmb, self.Natm],
                        [self.Acmb, self.Aatm],
                        [self.Ecmb, self.Eatm],
                        [self.Tcmb, self.Tatm])
            else:
                return ([self.Ncmb],
                        [self.Acmb],
                        [self.Ecmb],
                        [self.Tcmb])

    # ***** Private methods *****
    # Initialize atmosphere.
    # If "create" is True, then create pickle files from text files of spectra
    def _init_atm(self, create=False):
        self._um_to_mm = 1.e-3
        if create:
            atmFileArrs = {site: np.array(sorted(gb.glob(os.path.join(
                self.siteDirs[site], 'TXT', 'atm*.txt'))))
                for site in self.siteNames}
            self.elevArrs = {site: np.array([float(
                os.path.split(atmFile)[-1].split('_')[1][:2])
                for atmFile in atmFileArrs[site]])
                for site in self.siteNames}
            self.pwvArrs = {site: np.array([float(
                os.path.split(atmFile)[-1].split('_')[2][:4]) *
                self._um_to_mm
                for atmFile in atmFileArrs[site]])
                for site in self.siteNames}
            self.atm_dicts = cl.OrderedDict({})
            for site in self.siteNames:
                freqArr, tempArr, tranArr = np.hsplit(np.array(
                    [np.loadtxt(atmFile, usecols=[0, 2, 3], unpack=True)
                     for atmFile in atmFileArrs[site]]), 3)
                self.atm_dicts[site] = {
                    (int(round(self.elevArrs[site][i])),
                     round(self.pwvArrs[site][i], 1)): (
                         freqArr[i][0], tempArr[i][0], tranArr[i][0])
                    for i in range(len(atmFileArrs[site]))}
                for i in range(self.nfiles):
                    sub_dict = self.atm_dicts[site].items()[i::self.nfiles]
                    pk.dump(sub_dict, open(os.path.join(
                        self.siteDirs[site], 'PKL',
                        ('atmDict_%d.pkl' % (i))), 'wb'))
            self.atm_dict = self.atm_dicts[self.site]
        else:
            self.atm_dict = {}
            for i in range(self.nfiles):
                if self.cm.PY2:
                    sub_dict = pk.load(open(os.path.join(
                        self.siteDirs[self.site], 'PKL',
                        ('atmDict_%d.pkl' % (i))), 'rb'))
                else:
                    sub_dict = pk.load(io.open(os.path.join(
                        self.siteDirs[self.site], 'PKL',
                        ('atmDict_%d.pkl' % (i))), 'rb'), encoding='latin1')
                self.atm_dict.update(sub_dict)
