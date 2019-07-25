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
    chs (list): src.Channel objects
    cams (list): src.Camera objects
    tels (list): src.Telescope objects
    """
    def __init__(self, sim):
        # Store passed parameters
        self._sim = sim
        self._exp = self.sim.exp

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
    def calc_sens(self, ch):
        """
        Calculate sensitivity for a given channel in a given telescope

        Args:
        ch (src.Channel): input Channel object
        tp (src.Telescope): input Telescope object
        """
        return self.sens.sensitivity(ch)

    def calc_opt_pow(self, ch):
        """
        Calculate optical power for a given channel in a given telescope

        Args:
        ch (src.Channel): input Channel object
        tp (src.Telescope): input Telescope object
        """
        return self.sens.opt_pow(ch)

    def comb_sens(self, sens_arr):
        """
        Combine sensitivites of multiple Sensitivity objects

        Args:
        sens_arr (list): list of sensitivities to be combined
        """
        self.sns_means = [[[[sens_arr[i][j][k][0][m]
                          for m in range(len(sens_arr[i][j][k][0]))]
                          for k in range(len(sens_arr[i][j]))]
                          for j in range(len(sens_arr[i]))]
                          for i in range(len(sens_arr))]
        self.sns_stds = [[[[sens_arr[i][j][k][1][m]
                         for m in range(len(sens_arr[i][j][k][1]))]
                         for k in range(len(sens_arr[i][j]))]
                         for j in range(len(sens_arr[i]))]
                         for i in range(len(sens_arr))]

    # Combine the optical powers of multiple channels
    def comb_opt_pow(self, opt_arr):
        """
        Combine optical powers of multiple Sensitivity objects

        Args:
        opt_arr (list): list of optical powers to be combined
        """
        self.opt_means = [[[[opt_arr[i][j][k][0][m]
                          for m in range(len(opt_arr[i][j][k][0]))]
                          for k in range(len(opt_arr[i][j]))]
                          for j in range(len(opt_arr[i]))]
                          for i in range(len(opt_arr))]
        self.opt_stds = [[[[opt_arr[i][j][k][1][m]
                         for m in range(len(opt_arr[i][j][k][1]))]
                         for k in range(len(opt_arr[i][j]))]
                         for j in range(len(opt_arr[i]))]
                         for i in range(len(opt_arr))]
