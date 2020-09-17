# Built-in modules
import numpy as np


class Distribution:
    """
    Distribution object holds probability distribution functions (PDFs)
    for instrument parameters

    Args:
    inp (str or arr): file name for the input PDF or input data array
    std_param (src.StandardParameter): StandardParameter object.
    Defaults to None.
    name (str): parameter name. Defaults to None
    unit (src.Unit): Unit object. Defaults to None
    min (float): minimum allowed value for the parameter.
    Defaults to None
    max (float): maximum allowed value for the parameter.
    Defaults to None

    Attributes:
    name (str): parameter name
    prob (array): probabilities
    val (array): values
    """
    def __init__(self, inp, std_param=None, name=None, unit=None,
                 min=None, max=None):
        # Store passed parameters
        self._inp = np.array(inp)

        # Convert min and max to SI units
        if std_param is not None:
            self.name = std_param.name
            self._unit = std_param.unit
            if std_param.min is not None:
                self._min = self._unit.to_SI(std_param.min)
            else:
                self._min = std_param.min
            if std_param.max is not None:
                self._max = self._unit.to_SI(std_param.max)
            else:
                self._max = std_param.max
        else:
            if unit is not None:
                if min is not None:
                    self._min = unit.to_SI(min)
                else:
                    self._min = min
                if max is not None:
                    self._max = unit.to_SI(max)
                else:
                    self._max = max
            else:
                self._min = min
                self._max = max

        # Load PDF from file if 'finput' is a string
        if len(self._inp.shape) == 1:
            self.val = inp
            self.prob = None
            self._cum = None
        elif len(self._inp.shape) == 2:
            self.val = self._inp[0]
            self.prob = self._inp[1]
            # Rescale probabilities to 1 in case they are not already
            self.prob = self.prob / np.sum(self.prob)
            self._cum = np.cumsum(self.prob)

    # ***** Public Methods *****
    def sample(self, nsample=1):
        """
        Samle the distribution nsample times

        Args:
        nsample (int): the number of times to sample the distribution
        """
        if nsample == 1:
            samps = np.random.choice(self.val, size=nsample, p=self.prob)[0]
        else:
            samps = np.random.choice(self.val, size=nsample, p=self.prob)
        samps = np.where(samps > self._max, self._max, samps)
        samps = np.where(samps < self._min, self._min, samps)
        return samps
    
    def change(self, new_avg):
        # Arithmetically shift the distribution to the new central value
        old_mean = self.mean()
        shift = new_avg - old_mean
        self.val += shift
        return

    def mean(self):
        """ Return the mean of the distribution """
        if self.prob is not None:
            return np.sum(self.prob * self.val)
        else:
            return np.mean(self.val)

    def std(self):
        """ Return the standard deviation of the distribution """
        if self.prob is not None:
            mean = self.mean()
            return np.sqrt(np.sum(self.prob * ((self.val - mean) ** 2)))
        else:
            return np.std(self.val)

    def median(self):
        """ Return the median of the distribution """
        if self.prob is not None:
            arg = np.argmin(abs(self._cum - 0.5))
            return self.val[arg]
        else:
            return np.median(self.val)

    def one_sigma(self):
        """ Return the 15.9% and 84.1% values """
        med = self.median()
        if self.prob is not None:
            lo, hi = np.interp((0.159, 0.841), self._cum, self.val)
        else:
            lo, hi = np.percentile(self.val, [0.159, 0.841])
        return (hi-med, med-lo)

    def two_sigma(self):
        """ Return the 2.3% and 97.7% values """
        med = self.median()
        if self.prob is not None:
            lo, hi = np.interp((0.023, 0.977), self._cum, self.val)
        else:
            lo, hi = np.percentile(self.val, [0.023, 0.977])
        return (hi-med, med-lo)
