# Take in multiple output.txt files and overplot the popt histograms
# for multiple instrument scenarios
# This script needs to be updated later to be more generalized to any 
# input parameter

import sys as sy
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
sns.set(style="whitegrid", font_scale=3)

fnames = sy.argv[1:]
scenarios = ["20%", "40%", "60%", "80%"]
colors = ['r', 'b', 'g', 'c', 'm']

figsize = (15, 12)
lw = 3
#hist_bins = np.linspace(0, 17.5, 36)
#hist_bins = np.linspace(0, 0.24, 11)
#xlim = [0, 18]
nfig = 0
# Loop over and overplot scenarios
for i, fname in enumerate(fnames):
    data = np.loadtxt(fname, unpack=True, dtype=str, skiprows=1)
    #ch1, ch2 = np.take(data, (1, 12), axis=0).astype(float)  # Popt
    ch1, ch2 = np.take(data, (0, 11), axis=0).astype(float)  # eff
    #plt.figure(nfig, figsize)
    plt.figure(0, figsize)
    hist_bins = np.linspace(0, 0.24, 130)
    sns.distplot(ch1, bins=hist_bins, kde=False, color=colors[i],
                 label=("%s" % (scenarios[i])), hist_kws={'alpha': 0.5})
    #sns.distplot(ch1, kde=False, color=colors[i],
    #             label=("%s" % (scenarios[i])), hist_kws={'alpha': 0.5})
    med_line = np.median(ch1)
    one_sigma_lines = np.percentile(ch1, (15.9, 84.1))
    two_sigma_lines = np.percentile(ch1, (2.3, 97.7))
    print("median: ", med_line)
    print("85%: ", one_sigma_lines[1])
    print("98%: ", two_sigma_lines[1])
    #plt.axvline(med_line, linewidth=lw, color=colors[i], linestyle='-')
    #for j in range(2):
    #    plt.axvline(one_sigma_lines[j], linewidth=lw,
    #                color=colors[i], linestyle='--')
    #    plt.axvline(two_sigma_lines[j], linewidth=lw,
    #                color=colors[i], linestyle=':')
    #plt.title("220 GHz Band")
    #plt.xlabel("Optical Power [pW]")
    #plt.xlabel("Optical Efficiency")
    #plt.ylabel("Occurances")
    #plt.xlim(xlim)
    #plt.legend(loc='best', title='Det Eff')
    #plt.savefig("220GHz_%spct_popt_dist.jpg" % (scenarios[i].strip("%")))
    #plt.savefig("220GHz_%spct_eff_dist.jpg" % (scenarios[i].strip("%")))
    #nfig += 1

    #plt.figure(nfig, figsize)
    plt.figure(1, figsize)
    hist_bins = np.linspace(0, 0.128, 130)
    sns.distplot(ch2, bins=hist_bins, kde=False, color=colors[i],
                 label=("%s" % (scenarios[i])), hist_kws={'alpha': 0.5})
    #sns.distplot(ch2, kde=False, color=colors[i],
    #             label=("%s" % (scenarios[i])), hist_kws={'alpha': 0.5})
    med_line = np.median(ch2)
    one_sigma_lines = np.percentile(ch2, (15.9, 84.1))
    two_sigma_lines = np.percentile(ch2, (2.3, 97.7))
    print("median: ", med_line)
    print("85%: ", one_sigma_lines[1])
    print("98%: ", two_sigma_lines[1])
    #plt.axvline(med_line, linewidth=lw, color=colors[i], linestyle='-')
    #for j in range(2):
    #    plt.axvline(one_sigma_lines[j], linewidth=lw,
    #                color=colors[i], linestyle='--')
    #    plt.axvline(two_sigma_lines[j], linewidth=lw,
    #                color=colors[i], linestyle=':')
    #plt.title("270 GHz Band")
    #plt.xlabel("Optical Power [pW]")
    #plt.xlabel("Optical Efficiency")
    #plt.ylabel("Occurances")
    #plt.xlim(xlim)
    #plt.legend(loc='best', title='Det Eff')
    #plt.savefig("270GHz_%spct_popt_dist.jpg" % (scenarios[i].strip("%")))
    #plt.savefig("270GHz_%spct_effp_dist.jpg" % (scenarios[i].strip("%")))
    #nfig += 1

plt.figure(0)
plt.title("220 GHz Band")
#plt.xlabel("Optical Power [pW]")
plt.xlabel("Optical Efficiency")
plt.ylabel("Occurances")
xlim = [0.02, 0.22]
plt.xlim(xlim)
plt.legend(loc='best', title='Det Eff')
#plt.savefig("220GHz_%spct_popt_dist.jpg" % (scenarios[i].strip("%")))
plt.savefig("220GHz_eff_dist.jpg")

plt.figure(1)
plt.title("270 GHz Band")
#plt.xlabel("Optical Power [pW]")
plt.xlabel("Optical Efficiency")
plt.ylabel("Occurances")
xlim = [0.02, 0.126]
plt.xlim(xlim)
plt.legend(loc='best', title='Det Eff')
#plt.savefig("270GHz_%spct_popt_dist.jpg" % (scenarios[i].strip("%")))
plt.savefig("270GHz_eff_dist.jpg")

"""
# Now check the NETs
# Loop over and overplot scenarios
for i, fname in enumerate(fnames):
    data = np.loadtxt(fname, unpack=True, dtype=str, skiprows=1)
    ch1, ch2 = np.take(data, (8, 19), axis=0).astype(float)
    plt.figure(nfig, figsize)
    sns.distplot(ch1, kde=False, color=colors[i],
                 label=("%s" % (scenarios[i])), hist_kws={'alpha': 0.5})
    med_line = np.median(ch1)
    one_sigma_lines = np.percentile(ch1, (15.9, 84.1))
    two_sigma_lines = np.percentile(ch1, (2.3, 97.7))
    plt.axvline(med_line, linewidth=lw, color=colors[i], linestyle='-')
    for j in range(2):
        plt.axvline(one_sigma_lines[j], linewidth=lw,
                    color=colors[i], linestyle='--')
        plt.axvline(two_sigma_lines[j], linewidth=lw,
                    color=colors[i], linestyle=':')
    plt.title("220 GHz Band")
    plt.xlabel("NET [uK-rts]")
    plt.ylabel("Occurances")
    plt.legend(loc='best', title='Det Eff')
    plt.savefig("220GHz_%spct_net_dist.jpg" % (scenarios[i].strip("%")))
    nfig += 1

    plt.figure(nfig, figsize)
    sns.distplot(ch2, kde=False, color=colors[i],
                 label=("%s" % (scenarios[i])), hist_kws={'alpha': 0.5})
    med_line = np.median(ch2)
    one_sigma_lines = np.percentile(ch2, (15.9, 84.1))
    two_sigma_lines = np.percentile(ch2, (2.3, 97.7))
    plt.axvline(med_line, linewidth=lw, color=colors[i], linestyle='-')
    for j in range(2):
        plt.axvline(one_sigma_lines[j], linewidth=lw,
                    color=colors[i], linestyle='--')
        plt.axvline(two_sigma_lines[j], linewidth=lw,
                    color=colors[i], linestyle=':')
    plt.title("270 GHz Band")
    plt.xlabel("NET [uK-rts]")
    plt.ylabel("Occurances")
    plt.legend(loc='best', title='Det Eff')
    plt.savefig("270GHz_%spct_net_dist.jpg" % (scenarios[i].strip("%")))
    nfig += 1
"""