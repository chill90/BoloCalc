import numpy as np
import sys   as sy
import          os

import src.physics    as ph
import src.units      as un
import src.compatible as cm

class Vary:
    def __init__(self, sim, paramFile, fileHandle=None, varyTogether=False):
        #For logging
        self.sim          = sim
        self.log          = self.sim.log
        self.paramFile    = paramFile
        self.fileHandle   = fileHandle
        self.varyTogether = varyTogether

        #Private instances
        self.__ph = ph.Physics()
        self.__cm = cm.Compatible()

        #Status bar length
        self.barLen = 100

        #Delimiters
        self.__paramDelim_str = '|'
        self.__xyDelim_str = '|||'
        
        #Parameter ID flags/enums
        self.POPT_FLAG   = 1
        self.NEPPH_FLAG  = 2
        self.NETARR_FLAG = 3
        self.PARAM_FLAGS = np.arange(1, 4)

        #Output parameter IDs
        self.savedir = "paramVary"
        self.vary_id   = "vary"
        self.Popt_id   = "Popt"
        self.NEPph_id  = "NEPph"
        self.NETarr_id = "NETarr"
        
        #Load parameters to vary
        self.log.log("Loading parameters to vary from %s" % (os.path.join(os.path.dirname(sy.argv[0]), 'config', 'paramsToVary.txt')))
        self.tels, self.cams, self.chs, self.opts, self.params, self.mins, self.maxs, self.stps = np.loadtxt(self.paramFile, delimiter='|', dtype=np.str, unpack=True, ndmin=2)
        self.tels   = [tel.strip('\t ')   for tel   in self.tels] 
        self.cams   = [cam.strip('\t ')   for cam   in self.cams] 
        self.chs    = [ch.strip('\t ')    for ch    in self.chs] 
        self.opts   = [opt.strip('\t ')   for opt   in self.opts] 
        self.params = [param.strip('\t ') for param in self.params]
        #Special joint consideration of pixel size, spill efficiency, and detector number
        if 'Pixel Size**' in self.params:
            if 'Waist Factor' not in self.params and 'Aperture' not in self.params and 'Lyot' not in self.params and 'Stop' not in self.params and 'Num Det per Wafer' not in self.params:
                self.pixSizeSpecial = True
            else:
                raise Exception("FATAL BoloCalc Error: Cannot pass 'Pixel Size**' as a parameter to vary when 'Aperture', 'Lyot', 'Stop', or 'Num Det per Wafer' is also passed as a param to vary")
        else:
            self.pixSizeSpecial = False
        #Check for consistency of number of parameters varied
        if len(self.tels) == len(self.params) and len(self.params) == len(self.mins) and len(self.mins) == len(self.maxs) and len(self.maxs) == len(self.stps):
            self.numParams = len(self.params)
        else:
            raise Exception('FATAL: Number of telescopes, parameters, mins, maxes, and steps must match for parameters to be varied. Problem with parameter vary file "BoloCalc/config/paramsToVary.txt"\n')

        #Input parameters ID
        if not self.fileHandle is None: 
            self.paramString = '_'+self.fileHandle.rstrip('_').lstrip('_')
        else:
            self.paramString = ""
            for i in range(len(self.params)):
                if not self.tels[i] == '':
                    self.paramString += ("_%s" % (self.tels[i]))
                if not self.cams[i] == '':
                    self.paramString += ("_%s" % (self.cams[i]))
                if not self.chs[i] == '':
                    self.paramString += ("_%s" % (self.chs[i]))
                if not self.opts[i] == '':
                    self.paramString += ("_%s" % (self.opts[i]))
                if not self.params[i] == '':
                    self.paramString += ("_%s" % (self.params[i]))
            
        #Construct arrays of parameters
        paramArr = [np.arange(float(self.mins[i]), float(self.maxs[i])+float(self.stps[i]), float(self.stps[i])).tolist() for i in range(len(self.params))]
        self.numParams = len(paramArr)
        self.log.log("Processing %d parameters" % (self.numParams))
        #Length of each parameter array
        lenArr   = [len(paramArr[i]) for i in range(len(paramArr))]

        #Store the telescope, camera, channels, and optic name information for each parameter
        telsArr  = [[self.tels[i] for j in range(len(paramArr[i]))] for i in range(len(paramArr))]
        camsArr  = [[self.cams[i] for j in range(len(paramArr[i]))] for i in range(len(paramArr))]
        chsArr   = [[self.chs[i]  for j in range(len(paramArr[i]))] for i in range(len(paramArr))]
        optsArr  = [[self.opts[i] for j in range(len(paramArr[i]))] for i in range(len(paramArr))]
        
        if varyTogether:
            #Vary the parameters together. All arrays need to be the same length
            if not len(np.shape(np.array(paramArr))) == 2: raise Exception('FATAL: When all parameters are varied together, all parameter arrays must have the same length. Array length is set by np.arange(min, max+step, step)')
            self.numEntries = lenArr[0]
            self.log.log("Processing %d combinations of parameters" % (self.numEntries))
            self.telArr = np.array(telsArr)
            self.camArr = np.array(camsArr)
            self.chArr  = np.array(chsArr)
            self.optArr = np.array(optsArr)
            self.setArr = np.array(paramArr)
        else:
            self.numEntries = np.prod(lenArr)
            self.log.log("Processing %d combinations of parameters" % (self.numEntries))
            #In order to loop over all possible combinations of the parameters, the arrays need to be rebuilt
            telArr = []
            camArr = []
            chArr  = []
            optArr = []
            setArr = []
            #Construct one array for each parameter
            for i in range(self.numParams):
                #For storing names
                telArrArr = []
                camArrArr = []
                chArrArr  = []
                optArrArr = []
                #For storing values
                setArrArr = []
                #Number of values to be calculated for this parameter
                if i < self.numParams-1:
                    for j in range(lenArr[i]):
                        telArrArr = telArrArr + [telsArr[i][j]]*np.prod(lenArr[i+1:])
                        camArrArr = camArrArr + [camsArr[i][j]]*np.prod(lenArr[i+1:])
                        chArrArr  = chArrArr +  [chsArr[i][j]]*np.prod(lenArr[i+1:])
                        optArrArr = optArrArr + [optsArr[i][j]]*np.prod(lenArr[i+1:])
                        setArrArr = setArrArr + [paramArr[i][j]]*np.prod(lenArr[i+1:])
                else:
                    telArrArr = telArrArr + telsArr[i]
                    camArrArr = camArrArr + camsArr[i]
                    chArrArr  = chArrArr  +  chsArr[i]
                    optArrArr = optArrArr + optsArr[i]
                    setArrArr = setArrArr + paramArr[i]
                if i > 0:
                    telArr.append(telArrArr*np.prod(lenArr[:i]))
                    camArr.append(camArrArr*np.prod(lenArr[:i]))
                    chArr.append( chArrArr*np.prod( lenArr[:i]))
                    optArr.append(optArrArr*np.prod(lenArr[:i]))
                    setArr.append(setArrArr*np.prod(lenArr[:i]))
                else:
                    telArr.append(telArrArr)
                    camArr.append(camArrArr)
                    chArr.append( chArrArr)
                    optArr.append(optArrArr)
                    setArr.append(setArrArr)
                    
            self.telArr = np.array(telArr)
            self.camArr = np.array(camArr)
            self.chArr  = np.array(chArr)
            self.optArr = np.array(optArr)
            self.setArr = np.array(setArr)

    #**** Public Methods ****
    def vary(self):
        self.sim.verbosity = 0
        self.sim.generateExps()
        self.sim.verbosity = None
        self.experiments = self.sim.experiments
        
        #At which level to regenerate each parameter
        exR = False; tlR = False; cmR = False
        for i in range(len(self.setArr)):
            if np.any(self.tels != ''):
                exR = True
            if np.any(self.cams[i] != ''):
                tlR = True
            if np.any(self.chs[i] != ''):
                cmR = True

        #Loop over experiments and store optical power, photon NEP, and NET
        expNames = []
        telNames = []
        camNames = []
        chnNames = []
        filledNames = False
        
        popt_final = []; poptstd_final = []
        nepph_final = []; nepphstd_final = []
        netarr_final = []; netarrstd_final = []

        self.totIters = len(self.experiments)*len(self.setArr[0])
        
        for n in range(len(self.experiments)):
            experiment = self.experiments[n]
            popt  = []; poptstd  = []
            nepph = []; nepphstd = []
            net   = []; netstd   = []
            for i in range(len(self.setArr[0])):
                for j in range(len(self.setArr)):
                    if self.tels[j] != '':
                        if self.cams[j] != '':
                            if self.chs[j] != '':
                                if self.opts[j] != '':
                                    experiment.telescopes[self.tels[j]].cameras[self.cams[j]].optChain.optics[self.opts[j]].paramsDict[self.params[j]].change(self.setArr[j][i], bandID=int(self.chs[j]))
                                    experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].generate()
                                else:
                                    #Vary aperture spill efficiency and number of detectors along with pixel size
                                    if 'Pixel Size' in self.params[j] and self.pixSizeSpecial:
                                        #Check that the f-number is defined
                                        if experiment.telescopes[self.tels[j]].cameras[self.cams[j]].paramsDict['F Number'].isEmpty():
                                            raise Exception("FATAL BoloCalc Error: Cannot set 'Pixel Size**' as a parameter to vary without 'F Number' also defined for this camera")
                                        else:
                                            fnum = experiment.telescopes[self.tels[j]].cameras[self.cams[j]].paramsDict['F Number'].getAvg(bandID=int(self.chs[j]))
                                        #Check that the band center is defined
                                        if experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict['Band Center'].isEmpty():
                                            raise Exception("FATAL BoloCalc Error: Cannot set 'Pixel Size**' as a parameter to vary without 'Band Center' also defined for this channel")
                                        else:
                                            freq = experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict['Band Center'].getAvg(bandID=int(self.chs[j]))
                                        #Check that the waist factor is defined
                                        if experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict['Waist Factor'].isEmpty():
                                            raise Exception("FATAL BoloCalc Error: Cannot set 'Pixel Size**' as a parameter to vary without 'Waist Factor' also defined for this channel")
                                        else:
                                            w0 = experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict['Waist Factor'].getAvg(bandID=int(self.chs[j]))
                                        #Check for what the aperture is called
                                        if 'Aperture' in experiment.telescopes[self.tels[j]].cameras[self.cams[j]].optChain.optics.keys():
                                            apName = 'Aperture'
                                        elif 'Lyot' in experiment.telescopes[self.tels[j]].cameras[self.cams[j]].optChain.optics.keys():
                                            apName = 'Lyot'
                                        elif 'Stop' in experiment.telescopes[self.tels[j]].cameras[self.cams[j]].optChain.optics.keys():
                                            apName = 'Stop'
                                        else:
                                            raise Exception("FATAL BoloCalc Error: Cannot pass 'Pixel Size**' as a parameter to vary when neither 'Aperture' nor 'Lyot' nor 'Stop' is defined in the camera's optical chain")
                                        #Store current values for detector number, aperture efficiency, and pixel size
                                        pixSize_current = experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict['Pixel Size'].getAvg(bandID=int(self.chs[j]))
                                        Ndet_per_wafer_current = experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict['Num Det per Wafer'].getAvg(bandID=int(self.chs[j]))
                                        apAbs_current = experiment.telescopes[self.tels[j]].cameras[self.cams[j]].optChain.optics[apName].paramsDict['Absorption'].getAvg(bandID=int(self.chs[j]))
                                        if apAbs_current == 'NA':
                                            apAbs_current = None
                                        #Calculate new values for detector number, aperture efficiency, and pixel size
                                        pixSize_new = self.setArr[j][i]
                                        Ndet_per_wafer_new = Ndet_per_wafer_current*np.power((pixSize_current/(pixSize_new*un.mmToM)),2.)
                                        if apAbs_current is not None:
                                            apAbs_new = 1. - (1. - apAbs_current)*self.__ph.spillEff(freq, pixSize_new*un.mmToM, fnum, w0)/self.__ph.spillEff(freq, pixSize_current, fnum, w0)
                                        else:
                                            apAbs_new = 1. - self.__ph.spillEff(freq, pixSize_new*un.mmToM, fnum, w0)
                                        #Define new values
                                        experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict['Pixel Size'].change(pixSize_new, bandID=int(self.chs[j]))
                                        experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict['Num Det per Wafer'].change(Ndet_per_wafer_new, bandID=int(self.chs[j]))
                                        experiment.telescopes[self.tels[j]].cameras[self.cams[j]].optChain.optics[apName].paramsDict['Absorption'].change(apAbs_new, bandID=int(self.chs[j]))
                                    else:
                                        experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].paramsDict[self.params[j]].change(self.setArr[j][i], bandID=int(self.chs[j]))
                                    experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].generate()
                            else:
                                experiment.telescopes[self.tels[j]].cameras[self.cams[j]].paramsDict[self.params[j]].change(self.setArr[j][i])
                                experiment.telescopes[self.tels[j]].cameras[self.cams[j]].generate()
                        else:
                            experiment.telescopes[self.tels[j]].paramsDict[self.params[j]].change(self.setArr[j][i])
                            experiment.telescopes[self.tels[j]].generate()
                    else:
                        experiment.paramsDict[self.params[j]].change(self.setArr[j][i])
                        experiment.generate()
                #After new parameters are stored, re-run mapping speed calculation
                dsp = self.sim.calculate()
                #Store new sensitivity values
                valDict = dsp.dict
                #Write the names and values
                poptArr  = []
                nepPhArr = []
                netArr    = []
                for t in sorted(experiment.telescopes.keys()):
                    telescope = experiment.telescopes[t]
                    for c in sorted(telescope.cameras.keys()):
                        camera = telescope.cameras[c]
                        for h in sorted(camera.channels.keys()):
                            channel = camera.channels[h]
                            #Only need to store names of telescopes, cameras, and channels one time
                            if not filledNames:
                                expNames.append(experiment.name)
                                telNames.append(telescope.name)
                                camNames.append(camera.name)
                                chnNames.append(channel.name)
                            poptArr.append(valDict[telescope.name][camera.name][channel.name]['Optical Power'])
                            nepPhArr.append(valDict[telescope.name][camera.name][channel.name]['Photon NEP'])
                            netArr.append(valDict[telescope.name][camera.name][channel.name]['Array NET'])
                filledNames = True
                popt.append(np.array(poptArr).T[0])
                poptstd.append(np.array(poptArr).T[1])
                nepph.append(np.array(nepPhArr).T[0])
                nepphstd.append(np.array(nepPhArr).T[1])
                net.append(np.array(netArr).T[0])
                netstd.append(np.array(netArr).T[1])
                iter = n*len(self.setArr[0])*len(self.setArr) + i + 1
                self.__status(iter)
            popt_final.append(popt)
            poptstd_final.append(poptstd)
            nepph_final.append(nepph)
            nepphstd_final.append(nepphstd)
            netarr_final.append(net)
            netarrstd_final.append(netstd)

        #Store the names of the telescopes, cameras, and channels
        self.expNames = expNames
        self.telNames = telNames
        self.camNames = camNames
        self.chnNames = chnNames
        
        #Calculate average and standard deviation across experiments
        self.popt_final  = np.mean(popt_final, axis=0);  self.poptstd_final  = np.sqrt(np.mean(np.array(poptstd_final)**2, axis=0)  + np.var(np.array(popt_final),  axis=0))
        self.nepph_final = np.mean(nepph_final, axis=0); self.nepphstd_final = np.sqrt(np.mean(np.array(nepphstd_final)**2, axis=0) + np.var(np.array(nepph_final), axis=0))
        self.netarr_final   = np.mean(netarr_final, axis=0);   self.netarrstd_final   = np.sqrt(np.mean(np.array(netarrstd_final)**2, axis=0)   + np.var(np.array(netarr_final),   axis=0))
        sy.stdout.write('\n')

    def save(self):        
        #Write parameter vary files
        for i in self.PARAM_FLAGS:
            self.__save(i)

    # ***** Private Methods *****
    #Status bar
    def __status(self, rel):
        frac = float(rel)/float(self.totIters)
        sy.stdout.write('\r')
        sy.stdout.write("[%-*s] %02.1f%%" % (int(self.barLen), '='*int(self.barLen*frac), frac*100.))
        sy.stdout.flush()
    #Save an output parameter
    def __save(self, param=None):
        if param is None:
            return False
        #Which parameter is being saved?
        if param == self.POPT_FLAG:
            param_id = self.Popt_id
            meanArr = self.popt_final
            stdArr = self.poptstd_final
        elif param == self.NEPPH_FLAG:
            param_id = self.NEPph_id
            meanArr = self.nepph_final
            stdArr = self.nepphstd_final
        elif param == self.NETARR_FLAG:
            param_id = self.NETarr_id
            meanArr = self.netarr_final
            stdArr = self.netarrstd_final            
        else:
            return False
        #File name to save to
        fname  = os.path.join(self.experiments[0].dir, self.savedir, ('%s_%s%s.txt' % (param_id, self.vary_id, self.paramString)))
        
        #Write to file
        f = open(fname, 'w')
        #Line 1 -- telescope name
        self.__tableEntry(f, self.tels, self.telNames)
        #Line 2 -- camera name
        self.__tableEntry(f, self.cams, self.camNames)
        #Line 3 -- channel name
        self.__tableEntry(f, self.chs, self.chnNames)
        #Line 4 -- optical element name
        self.__tableEntry(f, self.opts, [' ']*len(self.chnNames))
        #Line 5 -- parameter being varied
        self.__tableEntry(f, self.params, [param_id]*len(self.chnNames))
        f.write(self.__horizLine())
        #Write the rest of the lines
        for i in range(self.numEntries):
            self.__tableEntry(f, self.__input_vals(self.setArr.T[i]), self.__output_vals(meanArr[i], stdArr[i]))
        #Close file
        f.close()
    #Construct value entries to table
    def __input_val(self, val):
        return ('%-15.3f' % (val))
    def __input_vals(self, valArr):
        return np.array([self.__input_val(val) for val in valArr])
    def __output_val(self, mean, std):
        return ('%6.2f +/- %-6.2f' % (mean, std))
    def __output_vals(self, meanArr, stdArr):
        if len(meanArr) != len(stdArr):
            return None
        else:
            return np.array([self.__output_val(mean, std) for mean, std in self.__cm.zip(meanArr, stdArr)])
    #Write entries to table
    def __xEntry(self, string):
        return ('%-15s' % (string))
    def __yEntry(self, string):
        return ('%-17s' % (string))
    #Write parameter delimiter
    def __paramDelim(self):
        return (' %s ' % (self.__paramDelim_str))
    #Write x-y delimiter
    def __xyDelim(self):
        return (' %s ' % (self.__xyDelim_str))
    #Write horizontal line
    def __horizLine(self):
        return (('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
    #Write table row
    def __tableEntry(self, f, xEntries, yEntries):
        for i in range(self.numParams):
            f.write(self.__xEntry(xEntries[i]))
            if i < self.numParams-1:
                f.write(self.__paramDelim())
        f.write(self.__xyDelim())
        for i in range(len(self.telNames)):
            f.write(self.__yEntry(yEntries[i]))
            if i < len(self.telNames)-1:
                f.write(self.__paramDelim())
        f.write('\n')
        f.write(self.__horizLine())
