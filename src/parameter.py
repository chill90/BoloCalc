# Built-in modules
import numpy as np
import sys as sy


class Parameter:
    """
    The Parameter object contains attributes for input and output parameters.
    If 'input' argument is a float, one band is assumed; if it is a list, 
    len(list) bands are assumed.

    Args:
    log (src.Logging): logging object
    name (str): parameter name
    input (float or list): parameter value
    unit (src.Unit): parameter unit, conversion to SI
    min (float): minimum allowed value. Defaults to None
    max (float): maximum allowe value. Defaults to None
    type (type): parameter data type. Defaults to numpy.float

    Attributes:
    log (src.Logging): where the 'log' arg is stored
    name (str): where the 'name' arg is stored
    input (float or list): where the 'input' arg is stored
    unit (src.Unit): where the 'unit' arg is stored
    min (float): where the 'min' arg is stored
    max (float): where the 'max' arg is stored
    type (type): where the 'type' arg is stored
    """

    def __init__(self, log, name, input, unit=1.0,
                 min=None, max=None, type=np.float):
        # Store passed arguments
        self.log = log
        self.name = name
        self.inst = input
        self.unit = unit
        self.min = self._float(min)
        self.max = self._float(max)
        self.type = type

        # Store the parameter mean and standard deviation
        self._spread_delim = '+/-'
        if self._spread_delim in input:
            vals = input.split(self._spread_delim)
            self.avg = self._float(vals[0], self.unit)
            self.std = self._float(vals[1], self.unit)
        else:
            self.avg = self._float(input,   self.unit)
            self.std = self._zero(self.avg)

        # Check that the value is within the allowed range.
        if not isinstance(self.avg, str):
            if np.any(self.avg < self.min):
                self.log.log(
                    "Passed value %f for parameter %s lower than the mininum \
                    allowed value %f" % (self.avg, self.name, self.min), 0)
                sy.exit(1)
            elif np.any(self.avg > self.max):
                self.log.log(
                    "Passed value %f for parameter %s greater than the maximum \
                    allowed value %f" % (self.avg, self.name, self.max), 0)
                sy.exit(1)

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
        Return self.avg and self.std given a band_id

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        if self.is_empty():
            return ('NA', 'NA')
        else:
            if 'array' in str(type(self.avg)):
                return (self.avg[band_id-1], self.std[band_id-1])
            else:
                return (self.avg, self.std)

    def change(self, new_avg, new_std=None, band_id=1):
        """
        Change self.avg to new_avg and self.std to new_std

        Args:
        new_avg (int or list): new
        """
        if 'array' in str(type(self.avg)):
            self.avg[band_id -1] = new_avg * self.unit
            if new_std is not None:
                self.std[band_id -1] = new_std * self.unit
        else:
            self.avg = new_avg * self.unit
            if new_std is not None:
                self.std = new_std * self.unit

    def get_avg(self, band_id=1):
        return self.fetch(band_id)[0]

    def get_std(self, band_id =1):
        return self.fetch(band_id)[1]

    def sample(self, band_id=1, nsample=1, min=None, max=None):
        if self.is_empty():
            return 'NA'
        else:
            avg, std = self.fetch(band_id)
            if np.any(std <= 0.):
                return avg
            else:
                if nsample == 1:
                    samp = np.random.normal(avg, std, nsample)[0]
                else:
                    samp = np.random.normal(avg, std, nsample)

            if min is not None:
                if samp < min:
                    return min
            if max is not None:
                if samp > max:
                    return max
            return samp

    # ***** Private Methods *****
    def _float(self, val, unit=1.0):
        try:
            return unit*float(val)
        except:
            try:
                return unit*np.array(eval(val)).astype(np.float)
            except:
                return str(val)

    def _zero(self, val):
        try:
            return np.zeros(len(val))
        except:
            return 0.
