#!/usr/local/bin/python

import pickle as pkl
import matplotlib.pyplot as plt

detPitch, apertureCorrFact = pkl.load(open('./PKL/coherentApertCorr.pkl',  'rb'))
detPitch, stopCorrFact     = pkl.load(open('./PKL/coherentStopCorr.pkl',   'rb'))

plt.figure(0, figsize=(15,10))
plt.rc('font', size=32)
plt.rc('font', family='serif')
plt.rc('text', usetex=True)
lw = 4

#plt.title('Pixel-Pixel Intensity Correlations')
plt.plot(detPitch, apertureCorrFact, linestyle='-',  label='Aperture', linewidth=lw)
#plt.plot(detPitch, stopCorrFact,     linestyle='--', label='Stop',     linewidth=lw)
plt.xlabel('Detector Pitch [F \lambda]')
plt.ylabel('Correlation Factor')
#plt.legend(loc='best', fontsize=24)
plt.xlim([0, 3])
plt.savefig('correlationsPlot.pdf')
plt.show()
