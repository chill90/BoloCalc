# Built-in modules
import numpy as np
import sys as sy

# BoloCalc modules
import src.units as un


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
                 min=None, max=None, inp_type=np.float):
        # Store passed arguments
        self._log = log
        self.name = name
        if unit is not None:
            self.unit = unit
        else:
            self.unit = un.Units("NA")
        self._min = self._float(min)
        self._max = self._float(max)
        self.type = inp_type

        # Store the parameter value, mean, and standard deviation
        self._store_param()

        # Check that the value is within the allowed range
        self._check_range()

    # ***** Public Methods *****
    def is_empty(self):
        """ Check if a parameter is 'NA' """
        if 'NA' in str(self.avg):
            return True
        else:
            return False

    def convolve(self, param):
        """
        Multiply self.avg with param.avg
        and quadrature sum self.std with param.std
        The new avg and std replace self.avg and self.std

        Args:
        param (src.Parameter): parameter to convolve with this object.
        """
        if not self.is_empty() and not param.is_empty():
            self.avg = self.avg * param.avg
            self.std = np.sqrt(self.std**2 + param.std**2)

    def multiply(self, factor):
        """
        Multiply self.avg and self.std by factor

        Args:
        factor (float): factor to multiply self.avg and self.std by
        """
        if not self.is_empty():
            self.avg = self.avg * factor
            self.std = self.std * factor

    def fetch(self, band_id=1):
        """
        Return self.avg and self.std given a band_id,
        or return the parameter value

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        if self._val is not None:
            return self._val
        elif self.is_empty():
            return ('NA', 'NA')
        else:
            if 'array' in str(type(self.avg)):
                return (self.avg[band_id - 1], self.std[band_id - 1])
            else:
                return (self.avg, self.std)

    def change(self, new_avg, new_std=None, band_id=1):
        """
        Change self.avg to new_avg and self.std to new_std

        Args:
        new_avg (int or list): new
        """
        if 'array' in str(type(self.avg)):
            self.avg[band_id-1] = self.unit.to_SI(new_avg)
            if new_std is not None:
                self.std[band_id-1] = self.unit.to_SI(new_std)
        else:
            self.avg = self.unit.to_SI(new_avg)
            if new_std is not None:
                self.std = self.unit.to_SI(new_std)

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
        if self.is_empty():
            return 'NA'
        elif isinstance(self._val, Distribution):
            return self._val.sample()
        else:
            avg, std = self.fetch(band_id)
            if np.any(std <= 0.):
                return avg
            else:
                if nsample == 1:
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
        try:
            return self.unit.to_SI(float(val))
        except:
            try:
                return self.unit.to_SI(np.array(eval(val)).astype(np.float))
            except:
                return str(val)

    def _zero(self, val):
        """Convert val to an array of or single zero(s)"""
        try:
            return np.zeros(len(val))
        except:
            return 0.

    def _check_range(self):
        if self.avg is None:
            return True
        else:
            if np.any(self._avg < self._min):
                self.log.err(
                    "Passed value %f for parameter %s lower than the mininum \
                    allowed value %f" % (self.avg, self.name, self._min), 0)
            elif np.any(self._avg > self._max):
                self.log.err(
                    "Passed value %f for parameter %s greater than the maximum \
                    allowed value %f" % (self.avg, self.name, self._max), 0)
            else:
                return True

    def _store_param(self):
        if self.type is bool:
            self._val = self._bool(inp)
            self._avg = None
            self._std = None
        elif self.type is np.float or self.type is np.int:
            if isinstance(inp, str):
                self._spread_delim = '+/-'
                if self._spread_delim in inp:
                    self._val = None
                    values = inp.split(self._spread_delim)
                    self._avg = self._float(vals[0])
                    self._std = self._float(vals[1])
                else:
                    self._val = None
                    self._avg = self._float(inp)
                    self._std = self._zero(self.avg)
            elif isinstance(inp, Distribution):
                self._val = inp
                self._avg = inp.mean()
                self._std = inp.std()
        elif self.type is np.str:
            self._val = str(inp)
            self._avg = None
            self._std = None
        else:
            self.log.err(
                "Passed paramter '%s' not one of allowed data types: \
                bool, np.float, np.int, np.str" % (self.name))
        return True
