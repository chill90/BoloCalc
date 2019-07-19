# Built-in modules
import numpy as np

# BoloCalc modules
import src.loader as ld


class Distribution:
    """
    Distribution object holds probability distribution functions (PDFs)
    for instrument parameters

    Args:
    finput (str or arr): file name for the input PDF or input data array

    Attributes:
    prob (array): probabilities
    val (array): values
    """
    def __init__(self, input):
        # Load PDF from file if 'finput' is a string
        if isinstance(input, str):
            self._ld = ld.Loader()
            self.prob, self.val = self._ld.pdf(input)
            # Rescale probabilities to 1 in case they are not already
            self.prob = self.prob/np.sum(self.prob)
            self._cum = np.cumsum(self.prob)
        # Store values if 'finput' is a data array
        if isinstance(input, list) or isinstance(input, np.array):
            self.val = input
            self.prob = None
            self._cum = None

    def mean(self):
        if self.prob is not None:
            return np.sum(self.prob * self.val)
        else:
            return np.mean(self.val)

    def std(self):
        if self.prob is not None:
            mean = self.mean()
            return np.sqrt(np.sum(self.prob * ((self.val - mean) ** 2)))
        else:
            return np.mean(self.val)

    def median(self):
        if self.prob is not None:
            arg = np.argmin(abs(self._cum - 0.5))
            return self.val[arg]
        else:
            return np.median(self.val)

    def one_sigma(self):
        if self.prob is not None:
            return np.interp((0.159, 0.841), self._cum, self.val)
        else:
            return np.pecentile(self.val, [0.159, 0.841])

    def two_sigma(self):
        if self.prob is not None:
            return np.interp((0.023, 0.977), self._cum, self.val)
        else:
            return np.percentile(self.val, [0.023, 0.977])
