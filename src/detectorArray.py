import src.detector  as dt
import src.band      as bd

class DetectorArray:
    def __init__(self, log, ch, nrealize=1, bandFile=None):
        self.log      = log
        self.ch       = ch
        self.nrealize = nrealize
        self.nDet     = int(self.ch.clcDet) #Number of detectors to calculate

        #Store detectors
        if bandFile: 
            band  = bd.Band(log, bandFile, ch.freqs)
            if band.eff is not None:
                if self.nrealize == 1: bands = band.getAvg(nsample=self.nDet)
                else:                  bands = band.sample(nsample=self.nDet)
                self.detectors  = [dt.Detector(log, self.ch, bands[i]) for i in range(self.nDet)]
            else:
                self.detectors  = [dt.Detector(log, self.ch)           for i in range(self.nDet)]
        else:
            self.detectors  = [dt.Detector(log, self.ch)           for i in range(self.nDet)]
