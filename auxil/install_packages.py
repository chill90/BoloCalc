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

# Check if using anaconda
#print("Checking python distribution")
#output = sp.check_output("which python", shell=True)

# Install package requirements
req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
#if 'conda' in str(output):
#    print("Using Anaconda")
    #os.system("conda install --file %s" % (req_file))
os.system("pip3 install -r %s" % (req_file))
#else:
#    print("Not using Anaconda")
#    os.system("pip install -r %s" % (req_file))
print("Finished installing python packages")
