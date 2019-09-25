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
    def __init__(self, sim):
        self._log = sim.log
        self._std_params = sim.std_params
        self._ds_dir = "Dist"
        self._bd_dir = "Bands"
        self._opt_dir = "Optics"
        self._det_dir = "Detectors"
        self._ftypes = ["CSV", "TXT"]

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
        except IndexError:
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
        except IndexError:
            self._log.err("Failed to load atm file '%s'" % (fname))
        return (freq, temp, tran)

    def band(self, fname):
        """
        Load either a CSV or TXT band file

        Args:
        fname (str): band file name
        """
        if ".CSV" in fname.upper():
            return self._csv(fname)
        elif ".TXT" in fname.upper():
            return self._txt(fname)
        else:
            self._log.err("Illegal file format passed to Loader.band()")

    def optics_bands(self, inp_dir):
        """
        Load all band files in a specified directory for an optical chain.
        Bands assumed to cover all frequency channels.
        Returns a dictionary with key = optic name and value = list of
        valid band files, which will be sorted through at the optic level.

        Args:
        inp_dir (str): optics band directory
        """
        # Gather band files
        band_dir = os.path.join(inp_dir, self._bd_dir)
        if not os.path.exists(band_dir):
            os.mkdir(band_dir)
        opt_band_dir = os.path.join(band_dir, self._opt_dir)
        if not os.path.exists(opt_band_dir):
            os.mkdir(opt_band_dir)
        band_files = os.listdir(opt_band_dir)
        # Ignore temporary files
        band_files = [f for f in band_files if "~" not in f]
        # Case-insensitive fname comparison
        band_files_upper = [band_file.upper() for band_file in band_files]
        if len(band_files):
            names = [band_file.split('.')[0]
                     for band_file in band_files_upper]
            # No repeat names allowed
            if len(set(names)) != len(names):
                self._log.err(
                    "Repeat band name found in %s" % (inp_dir))
            # Group repeat distributions, IDed by optic name
            dist_ids = [name.split('_')[0] for name in names]
            unique_ids = set(dist_ids)  # unique optics
            # Return dictionary of band files for each unique optic,
            # keyed by the optic name listed in the band file name
            ret_dict = {}
            for u_id in unique_ids:
                args = np.argwhere(np.array(dist_ids) == u_id).flatten()
                files = np.take(np.array(band_files), args)
                ret_dict[u_id] = [os.path.join(opt_band_dir, f) for f in files]
            return ret_dict
        else:
            return None

    def det_band_dir(self, inp_dir):
        """
        Load all band files in a specified directory for detectors

        Args:
        inp_dir (str): detectors band directory
        """
        if not os.path.exists(inp_dir):
            os.mkdir(inp_dir)
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
            keys, values = np.loadtxt(
                fname, unpack=True, usecols=[0, 2],
                dtype=np.str, delimiter='|')
        except IndexError:
            self._log.err(
                "Failed to load foreground file '%s'" % (fname))
        fgnd_dict = self._dict(keys, values, self._dist_dir(fname))
        return fgnd_dict

    def telescope(self, fname):
        """
        Load telescope file, skipping column 1, which defines units

        fname (str): telescope file name
        """
        try:
            keys, values = np.loadtxt(
                fname, unpack=True, usecols=[0, 2],
                dtype=bytes, delimiter='|').astype(str)
        except IndexError:
            self._log.err(
                "Failed to load telescope file '%s'" % (fname))
        tel_dict = self._dict(keys, values, self._dist_dir(fname))
        return tel_dict

    def camera(self, fname):
        """
        Load camera file, skipping column 1, which defines the units

        Args:
        fname (str): camera file name
        """
        try:
            keys, values = np.loadtxt(
                fname, dtype=bytes, unpack=True,
                usecols=[0, 2], delimiter='|').astype(str)
        except IndexError:
            self._log.err(
                "Failed to load camera file '%s'" % (fname))
        cam_dict = self._dict(keys, values, self._dist_dir(fname))
        return cam_dict

    def optics(self, fname):
        """
        Load optics file

        Args:
        fname (str): optics file name
        """
        keys, values = self._txt_2D(fname)
        opt_dict = self._dict_optics(
            keys, values, self._dist_dir_opt(fname))
        return opt_dict

    def channels(self, fname):
        """
        Load channel file

        Args:
        fname (str): camera file name
        """
        keys, values = self._txt_2D(fname)
        chan_dict = self._dict_channels(
            keys, values, self._dist_dir_det(fname))
        return chan_dict

    def elevation(self, fname):
        """
        Load elevation file

        Args:
        fname (str): elevation file name
        """
        try:
            params, vals = self._txt(fname)
        except IndexError:
            self._log.err(
                "Failed to load elevation file '%s'" % (fname))
        return {params[i]: vals[i]
                for i in range(len(params))}

    # ***** Helper methods *****
    def _csv(self, fname):
        return np.loadtxt(fname, unpack=True, dtype=np.float, delimiter=',')

    def _txt(self, fname):
        return np.loadtxt(fname, unpack=True, dtype=np.float)

    def _txt_2D(self, fname):
        output = np.loadtxt(fname, dtype=bytes, delimiter='|').astype(str)
        output = np.char.strip(output)
        keys = output[0]
        values = output[1:]
        return keys, values

    def _pdf(self, fname):
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

    def _dict(self, params, vals, dist_dir=None):
        if dist_dir is not None:
            # Available distribution files
            dist_files = os.listdir(dist_dir)
            # No temporary files allowed
            dist_files = [f for f in dist_files
                          if '~' not in f and '#' not in f]
            # Capitalized file names for fname matching
            dist_files_upper = [dist_file.upper() for dist_file in dist_files]
        # Load data into a dictionary and modify as needed
        data = {params[i].replace(" ", "").strip().upper(): vals[i].strip()
                for i in range(len(params))}
        # Check for PDFs
        for key, val in data.items():
            if 'PDF' in val.upper():
                if dist_dir is None:
                    self._log.err(
                        "Parameter '%s' has value 'PDF' but no "
                        "distribution directory %s not found"
                        % (str(key), dist_dir))
                dist_files_found = 0
                f_id = key.replace(" ", "").upper()
                for i, fname in enumerate(self._dist_fnames(f_id)):
                    if fname in dist_files_upper:
                        ind = dist_files_upper.index(fname)
                        dfile = os.path.join(dist_dir, dist_files[ind])
                        data[f_id] = ds.Distribution(
                            self._pdf(dfile), std_param=self._std_params[f_id])
                        dist_files_found += 1
                if dist_files_found == 0:
                    self._log.err(
                        "Parameter '%s' has "
                        "value 'PDF' but no distribution file found in %s"
                        % (key, dist_dir))
                elif dist_files_found > 1:
                    self._log.err(
                        "Multiple distribution files found in %s for "
                        "parameter '%s'"
                        % (dist_dir, key))
                else:
                    self._log.log(
                        "** Using PDF file %s for parameter '%s'"
                        % (dfile, key))
            else:
                continue
        return data

    def _dict_optics(self, keys, values, dist_dir=None):
        # Optic names stored in first column
        optic_names = [value[0] for value in values]
        # Parameter names stored in first row
        param_names = keys
        # Parameter values stored in subsequent rows
        vals = [value for value in values]
        # Loop over optics
        opt_dict = {}
        for i, optic_name in enumerate(optic_names):
            # Loop over parameters for each optic
            param_dict = {}
            for j, param_name in enumerate(param_names):
                param_name_upper = param_name.replace(" ", "").upper()
                # Check if the parameter calls for a PDF in either of its bands
                if 'PDF' in vals[i][j].upper():
                    # Throw error if the dist directory doesn't exist
                    if dist_dir is None:
                        self._log.err(
                            "Parameter '%s' for optic '%s' has value 'PDF' "
                            "but no distribution directory %s not found"
                            % (param_name, optic_name, dist_dir))
                    # Store dict of distributions where a PDF file is found
                    dist_dict = self._dict_optics_params(
                        dist_dir, optic_name, param_name)
                    # Throw an error if the dict is empty
                    if not dist_dict:
                        self._log.err(
                            "Parameter '%s' for optic '%s' has value 'PDF' "
                            "but no file '%s_%s_*.txt/csv' (case insensitive) "
                            "found in %s"
                            % (param_name, optic_name,
                               optic_name.replace(" ", ""),
                               param_name.replace(" ", ""),
                               dist_dir))
                    # Tuple = (param string, dict of dists)
                    param_dict[param_name_upper] = (vals[i][j], dist_dict)
                # Otherwise, just store the paramter string
                else:
                    param_dict[param_name_upper] = (vals[i][j], None)
            opt_dict[optic_name] = param_dict
        return opt_dict

    def _dict_optics_params(self, dist_dir, optic_name, param_name):
        ret_dict = {}
        # Available distribution files
        dist_files = os.listdir(dist_dir)
        dist_files = [f for f in dist_files
                      if '~' not in f and '#' not in f]
        dist_files_upper = [dist_file.upper() for dist_file in dist_files]
        # Accepted filenames need to have a specific structure
        # opticName_paramName_bandID.txt/csv
        param_id = param_name.replace(" ", "").upper()
        f_id = "%s_%s" % (
            optic_name.replace(" ", ""),
            param_name.replace(" ", ""))
        f_id_upper = f_id.upper()
        files = []
        for fname in dist_files_upper:
            ftag = fname.split('.')[-1]
            if f_id_upper in fname and ftag in self._ftypes:
                ind = dist_files_upper.index(fname)
                files.append(dist_files[ind])
        if len(files) == 0:
            self._log.err(
                "Parameter '%s' has "
                "value 'PDF' but no distribution file found in %s"
                % (f_id, dist_dir))
        else:
            self._log.log(
                "** Using PDF files %s in %s for parameter '%s' "
                "for optic '%s'"
                % (str(files), dist_dir, f_id, optic_name))
        # Use the band ID as the key for the return dictionary
        for f in files:
            # Split the file name (minus .csv/txt) into its three
            # identifiers, separated by underscores
            ids = os.path.split(f)[-1].split('.')[0].split('_')
            if len(ids) == 3:
                # Dictionary key is the third idenfier, which should
                # be the Band ID
                key = ids[-1].upper()
            elif len(ids) == 2:
                # If no Band ID key, this PDF is assumed to be the same for
                # all bands (e.g. optic temperature)
                key = 'ALL'
            else:
                # Ignore illegal file names in case the user 'deadened'
                # it intentionally
                self._log.log(
                    "Illegal optic PDF file name '%s'. Ignoring...")
                continue
            # Return a dictionary of distributions, keyed by the
            # third file identifier, which should be the Band ID,
            # or keyed by 'ALL'
            ret_dict[key] = ds.Distribution(self._pdf(
                os.path.join(dist_dir, f)),
                std_param=self._std_params[param_id])
        return ret_dict

    def _dict_channels(self, keys, values, dist_dir=None):
        if dist_dir is not None:
            # Available distribution files
            dist_files = os.listdir(dist_dir)
            dist_files = [f for f in dist_files
                          if '~' not in f and '#' not in f]
            dist_files_upper = [dist_file.upper() for dist_file in dist_files]
        # Channel names stored in the first column
        band_ids = np.array([value[0] for value in values])
        # Parameter names stored in first row
        param_names = keys
        # Parameter values stored in subsequent rows
        vals = np.array([value for value in values])
        # Loop over channels
        chan_dict = {}
        for i, band_id in enumerate(band_ids):
            # Loop over parameters for each channel
            param_dict = {}
            for j, param_name in enumerate(param_names):
                param_name_upper = param_name.replace(" ", "").upper()
                # Check if the parameter calls for a PDF
                if 'PDF' in vals[i][j].upper():
                    if dist_dir is None:
                        self._log.err(
                            "Parameter '%s' for Band ID '%s' has value 'PDF' "
                            "but no distribution directory %s not found"
                            % (param_name, band_id, dist_dir))
                    # Store dist when a PDF file is found
                    param_id = param_name.replace(" ", "").upper()
                    f_id = "%s_%s" % (
                        param_id,
                        str(band_id).replace(" ", "").upper())
                    # Load possible distribution file names
                    fnames = self._dist_fnames(f_id)
                    dist_files_found = 0  # keep track of fname matches
                    for k, fname in enumerate(dist_files_upper):
                        if fname in fnames:
                            dfile = os.path.join(dist_dir, dist_files[k])
                            param_dict[param_name_upper] = ds.Distribution(
                                self._pdf(dfile), self._std_params[param_id])
                            dist_files_found += 1
                    if dist_files_found == 0:
                        self._log.err(
                            "Channel parameter '%s' for Band ID '%s' has "
                            "value 'PDF' but no distribution file found in %s"
                            % (str(param_name), str(band_id), dist_dir))
                    elif dist_files_found > 1:
                        self._log.err(
                            "Multiple distribution files found in %s for "
                            "channel parameter '%s' for Band ID '%s'"
                            % (dist_dir, str(param_name), str(band_id)))
                    else:
                        self._log.log(
                            "** Using distribution file %s for parameter '%s' "
                            "in channel Band_ID '%s'"
                            % (dfile, str(param_name), str(band_id)))
                else:
                    # Otherwise, just store the paramter string
                    param_dict[param_name_upper] = vals[i][j]
            chan_dict[band_id] = param_dict
        return chan_dict

    def _dist_dir(self, fname):
        """ Return dist dir given location of pramf file. e.g. config/Dist/ """
        dist_dir = os.path.join(
            os.path.split(fname)[0], self._ds_dir)
        if not os.path.exists(dist_dir):
            return None
        else:
            return dist_dir

    def _dist_dir_opt(self, fname):
        """ Return dist dir for optics e.g. config/Dist/Optics """
        dist_dir = os.path.join(
            os.path.split(fname)[0], self._ds_dir, self._opt_dir)
        if not os.path.exists(dist_dir):
            return None
        else:
            return dist_dir

    def _dist_dir_det(self, fname):
        """ Return dist dir for detectors e.g. config/Dist/Detectors """
        dist_dir = os.path.join(
            os.path.split(fname)[0], self._ds_dir, self._det_dir)
        if not os.path.exists(dist_dir):
            return None
        else:
            return dist_dir

    def _dist_fnames(self, f_id, dist_dir=None):
        """
        Gather possible dist file names given a file ID
        in a given dist dir
        """
        if dist_dir is not None:
            ret_arr = [os.path.join(
                dist_dir, "%s.%s" % (f_id, ftype.upper()))
                for ftype in self._ftypes]
        else:
            ret_arr = [
                "%s.%s" % (f_id, ftype.upper())
                for ftype in self._ftypes]
        return ret_arr
