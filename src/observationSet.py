# Built-in modules
import numpy as np

# BoloCalc modules
import src.observation as ob
import src.scanStrategy as sc
import src.units as un


class ObservationSet:
    def __init__(self, ch):
        # Store passed parameters
        self.ch = ch

        # Store the elevation values and probabilities
        if ch.elvDict is not None:
            self.elev_vals = np.fromiter(ch.elev_dict.keys(),   dtype=np.float)
            self.elev_frac = np.fromiter(ch.elev_dict.values(), dtype=np.float)
        else:
            self.elVals = None
            self.elFrac = None

        # Store observation objects
        self.obs = [ob.Observation(self) for n in range(nobs)]
        # Store sky temperatures and efficiencies
        self.temps = np.array([obs.temp for obs in self.obs])
        self.effics = np.array([obs.effic for obs in self.obs])

    # ***** Pubic Methods *****
    # Sample elevation distribution
    def sample_pix_elev(self):
        if self.elVals is not None and self.elFrac is not None:
            return np.random.choice(
                self.elVals, size=1,
                p=self.elFrac/float(np.sum(self.elFrac)))[0]
        else:
            return 0.
