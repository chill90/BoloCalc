class ScanStrategy:
    """
    ScanStrategy object is used to sample the elevation distribution

    Args:
    tel (src.Telescope): parent Telescope object

    Parents:
    tel (src.Telescope): Telescope object
    """
    def __init__(self, tel):
        # Store passed parameters
        self._tel = tel
        self._log = self._tel.exp.sim.log

        # Mininum and maximum allowed elevations
        self.min_elev = 20.
        self.max_elev = 90.

    # ***** Public Methods *****
    def elev_sample(self):
        """ Sample telescope elevation """
        samp = self._tel.elev_sample()
        # Minimum allowed elevation = 20 deg
        if samp < self.min_elev:
            self._log.log(
                "Cannot have elevation %.1f < %.1f. Using %.1f instead"
                % (samp, self.min_elev, self.min_elev))
            return self.min_elev
        # Maximum allowed elevation = 90 deg
        elif samp > self.max_elev:
            self._log.log(
                "Cannot have elevation %.1f > %.1f. Using %.1f instead"
                % (samp, self.max_elev, self.max_elev))
            return self.max_elev
        else:
            return samp
