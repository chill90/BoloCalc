# Built-in modules
import numpy as np
# BoloCalc modules
import src.sensitivity as sn


class Calculate:
    def __init__(self, log, exp, corr=True):
        # Store passed parameters
        self.log = log
        self.exp = exp
        self.corr = corr

        self.log.log("Calculating sensitivity for experiment %s" %
                     (self.exp.name), 1)
        self.chans = [[[ch for ch in camera.channels.values()]
                      for camera in telescope.cameras.values()]
                      for telescope in self.exp.telescopes.values()]
        self.cams = [[[cm for i in cm.channels.values()]
                     for cm in telescope.cameras.values()]
                     for telescope in self.exp.telescopes.values()]
        self.teles = [[[tp for i in cm.channels.values()]
                      for cm in tp.cameras.values()]
                      for tp in self.exp.telescopes.values()]
        self.sens = sn.Sensitivity(log, exp, corr)

    # ***** Public Methods *****
    # Calculate sensitivity for this channel
    def calcSensitivity(self, ch, tp):
        return self.sens.sensitivity(ch, tp)

    # Calculate optical power for this channel
    def calcOpticalPower(self, ch, tp):
        return self.sens.opticalPower(ch, tp)

    # Combine the sensitivities of multiple channels
    def combineSensitivity(self, sensArr):
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
    def combineOpticalPower(self, optArr):
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
