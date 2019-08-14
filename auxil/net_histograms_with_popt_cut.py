import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import sys as sy
import pandas as pd

# There are four detector efficiency scenarios to consider
# 20%, 40%, 60%, and 80%
# For each of these scenarios, we consider three different Psat values
# 2 * median Popt
# 2 * 85% CL Popt
# 2 * 98% CL Popt

# Array which holds the maximum allowed optical power
# for each scenario


def ms(nets):
    net_arr = (
        1. / np.sqrt(np.sum(1. / np.power(np.array(nets), 2.))))
    return (1. / np.power(net_arr, 2))

ch1_max_popt = np.array([3.70, 5.76, 9.86,
                         7.06, 10.34, 18.94,
                         11.90, 20.52, 30.08,
                         14.94, 26.58, 46.10])/2.
ch2_max_popt = np.array([3.00, 4.94, 8.44,
                        6.42, 10.84, 18.14,
                        9.08, 14.56, 23.20,
                        12.08, 19.98, 35.42])/2.
id1 = np.array(["50% CL", "85% CL", "98% CL"]*4)
id2 = np.array(["20%"]*3 + ["40%"]*3 + ["60%"]*3 + ["80%"]*3)

fnames = sy.argv[1:]

ch1_net_arr = []
ch1_net_tot = []
ch1_ms_tot = []
ch1_id1_arr = []
ch1_id2_arr = []

ch2_net_arr = []
ch2_net_tot = []
ch2_ms_tot = []
ch2_id1_arr = []
ch2_id2_arr = []

for i, fname in enumerate(fnames):
    data = np.loadtxt(fname, unpack=True, dtype=str, skiprows=1)
    ch1_opt, ch1_net, ch2_opt, ch2_net = np.take(
        data, (1, 8, 12, 19), axis=0).astype(float)

    # Store channel 1
    ch1_args = (ch1_opt <= ch1_max_popt[i])
    ch1_net_select = ch1_net[ch1_args]
    ch1_yield = len(ch1_net_select) / len(ch1_net)
    ch1_net_yield = (np.array(ch1_net_select) / np.sqrt(ch1_yield)).tolist()
    ch1_ms = ms(ch1_net_select)
    ch1_id1 = [id1[i]]*len(ch1_net_select)
    ch1_id2 = [id2[i]]*len(ch1_net_select)

    # Store channel 2
    ch2_args = (ch2_opt <= ch2_max_popt[i])
    ch2_net_select = ch2_net[ch2_args]
    ch2_yield = len(ch2_net_select) / len(ch2_net)
    ch2_net_yield = (np.array(ch2_net_select) / np.sqrt(ch2_yield)).tolist()
    ch2_ms = ms(ch2_net_select)
    ch2_id1 = [id1[i]]*len(ch2_net_select)
    ch2_id2 = [id2[i]]*len(ch2_net_select)

    # Store for global analysis
    ch1_net_arr += ch1_net_select.tolist()
    ch1_net_tot += ch1_net_yield
    ch1_ms_tot += [ch1_ms]
    ch1_id1_arr += ch1_id1
    ch1_id2_arr += ch1_id2

    ch2_net_arr += ch2_net_select.tolist()
    ch2_net_tot += ch2_net_yield
    ch2_ms_tot += [ch2_ms]
    ch2_id1_arr += ch2_id1
    ch2_id2_arr += ch2_id2

sns.set(style="whitegrid", font_scale=3)

# Plot channel 1 selected NET
plt.figure(0, figsize=(17, 12))
sns.violinplot(x=ch1_id2_arr, y=ch1_net_arr, hue=ch1_id1_arr, cut=0,
               palette='bright')
plt.xlabel("Detector Efficiency")
plt.ylabel("NET [uK_CMB-rts]")
plt.ylim(top=4000)
plt.savefig("220GHz_NET_violin.jpg")

# Plot channel 2 selected NET
plt.figure(1, figsize=(17, 12))
sns.violinplot(x=ch2_id2_arr, y=ch2_net_arr, hue=ch2_id1_arr, cut=0,
               palette='bright')
plt.xlabel("Detector Efficiency")
plt.ylabel("NET [uK_CMB-rts]")
plt.ylim(top=10000)
plt.savefig("270GHz_NET_violin.jpg")

# Plot channel 1 selected NET
plt.figure(2, figsize=(17, 12))
sns.violinplot(x=ch1_id2_arr, y=ch1_net_tot, hue=ch1_id1_arr, cut=0,
               palette='bright')
plt.xlabel("Detector Efficiency")
plt.ylabel("Time-weighted NET [uK_CMB-rts]")
plt.ylim(top=4000)
plt.savefig("220GHz_NET_weight_violin.jpg")

# Plot channel 2 selected NET
plt.figure(3, figsize=(17, 12))
sns.violinplot(x=ch2_id2_arr, y=ch2_net_tot, hue=ch2_id1_arr, cut=0,
               palette='bright')
plt.xlabel("Detector Efficiency")
plt.ylabel("Time-weighted NET [uK_CMB-rts]")
plt.ylim(top=10000)
plt.savefig("270GHz_NET_weight_violin.jpg")

# Plot channel 1 Mapping Speed
ms = (1. / np.power(np.array(ch1_net_tot), 2.))*1.e6
plt.figure(4, figsize=(17, 12))
sns.violinplot(x=ch1_id2_arr, y=ms, hue=ch1_id1_arr, cut=0,
               palette='bright')
plt.xlabel("Detector Efficiency")
plt.ylabel("Per-det Mapping Speed [uK^-2 s^-1]")
plt.ylim(top=1.2)
plt.savefig("220GHz_MS_violin.jpg")

# Plot channel 2 Mapping Speed
ms = (1. / np.power(np.array(ch2_net_tot), 2.))*1.e6
plt.figure(5, figsize=(17, 12))
sns.violinplot(x=ch2_id2_arr, y=ms, hue=ch2_id1_arr, cut=0,
               palette='bright')
plt.xlabel("Detector Efficiency")
plt.ylabel("Per-det Mapping Speed [uK^-2 s^-1]")
plt.ylim(top=0.22)
plt.savefig("270GHz_MS_violin.jpg")

# Plot channel 1 mapping speed
colors = ['r', 'b', 'g', 'c']
labels = ["20%", "40%", "60%", "80%"]
ticks = [0, 1, 2]
plt.figure(6, figsize=(17, 12))
ms_arr = np.reshape(np.array(ch1_ms_tot), (4, 3))
ms_max = np.amax(ms_arr)
for i, ms in enumerate(ms_arr):
    plt.plot(ms/ms_max, label=labels[i], color=colors[i],
             linewidth=4, marker='o')
plt.xticks(ticks=ticks, labels=["50% CL", "85% CL", "98% CL"])
plt.xlabel("Psat")
plt.ylabel("Normalized Mapping Speed")
plt.legend(title='Det Eff')
plt.savefig("220GHz_MS_plot.jpg")

# Plot channel 2 mapping speed
colors = ['r', 'b', 'g', 'c']
labels = ["20%", "40%", "60%", "80%"]
ticks = [0, 1, 2]
plt.figure(7, figsize=(17, 12))
ms_arr = np.reshape(np.array(ch2_ms_tot), (4, 3))
ms_max = np.amax(ms_arr)
for i, ms in enumerate(ms_arr):
    plt.plot(ms/ms_max, label=labels[i], color=colors[i],
             linewidth=4, marker='o')
plt.xticks(ticks=ticks, labels=["50% CL", "85% CL", "98% CL"])
plt.xlabel("Psat")
plt.ylabel("Normalized Mapping Speed")
plt.legend(title='Det Eff')
plt.savefig("270GHz_MS_plot.jpg")
