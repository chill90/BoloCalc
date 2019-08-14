# Built-in modules
import numpy as np
import sys as sy
import os

# BoloCalc modules
import src.physics as ph
import src.units as un
import src.compatible as cm


class Vary:
    def __init__(self, sim, param_file, file_id=None, vary_tog=False):
        # For logging
        self._sim = sim
        self._exp = self._sim.exp
        self._log = self._sim.log
        self._ph = self._sim.ph
        self._param_file = param_file
        self._file_id = file_id
        self._vary_tog = vary_tog

        # Status bar length
        self._bar_len = 100

        # Delimiters
        self._param_delim = '|'
        self._xy_delim = '|||'

        # Output parameter IDs
        self._save_dir = "paramVary"

        # Load parameters to vary
        self._load_param_vary()

        # Generate the output file tag
        self._store_file_tag()

        # Configure parameter arrays
        self._config_params()

    # **** Public Methods ****
    def vary(self):
        self._out = []
        self._vary_ids = []
        # Loop over parameters values
        for i in range(len(self.set_arr[0])):
            # Loop over parameters
            for j in range(len(self.set_arr)):
                # Change experiment parameter
                if self._vary_depth(j) is 'exp':
                    self._exp.change_param(self.setArr[j][i])
                    self._exp.evaluate()
                # Change telescope parameter
                elif self._vary_depth(j) is 'tel':
                    tel = self._exp.tels[self._tels[j]]
                    tel.change_param(self.setArr[j][i])
                    tel.evaluate()
                # Change camera parameter
                elif self._vary_depth(j) is 'cam':
                    cam = self._exp.tels[self._tels[j]].cams[self._cams[j]]
                    cam.change_param(self.setArr[j][i])
                    cam.evalutate()
                # Change channel parameter
                elif self._vary_depth(j) is 'ch':
                    ch = (self._exp.tels[self._tels[j]].cams[self._cams[j]]
                          .chs[self.chs[j]])
                    ch.change_param(self.setArr[j][i])
                    ch.evaluate()
                # Change optic parameter
                elif self._vary_depth(j) is 'opt':
                    ch = (self._exp.tels[self._tels[j]].cams[self._cams[j]]
                          .chs[self.chs[j]])
                    opt = (self._exp.tels[self._tels[j]]
                           .cams[self._cams[j]].opt_cnh.opts[self._opts[j]])
                    band_id = int(self.chs[j])
                    opt.change_param(self.setArr[j][i], band_id=band_id)
                    opt.evaluate(ch)
                # Change the pixel size, varying detector number also
                elif self._vary_depth(j) is 'pix':
                    cam = self._exp.tels[self._tels[j]].cams[self._cams[j]]
                    ch = cam.chs[self.chs[j]]
                    # Check that the f-number is defined
                    f_num = cam.get_param('F Number')
                    if f_num == 'NA':
                        self._log.err("Cannot set 'Pixel Size**' as a "
                                      "parameter to vary without 'F Number' "
                                      "also defined for this camera")
                    # Check that the band center is defined
                    bc = ch.get_param('Band Center')
                    if bc == 'NA':
                        self._log.err("Cannot set 'Pixel Size**' as a "
                                      "parameter to vary without "
                                      "'Band Center' also defined for this "
                                      "channel")
                    # Check that the waist factor is defined
                    w0 = ch.get_param('Waist Factor')
                    if w0 == 'NA':
                        self._log.err("Cannot set 'Pixel Size**' as a "
                                      "parameter to vary without "
                                      "'Waist Factor' also defined for this "
                                      "channel")
                    # Check that the aperture defined
                    opt_keys = cam.opt_chn.opts.keys()
                    if 'Aperture' in opt_keys:
                        ap_name = 'Aperture'
                    elif 'Lyot' in opt_keys:
                        ap_name = 'Lyot'
                    elif 'Stop' in opt_keys:
                        ap_name = 'Stop'
                    else:
                        self._log.err("Cannot pass 'Pixel Size**' as a "
                                      "parameter to vary when neither "
                                      "'Aperture' nor 'Lyot' nor 'Stop' "
                                      "is defined in the camera's optical "
                                      "chain")
                    ap = cam.opt_chn.opts[ap_name]
                    # Store current values for detector number, aperture
                    # efficiency, and pixel size
                    curr_pix_sz = ch.get_param('Pixel Size')
                    curr_ndet = ch.get_param('Num Det per Wafer',
                                             band_id=band_id)
                    curr_ap = ap.get_param('Absorption', band_id=band_id)
                    if curr_ap == 'NA':
                        curr_ap = None
                    # Calculate new values for detector number,
                    # aperture efficiency, and pixel size
                    new_pix_sz_mm = self.setArr[j][i]
                    new_pix_sz = un.Unit('mm')._to_SI(new_pix_sz_mm)
                    new_ndet = curr_ndet * np.power(
                        (curr_pix_sz / new_pix_sz), 2.)
                    if curr_ap is not None:
                        curr_eff = self._ph.spillEff(
                            freq, curr_pix_sz, fnum, w0)
                        new_eff = self._ph.spillEff(
                            freq, new_pix_sz, fnum, w0)
                        apAbs_new = 1. - (1. - curr_ap) * new_eff / curr_eff
                    else:
                        apAbs_new = 1. - self.__ph.spillEff(
                            freq, new_pix_sz, fnum, w0)
                    # Define new values
                    ch.change_param('Pixel Size', new_pix_sz_mm)
                    ch.change_param('Num Det per Wafer', new_ndet,
                                    band_id=band_id)
                    ap.change_param('Absorption', new_ap, band_id=band_id)
                    # Re-evaluate channel
                    ch.evaluate()

                # After new parameters are stored,
                # re-run sensitivity calculation
                self._sim.evaluate()
                # Store new sensitivity values
                self._out.append(self._sim.sns.sensitivity())

    def save_data(self):
        # Store raw data
        for out in self._out:

    
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
        fname  = os.path.join(self._exp.dir, self.savedir, ('%s_%s%s.txt' % (param_id, self.vary_id, self.paramString)))
        
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

    def _load_param_vary(self):
        self.log.log(
            "Loading parameters to vary from %s" % (
                os.path.join(os.path.dirname(sy.argv[0]),
                             'config', 'paramsToVary.txt')))
        convs = {i: str.strip() for i in range(8)}
        data = np.loadtxt(self._param_file, delimiter='|', dtype=str,
                          unpack=True, ndmin=2, converters=convs)
        self._tels, self._cams, self._chs, self._opts = data[:3]
        self._params, self._mins, self._maxs, self._stps = data[4:]

        # Special joint consideration of pixel size, spill efficiency,
        # and detector number
        if 'Pixel Size**' in self._params:
            if not np.any(np.isin(
                self._params, ['Waist Factor', 'Aperture', 'Lyot',
                              'Stop', 'Num Det per Wafer'])):
                self.pix_size_special = True
            else:
                self._log.err("Cannot pass 'Pixel Size**' as a parameter to "
                              "vary when 'Aperture', 'Lyot', 'Stop', or "
                              "'Num Det per Wafer' is also passed in %s"
                              % (self._param_file))
        else:
            self.pix_size_special = False
        
        #Check for consistency of number of parameters varied
        if len(set([len(self._tels), len(self._params),
                    len(self._mins), len(self._maxs), len(self._stps)])) == 1:
            self._num_params = len(self._params)
        else:
            self._log.err("Number of telescopes, parameters, mins, maxes, and "
                          "steps must match for parameters to be varied "
                          " in %s" % (self._param_file))
        return

    def _store_file_tag(self):
        # Input parameters ID
        if self._file_tag is not None:
            self._file_id = '_' + self._file_id.strip('_')
        else:
            self._file_id = ""
            for i in range(len(self._params)):
                if not self._tels[i] == '':
                    self._file_tag += ("_%s" % (self._tels[i]))
                if not self._cams[i] == '':
                    self._file_tag += ("_%s" % (self._cams[i]))
                if not self._chs[i] == '':
                    self._file_tag += ("_%s" % (self._chs[i]))
                if not self._opts[i] == '':
                    self._file_tag += ("_%s" % (self._opts[i]))
                if not self._params[i] == '':
                    self._file_tag += ("_%s" % (self._params[i]))
        return

    def _config_params(self):
        # Construct arrays of parameters
        param_arr = [np.arange(
            float(self._mins[i]), float(self._maxs[i])+float(self._stps[i]),
            float(self._stps[i])).tolist()
            for i in range(len(self._params))]
        self._num_params = len(param_arr)
        self._log.log("Processing %d parameters" % (self._num_params),
                      self._log.level["CRIT"])
        
        #Length of each parameter array
        len_arr = [len(param_arr[i]) for i in range(self._num_params)]

        #Store the telescope, camera, channels, and optic name information for each parameter
        tels_arr = [[self._tels[i]
                     for j in range(len_arr[i])]
                     for i in range(self._num_params)]
        cams_arr = [[self._cams[i]
                    for j in range(len_arr[i])]
                    for i in range(self._num_params)]
        chs_arr = [[self._chs[i]
                    for j in range(len_arr[i])]
                    for i in range(self._num_params)]
        opts_arr = [[self._opts[i]
                     for j in range(len_arr[i])]
                     for i in range(self._num_params)]
        
        if self._vary_tog:
            # Vary the parameters together. All arrays need to be the same length
            if not set(len_arr) == 1:
                self._log.err("To vary all parameters together, all parameter "
                              "arrays in '%s' must have the same length."
                              % (self._param_file))
            num_entries = len_arr[0]
            self.log.log("Processing %d combinations of parameters"
                         % (num_entries))
            self._tel_arr = np.array(tels_arr)
            self._cam_arr = np.array(cams_arr)
            self._ch_arr  = np.array(chs_arr)
            self._opt_arr = np.array(opts_arr)
            self._set_arr = np.array(param_arr)
        else:
            num_entries = np.prod(len_arr)
            self.log.log("Processing %d combinations of parameters"
                         % (num_entries))
            #In order to loop over all possible combinations
            # of the parameters, the arrays need to be rebuilt
            tel_arr = []
            cam_arr = []
            ch_arr  = []
            opt_arr = []
            set_arr = []
            #Construct one array for each parameter
            for i in range(self._num_params):
                #For storing names
                tel_arr_arr = []
                cam_arr_arr = []
                ch_arr_arr  = []
                opt_arr_arr = []
                #For storing values
                set_arr_arr = []
                #Number of values to be calculated for this parameter
                if i < self._num_params-1:
                    for j in range(len_arr[i]):
                        telArrArr += [tels_arr[i][j]]*np.prod(len_arr[i+1:])
                        camArrArr += [cams_arr[i][j]]*np.prod(len_arr[i+1:])
                        chArrArr  += [chs_arr[i][j]]*np.prod(len_arr[i+1:])
                        optArrArr += [opts_arr[i][j]]*np.prod(len_arr[i+1:])
                        setArrArr += [param_arr[i][j]]*np.prod(len_arr[i+1:])
                else:
                    tel_arr_arr += tels_arr[i]
                    cam_arr_arr += cams_arr[i]
                    ch_arr_arr  += chs_arr[i]
                    opt_arr_arr += opts_arr[i]
                    set_arr_arr += param_arr[i]
                if i > 0:
                    tel_arr.append(tel_arr_arr*np.prod(len_arr[:i]))
                    cam_arr.append(cam_arr_arr*np.prod(len_arr[:i]))
                    ch_arr.append(ch_arr_arr*np.prod(len_arr[:i]))
                    opt_arr.append(opt_arr_arr*np.prod(len_arr[:i]))
                    set_arr.append(set_arr_arr*np.prod(len_arr[:i]))
                else:
                    tel_arr.append(tel_arr_arr)
                    cam_arr.append(cam_arr_arr)
                    ch_arr.append(ch_arr_arr)
                    opt_arr.append(opt_arr_arr)
                    set_arr.append(set_arr_arr)
                    
            self._tel_arr = np.array(tel_arr)
            self._cam_arr = np.array(cam_arr)
            self._ch_arr = np.array(ch_arr)
            self._opt_arr = np.array(opt_arr)
            self._set_arr = np.array(set_arr)

    def _vary_depth(self, ind):
        if self.tels[ind] != '':
            if self.cams[ind] != '':
                if self.chs[ind] != '':
                    if self.opts[ind] != '':
                        return 'opt'
                    elif ('Pixel Size' in self._params[j] and
                          self._pix_size_special):
                        return 'pix'
                    else:
                        return 'ch'
                else:
                    return 'cam'
            else:
                return 'tel'
        else:
            return 'exp'
