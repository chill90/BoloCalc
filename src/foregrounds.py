# Built-in modules
import numpy as np
import collections as cl

# BoloCalc modules
import src.physics as ph
import src.units as un


class Foregrounds:
    def __init__(self, sky):
        # Store passed parameters
        self.sky = sky

    # ***** Public methods *****
    # Polarized galactic dust spectral radiance [W/(m^2-Hz)]
    def dust_spec_rad(self, freq, emissivity=1.0):
        amp = emissivity * self.fgndDict['Dust Amplitude']
        fscale = ((freq/float(self.fgndDict['Dust Scale Frequency'])) **
                  self.fgndDict['Dust Spec Index'])
        spec = self._ph().bbSpecRad(freq, self.fgndDict['Dust Temperature'])
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

    def _ph(self):
        return self.sky.tel.exp.sim.phys
