#python Version 2.7.2
import numpy as np
import units as un

class Band:
    def __init__(self, log, bandFile, freqArr=None):
        self.log   = log
        self.ftype = bandFile.split('.')[-1]

        #Parse band file
        if 'csv' in self.ftype:
            try:    freqs, self.eff, self.err = np.loadtxt(bandFile, unpack=True, dtype=np.float, delimiter=',')
            except: freqs, self.eff,          = np.loadtxt(bandFile, unpack=True, dtype=np.float, delimiter=','); self.err = None
            if not np.all(freqs) > 1.e6: self.freqs = freqs*un.GHzToHz #Convert to Hz if band file is in GHz
            if freqArr is not None:
                mask = np.array([1. if f >= self.freqs[0] and f <= self.freqs[-1] else 0. for f in freqArr])
                self.eff   = np.interp(freqArr, self.freqs, self.eff)*mask
                if self.err is not None: self.err   = np.interp(freqArr, self.freqs, self.err)*mask
                self.freqs = freqArr
        elif 'txt' in self.ftype:
            try:    freqs, self.eff, self.err = np.loadtxt(bandFile, unpack=True, dtype=np.float)
            except: freqs, self.eff,          = np.loadtxt(bandFile, unpack=True, dtype=np.float); self.err = None
            if not np.all(freqs) > 1.e6: self.freqs = freqs*un.GHzToHz #Convert to Hz if band file is in GHz
            if freqArr is not None:
                mask = np.array([1. if f >= self.freqs[0] and f <= self.freqs[-1] else 0. for f in freqArr])
                self.eff   = np.interp(freqArr, self.freqs, self.eff)*mask
                if self.err is not None: self.err   = np.interp(freqArr, self.freqs, self.err)*mask
                self.freqs = freqArr
        else:
            self.log.log('Unable to parse band file %s.' % (bandFile), 0)
            self.freqs = None;  self.eff = None; self.err = None

        #Not allowed to have a standard deviation of zero or negative
        self.err[(self.err <= 0.)] = 1.e-6

    #***** Public Methods *****
    #Sample the band
    def sample(self, nsample=1):
        if self.eff is None: return [None]
        if self.err is None:
            return np.array([self.eff for n in range(nsample)])
        else:
            if nsample == 1: return np.array([np.random.normal(self.eff, self.err)])
            else:            return np.random.normal(self.eff, self.err, (nsample, len(self.eff)))
