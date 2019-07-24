# BoloCalc modules
import src.detector as dt
import src.band as bd


class DetectorArray:
    """
    DetectorArray object contains the Detector object for a given channel

    Args:
    ch (src.Channel): Channel object

    Attributes:
    dets (list): list of src.Detector objects
    """
    def __init__(self, ch):
        # Store some passed parameters
        self.ch = ch
        log = self.ch.cam.tel.exp.sim.log
        nexp = self.ch.cam.tel.exp.sim.param("nexp")
        ndet = self.ch.cam.tel.exp.sim.param("ndet")

        # Store detectors
        if self.ch.band is not None:
            if self.ch.band.eff is not None:
                if nexp == 1:
                    bands = self.ch.band.get_avg(nsample=ndet)
                else:
                    bands = band.sample(nsample=ndet)
                self.dets = [dt.Detector(log, self.ch, bands[i])
                             for i in range(ndet)]
            else:
                self.dets = [dt.Detector(log, self.ch)
                             for i in range(ndet)]
        else:
            self.dets = [dt.Detector(log, self.ch)
                         for i in range(ndet)]
