

class Unit:
    """
    Object for handling unit conversions

    Args:
    unit (str): name of the unit

    Attributes:
    name (str): where 'unit' arg is stored
    """
    def __init__(self, unit):
        self._to_SI_dict = {
            "GHz": 1.e+09,
            "mm": 1.e-03,
            "aW/rtHz": 1.e-18,
            "pA/rtHz": 1.e-12,
            "pW": 1.e-12,
            "um": 1.e-06,
            "pct": 1.e-02,
            "uK": 1.e-06,
            "uK-rts": 1.e-06,
            "uK-amin": 1.e-06,
            "uK^2": 1.e-12,
            "yr": (365.25*24.*60.*60),
            "e-4": 1.e-04,
            "e+6": 1.e+06,
            "um RMS": 1.e-06,
            "Ohm": 1.,
            "W/Hz": 1.,
            "Hz": 1.,
            "m": 1.,
            "W/rtHz": 1.,
            "A/rtHz": 1.,
            "W": 1.,
            "K": 1.,
            "K^2": 1.,
            "s": 1.,
            "deg": 1,
            "NA": 1.}
        # Check that passed unit is available
        if isinstance(unit, str):
            if unit not in self._to_SI_dict.keys():
                raise Exception("Passed unit '%s' not understood by \
                    Unit object" % (unit))
            else:
                self.name = unit
                self._SI = self._to_SI_dict[self.name]
        elif isinstance(unit, float):
            self.name = "NA"
            self._SI = unit

    def to_SI(self, val):
        """Convert value to SI unit """
        return val * self._SI

    def from_SI(self, val):
        return val / self._SI

        # Dictionary of units used in BoloCalc,
# identified by parameter name
std_units = {
    "Resolution": Unit("GHz"),
    "Dust Temperature": Unit("K"),
    "Dust Spec Index": Unit("NA"),
    "Dust Amplitude": Unit("NA"),
    "Dust Scale Frequency": Unit("GHz"),
    "Synchrotron Spec Index": Unit("NA"),
    "Synchrotron Amplitude": Unit("W/Hz"),
    "Elevation": Unit("deg"),
    "PWV": Unit("mm"),
    "Observation Time": Unit("yr"),
    "Sky Fraction": Unit("NA"),
    "Observation Efficiency": Unit("NA"),
    "NET Margin": Unit("NA"),
    "Boresight Elevation": Unit("deg"),
    "Optical Coupling": Unit("NA"),
    "F Number": Unit("NA"),
    "Bath Temp": Unit("K"),
    "Band Center": Unit("GHz"),
    "Fractional BW": Unit("NA"),
    "Pixel Size": Unit("mm"),
    "Num Det per Wafer": Unit("NA"),
    "Num Waf per OT": Unit("NA"),
    "Num OT": Unit("NA"),
    "Waist Factor": Unit("NA"),
    "Det Eff": Unit("NA"),
    "Psat": Unit("pW"),
    "Psat Factor": Unit("NA"),
    "Carrier Index": Unit("NA"),
    "Tc": Unit("K"),
    "Tc Fraction": Unit("NA"),
    "Flink": Unit("NA"),
    "G": Unit("pW"),
    "Yield": Unit("NA"),
    "SQUID NEI": Unit("pA/rtHz"),
    "Bolo Resistance": Unit("Ohm"),
    "Read Noise Frac": Unit("NA"),
    "Temperature": Unit("K"),
    "Absorption": Unit("NA"),
    "Reflection": Unit("NA"),
    "Thickness": Unit("mm"),
    "Index": Unit("NA"),
    "Loss Tangent": Unit("e-4"),
    "Conductivity": Unit("e+6"),
    "Surface Rough": Unit("um RMS"),
    "Spillover": Unit("NA"),
    "Spillover Temp": Unit("K"),
    "Scatter Frac": Unit("NA"),
    "Scatter Temp": Unit("K"),
    "Popt": Unit("pW"),
    "NEP": Unit("aW/rtHz"),
    "NET": Unit("uK-rts"),
    "Corr Fact": Unit("NA"),
    "Map Depth": Unit("uK-amin")}
