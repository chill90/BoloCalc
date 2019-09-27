# Built-in modules
import numpy as np
import copy as cp


class Band:
    """
    Band object contains transmission vs frequency, with errrors
    for detectors and optics

    Args:
    log (src.Log): parent Log object
    load (src.Load): parent Load object
    band_file (str): band file to be loaded
    freq_inp (list): frequencies at which to evaluate the band.
    Defaults to None.

    Attributes:
    freqs (list): list of frequencies [Hz] for this band

    Parents:
    log (src.Log): parent Log object
    load (src.Load): parent Load object
    """
    def __init__(self, log, load, band_file, freq_inp=None):
        # Store passed parameters
        self._log = log
        self._load = load
        self._band_file = band_file
        self._freq_inp = freq_inp
        self._ftype = band_file.split('.')[-1]

        self._log.log(
            "Processing band file %s" % (self._band_file))
        # Parse band file
        self._load_band()
        self._store_data()

    # ***** Public Methods *****
    def get_avg(self, nsample=1):
        """
        Return the average spectrum

        Args:
        nsample (int): number of lists to return
        """
        ret_arr = np.array([self._band for n in range(nsample)])
        ret_arr = self._check_range(ret_arr)
        return ret_arr

    def sample(self, nsample=1):
        """
        Return a sampled spectrum given its errors

        Args:
        nsample (int): number of sample lists to return
        """
        # Return the average if no errors are defined
        if self._err is None:
            return self.get_avg(nsample)
        # Otherwise, sample assuming data at each frequency is Gaussian
        else:
            if nsample == 1:
                ret_arr = np.array([np.random.normal(self._band, self._err)])
            else:
                ret_arr = np.random.normal(self._band, self._err,
                                           (nsample, len(self._band)))
        ret_arr = self._check_range(ret_arr)
        return ret_arr

    def interp_freqs(self, freq_inp):
        """
        Interpolate the band to the passed frequencies

        Args:
        freq_inp (list): frequencies for the band to interpolated to
        """
        # If the input array isn't None, interpolate the band to it
        if freq_inp is not None:
            # Don't extrapolate outside of band's defined frequency range
            mask = (freq_inp < self._freqs[-1]) * (
                freq_inp > self._freqs[0])
            # Interpolate the band
            self._band = np.interp(
                freq_inp, self._freqs, self._band) * mask
            # Interpolate the errors, if there are any
            if self._err is not None:
                self._err = np.interp(
                    freq_inp, self._freqs, self._err) * mask
            self.freqs = freq_inp
            self.tran = self._band
        # Otherwise, don't do anything
        else:
            self.freqs = self._freqs
            self.tran = self._band
        return

    # ***** Helper Methods *****
    def _load_band(self):
        """ Load band data """
        # Load the data
        data = self._load.band(self._band_file)
        # Check for error bars
        if len(data) == 3:
            self._freqs, self._band, self._err = data
        elif len(data) == 2:
            self._freqs, self._band = data
            self._err = None
        else:
            self._log.err(
                "Could not understand band CSV file '%s'. \
                Too many or too few colums." % (self._band_file))
        return

    def _store_data(self):
        """ Store the loaded data in SI units """
        # Convert to Hz if band file is in GHz
        if not np.all(self._freqs) > 1.e5:
            self._freqs = self._freqs * 1.e+09
        # Equalize arrays
        self.interp_freqs(self._freq_inp)
        # Not allowed to have a standard deviation of zero or negative
        if self._err is not None:
            self._err[(self._err <= 0.)] = 1.e-6
        # Not allowed to have band values < 0 or > 1
        self._band = self._check_range(self._band)
        return

    def _check_range(self, arr):
        ret_arr = cp.deepcopy(arr)
        ret_arr = np.where(ret_arr < 0, 0., ret_arr)
        ret_arr = np.where(ret_arr > 1, 1., ret_arr)
        return ret_arr
