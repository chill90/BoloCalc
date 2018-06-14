#python Version 2.7.2
import numpy   as np
import pickle  as pk
import physics as ph

class Noise:
    def __init__(self):     
        #Efficiency of the galaxy
        self.__skyEff = 1.0

        #Instantiate physics object for calculations
        self.ph = ph.Physics()

        #Correlation files
        dir = '/'.join(__file__.split('/')[:-1])+'/detCorrFiles/PKL/'
        self.p_c_apert, self.c_apert = pk.load(open(dir+'coherentApertCorr.pkl',   'rb'))
        self.p_c_stop,  self.c_stop  = pk.load(open(dir+'coherentStopCorr.pkl',    'rb'))
        self.p_i_apert, self.i_apert = pk.load(open(dir+'incoherentApertCorr.pkl', 'rb'))
        self.p_i_stop,  self.i_stop  = pk.load(open(dir+'incoherentStopCorr.pkl',  'rb'))
        #Detector pitch array
        self.DetP = self.p_c_apert
        #Geometric pitch factor
        self.corrFact = 6 #Hex packing
        
    #Bose correlation factors
    def corrFactors(self, elemArr, detPitchFlamb, FlambMax=3.):
        FlambMax = 3. #Consider correlations out to this length
        ndets = int(round(FlambMax/float(detPitchFlamb), 0))
        inds1 = [np.argmin(abs(np.array(self.DetP) - detPitchFlamb*(n+1)            )) for n in range(ndets)]
        inds2 = [np.argmin(abs(np.array(self.DetP) - detPitchFlamb*(n+1)*np.sqrt(3.))) for n in range(ndets)]
        inds  = np.sort(inds1 + inds2)
        c_apert = np.sum([abs(self.c_apert)[ind] for ind in inds])
        i_apert = np.sum([abs(self.c_apert)[ind] for ind in inds])
        i_stop  = np.sum([abs(self.c_stop)[ ind] for ind in inds])
        c_apert  = np.sqrt(c_apert*self.corrFact + 1.)
        i_apert  = np.sqrt(i_apert*self.corrFact + 1.)
        i_stop   = np.sqrt(i_stop*self.corrFact  + 1.)
        atDet = False
        factors = []
        for i in range(len(elemArr)):
            if 'CMB' in elemArr[i]:
                factors.append(c_apert)
            if ('Apert' in elemArr[i]) or ('Lyot' in elemArr[i]) or ('Stop' in elemArr[i]):
                factors.append(i_stop)
                atDet = True
            elif not atDet:
                factors.append(i_apert)
            else:
                factors.append(1.)
        return np.array(factors[:-1])
    #Photon noise equivalent power on a diffraction-limited detector [W/rtHz]
    def photonNEP(self, poptArr, freqs, elemArr=None, detPitchFlamb=None):
        popt  = sum([x for x in poptArr])
        #Don't consider correlations
        if elemArr is None and detPitchFlamb is None:
            popt2  = sum([x*y for x in poptArr for y in poptArr])
            nep    = np.sqrt(np.trapz((2*self.ph.h*freqs*popt + 2*popt2), freqs))
            neparr = nep
            return nep, neparr
        #Consider correlations
        else:
            factors = self.corrFactors(elemArr, detPitchFlamb)
            popt2    = sum([poptArr[i]*poptArr[j]                       for i in range(len(poptArr)) for j in range(len(poptArr))])
            popt2arr = sum([factors[i]*factors[j]*poptArr[i]*poptArr[j] for i in range(len(poptArr)) for j in range(len(poptArr))])
            nep    = np.sqrt(np.trapz((2*self.ph.h*freqs*popt + 2*popt2),    freqs))
            neparr = np.sqrt(np.trapz((2*self.ph.h*freqs*popt + 2*popt2arr), freqs))
            return nep, neparr
    #RJ approximation of photon noise equivalent power on a diffraction-limited detector [W/rt(Hz)]
    def photonNEPapprox(self, pow, freqs):
        deltaF = freqs[-1] - freqs[0]
        return np.sqrt(2*(self.ph.h*freqs*pow + ((pow**2)/deltaF)))
    #Bolometer noise equivalent power [W/rt(Hz)]
    def bolometerNEP(self, psat, n, Tc, Tb):
        return np.sqrt(4*self.ph.kB*psat*Tb*(((np.power((n+1),2.)/((2*n)+3))*((np.power((Tc/Tb),((2*n)+3)) - 1)/np.power((np.power((Tc/Tb),(n+1)) - 1),2.)))))
    #Readout noise equivalent power [W/rt(Hz)]
    def readoutNEP(self, pelec, boloR, nei):
        return np.sqrt(boloR*pelec)*nei
    #Change in power with change in CMB temperature [W/K]
    def dPdT(self, eff, freqs):
        temp = np.array([self.ph.Tcmb for f in freqs])
        return np.trapz(self.ph.aniPowSpec(np.array(freqs), temp, np.array(eff)), freqs)
    #Photon noise equivalent temperature [K-rts]
    def photonNET(self, poptArr, freqs, skyEff, elemArr=None, detPitchFlamb=None):
        nep  = self.photonNEP(poptArr, freqs, elemArr, detPitchFlamb)
        dpdt = self.dPdT(skyEff, freq, fbw)
        return nep/(np.sqrt(2.)*dpdt)
    #RJ approximation of photon noise equivalent tempeature [K-rt(s)]
    def photonNETapprox(self, pow, freqs, skyEff):
        nep  = photonNEPapprox(pow, freqs)
        dpdt = self.dPdT(skyEff, freqs)
        return nep/(np.sqrt(2.)*dpdt)
    #Bolometer noise equivalent temperature [K-rt(s)]
    def bolometerNET(self, psat, freq, fbw, n, Tc, Tb, skyEff):
        nep  = bolometerNEP(psat, n, Tc, Tb) 
        dpdt = self.dPdT(skyEff, freq, fbw)
        return nep/(np.sqrt(2.)*dpdt)
    #Readout noise equivalent temperature [K-rt(s)]
    def readoutNET(self, pelec, freq, fbw, boloR, nei, skyEff):
        nep  = readoutNEP(pelec, boloR, nei)
        dpdt = self.dPdT(skyEff, freq, fbw)
        return nep/(np.sqrt(2.)*dpdt)
    #Total noise equivalent temperature [K-rt(s)]
    def NETfromNEP(self, nep, freqs, skyEff, optCouple=1.0):
        dpdt = optCouple*self.dPdT(skyEff, freqs)
        return nep/(np.sqrt(2.)*dpdt)
    #Array noise equivalent temperature [K-rt(s)]
    def NETarr(self, net, nDet, detYield=1.0):
        return net/np.sqrt(nDet*detYield)
    #Sky sensitivity [K-arcmin]
    def sensitivity(self, netArr, fsky, tobs):
        return np.sqrt((4.*self.ph.PI*fsky*2.*np.power(netArr, 2.))/tobs)*(10800./self.ph.PI)
    #Mapping speed [(K^2*s)^-1]
    def mappingSpeed(self, net, nDet, detYield=1.0):
        return detYield/np.power(self.NETarr(net, nDet), 2.)
