# Built-in modules
import numpy as np

# BoloCalc modules
import src.sensitivity as sn


class Calculate:
    """
    Calculate object calculates sensitivity for a specific channel in
    a specific telescope, as well as combines sensitivites for multiple
    channels across an experiment

    Args:
    sim (src.Simulate): Simulation object

    Attributes:
    sim (src.Simulate): where the 'sim' arg is stored
    chs (list): src.Channel objects
    cams (list): src.Camera objects
    tels (list): src.Telescope objects
    """
    def __init__(self, sim):
        # Store passed parameters
        self.sim = sim

        self.chs = [[[ch for ch in cm.chs.values()]
                    for cm in tp.cams.values()]
                    for tp in self._exp().tels.values()]
        self.cams = [[[cm for i in cm.chs.values()]
                     for cm in tp.cams.values()]
                     for tp in self._exp().tels.values()]
        self.tels = [[[tp for i in cm.chs.values()]
                     for cm in tp.cams.values()]
                     for tp in self._exp().tels.values()]
        self.sens = sn.Sensitivity(self)

    # ***** Public Methods *****
    # Calculate sensitivity for this channel
    def calc_sens(self, ch, tp):
        """
        Calculate sensitivity for a given channel in a given telescope

        Args:
        ch (src.Channel): input Channel object
        tp (src.Telescope): input Telescope object
        """
        return self.sens.sensitivity(ch, tp)

    # Calculate optical power for this channel
    def calc_opt_pow(self, ch, tp):
        """
        Calculate optical power for a given channel in a given telescope

        Args:
        ch (src.Channel): input Channel object
        tp (src.Telescope): input Telescope object
        """
        return self.sens.opticalPower(ch, tp)

    # Combine the sensitivities of multiple channels
    def comb_sens(self, sensArr):
        self.snsmeans = [[[[sensArr[i][j][k][0][m]
                         for m in range(len(sensArr[i][j][k][0]))]
                         for k in range(len(sensArr[i][j]))]
                         for j in range(len(sensArr[i]))]
                         for i in range(len(sensArr))]
        self.snsstds = [[[[sensArr[i][j][k][1][m]
                        for m in range(len(sensArr[i][j][k][1]))]
                        for k in range(len(sensArr[i][j]))]
                        for j in range(len(sensArr[i]))]
                        for i in range(len(sensArr))]

    # Combine the optical powers of multiple channels
    def comb_opt_pow(self, optArr):
        self.optmeans = [[[[optArr[i][j][k][0][m]
                         for m in range(len(optArr[i][j][k][0]))]
                         for k in range(len(optArr[i][j]))]
                         for j in range(len(optArr[i]))]
                         for i in range(len(optArr))]
        self.optstds = [[[[optArr[i][j][k][1][m]
                        for m in range(len(optArr[i][j][k][1]))]
                        for k in range(len(optArr[i][j]))]
                        for j in range(len(optArr[i]))]
                        for i in range(len(optArr))]

    # ***** Helper Methods *****
    def _exp(self):
        return self.sim.exp
