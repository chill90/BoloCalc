# BoloCalc standard units and parameter values stored in 
# convenient dictionaries for use throughout the source code

class StandardParam:
    """
    StandardParam object is used to define the parameter characteristics
    of standard BoloCalc input and output parameters
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
