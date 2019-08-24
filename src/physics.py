# Built-in modules
import numpy as np

# BoloCalc modules
import src.unit as un


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
        self.co = {"J10": 115.e9,
                   "J21": 230.e9,
                   "J32": 345.e9,
                   "J43": 460.e9}

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

    def phase_to_thick(self, freq, phase, ind=1.0):
        """
        Convert from wave phase [rad] to thickness [m]

        Args:
        freq (float): frequencies [Hz]
        phase (float): wave phase
        ind (float): index of refraction
        """
        freq, phase, ind = self._check_inputs(freq, [phase, ind])
        return self.lamb(freq, ind) * phase

    def thick_to_phase(self, freq, thick, ind=1.0):
        """
        Convert thickness [m] to phase [rad]

        Args:
        freq (float): frequencies [Hz]
        thick (float): thickness [m]
        ind (float): index of refraction
        """
        freq, thick, index = self._check_inputs(freq, [thick, ind])
        return 2 * np.pi * (thick / self.lamb(freq, ind))

    def birefringent_rot(self, freq, thick, n_o, n_e):
        """
        Angle rotation by a birefringent material [deg]

        Args:
        freq (float): frequencies [Hz]
        thick (float): thickness [m]
        n_o (float): ordinary index of refraction
        n_e (float): extraordinary index of refraction
        """
        freq, thick, n_o, n_e = self._check_inputs(freq, [thick, n_o, n_e])
        return 360. * (n_e - n_o) * thick / (self.lamb(freq))

    def stokes(self, pol_frac, pol_ang):
        """
        Stokes vector given an input polarization fraction and angle [deg]

        Args:
        pol_frac (float): polarization fraction
        pol_ang (float): polarization angle [deg]
        """
        pol_ang = self.deg_to_rad(pol_ang)
        return np.matrix([[1.],
                          [pol_frac * np.cos(2. * pol_ang)],
                          [pol_frac * np.sin(2. * pol_ang)],
                          [0]])

    def band_edges(self, fcent, fbw):
        """
        Band edges given a band center and percent bandwidth

        Args:
        fcent (float): band center [Hz]
        fbw (float): percent bandwidth
        """
        flo = fcent - (fcent * fbw) / 2.
        fhi = fcent + (fcent * fbw) / 2.
        return flo, fhi

    def band(self, fcent, fbw, fstep=1.e9):
        """
        Band frequencies given a band center, percent bandwidth,
        and frequency step

        Args:
        fcent (float): band center [Hz]
        fbw (float): percent bandwidth
        fstep (float): frequency step [Hz]. Defaults to 1e9 Hz
        """
        flo, fhi = self.band_edges(fcent, fbw)
        return np.arange(flo, fhi, fstep)

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

    def brighntess_temp(self, freq, intensity):
        """
        Brightness temperature [K_RJ] given a frequency [Hz]
        and intensity [W/m^2]

        Args:
        freq (float): frequencies [Hz]
        intensity (float): intensity [W/m^2]
        """
        freq, intensity = self._check_inputs(freq, [intensity])
        return intensity * (self.c**2) / (2 * self.kB * (freq**2))

    def brightness_spec_rad(self, freq, bright_temp):
        """
        Spectral radiance [W/(m^2 sr Hz)] given a frequency [Hz] and
        brightness temperature [K_RJ]

        Args:
        freq (float): frequencies [Hz]
        intensity (float): brightness temp [K_RJ]
        """
        freq, intensity = self._check_inputs(freq, [bright_temp])
        return bright_temp * 2 * self.kB * (freq / self.c)**2

    def intensity_from_brightness_temp(self, freq, bw, bright_temp):
        """
        Intensity [W/m^2] given an atenna temperature [K_RJ], frequency [Hz],
        and bandwidth [Hz]

        Args:
        freq (float): frequencies [Hz]
        bw (float): bandwidth [Hz]
        ant_temp (float): antenna temperature [K_RJ]
        """
        return 2 * (bright_temp * self.kB * (freq**2) / (self.c**2)) * bw

    def Trj_over_Tb(self, freq, thermo_temp):
        """
        CMB temperature [K_CMB] given an antenna temperature [K_RJ]
        and frequency [Hz]

        Args:
        freq (float): frequencies [Hz]
        ant_temp (float): antenna temperature [K_RJ]
        """
        freq, thermo_temp = self._check_inputs(freq, [thermo_temp])
        x = (self.h * freq)/(thermo_temp * self.kB)
        thermo_fact = np.power(
            (np.exp(x) - 1.), 2.) / (np.power(x, 2.) * np.exp(x))
        return 1. / thermo_fact

    def deg_to_rad(self, deg):
        """
        Convert degrees to radians

        Args:
        deg (float): degree [deg]
        """
        return (deg / 360.) * 2 * self.PI

    def rad_to_deg(self, rad):
        """
        Convert radians to degrees

        Args:
        rad (float): radians [rad]
        """
        return (rad / (2. * self.PI)) * 360.

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

    def dielectric_band_avg_loss(self, freq, thick, ind, ltan):
        """
        The dielectric integrated loss of a substrate given the frequency [Hz],
        substrate thickness [m], index of refraction, and loss tangent

        Args:
        freq (float): frequencies [Hz]
        thick (float): substrate thickness [m]
        ind (float): index of refraction
        ltan (float): loss tangent
        """
        freq, thick, ind, ltan = self._check_inputs(
            freq, [thick, ind, ltan])
        return (np.trapz(dielectricLoss(freq, thick, ind, ltan), freq) /
                float(freq[-1] - freq[0]))

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
        temp = np.where(temp <= 0, 1.e-3, temp)  # 1 mK is minimum allowed temp
        with np.errstate(divide='raise'):
            try:
                return 1. / (np.exp((self.h * freq)/(self.kB * temp)) - 1.)
            except:
                print("problem dividing!")
                print(temp[0])
                print(freq)
                raise Exception()

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

    def bb_pow_spec(self, freq, temp, emiss=1.0):
        """
        Blackbody power spectrum [W/Hz] on a diffraction-limited polarimeter
        for a frequency [Hz], blackbody temperature [K],
        and blackbody emissivity

        Args:
        freq (float): frequencies [Hz]
        temp (float): blackbody temperature [K]
        emiss (float): blackbody emissivity. Defaults to 1.
        """
        freq, temp, emiss = self._check_inputs(freq, [temp, emiss])
        return 0.5 * self.a_omega(freq) * self.bb_spec_rad(freq, temp, emiss)

    def bb_power(self, freq, temp, emiss=1.0):
        """
        Blackbody power [J] on a diffraction-limited polarimeter for a
        frequency [Hz], blackbody temperature [K], and a blackbody
        emissivity

        Args:
        freq (float): frequency [Hz]
        temp (float): blackbody temperature [K]
        emiss (float): blackbody emissivity. Defaults to 1.
        """
        freq, temp, emiss = self._check_inputs(freq, [temp, emiss])
        return np.trapz(self.bb_pow_spec(freq, temp, emiss), freq)

    def bb_pow_cmb_temp_spec(self, freq, temp, emiss=1.0):
        """
        Blackbody equivalent CMB temperature spectrum [K_CMB/Hz]
        for a frequency [Hz], blackbody temperature [K], and
        blackbody emissivity

        Args:
        freq (float): frequency [Hz]
        temp (float): blackbody temperature [K]
        emiss (float): blackbody emissivity. Defaults to 1.
        """
        freq, temp, emiss, Tcmb = self._check_inputs(
            freq, [temp, emiss, self.Tcmb])
        return (self.bb_pow_spec(freq, temp, emiss) /
                (self.ani_pow_spec(freq, Tcmb, emiss)))

    def bb_pow_cmb_temp(self, freq, temp, emiss=1.0):
        """
        Blackbody equivalent CMB temperature [K_CMB] on a diffraction-limited
        detector for a frequency [Hz], blackbody temperature [K],
        and blackbody emssivity

        Args:
        freq (float): frequency [Hz]
        temp (float): blackbody temperature [K]
        emiss (float): blackbody emissivity. Defaults to 1.
        """
        freq, temp, emiss = self._check_inputs(freq, [temp, emiss])
        return np.trapz(self.bb_pow_cmb_temp_spec(freq, temp, emiss), freq)

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

    def ani_power(self, freq, temp, emiss=1.0):
        """
        Derivative of blackbody power with respect to blackbody
        temperature, dP/dT, on a diffraction-limited detector [W/K] given
        a frequency [Hz], blackbody temperature [K], and blackbody
        emissivity

        Args:
        freq (float): frequency [Hz]
        temp (float): blackbody temperature [K]
        emiss (float): blackbody emissivity. Defaults to 1.
        """
        freq, temp, emiss = self._check_inputs(freq, [temp, emiss])
        return np.trapz(self.aniPowSpec(freq, temp, emiss), freq)

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
