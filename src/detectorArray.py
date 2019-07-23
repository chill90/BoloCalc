# BoloCalc modules
import src.detector as dt
import src.band as bd


class DetectorArray:
    def __init__(self, ch):
        # Store some passed parameters
        self.ch = ch

        # Store detectors
        if self.ch.band_file is not None:
            band = bd.Band(self._log(), self.ch.band_file, self.ch.freqs)
            if band.eff is not None:
                if self._nexp() == 1:
                    bands = band.get_avg(nsample=self._ndet())
                else:
                    bands = band.sample(nsample=self._ndet())
                self.dets = [dt.Detector(self._log(), self.ch, bands[i])
                                  for i in range(self._ndet())]
            else:
                self.dets = [dt.Detector(self._log(), self.ch)
                                  for i in range(self._ndet())]
        else:
            self.dets = [dt.Detector(self._log(), self.ch)
                              for i in range(self._ndet())]

    def _log(self):
        return self.ch.cam.tel.exp.sim.log

    def _nexp(self):
        return self.cam.tel.exp.sim.fetch("nexp")

    def _ndet(self):
        return self.cam.tel.exp.sim.fetch("ndet")
