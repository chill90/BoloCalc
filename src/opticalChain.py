# Built-in methods
import numpy as np
import collections as cl
import os
import glob as gb

# BoloCalc methods
import src.optic as op


class OpticalChain:
    """
    OpticalChain object contains the Optics object for a given camera

    Args:
    cam (src.Camera): Camera object for this optical chain

    Attributes:
    cam (src.Camera): where 'cam' arg is stored
    elem (list): list of optic element names
    abso (list): list of optic element absorbtivities
    tran (list): list of optic element transmissions
    temp (list): list of optic element temperatures
    """
    def __init__(self, cam):
        # Store passed parameters
        self.cam = cam
        self._log = self.cam.tel.exp.sim.log
        self._load = self.cam.tel.exp.sim.load

        # Store optic objects
        self._gen_band_dict()
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
                  for optic in list(self._optics.values())]
        return [[optic[0] for optic in optics],
                [optic[1] for optic in optics],
                [optic[2] for optic in optics],
                [optic[3] for optic in optics]]

    # ***** Private Methods *****
    def _gen_band_dict(self):
        band_dir = os.path.join(self.cam.config_dir, 'Optics')
        self._band_dict = self._load.band_dir(band_dir)
        return

    def _store_optics(self):
        param_dicts = self._load.optics(
            os.path.join(self.cam.config_dir, 'optics.txt'))
        self._optics = cl.OrderedDict({})
        for param_dict in param_dicts:
            # Check for duplicate optic names
            if param_dict["Element"] in self._optics.keys():
                self._log.err(
                    "Multiple optical elements named '%s' in camera '%s'"
                    % (param_dict["Element"], self.cam.dir))
            # Check for optic band file
            if (self._band_dict is not None and param_dict["Element"] in
               self._band_dict.keys()):
                band_file = self._band_dict[param_dict["Element"]]
                self._log.log("Using user-input spectra for optic '%s'"
                              % (param_dict["Element"].fetch()),
                              self._log.level["MODERATE"])
            else:
                band_file = None
            # Store optic
            self._optics.update({param_dict['Element']: op.Optic(
                self, param_dict, band_file=band_file)})
        return
