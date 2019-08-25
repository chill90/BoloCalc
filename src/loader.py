# Built-in modules
import numpy as np
import glob as gb
import os

# BoloCalc modules
import src.distribution as ds


class Loader:
    """
    Loader object loads data for various file formats into dicts

    Args:
    log (src.Log): Log object
    """
    def __init__(self, log):
        self._log = log
        self._dir = "Dist/"
        self._ftypes = [".csv", ".txt"]
        return

    # ***** Public methods *****
    def sim(self, fname):
        """
        Load simulation TXT file, returning dictionary

        Args:
        fname (str): simulation file name
        """
        try:
            params, vals = np.loadtxt(
                fname, unpack=True, skiprows=1, usecols=[0, 1],
                dtype=bytes, delimiter='|').astype(str)
        except:
            self._log.err("Failed to load simulation file '%s'" % (fname))
        return self._dict(params, vals)

    def atm(self, fname):
        """
        Load atmosphere TXT file, returning (freq, temp, tran)

        Args:
        fname (str): atmosphere file name
        """
        try:
            freq, temp, tran = np.loadtxt(
                fname, unpack=True, usecols=[0, 2, 3], dtype=np.float)
        except:
            self._log.err("Failed to load atm file '%s'" % (fname))
        return (freq, temp, tran)

    def band(self, fname):
        """
        Load either a CSV or TXT band file

        Args:
        fname (str): band file name
        """
        if "CSV" in fname.upper():
            return self._csv(fname)
        elif "TXT" in fname.upper():
            return self._txt(fname)
        else:
            self._log.err("Illegal file format passed to Loader.band()")

    def optics_band_dir(self, inp_dir):
        """
        Load all band files in a specified directory for an optical chain

        Args:
        inp_dir (str): optics band directory
        """
        band_files = sorted(gb.glob(os.path.join(inp_dir, '*')))
        if len(band_files):
            # No temporary files
            band_files = [f for f in band_files if "~" not in f]
            if not len(band_files):
                return None
            names = [os.path.split(name)[-1].split('.')[0]
                     for name in band_files]
            # No repeat names allowed
            if len(set(names)) != len(names):
                self._log.err(
                    "Repeat band name found in %s" % (inp_dir))
            # Group repeat distribution IDs
            dist_ids = [name.split('_')[0] for name in names]
            unique_ids = set(dist_ids)
            ret_dict = {}
            for u_id in unique_ids:
                args = np.argwhere(np.array(dist_ids) == u_id).flatten()
                dist_id = str(dist_ids[args[0]]).strip()
                files = np.take(np.array(names), args)
                ret_dict[dist_id] = files
        else:
            return None

    def det_band_dir(self, inp_dir):
        """
        Load all band files in a specified directory for detectors

        Args:
        inp_dir (str): optics band directory
        """
        band_files = sorted(gb.glob(os.path.join(inp_dir, '*')))
        if len(band_files):
            # No temporary files
            band_files = [f for f in band_files if "~" not in f]
            if not len(band_files):
                return None
            names = [os.path.split(name)[-1].split('.')[0]
                     for name in band_files]
            # No repeat names allowed
            if len(set(names)) != len(names):
                self._log.err(
                    "Repeat band name found in %s" % (inp_dir))
            return {
                names[i].strip(): band_files[i].strip()
                for i in range(len(names))}
        else:
            return None

    def foregrounds(self, fname):
        """
        Load foregrounds file, skipping column 1, which defines units

        Args:
        fname (str): foreground file name
        """
        try:
            params, vals = np.loadtxt(
                fname, unpack=True, usecols=[0, 2],
                dtype=np.str, delimiter='|')
        except:
            self._log.err(
                "Failed to load foreground file '%s'" % (fname))
        return self._dict(params, vals, self._dist_dir(fname))

    def telescope(self, fname):
        """
        Load telescope file, skipping column 1, which defines units

        fname (str): telescope file name
        """
        try:
            params, vals = np.loadtxt(
                fname, unpack=True, usecols=[0, 2],
                dtype=bytes, delimiter='|').astype(str)
        except:
            self._log.err(
                "Failed to load telescope file '%s'" % (fname))
        return self._dict(params, vals, self._dist_dir(fname))

    def camera(self, fname):
        """
        Load camera file, skipping column 1, which defines the units

        Args:
        fname (str): camera file name
        """
        try:
            params, vals = np.loadtxt(
                fname, dtype=bytes, unpack=True,
                usecols=[0, 2], delimiter='|').astype(str)
        except:
            self._log.err(
                "Failed to load camera file '%s'" % (fname))
        return self._dict(params, vals, self._dist_dir(fname))

    def optics(self, fname):
        """
        Load optics file

        Args:
        fname (str): optics file name
        """
        return self._txt_2D(fname)

    def channel(self, fname):
        """
        Load channel file

        Args:
        fname (str): camera file name
        """
        return self._txt_2D(fname)

    def elevation(self, fname):
        """
        Load elevation file

        Args:
        fname (str): elevation file name
        """
        try:
            params, vals = np.loadtxt(
                fname, unpack=True, usecols=[0, 1],
                dtype=bytes, delimiter="|").astype(str)
        except:
            self._log.err(
                "Failed to load elevation file '%s'" % (fname))
        return {params[i].strip(): vals[i].strip()
                for i in range(2, len(params))}

    def pdf(self, fname):
        """
        Load either a CSV or TXT PDF file

        Args:
        fname (str): distribution file name
        """
        if "CSV" in fname.upper():
            return self._csv(fname)
        elif "TXT" in fname.upper():
            return self._txt(fname)
        else:
            self._log.err("Illegal file format passed to Loader.pdf()")

    # ***** Helper methods *****
    def _csv(self, fname):
        return np.loadtxt(fname, unpack=True, dtype=np.float, delimiter=',')

    def _txt(self, fname):
        return np.loadtxt(fname, unpack=True, dtype=np.float)

    def _txt_2D(self, fname):
        output = np.loadtxt(fname, dtype=bytes, delimiter='|').astype(str)
        keys = output[0]
        elems = output[1:]
        return [{keys[i].strip(): elem[i].strip()
                for i in range(len(keys))}
                for elem in elems]

    def _dict(self, params, vals, dist_dir=None):
        data = {params[i].strip(): vals[i].strip()
                for i in range(len(params))}
        for key, val in data.items():
            if 'PDF' in val.upper():
                if dist_dir is None:
                    self._log.err(
                        "Parameter '%s' has value 'PDF' but no "
                        "distribution directory %s not found"
                        % (str(key), dist_dir))
                file_found = False
                for fname in self._dist_fnames(dist_dir, key):
                    fpath = os.path.join(dist_dir, fname)
                    if os.path.exists(fpath):
                        data[key] = ds.Distribution(self.pdf(fpath))
                        file_found = True
                    else:
                        continue
                if not file_found:
                    self._log.err(
                        "Parameter '%s' has value 'PDF' but no "
                        "distribution file found in %s"
                        % (str(key), dist_dir))
            else:
                continue
        return data

    def _dist_dir(self, fname):
        dist_dir = os.path.join(os.path.split(fname)[0], self._dir)
        if not os.path.exists(dist_dir):
            return None
        else:
            return dist_dir

    def _dist_fnames(self, dist_dir, param_name):
        return [('_'.join(param_name.lower().split()) + tag)
                for tag in self._ftypes]
