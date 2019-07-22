# Built-in modules
import numpy as np

# BoloCalc modules
import src.units as un


class Physics:
    def __init__(self):
        # Planck constant [J/s]
        self.h = 6.6261e-34
        # Boltzmann constant [J/K]
        self.kB = 1.3806e-23
        # Speed of light [m/s]
        self.c = 299792458.0
        # Pi
        self.PI = 3.14159265
        # Permability of free space [H/m]
        self.mu0 = 1.256637e-6
        # Permittivity of free space [F/m]
        self.ep0 = 8.854188e-12
        # Impedance of free space [Ohm]
        self.Z0 = np.sqrt(self.mu0/self.ep0)
        # CMB Temperature [K]
        self.Tcmb = 2.725
        # CO Emission lines [Hz]
        self.coJ10 = 115.*un.GHzToHz
        self.coJ21 = 230.*un.GHzToHz
        self.coJ32 = 345.*un.GHzToHz
        self.coJ43 = 460.*un.GHzToHz

    # ***** Public Methods *****
    # Convert from from frequency [Hz] to wavelength [m]
    def lamb(self, freq, index=1.0):
        freq, index = self.__checkInputs(freq, [index])
        return self.c/(freq*index)

    # Convert from phase [rad] to physical thickness [m]
    def phaseToThick(self, freq, phase, index=1.0):
        freq, phase, index = self.__checkInputs(freq, [phase, index])
        return self.lamb(freq, index)*(phase)

    # Convert physical thickness [m] to phase [rad]
    def thickToPhase(self, freq, thick, index=1.0):
        freq, thick, index = self.__checkInputs(freq, [thick, index])
        return (2*np.pi)*(thick/(self.lamb(freq, index)))

    # Angle rotation by a birefringent material [deg]
    def birefringentRot(self, freq, thick, oN, eN):
        freq, thick, oN, eN = self.__checkInputs(freq, [thick, oN, eN])
        return 360.*(eN - oN)*thick/(self.lamb(freq))

    # Stokes vector
    def Stokes(self, polFrac, polAngle):
        polAngle = self.degToRad(polAngle)
        return np.matrix([[1.],
                          [polFrac*np.cos(2.*polAngle)],
                          [polFrac*np.sin(2.*polAngle)],
                          [0]])

    # Convert from central frequncy and fractional bandwidth to band edges
    def bandEdges(self, freqCent, fracBw):
        freqLo = freqCent - (freqCent*fracBw)/2.
        freqHi = freqCent + (freqCent*fracBw)/2.
        return freqLo, freqHi

    # Convert from a central frequency and fractional bandwidth to a band [Hz]
    def band(self, freqCent, fracBw, freqStep=1.e9):
        freqLo, freqHi = self.bandEdges(freqCent, fracBw)
        return np.arange(freqLo, freqHi, freqStep)

    # Spillover efficiency
    def spillEff(self, freq, pixDiameter, Fnumber, waistFactor=3.0):
        freq, pixDiameter, Fnumber, waistFactor = self.__checkInputs(
            freq, [pixDiameter, Fnumber, waistFactor])
        return 1. - np.exp(
            (-np.power(np.pi, 2)/2.) * np.power(
                (pixDiameter / (waistFactor*Fnumber*(self.c/freq))), 2))

    # Egde taper
    def edgeTaper(self, apEff):
        return 10. * np.log10(1. - apEff)

    # Aperture illumination efficiency
    def apertIllum(self, freq, pixDiameter, Fnumber, waistFactor=3.0):
        freq, pixDiameter, Fnumber, waistFactor = self.__checkInputs(
            freq, [pixDiameter, Fnumber, waistFactor])
        lamb = self.lamb(freq)
        w0 = pixDiameter/waistFactor
        thetaS = lamb/(np.pi*w0)
        thetaA = np.arange(0., np.arctan(1./(2.*Fnumber)), 0.01)
        V = np.exp(-np.power(thetaA, 2.)/np.power(thetaS, 2.))
        effNum = np.power(np.trapz(V*np.tan(thetaA/2.), thetaA), 2.)
        effDenom = np.trapz(np.power(V, 2.)*np.sin(thetaA), thetaA)
        effFact = 2.*np.power(np.tan(thetaA/2.), -2.)
        return (effNum/effDenom)*effFact

    # Scattering efficiency off of a rough conductor
    def ruzeEff(self, freq, sigma):
        freq, sigma = self.__checkInputs(freq, [sigma])
        return np.exp(-np.power(4*np.pi*sigma/(self.c/freq), 2.))

    # Ohmic efficiency for reflection off a mirror with finite conductivity
    def ohmicEff(self, freq, sigma):
        freq, sigma = self.__checkInputs(freq, [sigma])
        return 1. - 4.*np.sqrt(np.pi*freq*self.mu0/sigma)/self.Z0

    # Antenna temperature [K] given an intensity [W/m^2] and frequency [Hz]
    def antennaTemp(self, freq, intensity):
        freq, intensity = self.__checkInputs(freq, [intensity])
        return intensity*(self.c**2)/(2*self.kB*(freq**2))

    # Intensity [W/m^2] given an antenna temperatue [K] and a frequency [Hz]
    def intensityFromAntennaTemp(self, freq, fracBw, antennaTemp):
        return 2*(antennaTemp*self.kB*(freq**2)/(self.c**2))*fracBw

    # CMB temperature from antenna temperature
    def antennaToCMBTemp(self, freq, antennaTemp):
        freq, antennaTemp = self.__checkInputs(freq, [antennaTemp])
        x = (self.h*freq)/(self.Tcmb*self.kB)
        thermoFact = np.power((np.exp(x)-1.), 2.)/(np.power(x, 2.)*np.exp(x))
        return antennaTemp*thermoFact

    # Convert from degrees to radians
    def degToRad(self, deg):
        return (deg/360.)*2*self.PI

    # Convert radian to degree
    def radToDeg(self, rad):
        return (rad/(2.*self.PI))*360.

    # Inverse variance weight
    def invVar(self, errArr):
        np.seterr(divide='ignore')
        return 1./(np.sqrt(np.sum(1./(np.power(np.array(errArr), 2.)))))

    # Dielectric loss coefficient with thickness [m] and freq [GHz]
    def dielectricLoss(self, freq, thick, index, lossTan):
        freq, thick, index, lossTan = self.__checkInputs(
            freq, [thick, index, lossTan])
        return 1.0 - np.exp((-2*self.PI*index*lossTan*thick)/(self.lamb(freq)))

    # Integrate dielectric loss accross a frequency band to obtain emissivity
    def dielectricBandAvgLoss(self, freq, thick, index, lossTan):
        freq, thick, index, lossTan = self.__checkInputs(
            freq, [thick, index, lossTan])
        return (np.trapz(dielectricLoss(freq, thick, index, lossTan), freq) /
                float(freq[-1] - freq[0]))

    # Rayleigh-Jeans Temperature [K]
    def rjTemp(self, pow, deltaF, eff=1.0):
        return pow/(kB*deltaF*eff)

    # Photon Mode Occupation Number
    def nOcc(self, freq, temp):
        np.seterr(divide='ignore')
        np.seterr(over='ignore')
        freq, temp = self.__checkInputs(freq, [temp])
        return 1./(np.exp((self.h*freq)/(self.kB*temp)) - 1.)

    # Throughput for a diffraction-limited detector [m^2]
    def AOmega(self, freq):
        freq = self.__checkInputs(freq)
        return (self.c/(freq))**2

    # Blackbody spectral radiance [W/(m^2-Hz)]
    def bbSpecRad(self, freq, temp, emissivity=1.0):
        freq, temp, emissivity = self.__checkInputs(freq, [temp, emissivity])
        return (emissivity * (2 * self.h * (freq**3) /
                (self.c**2)) * self.nOcc(freq, temp))

    # Power spectrum of a blackbody on a diffraction-limited polarimeter [W/Hz]
    def bbPowSpec(self, freq, temp, emissivity=1.0):
        freq, temp, emissivity = self.__checkInputs(freq, [temp, emissivity])
        return 0.5*self.AOmega(freq)*self.bbSpecRad(freq, temp, emissivity)

    # Blackbody power  on a diffraction-limited polarimeter [J]
    def bbPower(self, freq, temp, emissivity=1.0):
        freq, temp, emissivity = self.__checkInputs(freq, [temp, emissivity])
        return np.trapz(self.bbPowSpec(freq, temp, emissivity), freq)

    # Blackbody power equivalent CMB temperature spectrum on a
    # diffraction-limited detector [K/s]
    def bbPowCMBTempSpec(self, freq, temp, emissivity=1.0):
        freq, temp, emissivity, Tcmb = self.__checkInputs(
            freq, [temp, emissivity, self.Tcmb])
        return (self.bbPowSpec(freq, temp, emissivity) /
                (self.aniPowSpec(freq, Tcmb, emissivity)))

    # Blackbody power equivalent CMB temperature on a
    # diffraction-limited detector [K/s]
    def bbPowCMBTemp(self, freq, temp, emissivity=1.0):
        freq, temp, emissivity = self.__checkInputs(freq, [temp, emissivity])
        return np.trapz(bbPowCMBTempSpec(freq, temp, emissivity), freq)

    # Derivative of power spectrum with respect to temperature dP/dT on a
    # diffraction-limited detector [W/K]
    def aniPowSpec(self, freq, temp, emissivity=1.):
        freq, temp, emissivity = self.__checkInputs(freq, [temp, emissivity])
        return (((self.h**2)/self.kB) * emissivity *
                (self.nOcc(freq, temp)**2) * ((freq**2)/(temp**2)) *
                np.exp((self.h*freq)/(self.kB*temp)))

    # Derivative of power with respect to temperature dP/dT on a
    # diffraction-limited detector [J/K]
    def aniPower(self, freq, temp, emissivity=1.0):
        freq, temp, emissivity = self.__checkInputs(freq, [temp, emissivity])
        return np.trapz(self.aniPowSpec(freq, temp, emissivity), freq)

    # ***** Helper Methods *****
    # Check that inputs are valid
    def __checkInputs(self, x, inputs=None):
        retArr = []
        if isinstance(x, np.ndarray) or isinstance(x, list):
            x = np.array(x).astype(np.float)
            if inputs is None:
                return x
            retArr.append(x)
            for input in inputs:
                if callable(input):
                    retArr.append(input(x).astype(np.float))
                elif isinstance(input, np.ndarray) or isinstance(input, list):
                    retArr.append(np.array(input).astype(np.float))
                elif isinstance(input, int) or isinstance(input, float):
                    retArr.append(np.array(
                        [input for i in x]).astype(np.float))
                else:
                    raise Exception(
                        "Non-numeric value %s passed in Physics" % (str(x)))
        elif isinstance(x, int) or isinstance(x, float):
            if inputs is None:
                return x
            retArr.append(float(x))
            for input in inputs:
                if callable(input):
                    retArr.append(float(input(x)))
                elif isinstance(input, int) or isinstance(input, float):
                    retArr.append(float(input))
                else:
                    retArr.append(input)
        else:
            raise Exception(
                "Non-numeric value %s passed in Physics" % (str(x)))
        return retArr
