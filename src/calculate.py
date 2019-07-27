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
    def __init__(self, exp):
        # Store passed parameters
        self.exp = exp

        self.chs = [[[ch for ch in cm.chs.values()]
                    for cm in tp.cams.values()]
                    for tp in self.exp.tels.values()]
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
