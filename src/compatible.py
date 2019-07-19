# Built-in modules
import sys
import itertools as it


class Compatible:
    def __init__(self):
        # Python version
        self.major = sys.version_info.major
        self.minor = sys.version_info.minor
        self.micro = sys.version_info.micro

    # Make the zip function a generator for both python versions
    def zip(self, *args):
        if self.major == 2:
            return it.izip(*args)
        elif self.major == 3:
            return zip(*args)
        else:
            raise Exception('Invalid Python version = %d' % (self.major))
