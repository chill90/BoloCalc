This directory contains tools for generating BoloCalc atmosphere profile files.

The atmosphere files for BoloCalc are stored in HDF5 files titled "atm_[yyyymmdd].hdf5,"
where "[yyyyddmm]" is a date. For example, the file name for December 17, 2020 would be
"atm_20201217.hdf5". This file is created using the Python executable
"create_atm_hdf5.py" in this directory. However, in order to generate an HDF5 file, we
first need to calculate the atmosphere profiles themselves.

BoloCalc uses atmospheric brightness and absorptivity vs. frequency as generated using
the "am atmospheric model" software. Follow these instructions to generate a (fresh)
HDF5 atmosphere file for BoloCalc:

(1) Download "am" from here: https://zenodo.org/record/3406483#.X9v2GulKh0w
(2) Install "am" into this directory. For example, for am version 9.0, you will
    have, after installation, a directory called "BoloCalc/auxil/AM/am-9.0/" in
    which all of am's files are, including its executale.
(3) You are now ready to generate atmosphere profiles. You can do this for any
    of three sites (as of Dec 2020) for BoloCalc: the Atacama's Cerro Toco site,
    the South Pole site, and the stratosphere for balloon experiments. The scripts
    for each of these sites is located in the "Atacama/", "Pole/", and "McMurdo/"
    directories, respectively.
(4) For example, to generate atmospheric profiles for the Atacama, do the following:
      $ cd Atacama
      $ python calcAtacamaAtmosphere.py
    This script will try to use as much of your computer's resources as it can using
    Python's "multiprocess" module. We do this because generating all of BoloCalc's
    needed atmospheric data (~1.2 GB) can many hours. On Berkeley's analysis machine,
    which has ~40 cores, it takes 1~2 hours.
(5) The atmosphere profiles for the above script will be populated into "AtacamaData/"
    as ".txt" files. Each text file's colums are, from left to right, frequency "f" [GHz],
    optical depth "tau", brightness temperaure "Tb" [K], and transmissivity "tx",
    and each column is calculated every 0.1 GHz between 1 and 600 GHz.
      IMPORTANT: The ".txt" files in "AtacamaData/" (for example) are only recalculated
      if the corresponding file does not exist. In other words, if the script
      "calcAtacamaAtmosphere.py" sees the that the file it wants to calculate already
      exists in "AtacamaData/", then it will not overwrite. Therefore, if you want
      to create a fresh batch of profiles, be sure to run
        $ rm AtacamaData/*.txt
      first.
(6) After all atmospheric profile data exists in "Atacama/AtacamaData",
    "Pole/PoleData/", and "McMurdo/McMurdoData", then run the following to generate
    the HDF5 file for BoloCalc:
      $ python create_atm_hdf5.py
    which will create the file "atm.hdf5" in the current directory. NOTE that if an
    existing "atm.hdf5" already exists at this location, it will be overwritten! So,
    perhaps save any old "atm.hdf5" files with a different name before doing this step.

Congratulations! You now have an "atm.hdf5" file that can be used by BoloCalc.

At this point, you're hacking BoloCalc for yourself, you can now replace the file
"BoloCalc/src/atm_[yyyymmdd].hdf5" file with your new one (make sure to duplicate
the name exactly!) and run "calcBolos.py", as normal, with your new data. However,
if you are an administrator that would like to "push" an atmosphere update for
all BoloCalc users, proceed with the following steps:
(1) Rename your new "atm.hdf5" file to "atm_[yyyymmdd].hdf5", where
    "[yyyymmdd]" is today's date. For example, if you were updating BoloCalc's
    atmosphere files on Dec 17, 2020, you would name your file "atm_20201217.hdf5".
(2) Send the atmosphere file to Charles Hill via "charles.a.hill01@gmail.com", who
    will make it downloadable. Please include a detailed description of what's
    exactly been changed.
      NOTE: as of Dec 2020, we are trying to find somebody other than Charles
      to manage this task, and we will update this README appropriately when so.
