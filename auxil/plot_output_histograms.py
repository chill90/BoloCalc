import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import sys as sy
import os

# Pass the output file to be parsed and plotted as a command-line argument
args = sy.argv[1:]
if not len(args) == 1:
    print("\nUsage: python plot_histogram.py [output.txt file]\n")
    sy.exit(False)
else:
    fname = args[0]

# Load the output file
ch_datas = np.loadtxt(fname, unpack=True, delimiter="|", dtype=str)[:-2]
data_dicts = {}
for i, ch_data in enumerate(ch_datas):
    ch_name = fname.split(os.sep)[-2]+str(i)
    data = np.transpose([dat.split() for dat in ch_data])
    keys = [dat[0] for dat in data]
    values = [dat[1:] for dat in data]
    data_dict = dict(zip(keys, values))
    data_dicts[ch_name] = data_dict

# Plot 