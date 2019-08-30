class Unit:
    """
    Object for handling unit conversions

    Args:
    unit (str): name of the unit

    Attributes:
    name (str): where 'unit' arg is stored
    """
    def __init__(self, unit):
        # Dictionary of SI unit conversions
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
            "MJy": 1.e-20,
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
        """ Convert value from SI unit """
        return val / self._SI

        # Dictionary of units used in BoloCalc,

# BoloCalc units identified by parameter name
std_units = {
    "NA": Unit("NA"),
    "RESOLUTION": Unit("GHz"),  # spec res
    "DUSTTEMPERATURE": Unit("K"),  # dust temp
    "DUSTSPECINDEX": Unit("NA"),  # dust spec index
    "DUSTAMPLITUDE": Unit("MJy"),  # dust amp
    "DUSTSCALEFREQUENCY": Unit("GHz"),  # dust scale freq
    "SYNCHROTRONSPECINDEX": Unit("NA"),  # synch spec index
    "SYNCHROTRONAMPLITUDE": Unit("K"),  # synch amp
    "SYNCSCALEFREQUENCY": Unit("GHz"),  # sync scale freq
    "ELEVATION": Unit("deg"),  # elevation
    "PWV": Unit("mm"),  # pwv
    "OBSERVATIONTIME": Unit("yr"),  # obs time
    "SKYFRACTION": Unit("NA"),  # sky frac
    "OBSERVATIONEFFICIENCY": Unit("NA"),  # obs eff
    "NETMARGIN": Unit("NA"),  # NET margin
    "BORESIGHTELEVATION": Unit("deg"),  # boresight elev
    "OPTICALCOUPLING": Unit("NA"),  # optical coupling
    "FNUMBER": Unit("NA"),  # f-number
    "BATHTEMP": Unit("K"),  # bath temp
    "BANDCENTER": Unit("GHz"),  # band center
    "FRACTIONALBW": Unit("NA"),  # fractional bw
    "PIXELSIZE": Unit("mm"),  # pixel size
    "NUMDETPERWAFER": Unit("NA"),  # num det per waf
    "NUMWAFPEROT": Unit("NA"),  # num waf per OT
    "NUMOT": Unit("NA"),  # num OT
    "WAISTFACTOR": Unit("NA"),  # waist factor
    "DETEFF": Unit("NA"),  # det eff
    "PSAT": Unit("pW"),  # psat
    "PSATFACTOR": Unit("NA"),  # psat factor
    "CARRIERINDEX": Unit("NA"),  # carrier index
    "TC": Unit("K"),  # Tc
    "TCFRACTION": Unit("NA"),  # Tc fraction
    "FLINK": Unit("NA"),  # Flink
    "G": Unit("pW"),  # G
    "YIELD": Unit("NA"),  # yield
    "SQUIDNEI": Unit("pA/rtHz"),  # SQUID NEI
    "BOLORESISTANCE": Unit("Ohm"),  # bolo R
    "READNOISEFACT": Unit("NA"),  # read noise fact
    "TEMPERATURE": Unit("K"),  # temp
    "ABSORPTION": Unit("NA"),  # absorption
    "REFLECTION": Unit("NA"),  # reflection
    "THICKNESS": Unit("mm"),  # thickness
    "INDEX": Unit("NA"),  # index
    "LOSSTANGENT": Unit("e-4"),  # loss tangent
    "CONDUCTIVITY": Unit("e+6"),  # conductivity
    "SURFACEROUGH": Unit("um RMS"),  # surface rough
    "SPILLOVER": Unit("NA"),  # spillover
    "SPILLOVERTEMP": Unit("K"),  # spill temp
    "SCATTERFRAC": Unit("NA"),  # scatter frac
    "SCATTERTEMP": Unit("K"),  # scatter temp
    "POPT": Unit("pW"),  # popt
    "NEP": Unit("aW/rtHz"),  # NEP
    "NET": Unit("uK-rts"),  # NET
    "CORRFACT": Unit("NA"),  # corr fact
    "MAPDEPTH": Unit("uK-amin")}  # map depth
