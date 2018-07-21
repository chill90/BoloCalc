import numpy           as np
import glob            as gb
import collections     as cl
import sys             as sy
import                    os
import                    io
import src.foregrounds as fg
import src.units       as un

#Pickling is different between Python 2 and 3
PY2 = (sy.version_info[0] == 2)
if PY2: import cPickle as pk
else:   import pickle  as pk

class Sky:
    def __init__(self, log, nrealize=1, fgndDict=None, atmFile=None, site=None, pwv=None, pwvDict=None, foregrounds=False):
        #Store passed parameters
        self.log      = log
        self.nrealize = nrealize
        self.fgndDict = fgndDict
        self.atmFile   = atmFile
        self.site      = site
        self.pwv       = pwv
        self.pwvDict   = pwvDict
        self.inclF    = foregrounds

        #Store global parameters
        self.fg       = fg.Foregrounds(self.log, fgndDict=fgndDict, nrealize=nrealize)
        self.nfiles   = 20 #Number of files to break the atmDict.pkl file into
        self.medianPwv = 0.934 #Atacama, as defined by the MERRA-2 dataset
        self.maxPWV    = 8.0
        self.minPWV    = 0.0
        self.atmDir    = os.path.join(os.path.split(__file__)[0], 'atmFiles')
        self.siteDirs  = sorted(gb.glob(os.path.join(self.atmDir, '*'+os.sep)))
        self.siteNames = np.array([siteDir.split(os.sep)[-2] for siteDir in self.siteDirs])
        self.siteDirs  = cl.OrderedDict({self.siteNames[i]: self.siteDirs[i] for i in range(len(self.siteNames))})

        self.__initATM(create=False)

    #***** Public methods ******
    #Sample PWV distribution
    def pwvSample(self):
        if self.pwv is not None: return self.pwv
        samp = np.random.choice(np.array(self.pwvDict.keys()).astype(np.float), size=1, p=np.array(self.pwvDict.values()).astype(np.float)/np.sum(np.array(self.pwvDict.values()).astype(np.float)))[0]
        if samp < self.minPWV:
            self.log.log('Cannot have PWV %.1f < %.1f. Using %.1f instead' % (samp, self.minPWV, self.minPWV), 2)
            return self.minPWV
        elif samp > self.maxPWV:
            self.log.log('Cannot have PWV %.1f > %.1f. Using %.1f instead' % (samp, self.maxPWV, self.maxPWV), 2)
            return self.maxPWV
        else:
            return samp
    #Retrieve user-defined PWV value
    def getPwv(self):
        return self.pwv
    #Retrieve ATM spectrum given some PWV, elevation, and array of frequencies
    def atmSpectrum(self, pwv, elev, freqs):
        if self.atmFile:
            self.log.log('Using provided ATM file -- ignoring provided PWV and El (%.1f, %.1f)' % (pwv, elev), 1)
            freq, temp, tran = np.loadtxt(self.atmFile, unpack=True, usecols=[0, 2, 3], dtype=np.float)
        else:
            freq, temp, tran = self.atmDict[(int(round(elev,0)), round(pwv,1))]
        freq = freq*un.GHzToHz; temp = np.interp(freqs, freq, temp); tran = np.interp(freqs, freq, tran)
        return freq.flatten().tolist(), temp.flatten().tolist(), tran.flatten().tolist()
    #Retrieve synchrotron spectrum given some array of frequencies
    def synSpectrum(self, freqs):
        return self.fg.syncSpecRad(1.0, freqs)
    #Retrieve dust spectrum given some array of frequencies
    def dstSpectrum(self, freqs):
        return self.fg.dustSpecRad(1.0, freqs)
    #Generate the sky
    def generate(self, pwv, elev, freqs):
        self.Ncmb = ['CMB' for f in freqs]; self.Tcmb = [2.725 for f in freqs]; self.Ecmb = [1. for f in freqs]; self.Acmb = [1. for f in freqs]
        self.Natm = ['ATM' for f in freqs]; freq, self.Tatm, self.Eatm = self.atmSpectrum(pwv, elev, freqs);     self.Aatm = [1. for f in freqs]
        if self.inclF:
            self.Nsyn = ['SYNC' for f in freqs]; self.Tsyn = self.synSpectrum(freqs); self.Esyn = [1. for f in freqs]; self.Asyn = [1. for f in freqs]
            self.Ndst = ['DUST' for f in freqs]; self.Tdst = self.dstSpectrum(freqs); self.Edst = [1. for f in freqs]; self.Adst = [1. for f in freqs]
            return ([self.Ncmb, self.Nsyn, self.Ndst, self.Natm],
                    [self.Acmb, self.Asyn, self.Adst, self.Aatm],
                    [self.Ecmb, self.Esyn, self.Edst, self.Eatm],
                    [self.Tcmb, self.Tsyn, self.Tdst, self.Tatm])
        else:
            return ([self.Ncmb, self.Natm],
                    [self.Acmb, self.Aatm],
                    [self.Ecmb, self.Eatm],
                    [self.Tcmb, self.Tatm])

    #***** Private methods *****
    #Initialize atmosphere. If "create" is True, then create pickle files from text files of spectra
    def __initATM(self, create=False):
        if create:
            atmFileArrs    = cl.OrderedDict({site: np.array(sorted(gb.glob(os.path.join(self.siteDirs[site], 'TXT', 'atm*.txt'))))        for site in self.siteNames})
            self.elevArrs  = cl.OrderedDict({site: np.array([float(os.path.split(atmFile)[-1].split('_')[1][:2])                          for atmFile in atmFileArrs[site]]) for site in self.siteNames})
            self.pwvArrs   = cl.OrderedDict({site: np.array([float(os.path.split(atmFile)[-1].split('_')[2][:4])*1e-3                     for atmFile in atmFileArrs[site]]) for site in self.siteNames})
            self.atmDicts = cl.OrderedDict({})
            for site in self.siteNames:
                freqArr, tempArr, tranArr = np.hsplit(np.array([np.loadtxt(atmFile, usecols=[0, 2, 3], unpack=True) for atmFile in atmFileArrs[site]]), 3)
                self.atmDicts[site] = cl.OrderedDict({(int(round(self.elevArrs[site][i])), round(self.pwvArrs[site][i],1)): (freqArr[i][0], tempArr[i][0], tranArr[i][0]) for i in range(len(atmFileArrs[site]))})
                for i in range(self.nfiles):        
                    sub_dict = self.atmDicts[site].items()[i::self.nfiles]
                    pk.dump(sub_dict, open(os.path.join(self.siteDirs[site], 'PKL', ('atmDict_%d.pkl' % (i))), 'wb'))
            self.atmDict = self.atmDicts[self.site]
        else:
            self.atmDict = cl.OrderedDict({})
            for i in range(self.nfiles):
                if PY2: sub_dict = pk.load(io.open(os.path.join(self.siteDirs[self.site], 'PKL', ('atmDict_%d.pkl' % (i))), 'rb'))
                else:   sub_dict = pk.load(io.open(os.path.join(self.siteDirs[self.site], 'PKL', ('atmDict_%d.pkl' % (i))), 'rb'), encoding='latin1')
                self.atmDict.update(sub_dict)
