import shutil as su
import urllib.request as ul
import sys as sy
import time as tm
import os

# Progress monitor
def reporthook(count, block_size, total_size):
    # Percent finished
    percent = int(count * block_size * 100 / total_size)
    # Download speed
    global start_time
    if count == 0:
        start_time = tm.time()
        return
    duration = tm.time() - start_time
    progress_size = int(count * block_size)
    if duration == 0:
        msg = (
            "\rDownloading atmosphere data: %d%%, %d MB" %
            (percent, progress_size / (1024 * 1024)))
    else:
        speed = int(progress_size / (1024 * duration))
        msg = (
            "\rDownloading atmosphere data: %d%%, %d MB, %d kB/s" %
            (percent, progress_size / (1024 * 1024), speed))
    sy.stdout.write(msg)
    sy.stdout.flush()

# Download atmosphere files
fname = "atm_20201217.hdf5"
atm_file = os.path.join(
    os.path.dirname(__file__), fname)
new_atm_file = os.path.join(
    os.path.dirname(__file__), "src", fname)
url_name = ("http://pbfs.physics.berkeley.edu/BoloCalc/ATM/%s" % (fname))
ul.urlretrieve(url_name, atm_file, reporthook)
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
