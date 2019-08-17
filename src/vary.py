# Built-in modules
import numpy as np
import sys as sy
import os

# BoloCalc modules
import src.experiment as ex
import src.physics as ph
import src.unit as un


class Vary:
    def __init__(self, sim, param_file, vary_name, vary_tog=False):
        # Store passed parameters
        self._sim = sim
        self._sns = self._sim.sns
        self._exp = self._sim.exp
        self._log = self._sim.log
        self._ph = self._sim.phys
        self._param_file = param_file
        self._vary_name = vary_name
        self._vary_tog = vary_tog
        self._nexp = self._sim.param("nexp")

        # Load parameters to vary
        self._load_params()

        # Status bar length
        self._bar_len = 100

        # Scope (exp, tel, cam, or ch) of the parameter set
        self._scope = ''

        # Generate the output file tag
        # self._store_file_tag()

        # Configure parameter arrays
        # self._config_params()

    # **** Public Methods ****
    def vary(self):
        # Start by generating "fiducial" experiments
        tot_sims = (self._sim.param("nexp") * self._sim.param("ndet") *
                    self._sim.param("nobs"))
        self._log.out((
                "Simulting %d experiment realizations each with "
                "%d detector realizations and %d sky realizations.\n"
                "Total sims = %d"
                % (self._sim.param("nexp"), self._sim.param("ndet"),
                   self._sim.param("nobs"), tot_sims)))
        self._exps = []
        self._sens = []
        for n in range(self._nexp):
            self._status(n, self._nexp)
            exp = ex.Experiment(self._sim)
            exp.evaluate()
            sns = self._sim.sns.sensitivity(exp)
            self._exps.append(exp)
            self._sens.append(sns)
        self._done()

        # Loop over parameter set and adjustsensitivities
        adj_sns = []
        tot_adjs = self._nexp * len(self._set_arr)
        self._log.out((
                "Looping over %d parameter sets for %d realizations\n"
                "Total sims = %d"
                % (tot_sims, len(self._set_arr), tot_adjs)))
        for n, (exp, sens) in enumerate(zip(self._exps, self._sens)):
            adj_sns.append(self._vary_exp(exp, sens, n, tot_adjs))
        self._done()

        # Combine experiment realizations
        self.adj_sns = np.concatenate(adj_sns, axis=-1)
        return

    # ***** Helper Methods *****
    def _save(self):
        # Write parameter by parameter
        it = 0
        for i in range(len(sns_arr)):
            self._save_param_iter(i)
        return

    def _adjust_sens(self, exp, sns, tel=None, cam=None, ch=None):
        # Recalculate specific channel
        if tel is not None and cam is not None and ch is not None:
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            ch_ind = list(exp.tels[tel].cams[cam].chs.keys()).index(ch)
            channel = exp.tels[tel].cams[cam].chs[ch]
            sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                channel)
        # Re calculate specific camera
        elif tel is not None and cam is not None and ch is None:
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            for ch_ind, channel in exp.tels[tel].cams[cam].chs.items():
                sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                    channel)
        # Recalculate specific telescope
        elif tel is not None and cam is None and ch is None:
            tel_ind = list(exp.tels.keys()).index(tel)
            for cam_ind, camera in exp.tels[tel].cams.items():
                for ch_ind, channel in camera.chs.items():
                    sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                        channel)
        # Recalculate entire experiment
        else:
            for tel_ind, telescope in exp.tels.items():
                for cam_ind, camera in telescope.cams.items():
                    for ch_ind, channel in camera.chs.items():
                        sns[tel_ind][cam_ind][ch_ind] = (
                            self._sns.ch_sensitivity(channel))
        return sns

    def _vary_exp(self, exp, sns, n, ntot):
        # Sensitivity for every parameter combination
        sns_arr = []
        # Loop over long-form data
        for i in range(len(self._set_arr)):
            self._status((n * len(self._set_arr) + i), ntot)
            for j in range(len(self._set_arr[i])):
                vary_depth = self._vary_depth(j)
                # Change experiment parameter
                if vary_depth is 'exp':
                    exp.change_param(
                        self._params[j], self._set_arr[i][j])
                    exp.evaluate()
                    sns = self._adjust_sens(exp, sns)
                # Change telescope parameter
                elif vary_depth is 'tel':
                    tel = exp.tels[self._tels[j]]
                    tel.change_param(
                        self._params[j], self._set_arr[i][j])
                    tel.evaluate()
                    sns = self._adjust_sens(
                        exp, sns, tel=self._tels[j])
                # Change camera parameter
                elif vary_depth is 'cam':
                    tel = exp.tels[self._tels[j]]
                    cam = tel.cams[self._cams[j]]
                    cam.change_param(
                        self._params[j], self._set_arr[i][j])
                    cam.evalutate()
                    sns = self._adjust_sens(
                        exp, sns, tel=self._tels[j], cam=self._cams[j])
                # Change channel parameter
                elif vary_depth is 'ch':
                    tel = exp.tels[self._tels[j]]
                    cam = tel.cams[self._cams[j]]
                    ch = cam.chs[self._chs[j]]
                    ch.change_param(
                        self._params[j], self._set_arr[i][j])
                    ch.evaluate()
                    sns = self._adjust_sens(
                        exp, sns, tel=self._tels[j],
                        cam=self._cams[j], ch=self._chs[j])
                # Change optic parameter
                elif vary_depth is 'opt':
                    tel = exp.tels[self._tels[j]]
                    cam = tel.cams[self._cams[j]]
                    ch = cam.chs[self._chs[j]]
                    opt = cam.opt_chn.optics[self._opts[j]]
                    band_id = ch.param("band_id")
                    opt.change_param(
                        self._params[j], self._set_arr[i][j], band_id=band_id)
                    opt.evaluate(ch)
                    sns = self._adjust_sens(
                        exp, sns, tel=self._tels[j],
                        cam=self._cams[j], ch=self._chs[j])
                # Change the pixel size,
                # varying detector number also
                elif vary_depth is 'pix':
                    tel = exp.tels[self._tels[j]]
                    cam = tel.cams[self._cams[j]]
                    ch = cam.chs[self._chs[j]]
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
                    new_pix_sz_mm = self._set_arr[i][j]
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
                    sns = self._adjust_sens(
                        exp, sns, tel=self._tels[j],
                        cam=self._cams[j], ch=self._chs[j])

            # Store new sensitivity values
            sns_arr.append(sns)
        return sns_arr

    def _save_param_iter(self, it):
        sns = self.sns[it]
        # Write output files for every channel
        if self._scope is not 'exp':
            tel_names = set(self._tels)  # unique tel names
            tels = [self._exp.tels[tel_name]
                    for tel_name in tel_names]
            tel_inds = [self._exp.tels.keys().index(tel_name)
                        for tel_name in tel_names]
        else:  # Loop over all telescopes
            tel_names = self._exp.tels.keys()
            tels = self._exp.tels.values()
            tel_inds = range(len(tels))
        for i, tel in zip(tel_inds, tels):
            if (self._scope is 'cam' or self._scope is 'ch' or
               self._scope is 'pix'):
                valid_inds = np.where(self._tels == tel_name[i])
                cam_names = set(self._cams[valid_inds])  # unique cam names
                cams = [tel.cams[cam_name]
                        for cam_name in cam_names]
                cam_inds = [tel.cams.keys().index(cam_name)
                            for cam_name in cam_names]
            else:  # Loop over all cameras
                cam_names = tel.cams.keys()
                cams = tel.cams.values()
                cam_inds = range(len(cams))
            for j, cam in zip(cam_inds, cams):
                param_dir = self._check_dir(
                    os.path.join(dir_val, self._param_dir))
                vary_dir = os.path.join(param_dir, self._vary_id)
                if it == 0 and os.path.isdir(vary_dir):
                    self._log.log(
                        "Overwriting param vary data at '%s'" % (vary_dir))
                    os.rmdir(vary_dir)
                os.mkdir(vary_dir)
                if (self._scope is 'ch' or self._scope is 'pix'):
                    valid_inds = np.where(
                        self._tels == tel_name[i] and
                        self._cams == cam_name[j])
                    ch_names = set(self._cams[valid_inds])  # uniqee ch names
                    chs = [cam.chs[ch_name]
                           for ch_name in ch_names]
                    ch_inds = [cam.chs.keys().index(ch_name)
                               for ch_name in ch_names]
                else:  # Loop over all channels
                    ch_names = cam.chs.keys()
                    chs = cam.chs.values()
                    ch_inds = range(len(chs))
                for k, ch in zip(ch_inds, chs):
                    fch = os.path.join(
                        vary_dir, "param_vary_%s.txt" % (ch.param("ch_name")))
                    if not os.path.exists(fch):
                        self._init_vary_file(fch)
                    ch_dir = self._check_dir(
                        os.path.join(vary_dir, ch.param("ch_name")))
                    fout = os.path.join(ch_dir, "output_%03d.txt" % (it))
                    self._write_output(sns[i][j][k], fout)
                    self._write_vary_row(it, sns[i][j][k], fcam)
        return

    def _init_vary_file(self, fvary):
        # Add a left-most column for the parameter index
        # Build formatting string using efficient spacer
        fmt_str = ""
        fmt_unit = ""
        for spc in self._param_widths:
            fmt_str += "%" + str(int(spc)) + "s | "
            fmt_unit += "[%" + str(int(spc) - 2) + "s] | "
        ind_str = "%5s | " % ("")
        # Formatting strings to be used when writing
        self._fmt_str = replace(fmt_str, "s", ".3f")
        self._fmt_ind = " %03d  | "  # for writing index values
        print(fmt_str)
        with open(fvary, 'w') as f:
            f.write(ind_str + (fmt_str % (*self._tels,) + "\n"))
            f.write(ind_str + (fmt_str % (*self._cams,) + "\n"))
            f.write(ind_str + (fmt_str % (*self._chs,) + "\n"))
            f.write(ind_str + (fmt_str % (*self._opts,) + "\n"))
            f.write(ind_str + (fmt_str % (*self._params,) + "\n"))
            self._write_vary_header_params(f)
            f.write(("Index | " + (fmt_unit % (*self._units,) + "\n")))
            self._write_vary_header_units
            self._horiz_line(f)

    def _write_vary_header_params(self, f):
        title = ("%-23s | %-23s | %-23s | %-23s | "
                 "%-23s | %-23s | %-23s | %-23s | %-26s | %-26s | "
                 "%-23s | %-23s | %-23s | %-23s | %-23s\n"
                 % ("Optical Throughput", "Optical Power",
                    "Telescope Temp", "Sky Temp",
                    "Photon NEP", "Bolometer NEP", "Readout NEP",
                    "Detector NEP", "Detector NET",
                    "Detector NET_RJ",  "Array NET",
                    "Array NET_RJ", "Correlation Factor",
                    "CMB Map Depth", "RJ Map Depth"))
        f.write(title)
        return

    def _write_vary_header_units(self, f):
        unit = ("%-23s | %-23s | %-23s | %-23s | "
                "%-23s | %-23s | %-23s | %-23s | %-26s | %-26s | "
                "%-23s | %-23s | %-23s | %-23s | %-23s\n"
                % ("", "[pW]", "[K_RJ]", "[K_RJ]",
                   "[aW/rtHz]", "[aW/rtHz]", "[aW/rtHz]",
                   "[aW/rtHz]", "[uK_CMB-rts]", "[uK_RJ-rts]",
                   "[uK_CMB-rts]", "[uK_RJ-rts]", "",
                   "[uK_CMB-amin]", "[uK_RJ-amin]"))
        f.write(unit)
        return

    def _horiz_line(self, f):
        f.write(("-"*int(150 + sum(self._param_widths))+"\n"))
        return

    def _write_output(self, data, fout):
        with open(fout, 'w') as fwrite:
            tdata = np.transpose(data)
            for i in range(len(data)):  # params
                row = tdata[i]
                wrstr = ""
                for k in range(len(row)):
                    wrstr += ("%-9.4f " % (row[k]))
                fwrite.write(wrstr)
            fwrite.write("\n")
        return

    def _write_vary_row(self, it, data, fcam):
        with open(fcam, 'a') as f:
            f.write(self._fmt_ind % (int(it)))
            f.write(self._fmt_str % (*self._set_arr[i],))
            wstr = ("%-5.3f +/- (%-5.3f,%5.3f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-6.1f +/- (%-6.1f,%6.1f) | "
                    "%-6.1f +/- (%-6.2f,%6.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.3f,%5.3f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f)\n"
                    % (*self._spread(data[0]),
                       *self._spread(data[1], un.std_units["Popt"]),
                       *self._spread(data[2], un.std_units["Temperature"]),
                       *self._spread(data[3], un.std_units["Temperature"]),
                       *self._spread(data[4], un.std_units["NEP"]),
                       *self._spread(data[5], un.std_units["NEP"]),
                       *self._spread(data[6], un.std_units["NEP"]),
                       *self._spread(data[7], un.std_units["NEP"]),
                       *self._spread(data[8], un.std_units["NET"]),
                       *self._spread(data[9], un.std_units["NET"]),
                       *self._spread(data[10], un.std_units["NET"]),
                       *self._spread(data[11], un.std_units["NET"]),
                       *self._spread(data[12], un.std_units["Corr Fact"]),
                       *self._spread(data[13], un.std_units["Map Depth"]),
                       *self._spread(data[14], un.std_units["Map Depth"])))
            f.write(wstr)
        return

    def _check_dir(self, dir_val):
        if not os.path.isdir(param_dir):
            os.mkdir(param_dir)
        return param_dir

    def _status(self, n, ntot):
        frac = float(n)/float(ntot)
        sy.stdout.write('\r')
        sy.stdout.write("[%-*s] %02.1f%%" % (int(self._bar_len),
                        '=' * int(self._bar_len * frac), frac * 100.))
        sy.stdout.flush()

    def _done(self):
        """ Print filled status bar """
        sy.stdout.write('\r')
        sy.stdout.write(
            "[%-*s] %.1f%%" % (self._bar_len, '=' * self._bar_len, 100.))
        sy.stdout.write('\n')
        sy.stdout.flush()
        return

    def _horiz_line(self):
        return (('-' * (
            self.numParams * 15 + len(self.telNames) * 17 +
            (self.numParams - 1) * 3 + (len(self.telNames) - 1) * 3 + 5))+'\n')

    def _load_params(self):
        self._log.log(
            "Loading parameters to vary from %s" % (self._param_file))
        convs = {i: lambda s: s.strip() for i in range(8)}
        data = np.loadtxt(self._param_file, delimiter='|', dtype=str,
                          unpack=True, ndmin=2, converters=convs)
        self._tels, self._cams, self._chs, self._opts = data[:4]
        self._params, mins, maxs, stps = data[4:]
        self._units = [un.std_units[param].name
                       for param in self._params]
        # Array to manage table spacing - don't waste space!
        self._param_widths = [len(max(
            [self._tels[i], self._cams[i], self._chs[i],
             self._opts[i], self._params[i]], key=len))
            for i in range(len(self._params))]

        # Check for consistency of number of parameters varied
        if len(set([len(d) for d in data])) == 1:
            self._num_params = len(self._params)
        else:
            self._log.err("Number of telescopes, parameters, mins, maxes, and "
                          "steps must match for parameters to be varied "
                          " in %s" % (self._param_file))

        self._set_arr = self._wide_to_long([np.arange(
            float(mins[i]), float(maxs[i])+float(stps[i]),
            float(stps[i])).tolist()
            for i in range(self._num_params)])
        '''
        self._params = self._wide_to_long(
            [[params[i]
              for j in range(len(self._params[i]))]
             for i in range(len(self._params))])
        self._tels = self._wide_to_long(
            [[tels[i]
              for j in range(len(self._params[i]))]
             for i in range(len(self._params))])
        self._cams = self._wide_to_long(
            [[cams[i]
              for j in range(len(self._params[i]))]
             for i in range(len(self._params))])
        self.chs = self._wide_to_long(
            [[chs[i]
              for j in range(len(self._params[i]))]
             for i in range(len(self._params))])
        self._opts = self._wide_to_long(
            [[opts[i]
              for j in range(len(self._params[i]))]
             for i in range(len(self._params))])
        '''

        # Special joint consideration of pixel size, spill efficiency,
        # and detector number
        if 'Pixel Size**' in self._params:
            if not np.any(np.isin(
                self._params, ['Waist Factor', 'Aperture', 'Lyot',
                               'Stop', 'Num Det per Wafer'])):
                self.pix_size_special = True
            else:
                self._log.err("Cannot pass 'Pixel Size**' as a parameter to "
                              "'%s' when 'Aperture', 'Lyot', 'Stop', or "
                              "'Num Det per Wafer' is also passed"
                              % (self._param_file))
        else:
            self.pix_size_special = False
        return

    '''
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
    '''

    '''
    def _config_params(self):
        # Construct arrays of parameters
        param_arr = [np.arange(
            float(self._mins[i]), float(self._maxs[i])+float(self._stps[i]),
            float(self._stps[i])).tolist()
            for i in range(len(self._params))]
        self._log.log("Processing %d parameters" % (self._num_params),
                      self._log.level["CRIT"])
        # Length of each parameter array
        len_arr = [len(param_arr[i]) for i in range(self._num_params)]

        if self._vary_tog:
            # Vary the parameters together.
            # All arrays need to be the same length
            if not set(len_arr) == 1:
                self._log.err("To vary all parameters together, all parameter "
                              "arrays in '%s' must have the same length."
                              % (self._param_file))
            num_entries = len_arr[0]
            self.log.log("Processing %d combinations of parameters"
                         % (num_entries))
            self._tel_arr = self._parallel_labels(self._tels, len_arr)
            self._cam_arr = self._parallel_labels(self._cams, len_arr)
            self._ch_arr = self._parallel_labels(self._chs, len_arr)
            self._opt_arr = self._parallel_labels(self._opts, len_arr)
            self._prm_arr = self._parallel_labels(self._params, len_arr)
            self._set_arr = param_arr
        else:
            num_entries = np.prod(len_arr)
            self.log.log("Processing %d combinations of parameters"
                         % (num_entries))
            # In order to loop over all possible combinations
            # of the parameters, the arrays need to be stacked
            self._tel_arr = self._stacked_labels(self._tels, len_arr)
            self._cam_arr = self._stacked_labels(self._cams, len_arr)
            self._ch_arr = self._stacked_labels(self._chs, len_arr)
            self._opt_arr = self._stacked_labels(self._opts, len_arr)
            self._prm_arr = self._stacked_labels(self._params, len_arr)
            self._set_arr = self._stacked_params(param_arr, len_arr)
    '''

    def _vary_depth(self, ind):
        if self._tels[ind] != '':
            if (self._scope is '' or
               self._scope is 'ch' or
               self._scope is 'cam'):
                self._scope = 'tel'
            if self._cams[ind] != '':
                if (self._scope is '' or
                   self._scope is 'ch'):
                    self._scope = 'cam'
                if self._chs[ind] != '':
                    if self._scope is '':
                        self._scope = 'ch'
                    if self._opts[ind] != '':
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
            self._scope = 'exp'
            return 'exp'

    def _wide_to_long(self, inp_arr):
        len_arr = [len(inp) for inp in inp_arr]
        ret_arr = []
        for i in range(len(inp_arr)):
            inner_arr = []
            if i < len(inp_arr) - 1:
                for j in range(len_arr[i]):
                    inner_arr += (
                        [inp_arr[i][j]] * np.prod(len_arr[i+1:]))
            else:
                inner_arr += inp_arr[i]
            if i > 0:
                ret_arr.append(inner_arr * np.prod(len_arr[:i]))
            else:
                ret_arr.append(inner_arr)
        return np.transpose(ret_arr)

    def _spread(self, inp, unit=None):
        pct_lo, pct_hi = self._sim.param("pct")
        if unit is None:
            unit = un.Unit("NA")
        lo, med, hi = unit.from_SI(np.percentile(
            inp, (float(pct_lo), 0.50, float(pct_hi))))
        return [med, abs(hi-med), abs(med-lo)]
