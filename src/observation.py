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
        self._obs_set = obs_set
        self._sky = self._obs_set.ch.cam.tel.sky
        self._scn = self._obs_set.ch.cam.tel.scn
        self._det_arr = self._obs_set.ch.det_arr
        self._ndet = self._obs_set.ch.cam.tel.exp.sim.param("ndet")

    def evaluate(self):
        # Store PWV and elevation
        self._get_pwv_elev()

        # Store sky values
        elem, emis, tran, temp = self._get_sky_vals()
        self.elem = np.squeeze(elem, axis=(0, 1)).T.tolist()
        self.emis = np.squeeze(emis, axis=1).tolist()
        self.tran = np.squeeze(tran, axis=1).tolist()
        self.temp = np.squeeze(temp, axis=1).tolist()

    # ***** Helper Methods *****
    def _get_pwv_elev(self):
        # Sample PWV
        self._pwv = self._sky.pwv_sample()
        # Sample Elevation
        tel_elev = self._scn.elev_sample()
        cam_elev = self._obs_set.ch.cam.param("bore_elev")
        # Sample and store sky optical parameters
        if self._ndet == 1:
            self._elev = tel_elev + cam_elev
        else:
            self._elev = tel_elev + cam_elev + self._obs_set.sample_pix_elev()
        return

    def _get_sky_vals(self):
        return np.hsplit(np.array([self._sky.evaluate(
            self._pwv, self._elev, self._det_arr.ch.freqs)
            for det in self._det_arr.dets]), 4)
