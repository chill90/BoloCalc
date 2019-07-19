# Built-in modules
import numpy as np


class Loader:
    def __init__(self, finput):
        self.finput = finput

    # ***** Public methods *****
    def band(self, fname):
        """ Load either a CSV or TXT band file """
        if 'csv' in fname.lower():
            return self._csv(fname)
        elif 'txt' in fname.lower():
            return _txt(fname)
        else:
            raise Exception("Illegal file format passed to Loader.band()")

    def foregrounds(self, fname):
        """ Load foregrounds file, skipping column 1, which defines units"""
        return np.loadtxt(
            fname, unpack=True, usecols=[0, 2], dtype=np.str, delimiter='|')

    def pdf(self, fname):
        """ Load either a CSV or TXT PDF file """
        if 'csv' in fname.lower():
            return self._csv(fname)
        elif 'txt' in fname.lower():
            return _txt(fname)
        else:
            raise Exception("Illegal file format passed to Loader.pdf()")

    # ***** Private methods *****
    def _csv(self, fname):
        return np.loadtxt(fname, unpack=True, dtype=np.float, delimiter=',')

    def _txt(self, fname):
        return np.loadtxt(fname, unpack=True, dtype=np.float)
