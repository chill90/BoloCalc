# Built-in methods
import os

# BoloCalc methods
import src.optic as op


class OpticalChain:
    """
    OpticalChain object contains the Optics object for a given camera

    Args:
    cam (src.Camera): Camera object for this optical chain

    Attributes:
    elem (list): list of optic element names
    abso (list): list of optic element absorbtivities
    tran (list): list of optic element transmissions
    temp (list): list of optic element temperatures

    Parents:
    cam (src.Camera): Camera object
    """
    def __init__(self, cam):
        # Store passed parameters
        self.cam = cam
        self._log = self.cam.tel.exp.sim.log
        self._load = self.cam.tel.exp.sim.load

        # Store optic objects
        self._store_optics()
        return

    # ***** Public Methods *****
    def evaluate(self, ch):
        """
        Generate names, absorbtivities, transmissions, and temperatures
        for all optical elements in a given channel

        Args:
        ch (src.Channel): Channel objects
        """
        optics = [optic.evaluate(ch)
                  for optic in list(self.optics.values())]
        return [[optic[0] for optic in optics],
                [optic[1] for optic in optics],
                [optic[2] for optic in optics],
                [optic[3] for optic in optics]]

    # ***** Private Methods *****
    def _store_optics(self):
        """ Store Optic objects into a dictionary """
        # Load optics parameters from the optics.txt file
        param_dicts = self._load.optics(
            os.path.join(self.cam.config_dir, 'optics.txt'))
        # Load optics bands
        opt_band_dict = self._load.optics_bands(self.cam.config_dir)
        # Store dictionary of optics objects
        self.optics = {}
        for param_dict in param_dicts.values():
            # Check for duplicate optic names
            upper_keys = [key.upper() for key in self.optics.keys()]
            elem = param_dict["ELEMENT"][0]  # tuple = (param_str, dist)
            elem_upper = elem.upper()
            if elem_upper in upper_keys:
                self._log.err(
                    "Multiple optical elements named '%s' in camera '%s'"
                    % (elem, self.cam.dir))
            # Check for optic band files
            if opt_band_dict is None:
                band_files = None
            else:
                upper_keys = [key.upper() for key in opt_band_dict.keys()]
                if elem_upper in upper_keys:
                    band_files = opt_band_dict[elem_upper]
                    self._log.log("Using user-input spectra for optic '%s'"
                                  % (elem))
                else:
                    band_files = None
            # Store optic
            self.optics.update({elem_upper: op.Optic(
                self, param_dict, band_files=band_files)})
        return
