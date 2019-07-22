# Built-in modules
import numpy as np


class Observation:
    def __init__(self, obs_set):
        # Sample PWV and Elevation for the camera
        self.pwv = self._sky().pwvSample()
        self.elv = self._scn().elvSample()
        if self.elv is not None:
            self.elv += self.belv

        # Sample and store sky optical parameters
        if detArray.nDet == 1:
            elv = self.elv
        else:
            elv = self.elv + self.obs_set.sample_pix_elev()
        elem, emiss, effic, temp = np.hsplit(
            np.array([self.sky.generate(
                self.pwv, self.elv, det.ch.freqs)
                for det in self._det_arr().detectors]), 4)

        # Store the element name
        self.elem = elem.reshape(
            len(elem), len(elem[0][0]), len(elem[0][0][0])).astype(np.str)
        self.elem = np.array(self.elem,  order='F')
        self.elem.resize(len(self.elem), len(self.elem[0]))
        self.elem = self.elem.tolist()
        # Emissivity
        self.emiss = emiss.reshape(
            len(emiss), len(emiss[0][0]), len(emiss[0][0][0])).astype(np.float)
        self.emiss = self.emiss.tolist()
        # Efficiency
        self.effic = effic.reshape(
            len(effic), len(effic[0][0]), len(effic[0][0][0])).astype(np.float)
        self.effic = self.effic.tolist()
        # Temperature
        self.temp = temp.reshape(
            len(temp), len(temp[0][0]), len(temp[0][0][0])).astype(np.float)
        self.temp = self.temp.tolist()

    # ***** Helper Methods *****
    def _sky(self):
        return self.obs_set.ch.cam.tel.sky

    def _scn(self):
        return self.obs_set.ch.cam.tel.scn

    def _det_arr(self):
        return self.obs_set.ch.det_arr
