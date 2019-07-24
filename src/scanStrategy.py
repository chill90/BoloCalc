class ScanStrategy:
    """
    ScanStrategy object is used to sample the elevation distribution

    Args:
    tel (src.Telescope): Telescope object
    """
    def __init__(self, tel):
        # Store passed parameters
        self._tel = tel
        self._log = self._tel.exp.sim.log

        # Mininum and maximum allowed elevations
        self._min_elev = 20.
        self._max_elev = 90.

    # ***** Public Methods *****
    def elev_sample(self):
        """ Sample elevation """
        if self._tel.exp.sim.param("nexp") == 1:
            return self._tel.param("elev")
        samp = self._tel.param("elev").sample()
        if samp < self._min_elev:
            self._log.log(
                "Cannot have elevation %.1f < %.1f. Using %.1f instead"
                % (samp, self._min_elev, self._min_elev),
                self._log.level["NOTIFY"])
            return self._min_elev
        elif samp > self._max_elev:
            self._log.log(
                "Cannot have elevation %.1f > %.1f. Using %.1f instead"
                % (samp, self._max_elev, self._max_elev),
                self._log.level["NOTIFY"])
            return self._max_elev
        else:
            return samp
