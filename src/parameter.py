# Built-in modules
import numpy as np
import sys as sy

# BoloCalc modules
import src.unit as un
import src.distribution as ds


class Parameter:
    """
    Parameter object contains attributes for input and output parameters.
    If 'inp' argument is a float, one band is assumed; if it is a list,
    len(list) bands are assumed.

    Args:
    log (src.Logging): logging object
    name (str): parameter name
    inp (str or src.Distribution): parameter value(s)
    unit (src.Unit): parameter unit. Defaults to src.Unit('NA')
    min (float): minimum allowed value. Defaults to None
    max (float): maximum allowe value. Defaults to None
    type (type): cast parameter data type. Defaults to numpy.float

    Attributes:
    name (str): where the 'name' arg is stored
    unit (src.Unit): where the 'unit' arg is stored
    type (type): where the 'type' arg is stored
    """

    def __init__(self, log, name, inp, unit=None,
                 min=None, max=None, inp_type=float):
        # Store passed arguments
        self._log = log
        self.name = name
        if unit is not None:
            self.unit = unit
        else:
            self.unit = un.Unit("NA")
        self._min = self._float(min)
        self._max = self._float(max)
        self._type = inp_type

        # Store the parameter value, mean, and standard deviation
        self._store_param(inp)
        # Check that the value is within the allowed range
        self._check_range()

    # ***** Public Methods *****
    def is_empty(self):
        """ Check if a parameter is 'NA' """
        if 'NA' in str(self._avg):
            return True
        else:
            return False

    def convolve(self, param):
        """
        Multiply self._avg with param.avg
        and quadrature sum self._std with param.std
        The new avg and std replace self._avg and self._std

        Args:
        param (src.Parameter): parameter to convolve with this object.
        """
        if not self.is_empty() and not param.is_empty():
            self._avg = self._avg * param.avg
            self._std = np.sqrt(self._std**2 + param.std**2)

    def multiply(self, factor):
        """
        Multiply self._avg and self._std by factor

        Args:
        factor (float): factor to multiply self._avg and self._std by
        """
        if not self.is_empty():
            self._avg = self._avg * factor
            self._std = self._std * factor

    def fetch(self, band_id=1):
        """
        Return (avg, std) given a band_id, or return (val)

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        if self._val is not None:
            return (self._val, 0.)
        elif self.is_empty():
            return ('NA', 'NA')
        else:
            if type(self._avg) is np.ndarray:
                return (self._avg[band_id - 1], self._std[band_id - 1])
            else:
                return (self._avg, self._std)

    def change(self, new_avg, new_std=None, band_id=1):
        """
        Change self._avg to new_avg and self._std to new_std

        Args:
        new_avg (int or list): new
        """
        if type(self._avg) is np.ndarray:
            self._avg[band_id-1] = self.unit.to_SI(new_avg)
            if new_std is not None:
                self._std[band_id-1] = self.unit.to_SI(new_std)
        else:
            self._avg = self.unit.to_SI(new_avg)
            if new_std is not None:
                self._std = self.unit.to_SI(new_std)

    def get_val(self):
        """ Return the input value """
        return self._val

    def get_avg(self, band_id=1):
        """
        Return average value for band_id

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        return self.fetch(band_id)[0]

    def get_std(self, band_id=1):
        """
        Return standard deviation for band_id

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        return self.fetch(band_id)[1]

    def sample(self, band_id=1, nsample=1, min=None, max=None):
        """
        Sample parameter distribution for band_id nsample times
        and return the sampled values in an array if nsample > 1
        or as a float if nsample = 1.

        Args:
        band_id (int): band ID indexes from 1. Defaults to 1.
        nsample (int): number of samples to draw from distribution
        min (float): the minimum allowed value to be returned
        max (float): the maximum allowed value to be returned
        """
        if min is None:
            min = self._min
        if max is None:
            max = self._max
        if self.is_empty():
            return 'NA'
        elif isinstance(self._val, ds.Distribution):
            return self._val.sample()
        else:
            avg, std = self.fetch(band_id)
            if np.any(std <= 0.):
                return avg
            else:
                if nsample == 1:
                    #print("taking a real sample of %s"
                    #      "with avg %f an std %f"
                    #      % (self.name, avg, std))
                    samp = np.random.normal(avg, std, nsample)[0]
                else:
                    samp = np.random.normal(avg, std, nsample)

            if min is not None and samp < min:
                return min
            if max is not None and samp > max:
                return max
            return samp

    # ***** Private Methods *****
    def _float(self, val):
        """Convert val to an array of or single float(s)"""
        if val is None:
            return None
        try:
            return self.unit.to_SI(float(val))
        except:
            try:
                return self.unit.to_SI(
                    np.array(eval(val)).astype(float))
            except:
                return str(val)

    def _zero(self, val):
        """Convert val to an array of or single zero(s)"""
        try:
            return np.zeros(len(val))
        except:
            return 0.

    def _check_range(self):
        if self._avg is None or isinstance(self._avg, str):
            return True
        else:
            avg = np.array(self._avg)
            if self._min is not None and np.any(avg < self._min):
                self.log.err(
                    "Passed value %s for parameter %s lower than the mininum \
                    allowed value %f" % (
                        str(self._avg), self.name, self._min), 0)
            elif self._max is not None and np.any(avg > self._max):
                self.log.err(
                    "Passed value %s for parameter %s greater than the maximum \
                    allowed value %f" % (
                        str(self._avg), self.name, self._max), 0)
            else:
                return True

    def _store_param(self, inp):
        if self._type is bool:
            self._val = bool(eval(inp.lower().capitalize()))
            self._avg = None
            self._std = None
        elif self._type is float:
            if isinstance(inp, str):
                self._spread_delim = '+/-'
                if self._spread_delim in inp:
                    self._val = None
                    vals = inp.split(self._spread_delim)
                    self._avg = self._float(vals[0])
                    self._std = self._float(vals[1])
                else:
                    self._val = self._float(inp)
                    self._avg = self._float(inp)
                    self._std = self._zero(self._avg)
            elif isinstance(inp, Distribution):
                self._val = inp
                self._avg = inp.mean()
                self._std = inp.std()
        elif self._type is int:
            self._val = int(inp)
            self._avg = None
            self._std = None
        elif self._type is str:
            self._val = str(inp)
            self._avg = None
            self._std = None
        else:
            self.log.err(
                "Passed paramter '%s' not one of allowed data types: \
                bool, np.float, np.int, np.str" % (self.name))
        return True
