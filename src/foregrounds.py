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
        # Passed amplitude [W/(m^2 sr Hz)] converted from [MJy]
        amp = emiss * self._param("dust_amp")

        # Frequency scaling
        # (freq / scale_freq)**dust_ind
        if (self._param("dust_freq") is not "NA" and
           self._param("dust_ind") is not "NA"):
            freq_scale = ((freq / float(self._param("dust_freq"))))**(
                        self._param("dust_ind"))
        else:
            freq_scale = 1.

        # Effective blackbody scaling
        # BB(freq, dust_temp) / BB(dust_freq, dust_temp)
        if (self._param("dust_temp") is not "NA" and
           self._param("dust_freq") is not "NA"):
            spec_scale = (
                self._phys.bb_spec_rad(
                    freq, self._param("dust_temp")) /
                self._phys.bb_spec_rad(
                    float(self._param("dust_freq")), self._param("dust_temp")))
        else:
            spec_scale = 1.

        return (amp * freq_scale * spec_scale)

    def sync_spec_rad(self, freq, emiss=1.0):
        """
        Return the synchrotron spectral radiance [W/(m^2-Hz)]

        Args:
        freq (float): frequency at which to evaluate the spectral radiance
        emiss (float): emissivity of the synchrotron radiation. Default to 1.
        """
        # Passed brightness temp [K_RJ]
        bright_temp = emiss * self._param("sync_amp")

        # Spectral radiance [W/(m^2 sr Hz)]
        amp = self._phys.brightness_spec_rad(freq, bright_temp)

        # Frequency scaling (freq / sync_freq)**sync_ind
        freq_scale = (freq / self._param("sync_freq"))**self._param("sync_ind")

        return (amp * freq_scale)

    # ***** Helper Methods *****
    def _param(self, param):
        return self._sky.tel.exp.param(param)
