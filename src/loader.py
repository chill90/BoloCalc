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
        try:
            params, vals = np.loadtxt(
                fname, unpack=True, skiprows=1, usecols=[0, 1],
                dtype=np.str, delimiter='|')
        except:
            self._log.err("Failed to load simulation file '%s'" % (fname))
        return self._dict(params, vals)

    def atm(self, fname):
        """ Load atmosphere TXT file, returning (freq, temp, tran) """
        try:
            freq, temp, tran = np.loadtxt(
                self.atmFile, unpack=True, usecols=[0, 2, 3], dtype=np.float)
        except:
            self._log_err("Failed to load atm file '%s'" % (fname))
        return (freq, temp, tran)

    def band(self, fname):
        """ Load either a CSV or TXT band file """
        if 'csv' in fname.lower():
            return self._csv(fname)
        elif 'txt' in fname.lower():
            return _txt(fname)
        else:
            self._log.err("Illegal file format passed to Loader.band()")

    def band_dir(self, inp_dir):
        band_files = sorted(gb.glob(os.path.join(inp_dir, '*')))
        if len(band_files):
            names = [os.path.split(f)[-1].split('.')[0]
                     for f in band_files if "~" not in f]
            if len(names):
                return {
                    names[i]: band_files[i]for i in range(len(names))}
            else:
                return None
        else:
            return None

    def foregrounds(self, fname):
        """ Load foregrounds file, skipping column 1, which defines units"""
        try:
            params, vals = np.loadtxt(
                fname, unpack=True, usecols=[0, 2], dtype=np.str, delimiter='|')
        except:
            self._log.err(
                "Failed to load foreground file '%s'" % (fname))
        return self._dict(params, vals, self._dist_dir(fname))

    def telescope(self, fname):
        """ Load telescope file, skipping column 1, which defines units"""
        try:
            params, vals = np.loadtxt(
                fname, unpack=True, usecols=[0, 2], dtype=np.str, delimiter='|')
        except:
            self._log_err(
                "Failed to load telescope file '%s'" % (fname))
        return self._dict(params, vals, self._dist_dir(fname))

    def camera(self, fname):
        """ Load camera file, skipping column 1, which defines the units"""
        try:
            params, vals = np.loadtxt(
                fname, dtype=np.str, unpack=True,
                usecols=[0, 2], delimiter='|')
        except:
            self._log_err(
                "Failed to load camera file '%s'" % (fname))
        return self._dict(params, vals, self._dist_dir(fname))

    def optics(self, fname):
        """ Load optics file """
        return self._txt_2D(fname)

    def channel(self, fname):
        """ Load channel file """
        return self._txt_2D(fname)

    def elevation(self, fname):
        """ Load elevation file """
        try:
            params, vals = np.loadtxt(
                fname, unpack=True, usecols=[0, 1],
                dtype=np.str, delimiter="|")
        except:
            self._log_err(
                "Failed to load elevation file '%s'" % (fname))
        return {params[i].strip(): vals[i].strip()
                for i in range(2, len(params))}

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

    def _txt_2D(self, fname):
        """ For loading 2D BoloCalc text files """
        output = np.loadtxt(fname, dtype=np.str, delimiter='|')
        keys = chans[0]
        elems = chans[1:]
        return [{keys[i].strip(): elem[i].strip()
                for i in range(len(keys))}
                for elem in elems]

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
