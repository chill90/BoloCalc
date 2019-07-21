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
        self.param_dicts = self._load().optics(os.path.join(self.cam.config_dir, 'optics.txt'))
        self._gen_band_dict()
        self.optics = cl.OrderedDict({})
        for param_dict in self.param_dicts:
            if param_dict['Element'] in self.optics.keys():
                self._log().err(
                    "Multiple optical elements named '%s' in camera '%s'" 
                    % (opticDict['Element'], self.cam.dir.))
            if self.band_dict is not None and param_dict['Element'] in self.optBands.keys(): 
                self.optics.update({opticDict['Element']: op.Optic(log, opticDict, nrealize=self.nrealize, bandFile=self.optBands[opticDict['Element']])})
                self.log.log("Using user-input spectra for optic '%s'" % (opticDict['Element']),1)
            else:
                self.optics.update({opticDict['Element']: op.Optic(log, opticDict, nrealize=self.nrealize)})

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
