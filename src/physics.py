# Built-in modules
import numpy as np


class Physics:
    """
    Physics object calculates physical quantities

    Attributes:
    h (float): Planck constant [J/s]
    kB (float): Boltzmann constant [J/K]
    c (float): Speed of light [m/s]
    PI (float): Pi
    mu0 (float): Permability of free space [H/m]
    ep0 (float): Permittivity of free space [F/m]
    Z0 (float): Impedance of free space [Ohm]
    Tcmb (float): CMB Temperature [K]
    co (dict): CO Emission lines [Hz]
    """
    def __init__(self):
        self.h = 6.6261e-34
        self.kB = 1.3806e-23
        self.c = 299792458.0
        self.PI = 3.14159265
        self.mu0 = 1.256637e-6
        self.ep0 = 8.854188e-12
        self.Z0 = np.sqrt(self.mu0/self.ep0)
        self.Tcmb = 2.725

    # ***** Public Methods *****
    def lamb(self, freq, ind=1.0):
        """
        Convert from from frequency [Hz] to wavelength [m]

        Args:
        freq (float): frequencies [Hz]
        ind: index of refraction. Defaults to 1
        """
        freq, ind = self._check_inputs(freq, [ind])
        return self.c/(freq*ind)

    def band_edges(self, freqs, tran):
        """ Find the -3 dB points of an arbirary band """
        max_tran = np.amax(tran)
        max_tran_loc = np.argmax(tran)
        lo_point = np.argmin(
            abs(tran[:max_tran_loc] - 0.5 * max_tran))
        hi_point = np.argmin(
            abs(tran[max_tran_loc:] - 0.5 * max_tran)) + max_tran_loc
        flo = freqs[lo_point]
        fhi = freqs[hi_point]
        return flo, fhi

    def spill_eff(self, freq, pixd, fnum, wf=3.0):
        """
        Pixel beam coupling efficiency given a frequency [Hz],
        pixel diameter [m], f-number, and beam wasit factor

        Args:
        freq (float): frequencies [Hz]
        pixd (float): pixel size [m]
        fnum (float): f-number
        wf (float): waist factor. Defaults to 3.
        """
        freq, pixd, fnum, wf = self._check_inputs(freq, [pixd, fnum, wf])
        return 1. - np.exp(
            (-np.power(np.pi, 2)/2.) * np.power(
                (pixd / (wf * fnum * (self.c/freq))), 2))

    def edge_taper(self, ap_eff):
        """
        Edge taper given an aperture efficiency

        Args:
        ap_eff (float): aperture efficiency
        """
        return 10. * np.log10(1. - ap_eff)

    def apert_illum(self, freq, pixd, fnum, wf=3.0):
        """
        Aperture illumination efficiency given a frequency [Hz],
        pixel diameter [m], f-number, and beam waist factor

        Args:
        freq (float): frequencies [Hz]
        pixd (float): pixel diameter [m]
        fnum (float): f-number
        wf (float): beam waist factor
        """
        freq, pixd, fnum, wf = self._check_inputs(freq, [pixd, fnum, wf])
        lamb = self.lamb(freq)
        w0 = pixd / wf
        theta_stop = lamb / (np.pi * w0)
        theta_apert = np.arange(0., np.arctan(1. / (2. * fnum)), 0.01)
        V = np.exp(-np.power(theta_apert, 2.) / np.power(theta_stop, 2.))
        eff_num = np.power(
            np.trapz(V * np.tan(theta_apert / 2.), theta_apert), 2.)
        eff_denom = np.trapz(
            np.power(V, 2.) * np.sin(theta_apert), theta_apert)
        eff_fact = 2. * np.power(np.tan(theta_apert/2.), -2.)
        return (eff_num / eff_denom) * eff_fact

    def ruze_eff(self, freq, sigma):
        """
        Ruze efficiency given a frequency [Hz] and surface RMS roughness [m]

        Args:
        freq (float): frequencies [Hz]
        sigma (float): RMS surface roughness
        """
        freq, sigma = self._check_inputs(freq, [sigma])
        return np.exp(-np.power(4 * np.pi * sigma / (self.c / freq), 2.))

    def ohmic_eff(self, freq, sigma):
        """
        Ohmic efficiency given a frequency [Hz] and conductivity [S/m]

        Args:
        freq (float): frequencies [Hz]
        sigma (float): conductivity [S/m]
        """
        freq, sigma = self._check_inputs(freq, [sigma])
        return 1. - 4. * np.sqrt(np.pi * freq * self.mu0 / sigma) / self.Z0

    #def brightness_temp(self, freq, spec_rad):
    #    """
    #    Brightness temperature [K_RJ] given a frequency [Hz] and
    #    spectral radiance [W Hz^-1 sr^-1 m^-2]
    #
    #    Args:
    #    freq (float): frequency [Hz]
    #    spec_rad (float): spectral radiance [W Hz^-1 sr^-1 m^-2]
    #    """
    #    #return spec_rad / (2 * self.kB * (freq / self.c)**2)
    #    return spec_rad / (self.kB * (freq / self.c)**2)

    def Trj_over_Tb(self, freq, Tb):
        """
        Brightness temperature [K_RJ] given a physical temperature [K]
        and frequency [Hz]. dTrj / dTb

        Args:
        freq (float): frequencies [Hz]
        Tb (float): physical temperature. Default to Tcmb
        """
        freq, Tb = self._check_inputs(freq, [Tb])
        x = (self.h * freq)/(Tb * self.kB)
        thermo_fact = np.power(
            (np.exp(x) - 1.), 2.) / (np.power(x, 2.) * np.exp(x))
        return 1. / thermo_fact

    def Tb_from_spec_rad(self, freq, pow_spec):
        return (
            (self.h * freq / self.kB) / 
            np.log((2 * self.h * (freq**3 / self.c**2) / pow_spec) + 1))

    def Tb_from_Trj(self, freq, Trj):
        alpha = (self.h * freq) / self.kB
        return alpha / np.log((2 * alpha / Trj) + 1)

    def inv_var(self, err):
        """
        Inverse variance weights based in input errors

        Args:
        err (float): errors to generate weights
        """
        np.seterr(divide='ignore')
        return 1. / (np.sqrt(np.sum(1. / (np.power(np.array(err), 2.)))))

    def dielectric_loss(self, freq, thick, ind, ltan):
        """
        The dielectric loss of a substrate given the frequency [Hz],
        substrate thickness [m], index of refraction, and loss tangent

        Args:
        freq (float): frequencies [Hz]
        thick (float): substrate thickness [m]
        ind (float): index of refraction
        ltan (float): loss tangent
        """
        freq, thick, ind, ltan = self._check_inputs(
            freq, [thick, ind, ltan])
        return 1. - np.exp(
            (-2. * self.PI * ind * ltan * thick) / (self.lamb(freq)))

    def rj_temp(self, powr, bw, eff=1.0):
        """
        RJ temperature [K_RJ] given power [W], bandwidth [Hz], and efficiency

        Args:
        powr (float): power [W]
        bw (float): bandwidth [Hz]
        eff (float): efficiency
        """
        return powr / (self.kB * bw * eff)

    def n_occ(self, freq, temp):
        """
        Photon occupation number given a frequency [Hz] and
        blackbody temperature [K]

        freq (float): frequency [Hz]
        temp (float): blackbody temperature [K]
        """
        freq, temp = self._check_inputs(freq, [temp])
        fact = (self.h * freq)/(self.kB * temp)
        fact = np.where(fact > 100, 100, fact)
        with np.errstate(divide='raise'):
            return 1. / (np.exp(fact) - 1.)

    def a_omega(self, freq):
        """
        Throughput [m^2] for a diffraction-limited detector
        given the frequency [Hz]

        Args:
        freq (float): frequencies [Hz]
        """
        freq = self._check_inputs(freq)
        return self.lamb(freq)**2

    def bb_spec_rad(self, freq, temp, emis=1.0):
        """
        Blackbody spectral radiance [W/(m^2 sr Hz)] given a frequency [Hz],
        blackbody temperature [K], and blackbody emissivity

        Args:
        freq (float): frequencies [Hz]
        temp (float): blackbody temperature [K]
        emiss (float): blackbody emissivity. Defaults to 1.
        """
        freq, temp, emis = self._check_inputs(freq, [temp, emis])
        return (emis * (2 * self.h * (freq**3) /
                (self.c**2)) * self.n_occ(freq, temp))

    def bb_pow_spec(self, freq, temp, emis=1.0):
        """
        Blackbody power spectrum [W/Hz] on a diffraction-limited polarimeter
        for a frequency [Hz], blackbody temperature [K],
        and blackbody emissivity

        Args:
        freq (float): frequencies [Hz]
        temp (float): blackbody temperature [K]
        emiss (float): blackbody emissivity. Defaults to 1.
        """
        freq, temp, emis = self._check_inputs(freq, [temp, emis])
        return 0.5 * self.a_omega(freq) * self.bb_spec_rad(freq, temp, emis)

    def ani_pow_spec(self, freq, temp, emiss=1.0):
        """
        Derivative of blackbody power spectrum with respect to blackbody
        temperature, dP/dT, on a diffraction-limited detector [W/K] given
        a frequency [Hz], blackbody temperature [K], and blackbody
        emissivity

        Args:
        freq (float): frequency [Hz]
        temp (float): blackbody temperature [K]
        emiss (float): blackbody emissivity, Defaults to 1.
        """
        freq, temp, emiss = self._check_inputs(freq, [temp, emiss])
        return (((self.h**2) / self.kB) * emiss *
                (self.n_occ(freq, temp)**2) * ((freq**2)/(temp**2)) *
                np.exp((self.h * freq)/(self.kB * temp)))

    # ***** Helper Methods *****
    def _check_inputs(self, x, inputs=None):
        ret = []
        if isinstance(x, np.ndarray) or isinstance(x, list):
            x = np.array(x).astype(np.float)
            if inputs is None:
                return x
            ret.append(x)
            for inp in inputs:
                if callable(inp):
                    ret.append(inp(x).astype(np.float))
                elif isinstance(inp, np.ndarray) or isinstance(inp, list):
                    ret.append(np.array(inp).astype(np.float))
                elif isinstance(inp, int) or isinstance(inp, float):
                    ret.append(np.array(
                        [inp for i in x]).astype(np.float))
                else:
                    raise Exception(
                        "Non-numeric value %s passed in Physics" % (str(x)))
        elif isinstance(x, int) or isinstance(x, float):
            if inputs is None:
                return x
            ret.append(float(x))
            for inp in inputs:
                if callable(inp):
                    ret.append(float(inp(x)))
                elif isinstance(inp, int) or isinstance(inp, float):
                    ret.append(float(inp))
                else:
                    ret.append(inp)
        else:
            raise Exception(
                "Non-numeric value %s passed in Physics" % (str(x)))
        return ret
