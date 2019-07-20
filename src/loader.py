# Built-in modules
import numpy as np
import os

# BoloCalc modules
import distribution as ds


class Loader:
    """
    Object for loading data for various file formats into dicts
    """
    def __init__(self, log):
        self._log = log
        self._dist_dir = "pdf/"
        self._ftypes = [".csv", ".txt"]
        return

    # ***** Public methods *****
    def sim(self, fname):
        """ Load simulation TXT file, returning dictionary"""
        params, vals = np.loadtxt(
            fname, unpack=True, skiprows=1, usecols=[0, 1],
            dtype=np.str, delimiter='|')
        return self._dict(params, vals)

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

    def telescope(self, fname):
        """ Load telescope file, skipping column 1, which defines units"""
        params, vals = np.loadtxt(
            fname, unpack=True, usecols=[0, 2], dtype=np.str, delimiter='|')
        return self._dict(params, vals, self._dist_dir(fname))

    def pdf(self, fname):
        """ Load either a CSV or TXT PDF file """
        if 'csv' in fname.lower():
            return self._csv(fname)
        elif 'txt' in fname.lower():
            return self._txt(fname)
        else:
            raise Exception("Illegal file format passed to Loader.pdf()")

    # ***** Private methods *****
    def _csv(self, fname):
        return np.loadtxt(fname, unpack=True, dtype=np.float, delimiter=',')

    def _txt(self, fname):
        return np.loadtxt(fname, unpack=True, dtype=np.float)

    def _dict(self, params, vals, dist_dir=None):
        data = {paramArr[i].strip(): valArr[i].strip()
                for i in range(len(paramArr))}
        if dist_dir is not None:
            for key, val in data.items():
                if 'NA' in val.upper():
                    for fname in self._dist_fnames(dist_dir, key):
                        if os.file.exists(fname):
                            val = ds.Distribution(self.pdf(fname))
                        else:
                            continue
                else:
                    continue
        return data

    def _dist_dir(self, fname):
        dist_dir = '/'.join(fname.split('/')[:-2]) + self._dist_dir
        if not os.path.exists(dist_dir):
            self._log.err(
                "Distribution dir '%s' does not exist" % (dist_dir))
        else:
            return dist_dir

    def _dist_fnames(self, dist_dir, param_name):
        return [('_'.join(param_name.lower().split()) + tag)
                for tag in self._ftypes]
