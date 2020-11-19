import shutil as su
import sys as sy
import os

# Require wget
if su.which('wget') is None:
    sy.stdout.write(
        "\nERROR: wget needs to be installed to download atmosphere files\n")
    sy.exit()

# Download atmosphere files
fname = "atm_20200916.hdf5"
atm_file = os.path.join(
    os.path.dirname(__file__), fname)
new_atm_file = os.path.join(
    os.path.dirname(__file__), "src", fname)
os.system("wget http://pbfs.physics.berkeley.edu/BoloCalc/ATM/%s" % (fname))
if os.path.exists(atm_file):
    sy.stdout.write(
        "\nSuccessfully downloaded atmosphere file %s." % (fname))
    sy.stdout.write(
        ("\nADVICE: delete any old atm files (~1 GB each) from BoloCalc" + 
        os.sep + "src" + os.sep + "\n\n"))
    os.rename(atm_file, new_atm_file)
else:
    sy.stdout.write(
        "\nERROR: problem downloading atmosphere file %s\n\n" % (fname))