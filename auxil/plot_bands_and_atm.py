import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import sys as sy
import h5py as hp

# This script needs to be updated to handle a distribution
# for any input parameter

# Args: 220 20% band, 270 20% band, 220 40% band, etc.

fnames = sy.argv[1:]
nbands = 2
scenarios = ["20%", "40%", "60%", "80%"]
colors = ['r', 'b', 'g', 'c']

sns.set(style="whitegrid", font_scale=3)
plt.figure(0, figsize=(15, 12))

# Plot the bands
ind = 0
for i, scenario in enumerate(scenarios):
    freq, tran = np.loadtxt(fnames[ind], unpack=True)
    plt.plot(freq, tran, linewidth=3, color=colors[i],
             linestyle="--")
    # Phantom line
    plt.plot(freq, [2 for f in freq], linewidth=3, color=colors[i],
             label=("Det Eff = ", scenario), linestyle="-")
    ind += 1
    freq, tran = np.loadtxt(fnames[ind], unpack=True)
    plt.plot(freq, tran, linewidth=3, color=colors[i],
             linestyle=":")
    ind += 1

# Plot the atmosphere: 1 mm PWV, 45 deg elevation
with hp.File("../src/atmFiles/atm.hdf5", "r") as hf:
        freq, depth, temp, tran = hf['Atacama']['1000,45']
plt.plot(freq, tran, linewidth=3.5, color='k', label="1 mm PWV, 45 deg",
         linestyle='-')
plt.xlabel("Frequency [GHz]")
plt.xlim([185, 320])
plt.ylim([0, 1])
plt.ylabel("Transmission")
plt.legend(loc='best')
plt.savefig("bands_and_atm.jpg")
