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

        # Store PWV and elevation
        self._get_pwv_elev()

        # Store sky values
        elem, emis, tran, temp = self._get_sky_vals()

        # Store the element name
        self.elem = elem.reshape(
            len(elem), len(elem[0][0]), len(elem[0][0][0])).astype(np.str)
        self.elem = np.array(self.elem,  order='F')
        self.elem.resize(len(self.elem), len(self.elem[0]))
        self.elem = self.elem.tolist()
        # Emissivity
        self.emis = emis.reshape(
            len(emis), len(emis[0][0]), len(emis[0][0][0])).astype(np.float)
        self.emis = self.emis.tolist()
        # Efficiency
        self.tran = tran.reshape(
            len(tran), len(tran[0][0]), len(tran[0][0][0])).astype(np.float)
        self.tran = self.tran.tolist()
        # Temperature
        self.temp = temp.reshape(
            len(temp), len(temp[0][0]), len(temp[0][0][0])).astype(np.float)
        self.temp = self.temp.tolist()

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
        return np.hsplit(np.array([self._sky.generate(
            self._pwv, self._elev, det.det_arr.ch.freqs)
            for det in self._det_arr.dets]), 4)
