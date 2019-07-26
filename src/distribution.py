# Built-in modules
import numpy as np

# BoloCalc modules
import src.loader as ld


class Distribution:
    """
    Distribution object holds probability distribution functions (PDFs)
    for instrument parameters

    Args:
    inp (str or arr): file name for the input PDF or input data array

    Attributes:
    prob (array): probabilities
    val (array): values
    """
    def __init__(self, inp, load=None):
        # Store passed parameters
        self._inp = inp
        self._load = load

        # Load PDF from file if 'finput' is a string
        if isinstance(inp, str):
            self._load = ld.Loader()
            self.prob, self.val = self._load.pdf(inp)
            # Rescale probabilities to 1 in case they are not already
            self.prob = self.prob / np.sum(self.prob)
            self._cum = np.cumsum(self.prob)
        # Store values if 'finput' is a data array
        if isinstance(inp, list) or isinstance(inp, np.array):
            self.val = inp
            self.prob = None
            self._cum = None

    # ***** Public Methods *****
    def sample(self, nsample=1):
        """
        Samle the distribution nsample times

        Args:
        nsample (int): the number of times to sample the distribution
        """
        return np.random.choice(self.val, size=nsample, p=self.prob)

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
            return np.mean(self.val)

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
            lo, hi = np.pecentile(self.val, [0.159, 0.841])
        return (hi-med, med-lo)

    def two_sigma(self):
        """ Return the 2.3% and 97.7% values """
        med = self.median()
        if self.prob is not None:
            lo, hi = np.interp((0.023, 0.977), self._cum, self.val)
        else:
            lo, hi = np.percentile(self.val, [0.023, 0.977])
        return (hi-med, med-lo)
