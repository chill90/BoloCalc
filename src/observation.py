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
        self._ch = self._obs_set.ch
        self._sky = self._ch.cam.tel.sky
        self._scn = self._ch.cam.tel.scn
        self._det_arr = self._ch.det_arr
        self._ndet = self._ch.cam.tel.exp.sim.param("ndet")

    def evaluate(self):
        """ Evaluate the observation's elem, emiss, tran, and temp arrays """
        # Store PWV and elevation
        self._get_pwv_elev()

        # Store sky values
        elem, emis, tran, temp = self._get_sky_vals()
        self.elem = np.squeeze(elem[0], axis=0).T.tolist()
        self.emis = np.squeeze(emis, axis=1).tolist()
        self.tran = np.squeeze(tran, axis=1).tolist()
        self.temp = np.squeeze(temp, axis=1).tolist()
        return

    # ***** Helper Methods *****
    def _get_pwv_elev(self):
        """ Sample the pixel elevation """
        # Sample PWV
        self._pwv = self._sky.pwv_sample()
        # Sample telescope elevation
        tel_elev = self._scn.elev_sample()
        # Retrieve camera boresight elevation
        cam_elev = self._obs_set.ch.cam.param("bore_elev")
        # Sample pixel elevation
        bore_elev = tel_elev + cam_elev
        if self._ndet == 1:
            self._pix_elev = [bore_elev]
        else:
            self._pix_elev = (
                self._obs_set.sample_pix_elev(self._ndet) + bore_elev)
        # Maximum allowed elevation = 90 deg, minimum = 20 deg
        self._pix_elev = np.array([e if e > self._scn.min_elev
                                   else self._scn.min_elev
                                   for e in self._pix_elev])
        self._pix_elev = np.array([e if e < self._scn.max_elev
                                   else self._scn.max_elev
                                   for e in self._pix_elev])
        return

    def _get_sky_vals(self):
        """ Get the sky values """
        return np.hsplit(np.array([self._sky.evaluate(
            self._pwv, elev, self._ch.freqs)
            for elev in self._pix_elev]), 4)
