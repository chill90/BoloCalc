# Built-in modules
import sys as sy
import itertools as it


class Compatible:
    def __init__(self):
        # Python version
        self.major = sy.version_info.major
        self.minor = sy.version_info.minor
        self.micro = sy.version_info.micro
        # Boolean for Python 2
        if self.major == 2:
            self.PY2 = True
        else:
            self.PY2 = False

    # Make the zip function a generator for both python versions
    def zip(self, *args):
        if self.major == 2:
            return it.izip(*args)
        elif self.major == 3:
            return zip(*args)
        else:
            raise Exception('Invalid Python version = %d' % (self.major))
