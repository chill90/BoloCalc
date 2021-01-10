class Foregrounds:
    """
    Foreground object contains the foreground parameters for the sky
    """
    def __init__(self, sky):
        # Store passed parameters
        self._sky = sky
        self._phys = self._sky.tel.exp.sim.phys

    # ***** Public methods *****
    def dust_temp(self, freq, emiss=1.0): 
        """
        Return the galactic effective physical temperature

        Args:
        freq (float): frequency at which to evaluate the physical temperature
        emiss (float): emissivity of the galactic dust. Default to 1.
        """
        # Passed amplitude [W/(m^2 sr Hz)] converted from [MJy]
        amp = emiss * self._param("dust_amp")
        # Frequency scaling
        # (freq / scale_freq)**dust_ind
        if (str(self._param("dust_freq")) != "NA" and
           str(self._param("dust_ind")) != "NA"):
            freq_scale = ((freq / float(self._param("dust_freq"))))**(
                        self._param("dust_ind"))
        else:
            freq_scale = 1.
        # Effective blackbody scaling
        # BB(freq, dust_temp) / BB(dust_freq, dust_temp)
        if (str(self._param("dust_temp")) != "NA" and
           str(self._param("dust_freq")) != "NA"):
            spec_scale = (
                self._phys.bb_spec_rad(
                    freq, self._param("dust_temp")) /
                self._phys.bb_spec_rad(
                    float(self._param("dust_freq")), self._param("dust_temp")))
        else:
            spec_scale = 1.
        # Convert [W/(m^2 sr Hz)] to brightness temperature [K_RJ]
        pow_spec_rad = (amp * freq_scale * spec_scale)
        # Convert brightness temperature [K_RJ] to physical temperature [K]
        phys_temp = self._phys.Tb_from_spec_rad(freq, pow_spec_rad)
        return phys_temp

    def sync_temp(self, freq, emiss=1.0):
        """
        Return the synchrotron spectral radiance [W/(m^2-Hz)]

        Args:
        freq (float): frequency at which to evaluate the spectral radiance
        emiss (float): emissivity of the synchrotron radiation. Default to 1.
        """
        # Passed brightness temp [K_RJ]
        bright_temp = emiss * self._param("sync_amp")
        # Frequency scaling (freq / sync_freq)**sync_ind
        freq_scale = (freq / self._param("sync_freq"))**self._param("sync_ind")
        scaled_bright_temp = bright_temp * freq_scale
        # Convert brightness temperature [K_RJ] to physical temperature [K]
        phys_temp = self._phys.Tb_from_Trj(freq, scaled_bright_temp)
        return phys_temp

    # ***** Helper methods *****
    def _param(self, param):
        """ Retrieve a foreground parameter """
        return self._sky.tel.exp.param(param)
