# Built-in modules
import numpy as np

# BoloCalc modules
import src.observation as ob
import src.scanStrategy as sc
import src.units as un


class ObservationSet:
    """
    ObservationSet object holds a set of observations for a given channel

    Args:
    ch (src.Channel): Channel object

    Attributes:
    temps (np.array): sky temperatures for each observation
    effs (np.array): sky efficiencies for each observation
    """
    def __init__(self, ch):
        # Store the elevation values and probabilities
        if ch.elev_dict is not None:
            self._elev_vals = np.fromiter(
                ch.elev_dict.keys(), dtype=np.float)
            self._elev_frac = np.fromiter(
                ch.elev_dict.values(), dtype=np.float)
        else:
            self._elev_vals = None
            self._elev_frac = None

        # Store observation objects
        nobs = ch.cam.tel.exp.sim.param("nobs")
        obs_arr = [ob.Observation(self) for n in range(nobs)]
        # Store sky temperatures and efficiencies
        self.temps = np.array([obs.temp for obs in obs_arr])
        self.effs = np.array([obs.effic for obs in obs_arr])

    # ***** Pubic Methods *****
    def sample_pix_elev(self):
        """ Sample pixel elevation """
        if self._elev_vals is not None and self._elev_frac is not None:
            return np.random.choice(
                self._elev_vals, size=1,
                p=self._elev_frac / float(np.sum(self._elev_frac)))[0]
        else:
            return 0.
