# Built-in modules
import numpy as np
import warnings as wn
import functools as ft

# BoloCalc modules
import src.units as un


class Sensitivity:
    def __init__(self, calc):
        # Store passed parameters
        self.calc = calc

    # ***** Public Methods *****
    # Optical power given some array of optical elements
    def popt(self, elem, emiss, eff, temp, freqs):
        eff = np.insert(eff, len(eff), [1. for f in freqs], axis=0)
        eff = np.array(eff).astype(np.float)
        return np.sum([np.trapz(
            self._phys().bb_pow_spec(
                freqs, temp[i], emiss[i] *
                np.prod(eff[i+1:], axis=0)), freqs)
                for i in range(len(elem))])

    # Photon NEP given some array of optical elements
    def photon_NEP(self, elem, emiss, eff, temp, freqs, ch=None):
        eff = np.insert(eff, len(eff), [1. for f in freqs], axis=0)
        eff = np.array(eff).astype(np.float)
        if ch:
            corrs = True
        else:
            corrs = False
        pow_ints = np.array([self._phys().bb_pow_spec(
            freqs, temp[i], emiss[i]*np.prod(eff[i+1:], axis=0))
            for i in range(len(elem))])
        if corrs:
            NEP_ph, NEP_ph_arr = self._noise().photon_nep(
                pow_ints, freqs, elem, (
                    ch.fetch("pix_sz") /
                    float(ch.cam.fetch("fnum") * self._ph().lamb(
                        ch.fetch("bc")))))
        else:
            NEP_ph, NEP_ph_arr = self.nse.photon_nep(pow_ints, freqs)
        return NEP_ph, NEP_ph_arr

    # Thermal carrier NEP given some optical power on the bolometer
    def bolo_NEP(self, opt_pow, det):
        if 'NA' in str(det.fetch("g")):
            if 'NA' in str(det.fetch("psat")):
                g = self._noise().G(
                    det.fetch("psat_fact") * opt_pow, det.fetch("n"),
                    det.fetch("tb"), det.fetch("tc"))
            else:
                g = self.nse.G(
                    det.fetch("psat"), det.fetch("n"),
                    det.fetch("tb"), det.fetch("tc"))
        else:
            g = det.fetch("g")
        if 'NA' in str(det.Flink):
            return self.nse.bolo_NEP(
                self.nse.Flink(
                    det.fetch("n"), det.fetch("tb"), det.fetch("tc")),
                g, det.fetch("tc"))
        else:
            return self.nse.bolometerNEP(
                det.fetch("flink"), g, det.fetch("tc"))

    # Readout NEP given some optical power on the bolometer
    def read_NEP(self, optPow, det):
        if 'NA' in str(det.float("nei")):
            return 'NA'
        elif 'NA' in str(det.fetch("bolo_r")):
            return 'NA'
        elif 'NA' in str(det.fetch("psat")):
            return self.nse.readoutNEP(
                (det.fetch("psat_fact") - 1.) * optPow,
                det.fetch("bolo_r"), det.fetch("nei"))
        else:
            if optPow >= det.psat:
                return 0.
            else:
                return self.nse.readoutNEP(
                    (det.psat-optPow), det.boloR, det.nei)

    # Mapping speed given some channel and telescope
    def sensitivity(self, ch, tp):

        ApEff = ch.apEff
        PoptArr = np.array([[self.Popt(
            ch.elem[i][j], ch.emiss[i][j], ch.effic[i][j],
            ch.temp[i][j], ch.freqs)
            for j in range(ch.detArray.nDet)]
            for i in range(ch.nobs)])
        if self._corr():
            NEPPhArr = np.array([[self.NEPph(
                ch.elem[i][j], ch.emiss[i][j], ch.effic[i][j],
                ch.temp[i][j], ch.freqs, ch)
                for j in range(ch.detArray.nDet)]
                for i in range(ch.nobs)])
        else:
            NEPPhArr = np.array([[self.NEPph(
                ch.elem[i][j], ch.emiss[i][j], ch.effic[i][j],
                ch.temp[i][j], ch.freqs)
                for j in range(ch.detArray.nDet)]
                for i in range(ch.nobs)])
        NEPboloArr = np.array([[self.NEPbolo(
            PoptArr[i][j], ch.detArray.detectors[j])
            for j in range(ch.detArray.nDet)]
            for i in range(ch.nobs)])
        NEPrdArr = np.array([[self.NEPrd(
            PoptArr[i][j], ch.detArray.detectors[j])
            for j in range(ch.detArray.nDet)]
            for i in range(ch.nobs)])

        NEPPhArr, NEPPhArrArr = np.split(NEPPhArr, 2, axis=2)
        NEPPhArr = np.reshape(NEPPhArr, np.shape(NEPPhArr)[:2])
        NEPPhArrArr = np.reshape(NEPPhArrArr, np.shape(NEPPhArrArr)[:2])

        if 'NA' in NEPrdArr:
            NEPrdArr = np.array([[np.sqrt(
                (1. + ch.detArray.detectors[j].readN)**2 - 1.) *
                np.sqrt(NEPPhArr[i][j]**2 + NEPboloArr[i][j]**2)
                for j in range(ch.detArray.nDet)]
                for i in range(ch.nobs)])
        NEP = np.sqrt(NEPPhArr**2 + NEPboloArr**2 + NEPrdArr**2)
        NEParr = np.sqrt(NEPPhArrArr**2 + NEPboloArr**2 + NEPrdArr**2)
        NET = np.array([[self.nse.NETfromNEP(
            NEP[i][j], ch.freqs, np.prod(ch.effic[i][j], axis=0), ch.optCouple)
            for j in range(ch.detArray.nDet)]
            for i in range(ch.nobs)]).flatten() * tp.params['NET Margin']
        NETar = np.array([[self.nse.NETfromNEP(
            NEParr[i][j], ch.freqs, np.prod(ch.effic[i][j], axis=0),
            ch.optCouple)
            for j in range(ch.detArray.nDet)]
            for i in range(ch.nobs)]).flatten() * tp.params['NET Margin']
        NETarr = self.ph.invVar(NETar) * np.sqrt(float(ch.nobs)) * np.sqrt(
            float(ch.clcDet) / float(ch.params['Yield']*ch.numDet))
        NETarrStd = np.std(NET)*np.sqrt(1./ch.numDet)
        MS = 1./(np.power(NETarr,    2.))
        # MSStd = abs(1./(np.power(NETarr+NETarrStd, 2.) - 1.) /
        # (np.power(NETarr-NETarrStd, 2.)))/2.
        MSStd = (NETarrStd/NETarr)*MS if (NETarrStd/NETarr) > 1.e-3 else 0.

        Sens = self.nse.sensitivity(
            NETarr, tp.params['Sky Fraction'],
            tp.params['Observation Time'] *
            tp.params['Observation Efficiency'])
        SensStd = self.nse.sensitivity(
            NETarrStd, tp.params['Sky Fraction'],
            tp.params['Observation Time'] *
            tp.params['Observation Efficiency'])

        # Return a dictionary of output parameters
        ret_dict = {
            "Stop Efficiency": 
        }
        means = [ch.apEff,
                 np.mean(PoptArr.flatten()),
                 np.mean(NEPPhArr.flatten()),
                 np.mean(NEPboloArr.flatten()),
                 np.mean(NEPrdArr.flatten()),
                 np.mean(NEP.flatten()),
                 np.mean(NET),
                 NETarr,
                 MS,
                 Sens]
        stds  = [0.,
                 np.std(PoptArr.flatten()),
                 np.std(NEPPhArr.flatten()),
                 np.std(NEPboloArr.flatten()),
                 np.std(NEPrdArr.flatten()),
                 np.std(NEP.flatten()),
                 np.std(NET),
                 NETarrStd,
                 MSStd,
                 SensStd]

        return means, stds

    # Optical power element by element given some channel and telescope
    def opticalPower(self, ch, tp):
        powSkySide = []
        powDetSide = []
        effDetSide = []
        for i in range(len(ch.elem)):
            powSkySide1 = []
            powDetSide1 = []
            effDetSide1 = []
            for j in range(len(ch.elem[i])):
                powers      = []
                powSkySide2 = []
                powDetSide2 = []
                effSkySide2 = []
                effDetSide2 = []
                #Store efficiency towards sky and towards detector
                for k in range(len(ch.elem[i][j])):
                    effArr = np.vstack([ch.effic[i][j], np.array([1. for f in ch.freqs])])
                    cumEffDet = ft.reduce(lambda x, y: x*y, effArr[k+1:])
                    effDetSide2.append(cumEffDet)
                    if   k == 0: cumEffSky = [[0. for f in ch.freqs]]                         #Nothing sky-side
                    elif k == 1: cumEffSky = [[1. for f in ch.freqs], [0. for f in ch.freqs]] #Only one element sky-side
                    else:        cumEffSky = [ft.reduce(lambda x, y: x*y, effArr[m+1:k]) if m < k-2 else effArr[m+1] for m in range(k-1)] + [[1. for f in ch.freqs], [0. for f in ch.freqs]]
                    effSkySide2.append(np.array(cumEffSky))
                    pow = self.ph.bbPowSpec(ch.freqs, ch.temp[i][j][k], ch.emiss[i][j][k])
                    powers.append(pow)
                #Store power from sky and power on detector
                for k in range(len(ch.elem[i][j])):
                    powOut = np.trapz(powers[k]*effDetSide2[k]*ch.bandMask, ch.freqs)
                    effDetSide2[k] = np.trapz(effDetSide2[k]*ch.bandMask, ch.freqs)/float(ch.bandDeltaF)
                    powDetSide2.append(powOut)
                    powIn = sum([np.trapz(powers[m]*effSkySide2[k][m]*ch.bandMask, ch.freqs) for m in range(k+1)])
                    powSkySide2.append(powIn)
                powSkySide1.append(powSkySide2)
                powDetSide1.append(powDetSide2)
                effDetSide1.append(effDetSide2)
            powSkySide.append(powSkySide1)
            powDetSide.append(powDetSide1)
            effDetSide.append(effDetSide1)
        #Build table of optical powers and efficiencies for each element
        shape = np.shape(powSkySide)
        newshape = (shape[0]*shape[1], shape[2])
        powSkySide = np.transpose(np.reshape(powSkySide, newshape))
        powDetSide = np.transpose(np.reshape(powDetSide, newshape))
        effDetSide = np.transpose(np.reshape(effDetSide, newshape))
        means = [np.mean(powSkySide, axis=1),
                 np.mean(powDetSide, axis=1),
                 np.mean(effDetSide, axis=1)]
        stds  = [np.std(powSkySide,  axis=1),
                 np.std(powDetSide,  axis=1),
                 np.std(effDetSide,  axis=1)]
        return means, stds

    def _phys(self):
        return self.calc.sim.phys

    def _noise(self):
        return self.calc.sim.noise

    def _corr(self):
        return self.calc.sim.fetch("corr")
