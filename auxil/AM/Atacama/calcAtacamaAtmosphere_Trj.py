#!/usr/local/bin/python

import numpy as np
import os
import glob as gb
from multiprocessing import Pool

#Directory to save the files
data_dir = os.path.join('.', 'AtacamaData_Trj')
am_installs = np.array(gb.glob(
    '..' + os.sep + 'am-*' + os.sep))
am_versions = np.array([
    float(am.split('-')[-1].split(os.sep)[0])
    for am in am_installs])
sorted_args = np.argsort(am_versions)
am_exec = os.path.join(
    am_installs[sorted_args][-1], 'am')

# Create data directory if needed
if not os.path.exists(data_dir):
    os.mkdir(data_dir)

#Unit conversions
mmToUm = lambda mm: mm*1.e3  #mm to um
zenith = lambda el: 90. - el #elevation angle to zenith angle
defaultScale = 0.931

#PWV values [mm]
pwvLo = 0.0
pwvHi = 4.0
pwvSp = 0.1
#PWV array [um]
pwvArr = np.arange(pwvLo, pwvHi, pwvSp)

#Elevation values as measured from the horizon [deg]
elLo = 50.
elHi = 60.
elSp = 10.
#Angle array [deg]
angArr = np.arange(elLo, elHi, elSp)

#Frequency range [GHz]
fLo = 10.
fHi = 600.

#Temperature of the ground [K]
#Tground = 273.

#Calculate for range of zenith angles and PWV values
def doIt(arg):
    ang = arg[0]
    pwv = arg[1]
    fName = os.path.join(
        data_dir, "atm_%02ddeg_%04dum.txt" % (ang, mmToUm(pwv)))
    if not os.path.isfile(fName) or not os.stat(fName).st_size:
        arg = "%s ACT_annual_median_MERRA2_2007-2016_Trj.amc %d %d %d %.2f > %s" % (am_exec, fLo, fHi, zenith(ang), pwv/defaultScale, fName)
        os.system(arg)

# ***** MAIN *****
args = []
for pwv in pwvArr:
    for ang in angArr:
        args.append([ang, pwv])

#Multiprocessing thread
p = Pool()
p.map(doIt,args)
