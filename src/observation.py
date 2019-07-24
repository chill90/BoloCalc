# Built-in modules
import numpy as np


class Observation:
    """
    Observation object holds sky elements, absorbtivities, tranmissions,
    and temperatures for a given observation, defined by PWV and the
    elevation for the detector pixel being calculated

    Args:
    obs_set (src.ObservationSet): ObservationSet object

    Attributes:
    elem (list): sky element names
    emis (list): sky element absorbtivities
    tran (list): sky element transmissions
    temp (list): sky element temperatures
    """
    def __init__(self, obs_set):
        # Store passed parameters
        self._sky = self.obs_set.ch.cam.tel.sky
        self._scn = self.obs_set.ch.cam.tel.scn
        self._det_arr = self.obs_set.ch.det_arr
        self._ndet = self.cam.tel.exp.sim.fetch("ndet")

        # Store PWV and elevation
        self._get_pwv_elev()

        # Store sky values
        elem, emiss, effic, temp = self._get_sky_vals()

        # Store the element name
        self.elem = elem.reshape(
            len(elem), len(elem[0][0]), len(elem[0][0][0])).astype(np.str)
        self.elem = np.array(self.elem,  order='F')
        self.elem.resize(len(self.elem), len(self.elem[0]))
        self.elem = self.elem.tolist()
        # Emissivity
        self.emis = emiss.reshape(
            len(emiss), len(emiss[0][0]), len(emiss[0][0][0])).astype(np.float)
        self.emis = self.emiss.tolist()
        # Efficiency
        self.tran = effic.reshape(
            len(effic), len(effic[0][0]), len(effic[0][0][0])).astype(np.float)
        self.tran = self.effic.tolist()
        # Temperature
        self.temp = temp.reshape(
            len(temp), len(temp[0][0]), len(temp[0][0][0])).astype(np.float)
        self.temp = self.temp.tolist()

    # ***** Helper Methods *****
    def _get_pwv_elev(self):
        # Sample PWV and Elevation for the camera
        pwv = self._sky().get_pwv()
        cam_elev = self._scn().get_elev()
        if self.elv is not None:
            self.elv += self.belv
        # Sample and store sky optical parameters
        if self._ndet() == 1:
            elev = cam_elev
        else:
            elev = cam_elv + obs_set.sample_pix_elev()
        return

    def _get_sky_vals(self):
        return np.hsplit(np.array([self._sky().generate(
            pwv, elv, det.ch.freqs)
            for det in self._det_arr().dets]), 4)
