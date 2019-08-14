import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import sys as sy

# This script needs to be updated to handle a distribution
# for any input parameter

fname = sy.argv[1]
vals, probs = np.loadtxt(fname, unpack=True)

sns.set(style="whitegrid", font_scale=3)

plt.figure(0, figsize=(15, 12))
plt.plot(vals, probs, linewidth=3.5, color='r')
plt.fill_between(vals, probs, color='r', alpha=0.5)
plt.xlabel("PWV [mm]")
plt.ylabel("Probability Density")
plt.savefig("pwv_dist.jpg")
