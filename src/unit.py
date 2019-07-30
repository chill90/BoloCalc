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
            "uK^2": 1.e-12,
            "yr": (365.25*24.*60.*60),
            "Hz": 1.,
            "m": 1.,
            "W/rtHz": 1.,
            "A/rtHz": 1.,
            "W": 1.,
            "K": 1.,
            "K^2": 1.,
            "s": 1.,
            "NA": 1.}
        # Check that passed unit is available
        if isinstance(unit, str):
            if unit not in self._to_SI_dict.keys():
                raise Exception("Passed unit '%s' not understood by \
                    Units object" % (unit))
            else:
                self._name = unit
                self._SI = self._to_SI_dict[self._name]
        elif isinstance(unit, float):
            self._name = "NA"
            self._SI = unit

    def to_SI(self, val):
        """Convert value to SI unit """
        return val * self._SI

    def from_SI(self, val):
        return val / self._SI