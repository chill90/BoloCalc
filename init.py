import shutil as su
import wget as wg
import zipfile as zf
import sys as sy
import os

# Install python packages
curr_dir = os.path.dirname(__file__)
install_file = os.path.join(
    curr_dir, 'auxil', 'install_packages.py')
if sy.version_info[0] == 3:
    if sy.version_info[1] >= 7:
        os.system("python %s" % (install_file))
    else:
        sy.stdout.write("\n***** Python 3.7 or higher required for "
                        "BoloCalc v0.10 (Sep 2019) and beyond *****\n\n")
        sy.exit()
else:
    sy.stdout.write("\n***** Python 2 is no longer supported for "
                    "BoloCalc v0.10 (Sep 2019) and beyond *****\n\n")
    sy.exit()

# Require wget
#if su.which('wget') is None:
#    sy.stdout.write(
#        "\nERROR: wget needs to be installed to download auxiliary files\n\n")
#    sy.exit()

# Download example experiment
example_dir = os.path.join(
    curr_dir, "Experiments", "ExampleExperiment")
if os.path.exists(example_dir):
    sy.stdout.write(
        ("\nNOTE: Experiments" + os.sep + "ExampleExperiment" +
        os.sep + " already exists. If you want a fresh copy, "
        "please use Experiments" + os.sep + "importExperiments.py.\n\n"))
else:
    ex_zip = os.path.join(curr_dir, "ex.zip")
    if os.path.exists(ex_zip):
        os.remove(ex_zip)
    #os.system("wget http://pbfs.physics.berkeley.edu/BoloCalc/EX/ex.zip")
    wg.download("http://pbfs.physics.berkeley.edu/BoloCalc/EX/ex.zip")
    ex_dir = ("Experiments" + os.sep)
    with zf.ZipFile(ex_zip, "r") as ex_file:
        ex_file.extractall(ex_dir)
    #os.system(("unzip ex.zip -d %s" % (zip_dir)))
    os.remove(ex_zip)

# Download atmosphere files
update_atm_file = os.path.join(
    os.path.dirname(__file__), "update_atm.py")
os.system("python %s" % (update_atm_file))
atm_files_dir = os.path.join(
    os.path.dirname(__file__), "src", "atmFiles")
if os.path.exists(atm_files_dir):
    sy.stdout.write(
        "\nNOTE: src" + os.sep + "atmFiles" + os.sep, " is no longer used by "
        "BoloCalc. We suggest removing it.\n\n")
