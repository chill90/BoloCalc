class StandardParam:
    """
    StandardParam object is used to define the parameter characteristics
    of standard BoloCalc input and output parameters

    Args:
    name (str): parameter name
    unit (src.Unit): parameter unit. Defaults to src.Unit('NA')
    inp_min (float): minimum allowed value. Defaults to None
    inp_max (float): maximum allowe value. Defaults to None
    inp_type (type): cast parameter data type. Defaults to numpy.float
    """
    def __init__(self, name, unit, inp_min, inp_max, inp_type):
        # Store passed values
        self.name = name
        self.unit = unit
        self.min = inp_min
        self.max = inp_max
        self.type = inp_type

        # Store derived parameters
        self.caps_name = self.name.replace(" ", "").strip().upper()
