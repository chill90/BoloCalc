# Built-in modules
import numpy as np

# BoloCalc modules
import src.observation as ob


class ObservationSet:
    """
    ObservationSet object holds a set of observations for a given channel

    Args:
    ch (src.Channel): parent Channel object

    Attributes:
    temps (np.array): sky temperatures for each observation
    effs (np.array): sky efficiencies for each observation

    Parents:
    ch (src.Channel): Channel object
    """
    def __init__(self, ch):
        # Store passed parameters
        self.ch = ch
        self._log = self.ch.cam.tel.exp.sim.log
        self._nobs = ch.cam.tel.exp.sim.param("nobs")

        # Store the elevation values and probabilities
        self._log.log(
            "Generating ObservationSet realization for "
            "channel Band_ID = '%s'" % (self.ch.band_id))
        if self.ch.elev_dict is not None:
            self._elev_vals = np.fromiter(
                self.ch.elev_dict.keys(), dtype=np.float)
            self._elev_frac = np.fromiter(
                self.ch.elev_dict.values(), dtype=np.float)
        else:
            self._elev_vals = None
            self._elev_frac = None

        # Store observation objects
        self._log.log(
            "Generating observation objects in ObservationSet for "
            "channel Band_ID '%s'" % (self.ch.band_id))
        self.obs_arr = [ob.Observation(self) for n in range(self._nobs)]

    # ***** Pubic Methods *****
    def evaluate(self):
        self._log.log(
            "Evaluating observation objects in ObservationSet for channel %s"
            % (self.ch.param("ch_name")))
        # Evaluate observations
        for obs in self.obs_arr:
            obs.evaluate()
        return

    def sample_pix_elev(self, nsamp=1):
        """ Sample pixel elevation w.r.t. its camera's boresight """
        # Sample pixel elevation w.r.t. boresight distribution if defined
        if self._elev_vals is not None and self._elev_frac is not None:
            return np.random.choice(
                self._elev_vals, size=nsamp,
                p=self._elev_frac / float(np.sum(self._elev_frac)))
        # Otherwise, return 0 deg
        else:
            return np.zeros(nsamp)
