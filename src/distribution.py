# BoloCalc modules
import src.loader as ld


class Distribution:
    """
    Distribution object holds probability distribution functions (PDFs)
    for instrument parameters

    Args:
    finput (str): file name for the input PDF

    Attributes:
    prob (array): probabilities
    val (array): values
    """
    def __init__(self, finput):
        self._ld = ld.Loader()
        self.prob, self.val = self._ld.pdf(finput)
