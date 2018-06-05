#python Version 2.7.2
import detector  as dt
import band      as bd

class DetectorArray:
    def __init__(self, log, ch, bandFile=None):
        self.log  = log
        self.ch   = ch
        self.nDet = int(self.ch.clcDet) #Number of detectors to calculate

        #Store detectors
        if bandFile: 
            band  = bd.Band(log, bandFile, ch.freqs)
            if band.eff is not None:
                bands = band.sample(nsample=self.nDet)
                self.detectors  = [dt.Detector(log, self.ch, bands[i]) for i in range(self.nDet)]
            else:
                self.detectors  = [dt.Detector(log, self.ch)           for i in range(self.nDet)]
        else:
            self.detectors  = [dt.Detector(log, self.ch)           for i in range(self.nDet)]
