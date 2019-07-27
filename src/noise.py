# Built-in modules
import numpy as np
import sys as sy
import os
import io
# Use fastest pickling module
PY2 = (sy.version_info[0] == 2)
if PY2:
    import cPickle as pk
else:
    import pickle as pk


class Noise:
    """
    Noise object calculates NEP, NET, mapping speed, and sensitivity

    Args:
    phys (src.Physics): Physics object
    """
    def __init__(self, phys):
        # Store passed parameters
        self._phys = phys

        # Aperture stop names
        self._ap_names = ["APERT", "STOP", "LYOT"]

        # Correlation files
        corr_dir = os.path.join(
            os.path.split(__file__)[0], "detCorrFiles", "PKL")
        if PY2:
            self._p_c_apert, self._c_apert = pk.load(io.open(
                os.path.join(corr_dir, "coherentApertCorr.pkl"), "rb"))
            self._p_c_stop,  self._c_stop = pk.load(io.open(
                os.path.join(corr_dir, "coherentStopCorr.pkl"), "rb"))
            self._p_i_apert, self._i_apert = pk.load(io.open(
                os.path.join(corr_dir, "incoherentApertCorr.pkl"), "rb"))
            self._p_i_stop,  self._i_stop = pk.load(io.open(
                os.path.join(corr_dir, "incoherentStopCorr.pkl"),  "rb"))
        else:
            self._p_c_apert, self._c_apert = pk.load(io.open(
                os.path.join(corr_dir, "coherentApertCorr.pkl"), "rb"),
                             encoding="latin1")
            self._p_c_stop,  self._c_stop = pk.load(io.open(
                os.path.join(corr_dir, "coherentStopCorr.pkl"), "rb"),
                             encoding="latin1")
            self._p_i_apert, self._i_apert = pk.load(io.open(
                os.path.join(corr_dir, "incoherentApertCorr.pkl"), "rb"),
                             encoding="latin1")
            self._p_i_stop,  self._i_stop = pk.load(io.open(
                os.path.join(corr_dir, "incoherentStopCorr.pkl"), "rb"),
                             encoding="latin1")

        # Detector pitch array
        self._det_p = self._p_c_apert
        # Geometric pitch factor
        self._geo_fact = 6  # Hex packing

    def corr_facts(self, elems, det_pitch, flamb_max=3.):
        """
        Calculate the Bose white-noise correlation factor

        Args:
        elems (list): optical elements in the camera
        det_pitch (float): detector pitch in f-lambda units
        flamb_max (float): the maximum detector pitch distance
        for which to calculate the correlation factor.
        Default is 3.
        """
        ndets = int(round(flamb_max / (det_pitch), 0))
        inds1 = [np.argmin(abs(np.array(self._det_p) -
                 det_pitch * (n + 1)))
                 for n in range(ndets)]
        inds2 = [np.argmin(abs(np.array(self._det_p) -
                 det_pitch * (n + 1) * np.sqrt(3.)))
                 for n in range(ndets)]
        inds = np.sort(inds1 + inds2)
        c_apert = np.sum([abs(self._c_apert)[ind] for ind in inds])
        i_apert = np.sum([abs(self._c_apert)[ind] for ind in inds])
        i_stop = np.sum([abs(self._c_stop)[ind] for ind in inds])
        c_apert = np.sqrt(c_apert*self._geo_fact + 1.)
        i_apert = np.sqrt(i_apert*self._geo_fact + 1.)
        i_stop = np.sqrt(i_stop*self._geo_fact + 1.)
        at_det = False
        factors = []
        for i in range(len(elems)):
            if "CMB" in elems[i]:
                factors.append(c_apert)
            if elems[i].upper() in self._ap_names:
                factors.append(i_stop)
                at_det = True
            elif not at_det:
                factors.append(i_apert)
            else:
                factors.append(1.)
        return np.array(factors[:-1])

    def photon_NEP(self, popts, freqs, elems=None, det_pitch=None):
        """
        Calculate photon NEP [W/rtHz] for a detector

        Args:
        popts (list): power from elements in the optical elements [W]
        freqs (list): frequencies of observation [Hz]
        elems (list): optical elements
        det_pitch (float): detector pitch in f-lambda units. Default is None.
        """
        popt = sum([x for x in popts])
        # Don't consider correlations
        if elems is None and det_pitch is None:
            popt2 = sum([x*y for x in popts for y in popts])
            nep = np.sqrt(np.trapz(
                (2. * self._phys.h * freqs * popt + 2. * popt2), freqs))
            neparr = nep
            return nep, neparr
        # Consider correlations
        else:
            factors = self.corr_facts(elems, det_pitch)
            popt2 = sum([popts[i]*popts[j]
                         for i in range(len(popts))
                         for j in range(len(popts))])
            popt2arr = sum([factors[i] * factors[j] * popts[i] * popts[j]
                            for i in range(len(popts))
                            for j in range(len(popts))])
            nep = np.sqrt(np.trapz(
                (2. * self._phys.h * freqs * popt + 2. * popt2), freqs))
            neparr = np.sqrt(np.trapz(
                (2. * self._phys.h * freqs * popt + 2. * popt2arr), freqs))
            return nep, neparr

    def photon_NEP_approx(self, powr, freqs):
        """
        Calculate RJ approximation of photon NEP [W/rtHz]

        Args:
        powr (list): total power incident on the detector [W]
        freqs (list): frequencies of observation [Hz]
        """
        bw = freqs[-1] - freqs[0]
        return np.sqrt(2. * (self._phys.h * freqs * powr + ((powr**2) / bw)))

    def Flink(self, n, Tb, Tc):
        """
        Link factor for the bolo to the bath

        Args:
        n (float): thermal carrier index
        Tb (float): bath temperature [K]
        Tc (float): transition temperature [K]
        """
        return (((n + 1)/(2 * n + 3)) * (1 - (Tb / Tc)**(2 * n + 3)) /
                (1 - (Tb / Tc)**(n + 1)))

    def G(self, psat, n, Tb, Tc):
        """
        Thermal conduction between the bolo and the bath

        Args:
        psat (float): saturation power [W]
        n (float): thermal carrier index
        Tb (float): bath temperature [K]
        Tc (float): bolo transition temperature [K]
        """
        return (psat * (n + 1) * (Tc**n) /
                ((Tc**(n + 1)) - (Tb**(n + 1))))

    def bolo_NEP(self, flink, G, Tc):
        """
        Thremal carrier NEP [W/rtHz]

        Args:
        flink (float): link factor to the bolo bath
        G (float): thermal conduction between the bolo and the bath [W/K]
        Tc (float): bolo transition temperature [K]
        """
        return np.sqrt(4 * self._phys.kB * flink * (Tc**2) * G)

    def read_NEP(self, pelec, boloR, nei):
        """
        Readout NEP [W/rtHz] for a voltage-biased bolo

        Args:
        pelec (float): bias power [W]
        boloR (float): bolometer resistance [Ohms]
        nei (float): noise equivalent current [A/rtHz]
        """
        return np.sqrt(boloR * pelec) * nei

    def dPdT(self, eff, freqs):
        """
        Change in power on the detector with change in CMB temperature [W/K]

        Args:
        eff (float): detector efficiency
        freqs (float): observation frequencies [Hz]
        """
        temp = np.array([self._phys.Tcmb for f in freqs])
        return np.trapz(self._phys.ani_pow_spec(
            np.array(freqs), temp, np.array(eff)), freqs)

    def photon_NET(self, freqs, popts, sky_eff,
                   elems=None, det_pitch=None):
        """
        Photon NET [K-rts]

        Args:
        popts (list): power from elements in the optical elements [W]
        freqs (list): frequencies of observation [Hz]
        sky_eff (float): efficiency between the detector and the sky
        elems (list): optical elements
        det_pitch (float): detector pitch in f-lambda units. Default is None.
        """
        nep = self.photon_NEP(popts, freqs, elems, det_pitch)
        dpdt = self.dPdT(sky_eff, freq, fbw)
        return nep/(np.sqrt(2.) * dpdt)

    def photon_NET_approx(self, freqs, powr, sky_eff):
        """
        RJ approximatino of photon NET [K-rts]

        rgs:
        freqs (list): observation frequencies [Hz]
        powr (list): total power incident on the detector [W]
        freqs (list): frequencies of observation [Hz]
        sky_eff (float): efficiency between the detector and the sky
        """
        nep = photon_NEP_approx(powr, freqs)
        dpdt = self.dPdT(sky_eff, freqs)
        return nep/(np.sqrt(2.) * dpdt)

    def bolo_NET(self, freqs, flink, G, Tc, sky_eff):
        """
        Thermal carrier NET [K-rts]

        Args:
        freqs (list): observation frequencies [Hz]
        flink (float): link factor to the bolo bath
        G (float): thermal conduction between the bolo and the bath [W/K]
        Tc (float): bolo transition temperature [K]
        sky_eff (float): efficiency between the detector and the sky
        """
        nep = bolo_NEP(psat, n, tc, tb)
        dpdt = self.dPdT(sky_eff, freqs)
        return nep/(np.sqrt(2.) * dpdt)

    def read_NET(self, freqs, pelec, boloR, nei, sky_eff):
        """
        Readout NEP [W/rtHz] for a voltage-biased bolo

        Args:
        freqs (list): observation frequencies [Hz]
        pelec (float): bias power [W]
        boloR (float): bolometer resistance [Ohms]
        nei (float): noise equivalent current [A/rtHz]
        sky_eff (float): efficiency between the detector and the sky
        """
        nep = read_NEP(pelec, boloR, nei)
        dpdt = self.dPdT(sky_eff, freq, fbw)
        return nep/(np.sqrt(2.) * dpdt)

    def NET_from_NEP(self, nep, freqs, sky_eff, opt_coup=1.0):
        """
        NET [K-rts] from NEP

        Args:
        nep (float): NEP [W/rtHz]
        freqs (list): observation frequencies [Hz]
        sky_eff (float): efficiency between the detector and the sky
        opt_coup (float): optical coupling to the detector. Default to 1.
        """
        dpdt = opt_coup * self.dPdT(sky_eff, freqs)
        return nep / (np.sqrt(2.) * dpdt)

    def NET_arr(self, net, n_det, det_yield=1.0):
        """
        Array NET [K-rts] from NET per detector and num of detectors

        Args:
        net (float): NET per detector
        n_det (int): number of detectors
        det_yield (float): detector yield. Defaults to 1.
        """
        return net/(np.sqrt(n_det * det_yield))

    def sensitivity(self, net_arr, fsky, tobs):
        """
        Sensitivity [K-arcmin] given array NET

        Arg:
        net_arr (float): array NET [K-rts]
        fsky (float): sky fraction
        tobs (float): observation time [s]
        """
        return np.sqrt(
            (4. * self._phys.PI * fsky * 2. * np.power(net_arr, 2.)) /
            float(tobs)) * (10800. / self._phys.PI)

    def mapping_speed(self, net, n_det, det_yield=1.0):
        """
        Mapping speed [(k^2*s)^-1] given detector NET and num of detectors

        Args:
        net (float): detector NET [K-rts]
        n_det (int): number of detectors
        det_yield (float): detector yield. Defaults to 1.
        """
        return det_yield / (np.power(self.NET_arr(net, n_det), 2.))
