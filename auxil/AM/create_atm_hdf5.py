import glob as gb
import pickle as pk
import os
import numpy as np
import h5py as hp

# Create the hdf5 file
output_file = hp.File("atm.hdf5", "w")

# Store atmosphere data
sites = ["Atacama", "Pole", "McMurdo"]
groups = []
for site in sites:
    print(site)
    group = output_file.create_group(site)
    files = gb.glob(os.path.realpath("./%s/%sData/*.txt" % (site, site)))
    for f in files:
        print(f)
        elev, pwv = f.split('/')[-1].strip('.txt').split('_')[1:]
        elev = int(elev.strip('deg'))
        pwv = int(pwv.strip('um'))
        key = "%d,%d" % (pwv, elev)
        freq, depth, temp, tran = np.loadtxt(f, unpack=True, dtype=np.float)
        value = (freq, depth, temp, tran)
        group.create_dataset(key, data=value)
output_file.close()
