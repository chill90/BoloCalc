# BoloCalc modules
import src.detector as dt
import src.band as bd


class DetectorArray:
    def __init__(self, ch):
        #Store some passed parameters
        self.ch = ch

        # Store detectors
        if bandFile is not None:
            band = bd.Band(self._log(), ch.band_file, self.ch.freqs)
            if band.eff is not None:
                if self._nexp() == 1:
                    bands = band.getAvg(nsample=self._ndet())
                else:
                    bands = band.sample(nsample=self._ndet())
                self.detectors = [dt.Detector(self._log(), self.ch, bands[i])
                                  for i in range(self._ndet())]
            else:
                self.detectors = [dt.Detector(self._log(), self.ch)
                                  for i in range(self._ndet())]
        else:
            self.detectors = [dt.Detector(self._log(), self.ch)
                              for i in range(self._ndet())]
    
    def _log(self):
        return self.ch.cam.tel.exp.sim.log
    
    def _nexp(self):
        return self.cam.tel.exp.sim.fetch("nexp")

    def _ndet(self):
        return self.cam.tel.exp.sim.fetch("ndet")
