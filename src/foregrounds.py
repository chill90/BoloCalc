# Built-in modules
import numpy as np
import collections as cl

# BoloCalc modules
import src.physics as ph
import src.units as un


class Foregrounds:
    def __init__(self, log, fgndDict=None, nrealize=1):
        # Store passed parameters
        self.log = log
        self.fgndDict = fgndDict
        self.nrealize = nrealize

        # Create physics object for calculations
        self.ph = ph.Physics()

        # Store foreground parameters
        self._GHz_to_Hz = 1.e+09
        if self.fgndDict is None:
            self.fgndDict = {
                'Dust Temperature': 19.7,
                'Dust Spec Index': 1.5,
                'Dust Amplitude': 2.e-3,
                'Dust Scale Frequency': 353. * self._GHz_to_Hz,
                'Synchrotron Spec Index': -3.0,
                'Synchrotron Amplitude': 6.e3}

    # ***** Public methods *****
    # Polarized galactic dust spectral radiance [W/(m^2-Hz)]
    def dust_spec_rad(self, freq, emissivity=1.0):
        amp = emissivity * self.fgndDict['Dust Amplitude']
        fscale = ((freq/float(self.fgndDict['Dust Scale Frequency'])) **
                  self.fgndDict['Dust Spec Index'])
        spec = self.ph.bbSpecRad(freq, self.fgndDict['Dust Temperature'])
        return (amp * fscale * spec)

    # Synchrotron spectral radiance [W/(m^2-Hz)]
    def sync_spec_rad(self, freq, emissivity=1.0):
        amp = emissivity * self.fgndDict['Synchrotron Amplitude']
        fscale = freq ** self.fgndDict['Synchrotron Spec Index']
        return (amp * fscale)

    # ***** Private Methods *****
    def _param_samp(self, param):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self.nrealize == 1:
            return param.getAvg()
        else:
            return param.sample(nsample=1)
