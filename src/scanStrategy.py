# Built-in modules
import numpy as np

# BoloCalc modules
import src.units as un


class ScanStrategy:
    def __init__(self, tel):
        # Store passed parameters
        self.tel = tel

        # Mininum and maximum allowed elevations
        self.min_elev = 20
        self.max_elev = 90

    # ***** Public Methods *****
    # Sample elevation distribution
    def elv_sample(self):
        samp = tel.fetch("elev").sample()
        if samp < self.min_elev:
            self.log.log(
                "Cannot have elevation %.1f < %.1f. Using %.1f instead"
                % (samp, self.min_elev, self.min_elev), 2)
            return self.min_elev
        elif samp > self.max_elev:
            self.log.log(
                "Cannot have elevation %.1f > %.1f. Using %.1f instead"
                % (samp, self.max_elev, self.max_elev), 2)
            return self.max_elev
        else:
            return samp

    # Retrieve elevation
    def get_elev(self):
        return tel.fetch('elev')
