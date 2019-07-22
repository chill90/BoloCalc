# Built-in methods
import numpy as np
import collections as cl
import os
import glob as gb

# BoloCalc methods
import src.optic as op


class OpticalChain:
    def __init__(self, cam):
        # Store passed parameters
        self.cam = cam

        # Store optic objects
        self.param_dicts = self._load().optics(
            os.path.join(self.cam.config_dir, 'optics.txt'))
        self._gen_band_dict()
        self._store_optics()

    # ***** Public Methods *****
    # Generate element, temperature, emissivity, and efficiency arrays
    def generate(self, ch):
        arr = [optic.generate(ch) for optic in list(self.optics.values())]
        elem = [a[0] for a in arr]
        emiss = [a[1] for a in arr]
        effic = [a[2] for a in arr]
        temp = [a[3] for a in arr]
        return elem, emiss, effic, temp

    # ***** Private Methods *****
    def _log(self):
        return self.cam.tel.exp.sim.log

    def _load(self):
        return self.cam.tel.exp.sim.ld

    def _gen_band_dict(self):
        band_dir = os.path.join(self.cam.config_dir, 'Optics')
        self.band_dict = self._load().band_dir(band_dir)
        return

    def _store_optics(self):
        self.optics = cl.OrderedDict({})
        for param_dict in self.param_dicts:
            # Check for duplicate optic names
            if param_dict["Element"].fetch() in self.optics.keys():
                self._log().err(
                    "Multiple optical elements named '%s' in camera '%s'"
                    % (param_dict["Element"].fetch(), self.cam.dir))
            # Check for optic band file
            if (self.band_dict is not None and
               param_dict["Element"].fetch() in self.band_dict.keys()):
                band_file = self.band_dict[param_dict["Element"].fetch()]
                self._log().log("Using user-input spectra for optic '%s'"
                                % (param_dict["Element"].fetch()), 1)
            else:
                band_file = None
            # Store optic
            self.optics.update({param_dict['Element'].fetch(): op.Optic(
                param_dict, band_file=band_file)})
