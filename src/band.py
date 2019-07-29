# Built-in modules
import numpy as np


class Band:
    """
    Band object contains transmission vs frequency, with errrors
    for detectors and optics

    Args:
    log (src.Log): Log object
    load (src.Load): Load object
    band_file (str): band file to be loaded
    freq_inp (list): frequencies at which to evaluate the band.
    Defaults to None.

    Attributes:
    freqs (list): list of frequencies [Hz] for this band
    """
    def __init__(self, log, load, band_file, freq_inp=None):
        # Store passed parameters
        self._log = log
        self._load = load
        self._band_file = band_file
        self._freq_inp = freq_inp
        self._ftype = band_file.split('.')[-1]

        # Parse band file
        self._load_band()
        self._store_data()

    # ***** Public Methods *****
    def get_avg(self, nsample=1):
        """
        Return the average transmission for each frequency

        Args:
        nsample (int): number of lists to return
        """
        return np.array([self._tran for n in range(nsample)])

    def sample(self, nsample=1):
        """
        Return a sampled of the band transmission given its errors

        Args:
        nsample (int): number of sample lists to return
        """
        if self._tran is None:
            return [None]
        if self._err is None:
            return self.get_avg(nsample)
        else:
            if nsample == 1:
                return np.array([np.random.normal(self._tran, self._err)])
            else:
                return np.random.normal(self._tran, self._err,
                                        (nsample, len(self._tran)))

    def interp_freqs(self, freq_inp):
        if freq_inp is not None:
            mask = (freq_inp < self._freqs[-1]) * (
                freq_inp > self._freqs[0])
            self._tran = np.interp(
                freq_inp, self._freqs, self._tran) * mask
            if self._err is not None:
                self._err = np.interp(
                    freq_inp, self._freqs, self._err) * mask
            self.freqs = freq_inp
        else:
            self.freqs = self._freqs
        return

    # ***** Helper Methods *****
    def _load_band(self):
        try:
            data = self._load.band(self._band_file)
            if len(data) == 3:
                self._freqs, self._tran, self._err = data
            elif len(data) == 2:
                self._freqs, self._tran = data
                self._err = None
            else:
                self._log.err(
                    "Could not understand band CSV file '%s'. \
                    Too many or too few colums." % (self._band_file))
        except:
            self._log.err('Unable to parse band file %s.' % (self._band_file))
        return

    def _store_data(self):
        # Convert to Hz if band file is in GHz
        if not np.all(self._freqs) > 1.e5:
            self._freqs = self._freqs * 1.e+09
        # Equalize arrays
        self.interp_freqs(self._freq_inp)
        # Not allowed to have a standard deviation of zero or negative
        if self._err is not None:
            self._err[(self._err <= 0.)] = 1.e-6
        return
