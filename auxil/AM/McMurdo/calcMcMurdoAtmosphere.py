#!/usr/local/bin/python

import numpy as np
import os
import glob as gb
from multiprocessing import Pool

#Directory to save the files
data_dir = os.path.join('.', 'McMurdoData')
am_installs = np.array(gb.glob(
    '..' + os.sep + 'am-*' + os.sep))
am_versions = np.array([
    float(am.split('-')[-1].split(os.sep)[0])
    for am in am_installs])
sorted_args = np.argsort(am_versions)
am_exec = os.path.join(
    am_installs[sorted_args][-1], 'am')

if not os.path.exists(data_dir):
    os.mkdir(data_dir)

#Unit conversions
zenith = lambda el: 90. - el #elevation angle to zenith angle

#Elevation values as measured from the horizon [deg]
elLo = 1.
elHi = 91.
elSp = 1.0
#Angle array [deg]
angArr = np.arange(elLo, elHi, elSp)

#Frequency range [GHz]
fLo = 1.
fHi = 1000.

#Frequency step [MHz]
df = 200.0

#Calculate for range of zenith angles and PWV values
def doIt(ang):
    fName = os.path.join(
        data_dir, "atm_%02ddeg_%04dum.txt" % (ang, 0))
    if not os.path.isfile(fName) or not os.stat(fName).st_size:
        arg = "%s McMurdo_balloon_Dec.amc %d GHz %d GHz %.1f MHz %d deg > %s" % (am_exec, fLo, fHi, df, zenith(ang), fName)
        os.system(arg)

# ***** MAIN *****

#Multiprocessing thread
p = Pool()
p.map(doIt,angArr)
