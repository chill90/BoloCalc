class Foregrounds:
    """
    Foreground object contains the foreground parameters for the sky
    """
    def __init__(self, sky):
        # Store passed parameters
        self._sky = sky
        self._phys = self._sky.tel.exp.sim.phys

    # ***** Public methods *****
    def dust_spec_rad(self, freq, emiss=1.0):
        """
        Return the galactic dust spectral radiance [W/(m^2-Hz)]

        Args:
        freq (float): frequency at which to evaluate the spectral radiance
        emiss (float): emissivity of the galactic dust. Default to 1.
        """
        amp = emiss * self._param("dust_amp")
        fscale = ((freq / float(self._param("dust_freq"))))**(
                    self._param("dust_ind"))
        spec = self._phys.bb_spec_rad(freq, self._param("dust_temp"))
        return (amp * fscale * spec)

    def sync_spec_rad(self, freq, emiss=1.0):
        """
        Return the synchrotron spectral radiance [W/(m^2-Hz)]

        Args:
        freq (float): frequency at which to evaluate the spectral radiance
        emiss (float): emissivity of the synchrotron radiation. Default to 1.
        """
        amp = emiss * self._param("sync_amp")
        fscale = freq**self._param("sync_ind")
        return (amp * fscale)

    # ***** Helper Methods *****
    def _param(self, param):
        return self._sky.tel.exp.param(param)
