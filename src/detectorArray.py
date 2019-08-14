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
        self._log = self.ch.cam.tel.exp.sim.log
        self._nexp = self.ch.cam.tel.exp.sim.param("nexp")
        self._ndet = self.ch.cam.tel.exp.sim.param("ndet")

        # Store detector objects
        self.dets = [dt.Detector(self) for n in range(self._ndet)]

    def evaluate(self):
        # Evaluate detectors
        if self.ch.det_band is not None:
            if self._ndet == 1:
                bands = self.ch.det_band.get_avg()
            else:
                bands = self.ch.det_band.sample(nsample=self._ndet)
            for det, band in zip(self.dets, bands):
                det.evaluate(band)
        else:
            for det in self.dets:
                det.evaluate()
        return
