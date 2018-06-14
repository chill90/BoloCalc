#python Version 2.7.2
import numpy as np
import sys   as sy
import os

class Vary:
    def __init__(self, sim, paramFile):
        #For logging
        self.sim       = sim
        self.log       = self.sim.log
        self.paramFile = paramFile

        #Status bar length
        self.barLen = 100
        
        #Load parameters to vary
        self.log.log("Loading parameters to vary from %s" % (os.path.dirname(sy.argv[0])+'config/paramsToVary.txt'))
        self.tels, self.cams, self.chs, self.opts, self.params, self.mins, self.maxs, self.stps = np.loadtxt(self.paramFile, delimiter='|', dtype=np.str, unpack=True)
        self.tels   = [tel.strip('\t ')   for tel   in self.tels] 
        self.cams   = [cam.strip('\t ')   for cam   in self.cams] 
        self.chs    = [ch.strip('\t ')    for ch    in self.chs] 
        self.opts   = [opt.strip('\t ')   for opt   in self.opts] 
        self.params = [param.strip('\t ') for param in self.params]
        #Check for consistency of number of parameters varied
        if len(self.tels) == len(self.params) and len(self.params) == len(self.mins) and len(self.mins) == len(self.maxs) and len(self.maxs) == len(self.stps):
            self.numParams = len(self.params)
        else:
            sy.exit('Number of telescopes, parameters, mins, maxes, and steps must match for parameters to be varied. Problem with parameter vary file\n')
            
        #Construct arrays of parameters
        paramArr = [np.arange(float(self.mins[i]), float(self.maxs[i])+float(self.stps[i]), float(self.stps[i])).tolist() for i in range(len(self.params))]
        self.numParams = len(paramArr)
        self.log.log("Processing %d parameters" % (self.numParams))
        #Length of each parameter array
        lenArr   = [len(paramArr[i]) for i in range(len(paramArr))]
        self.numEntries = np.prod(lenArr)
        self.log.log("Processing %d combinations of parameters" % (self.numEntries))

        #Store the telescope, camera, channels, and optic name information for each parameter
        telsArr  = [[self.tels[i] for j in range(len(paramArr[i]))] for i in range(len(paramArr))]
        camsArr  = [[self.cams[i] for j in range(len(paramArr[i]))] for i in range(len(paramArr))]
        chsArr   = [[self.chs[i]  for j in range(len(paramArr[i]))] for i in range(len(paramArr))]
        optsArr  = [[self.opts[i] for j in range(len(paramArr[i]))] for i in range(len(paramArr))]
        
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
        net_final = []; netstd_final = []

        self.totIters = len(self.experiments)*len(self.setArr[0])
        print "Calculating %d mapping speeds..." % (int(self.totIters))
        
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
                                    experiment.telescopes[self.tels[j]].cameras[self.cams[j]].optChain.optics[self.opts[j]].params[self.params[j]].change(self.setArr[j][i], bandID=int(self.chs[j]))
                                    experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].generate()
                                else:
                                    experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].params[self.params[j]].change(self.setArr[j][i], bandID=int(self.chs[j]))
                                    experiment.telescopes[self.tels[j]].cameras[self.cams[j]].channels[self.chs[j]].generate()
                            else:
                                experiment.telescopes[self.tels[j]].cameras[self.cams[j]].params[self.params[j]].change(self.setArr[j][i])
                                experiment.telescopes[self.tels[j]].cameras[self.cams[j]].generate()
                        else:
                            experiment.telescopes[self.tels[j]].params[self.params[j]].change(self.setArr[j][i])
                            experiment.telescopes[self.tels[j]].generate()
                    else:
                        experiment.params[self.params[j]].change(self.setArr[j][i])
                        experiment.generate()
                #After new parameters are stored, re-run mapping speed calculation
                dsp = self.sim.calculate()
                #Store new sensitivity values
                valDict = dsp.dict
                #Write the names and values to the file
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
            net_final.append(net)
            netstd_final.append(netstd)

        #Store the names of the telescopes, cameras, and channels
        self.expNames = expNames
        self.telNames = telNames
        self.camNames = camNames
        self.chnNames = chnNames
        
        #Calculate average and standard deviation across experiments
        self.popt_final  = np.mean(popt_final, axis=0);  self.poptstd_final  = np.sqrt(np.mean(np.array(poptstd_final)**2, axis=0)  + np.var(np.array(popt_final),  axis=0))
        self.nepph_final = np.mean(nepph_final, axis=0); self.nepphstd_final = np.sqrt(np.mean(np.array(nepphstd_final)**2, axis=0) + np.var(np.array(nepph_final), axis=0))
        self.net_final   = np.mean(net_final, axis=0);   self.netstd_final   = np.sqrt(np.mean(np.array(netstd_final)**2, axis=0)   + np.var(np.array(net_final),   axis=0))
        sy.stdout.write('\n')

    def save(self):
        #Save parameters to files
        #Crate string for file names
        paramString = ""
        for i in range(len(self.params)):
            if not self.tels[i] == '':
                paramString += ("_%s" % (self.tels[i]))
            if not self.cams[i] == '':
                paramString += ("_%s" % (self.cams[i]))
            if not self.chs[i] == '':
                paramString += ("_%s" % (self.chs[i]))
            if not self.opts[i] == '':
                paramString += ("_%s" % (self.opts[i]))
            if not self.params[i] == '':
                paramString += ("_%s" % (self.params[i]))
        #paramString += "_"
        savedir = "paramVary/"
        fname_popt  = ('%s/%s/mappingSpeedVary_Popt%s.txt'   % (self.experiments[0].dir, savedir, paramString))
        fname_nepph = ('%s/%s/mappingSpeedVary_NEPph%s.txt'  % (self.experiments[0].dir, savedir, paramString))
        fname_net   = ('%s/%s/mappingSpeedVary_NETarr%s.txt' % (self.experiments[0].dir, savedir, paramString))
        #print '%s/%s/mappingSpeedVary_Popt%s.txt'   % (self.experiments[0].dir, savedir, paramString)

        #Write optical power file
        f = open(fname_popt, 'w')
        #Line 1
        for i in range(self.numParams):
            f.write('%-15s' % (self.tels[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.telNames)):
            f.write('%-17s' % (self.telNames[i]))
            if i < len(self.telNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 2
        for i in range(self.numParams):
            f.write('%-15s' % (self.cams[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.camNames)):
            f.write('%-17s' % (self.camNames[i]))
            if i < len(self.camNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 3
        for i in range(self.numParams):
            f.write('%-15s' % (self.chs[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
            f.write('%-17s' % (self.chnNames[i]))
            if i < len(self.chnNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 4
        for i in range(self.numParams):
            f.write('%-15s' % (self.opts[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
           f.write(' '*17)
           if i < len(self.chnNames)-1:
               f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 5
        for i in range(self.numParams):
            f.write('%-15s' % (self.params[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
           f.write(' '*17)
           if i < len(self.chnNames)-1:
               f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')        
        #Write the rest of the lines
        for i in range(self.numEntries):
            for j in range(self.numParams):
                f.write('%-15f' % (self.setArr[j][i]))
                if j < self.numParams-1:
                    f.write(' | ')
            f.write(' ||| ')
            for j in range(len(self.popt_final[i])):
                f.write('%6.2f +/- %-6.2f' % (self.popt_final[i][j], self.poptstd_final[i][j]))
                if j < len(self.popt_final[i])-1:
                    f.write(' | ')
            f.write('\n')
            f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Close file
        f.close()

        #Write photon NEP to a file
        f = open(fname_nepph, 'w')
        #Line 1
        for i in range(self.numParams):
            f.write('%-15s' % (self.tels[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.telNames)):
            f.write('%-17s' % (self.telNames[i]))
            if i < len(self.telNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 2
        for i in range(self.numParams):
            f.write('%-15s' % (self.cams[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.camNames)):
            f.write('%-17s' % (self.camNames[i]))
            if i < len(self.camNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 3
        for i in range(self.numParams):
            f.write('%-15s' % (self.chs[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
            f.write('%-17s' % (self.chnNames[i]))
            if i < len(self.chnNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 4
        for i in range(self.numParams):
            f.write('%-15s' % (self.opts[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
           f.write(' '*17)
           if i < len(self.chnNames)-1:
               f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 5
        for i in range(self.numParams):
            f.write('%-15s' % (self.params[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
           f.write(' '*17)
           if i < len(self.chnNames)-1:
               f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')        
        #Write the rest of the lines
        for i in range(self.numEntries):
            for j in range(self.numParams):
                f.write('%-15f' % (self.setArr[j][i]))
                if j < self.numParams-1:
                    f.write(' | ')
            f.write(' ||| ')
            for j in range(len(self.nepph_final[i])):
                f.write('%6.2f +/- %-6.2f' % (self.nepph_final[i][j], self.nepphstd_final[i][j]))
                if j < len(self.nepph_final[i])-1:
                    f.write(' | ')
            f.write('\n')
            f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Close file
        f.close()

        #Write mapping speed to a file
        f = open(fname_net, 'w')
        #Line 1
        for i in range(self.numParams):
            f.write('%-15s' % (self.tels[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.telNames)):
            f.write('%-17s' % (self.telNames[i]))
            if i < len(self.telNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 2
        for i in range(self.numParams):
            f.write('%-15s' % (self.cams[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.camNames)):
            f.write('%-17s' % (self.camNames[i]))
            if i < len(self.camNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 3
        for i in range(self.numParams):
            f.write('%-15s' % (self.chs[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
            f.write('%-17s' % (self.chnNames[i]))
            if i < len(self.chnNames)-1:
                f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 4
        for i in range(self.numParams):
            f.write('%-15s' % (self.opts[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
           f.write(' '*17)
           if i < len(self.chnNames)-1:
               f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Line 5
        for i in range(self.numParams):
            f.write('%-15s' % (self.params[i]))
            if i < self.numParams-1:
                f.write(' | ')
        f.write(' ||| ')
        for i in range(len(self.chnNames)):
           f.write(' '*17)
           if i < len(self.chnNames)-1:
               f.write(' | ')
        f.write('\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')        
        #Write the rest of the lines
        for i in range(self.numEntries):
            for j in range(self.numParams):
                f.write('%-15f' % (self.setArr[j][i]))
                if j < self.numParams-1:
                    f.write(' | ')
            f.write(' ||| ')
            for j in range(len(self.net_final[i])):
                f.write('%6.2f +/- %-6.2f' % (self.net_final[i][j], self.netstd_final[i][j]))
                if j < len(self.net_final[i])-1:
                    f.write(' | ')
            f.write('\n')
            f.write(('-'*(self.numParams*15 + len(self.telNames)*17 + (self.numParams-1)*3 + (len(self.telNames)-1)*3 + 5))+'\n')
        #Close file
        f.close()
    
    #Status bar
    def __status(self, rel):
        frac = float(rel)/float(self.totIters)
        sy.stdout.write('\r')
        sy.stdout.write("[%-*s] %02.1f%%" % (int(self.barLen), '='*int(self.barLen*frac), frac*100.))
        sy.stdout.flush()
