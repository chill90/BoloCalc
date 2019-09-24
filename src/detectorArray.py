# BoloCalc modules
import src.detector as dt


class DetectorArray:
    """
    DetectorArray object contains the Detector object for a given channel

    Args:
    ch (src.Channel): parent Channel object

    Parents:
    ch (src.Channel): Channel object

    Attributes:
    dets (list): list of src.Detector objects
    """
    def __init__(self, ch):
        # Store passed parameters
        self.ch = ch
        self._log = self.ch.cam.tel.exp.sim.log
        self._nexp = self.ch.cam.tel.exp.sim.param("nexp")
        self._ndet = self.ch.cam.tel.exp.sim.param("ndet")

        # Store detector objects
        self._log.log(
            "Storing detector objects in DetectorArray for "
            "channel Band_ID '%s'" % (self.ch.band_id))
        self.dets = [dt.Detector(self) for n in range(self._ndet)]

    def evaluate(self):
        """ Evaluate detector objects """
        self._log.log(
            "Evaluating detector objects in DetectorArray for channel %s"
            % (self.ch.param("ch_name")))
        # Sample the detector band if defined when evaluating detectors
        if self.ch.det_band is not None:
            if self._ndet == 1:
                bands = self.ch.det_band.get_avg()
            else:
                bands = self.ch.det_band.sample(nsample=self._ndet)
            for det, band in zip(self.dets, bands):
                det.evaluate(band)
        # Otherwise, simply evaluate the detectors
        else:
            for det in self.dets:
                det.evaluate()
        return
