import sys as sy
import os
import subprocess as sp

# BoloCalc requires Python 3
print("\nChecking python version")
if sy.version_info[0] < 3:
    raise Exception(
        "\nBoloCalc requires Python 3. Please install Python 3 before "
        "proceeding. We recommend using the Anaconda environment, for "
        "which instructions can be found at www.anaconda.com.\n")
print("Python 3 confirmed")

# Install package requirements
req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
os.system("pip3 install -r %s" % (req_file))
print("Finished installing python packages")
