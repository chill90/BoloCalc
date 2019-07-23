# Built-in modules
import numpy as np

# BoloCalc modules
import src.loader as ld
import src.units as un


class Band:
    def __init__(self, band_file, freq_inp=None):
        self.ftype = self.band_file.split('.')[-1]
        self._load = ld.Loader()

        # Parse band file
        try:
            data = self._load.band(band_file)
            if len(data) == 3:
                freqs, self.eff, self.err = data
            elif len(data) == 2:
                freqs, self.eff = data
                self.err = None
            else:
                raise Exception(
                    "Could not understand band CSV file '%s'. \
                    Too many or too few colums." % (self.band_file))
        except:
            raise Exception('Unable to parse band file %s.' % (self.band_file))

        # Convert to Hz if band file is in GHz
        if not np.all(freqs) > 1.e5:
            self.freqs = freqs * 1.e+09
        # Equalize arrays
        if freq_inp is not None:
            mask = np.array([1. if f >= self.freqs[0] and
                             f <= self.freqs[-1] else 0. for f in freq_inp])
            self.eff = np.interp(freq_inp, self.freqs, self.eff) * mask
            if self.err is not None:
                self.err = np.interp(freq_inp, self.freqs, self.err) * mask
            self.freqs = freq_inp

        # Not allowed to have a standard deviation of zero or negative
        if self.err is not None:
            self.err[(self.err <= 0.)] = 1.e-6

    # ***** Public Methods *****
    # Return the average efficiency
    def get_avg(self, nsample=1):
        return np.array([self.eff for n in range(nsample)])

    # Sample the band
    def sample(self, nsample=1):
        if self.eff is None:
            return [None]
        if self.err is None:
            return self.getAvg(nsample)
        else:
            if nsample == 1:
                return np.array([np.random.normal(self.eff, self.err)])
            else:
                return np.random.normal(self.eff, self.err,
                                        (nsample, len(self.eff)))
