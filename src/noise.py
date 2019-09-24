# Built-in modules
import numpy as np
import pickle as pk
import os
import io


class Noise:
    """
    Noise object calculates NEP, NET, mapping speed, and sensitivity

    Args:
    phys (src.Physics): parent Physics object

    Parents:
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
            elif elems[i].upper() in self._ap_names:
                factors.append(i_stop)
                at_det = True
            elif not at_det:
                factors.append(i_apert)
            else:
                factors.append(1.)
        # return np.array(factors[:-1])
        return np.array(factors)

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
            popt2 = sum([popts[i] * popts[j]
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

    def bolo_NEP(self, flink, G, Tc):
        """
        Thremal carrier NEP [W/rtHz]

        Args:
        flink (float): link factor to the bolo bath
        G (float): thermal conduction between the bolo and the bath [W/K]
        Tc (float): bolo transition temperature [K]
        """
        return np.sqrt(4 * self._phys.kB * flink * (Tc**2) * G)

    def read_NEP(self, pelec, boloR, nei, sfact=1.):
        """
        Readout NEP [W/rtHz] for a voltage-biased bolo

        Args:
        pelec (float): bias power [W]
        boloR (float): bolometer resistance [Ohms]
        nei (float): noise equivalent current [A/rtHz]
        """
        responsivity = sfact / np.sqrt(boloR * pelec)
        return nei / responsivity

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

    def map_depth(self, net_arr, fsky, tobs, obs_eff):
        """
        Sensitivity [K-arcmin] given array NET

        Arg:
        net_arr (float): array NET [K-rts]
        fsky (float): sky fraction
        tobs (float): observation time [s]
        """
        return np.sqrt(
            (4. * self._phys.PI * fsky * 2. * np.power(net_arr, 2.)) /
            (tobs * obs_eff)) * (10800. / self._phys.PI)
