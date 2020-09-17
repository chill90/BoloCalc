# Built-in modules
import numpy as np
import sys as sy
import copy as cp
import os

# BoloCalc modules
import src.experiment as ex
import src.unit as un


class Vary:
    """
    Vary object takes a simulation object, which has information about
    the experiment, and an input parameter vary file and calculates
    sensitivity for a user-defined set of parameters

    Args:
    sim (src.Simulation): parent Simulation object
    param_file (str): parameter vary input filename
    vary_name (str): name to which to save vary outputs
    vary_tog (bool): whether or not to vary input parameter arrays together

    Parents:
    sim (src.Simulation): parent Simulation object
    """
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
        self._units = self._sim.output_units
        self._nexp = self._sim.param("nexp")

        # Status bar length
        self._bar_len = 100

        # Scope (exp, tel, cam, or ch) of the parameter setx
        self._scope = ''
        self._scope_enums = {
            'exp': 3, 'tel': 2, 'cam': 1, 'ch': 0,
            'opt': 0, 'pix': 0}

        # Name of parameter vary directory
        self._param_dir = "paramVary"
        self._input_param_dir = os.path.split(self._param_file)[0]
        self._cust_dir = os.path.join(self._input_param_dir, "customVary")
        self._cust_str = "CUST"

        # Load parameters to vary
        self._load_params()

    # **** Public methods ****
    def vary(self):
        """ Run parmaeter vary simulation """
        # Start by generating "fiducial" experiments
        tot_sims = (self._sim.param("nexp") * self._sim.param("ndet") *
                    self._sim.param("nobs"))
        self._log.out((
                "Simulting %d experiment realizations each with "
                "%d detector realizations and %d sky realizations. "
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

        # Loop over parameter set and adjust sensitivities
        adj_sns = []
        tot_adjs = self._nexp * len(self._set_arr)
        self._log.out((
                "Looping over %d parameter sets for %d realizations. "
                "Number of experiment realizations to adjust = %d"
                % (len(self._set_arr), self._sim.param("nexp"),
                   tot_adjs)))
        for n, (exp, sens) in enumerate(zip(self._exps, self._sens)):
            adj_sns.append(self._vary_exp(exp, sens, n, tot_adjs))
        self._done()

        # Combine and save experiment realizations
        self.adj_sns = np.concatenate(adj_sns, axis=-1)
        self._save()
        return

    # ***** Helper methods *****
    def _save(self):
        """ Save simulation outputs to files """
        # Write parameter by parameter
        tot_writes = len(self.adj_sns)
        self._log.out((
                "Writing outputs for %d parameters" % (tot_writes)))
        for i in range(tot_writes):
            self._status(i, tot_writes)
            self._save_param_iter(i)
        self._done()
        return

    def _adjust_sens(self, exp, sns, tel='', cam='', ch='', opt=''):
        """ Calculate new sensitivity array where needed """
        tel = self._cap(tel)
        cam = self._cap(cam)
        ch = self._cap(ch)
        opt = self._cap(opt)
        # Change channel parameter
        if str(tel) != '' and str(cam) != '' and str(ch) != '':
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            ch_ind = list(exp.tels[tel].cams[cam].chs.keys()).index(ch)
            channel = exp.tels[tel].cams[cam].chs[ch]
            channel.evaluate()
            sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                channel)
        # Change optics parameter for both channels
        elif (str(tel) != '' and str(cam) != '' and
              str(ch) == '' and str(opt) != ''):
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            # Evaluate all channels in this camera
            for ch in exp.tels[tel].cams[cam].chs:
                ch_ind = list(exp.tels[tel].cams[cam].chs.keys()).index(ch)
                channel = exp.tels[tel].cams[cam].chs[ch]
                channel.evaluate()
                sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                    channel)
        # Change camera parameter
        elif str(tel) != '' and str(cam) != '':
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            # Evaluate camera
            exp.tels[tel].cams[cam].evaluate()
            # Store new sensitivity values
            for ch_ind, channel in enumerate(
               exp.tels[tel].cams[cam].chs.values()):
                # channel.evaluate()
                sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                    channel)
        # Change telescope parameter
        elif str(tel) != '':
            tel_ind = list(exp.tels.keys()).index(tel)
            # Evaluate telescope
            exp.tels[tel].evaluate()
            for cam_ind, camera in enumerate(
               exp.tels[tel].cams.values()):
                for ch_ind, channel in enumerate(
                   camera.chs.values()):
                    # channel.evaluate()
                    sns[tel_ind][cam_ind][ch_ind] = (
                        self._sns.ch_sensitivity(channel))
        # Change experiment parameter
        else:
            for tel_ind, telescope in enumerate(
               exp.tels.values()):
                for cam_ind, camera in enumerate(
                   telescope.cams.values()):
                    for ch_ind, channel in enumerate(
                       camera.chs.values()):
                        channel.evaluate()
                        sns[tel_ind][cam_ind][ch_ind] = (
                            self._sns.ch_sensitivity(channel))
        return cp.deepcopy(sns)

    def _set_new_pix_sz(self, cam, ch, tup):
        """ Set new pixel size for given camera and channel """
        i = tup[0]
        j = tup[1]
        # Check that the f-number is defined
        f_num = cam.get_param('fnum')
        if str(f_num) == 'NA':
            self._log.err("Cannot set 'Pixel Size**' as a "
                          "parameter to vary without 'F Number' "
                          "also defined for this camera")
        # Check that the band center is defined
        bc = ch.get_param('bc')
        if str(bc) == 'NA':
            self._log.err("Cannot set 'Pixel Size**' as a "
                          "parameter to vary without "
                          "'Band Center' also defined for this "
                          "channel")
        # Check that the waist factor is defined
        wf = ch.get_param('wf')
        if str(wf) == 'NA':
            self._log.err("Cannot set 'Pixel Size**' as a "
                          "parameter to vary without "
                          "'Waist Factor' also defined for this "
                          "channel")
        # Check that the aperture defined
        opt_keys = list(cam.opt_chn.optics.keys())
        # opt_keys_upper = [opt.replace(" ", "").upper() for opt in opt_keys]
        if 'APERTURE' in opt_keys:
            ap_name = 'APERTURE'
        elif 'LYOT' in opt_keys:
            ap_name = 'LYOT'
        elif 'STOP' in opt_keys:
            ap_name = 'STOP'
        else:
            self._log.err("Cannot pass 'Pixel Size**' as a "
                          "parameter to vary when neither "
                          "'Aperture' nor 'Lyot' nor 'Stop' "
                          "is defined in the camera's optical "
                          "chain")
        ap = cam.opt_chn.optics[ap_name]
        # Store current values for detector number, aperture
        # efficiency, and pixel size
        curr_pix_sz = ch.get_param('pix_sz')
        curr_ndet = ch.get_param('det_per_waf')
        curr_ap = ap.get_param(
            'abs', band_ind=ch.band_ind)  # median value
        if curr_ap == 'NA':
            curr_ap = None
        # Calculate new values for detector number,
        # aperture efficiency, and pixel size
        new_pix_sz_mm = self._set_arr[i][j]
        new_pix_sz = un.Unit('mm').to_SI(new_pix_sz_mm)
        new_ndet = curr_ndet * np.power(
            (curr_pix_sz / new_pix_sz), 2.)
        if curr_ap is not None:  # scale the median value
            curr_eff = self._ph.spill_eff(
                bc, curr_pix_sz, f_num, wf)
            new_eff = self._ph.spill_eff(
                bc, new_pix_sz, f_num, wf)
            apAbs_new = 1. - (1. - curr_ap) * np.mean(new_eff / curr_eff)
        else:  # use band-averaged value
            apAbs_new = 1. - self._ph.spill_eff(
                bc, new_pix_sz, f_num, wf)
        # Define new values
        changed = []
        changed.append(ch.change_param(
            'pix_sz', new_pix_sz_mm))
        changed.append(ch.change_param(
            'det_per_waf', new_ndet))
        changed.append(ap.change_param(
            'abs', apAbs_new,
            band_ind=ch.band_ind, num_bands=len(ch.cam.chs)))
        return np.any(changed)

    def _set_new_param(self, exp, tup):
        """ Set new parameter value for given experiment """
        i = tup[0]
        j = tup[1]
        scope = self._vary_scope(j)
        # Change experiment parameter
        if str(scope) == 'exp':
            changed = exp.change_param(
                self._params[j], self._set_arr[i][j])
        # Change telescope parameter
        elif str(scope) == 'tel':
            tel = exp.tels[self._cap(self._tels[j])]
            changed = tel.change_param(
                self._params[j], self._set_arr[i][j])
        # Change camera parameter
        elif str(scope) == 'cam':
            tel = exp.tels[self._cap(self._tels[j])]
            cam = tel.cams[self._cap(self._cams[j])]
            changed = cam.change_param(
                self._params[j], self._set_arr[i][j])
        # Change channel parameter
        elif str(scope) == 'ch':
            tel = exp.tels[self._cap(self._tels[j])]
            cam = tel.cams[self._cap(self._cams[j])]
            ch = cam.chs[self._cap(self._chs[j])]
            changed = ch.change_param(
                self._params[j], self._set_arr[i][j])
        # Change optic parameter
        elif str(scope) == 'opt':
            tel = exp.tels[self._cap(self._tels[j])]
            cam = tel.cams[self._cap(self._cams[j])]
            opt = cam.opt_chn.optics[self._cap(self._opts[j])]
            if self._chs[j] != '':
                ch = cam.chs[self._cap(self._chs[j])]
                changed = opt.change_param(
                    self._params[j], self._set_arr[i][j],
                    band_ind=ch.band_ind,
                    num_bands=len(cam.chs))
            else:
                changed = opt.change_param(
                    self._params[j], self._set_arr[i][j],
                    band_ind=None,
                    num_bands=len(cam.chs))
        # Change the pixel size,
        # varying detector number also
        elif str(scope) == 'pix':
            tel = exp.tels[self._cap(self._tels[j])]
            cam = tel.cams[self._cap(self._cams[j])]
            ch = cam.chs[self._cap(self._chs[j])]
            changed = self._set_new_pix_sz(cam, ch, (i, j))
        return changed

    def _vary_exp(self, exp, sns, n, ntot):
        """ Set new parameter combinations for defined experiment """
        # Sensitivity for every parameter combination
        sns_arr = []
        # Loop over long-form data
        for i in range(len(self._set_arr)):
            self._status((n * len(self._set_arr) + i), ntot)
            changes = []
            # First adjust parameters
            for j in range(len(self._set_arr[i])):
                changed = self._set_new_param(exp, (i, j))
                changes.append(changed)
            # Where changes happened
            changed_args = np.argwhere(changes).flatten()
            chg_tels = self._tels[changed_args]
            chg_cams = self._cams[changed_args]
            chg_chs = self._chs[changed_args]
            chg_opts = self._opts[changed_args]
            # Only account for unique changes
            chgs = np.array([chg_tels, chg_cams, chg_chs, chg_opts]).T
            # If no changes occurred, move to the next parameter step
            if len(chgs) == 0:
                sns_arr.append(cp.deepcopy(sns))
                continue
            unique_chgs = np.unique(chgs, axis=0)
            # Store new sensitivity values
            for unique_chg in unique_chgs:
                out_sns = self._adjust_sens(exp, sns, *unique_chg)
            sns_arr.append(out_sns)
        return sns_arr

    def _save_param_iter(self, it):
        """ Save sensitiviy for this parameter iteration """
        exp = self._exps[0]  # Just for retrieving names
        sns = self.adj_sns[it]
        # Write output files for every channel
        if str(self._scope) != 'exp':  # Overall scope of vary
            tel_names = list(set(self._tels))  # unique tels
            tels = [exp.tels[self._cap(tel_name)]
                    for tel_name in tel_names]
            tel_inds = [list(exp.tels.keys()).index(self._cap(tel_name))
                        for tel_name in tel_names]
            tel_iter = range(len(tels))
        else:  # Loop over all telescopes
            tel_names = list(exp.tels.keys())
            tels = exp.tels.values()
            tel_inds = range(len(tels))
            tel_iter = tel_inds
        for i, tel, a in zip(tel_inds, tels, tel_iter):
            if (str(self._scope) == 'cam' or str(self._scope) == 'ch'):
                valid_inds = np.argwhere(
                    self._tels == tel_names[a]).flatten()
                cam_names = list(set(self._cams[valid_inds]))
                cams = [tel.cams[self._cap(cam_name)]
                        for cam_name in cam_names]
                cam_inds = [list(tel.cams.keys()).index(self._cap(cam_name))
                            for cam_name in cam_names]
                cam_iter = range(len(cams))
            else:  # Loop over all cameras
                cam_names = list(tel.cams.keys())
                cams = list(tel.cams.values())
                cam_inds = range(len(cams))
                cam_iter = cam_inds
            for j, cam, b in zip(cam_inds, cams, cam_iter):
                param_dir = self._check_dir(
                    os.path.join(cam.dir, self._param_dir))
                vary_dir = os.path.join(param_dir, self._vary_name)
                if it == 0:
                    if not os.path.isdir(vary_dir):
                        os.mkdir(vary_dir)
                if (str(self._scope) == 'ch' or str(self._scope) == 'pix'):
                    valid_inds = np.argwhere(
                        (self._tels == tel_names[a]) *
                        (self._cams == cam_names[b])).flatten()
                    ch_names = list(set(self._chs[valid_inds]))  # uniqee chs
                    chs = [cam.chs[self._cap(ch_name)]
                           for ch_name in ch_names]
                    ch_inds = [list(cam.chs.keys()).index(self._cap(ch_name))
                               for ch_name in ch_names]
                else:  # Loop over all channels
                    ch_names = list(cam.chs.keys())
                    chs = cam.chs.values()
                    ch_inds = range(len(chs))
                for k, ch in zip(ch_inds, chs):
                    fch = os.path.join(
                        vary_dir, "%s.txt" % (ch.param("ch_name")))
                    if it == 0:
                        self._init_vary_file(fch)
                    ch_dir = self._check_dir(
                        os.path.join(vary_dir, ch.param("ch_name")))
                    fout = os.path.join(ch_dir, "output_%03d.txt" % (it))
                    # Convert from SI
                    sns_in = [list(
                        self._units.values())[m].from_SI(
                        np.array(sns[i][j][k][m]))
                        for m in range(len(sns[i][j][k]))]
                    # Write to files
                    self._write_output(sns_in, fout)
                    self._write_vary_row(it, sns_in, fch)
        return

    def _init_vary_file(self, fvary):
        """ Initiate and format the output file """
        # Add a left-most column for the parameter index
        # Build formatting string using efficient spacer
        fmt_str = ""
        fmt_unit = ""
        for spc in self._param_widths:
            fmt_str += "%-" + str(int(spc)) + "s | "
            fmt_unit += "%-" + str(int(spc)) + "s | "
        ind_str = "%5s | " % ("")
        # Formatting strings to be used when writing
        self._fmt_str = fmt_str.replace("s", ".3f")
        self._fmt_ind = " %03d  | "  # for writing index values
        with open(fvary, 'w') as f:
            f.write(ind_str + (fmt_str % (*self._tels,) + "\n"))
            f.write(ind_str + (fmt_str % (*self._cams,) + "\n"))
            f.write(ind_str + (fmt_str % (*self._chs,) + "\n"))
            f.write(ind_str + (fmt_str % (*self._opts,) + "\n"))
            f.write(ind_str + (fmt_str % (*self._params,)))
            self._write_vary_header_params(f)
            f.write(("Index | " + (fmt_unit % (*self._unit_strs,))))
            self._write_vary_header_units(f)
            self._horiz_line(f)
        return

    def _write_vary_header_params(self, f):
        """ Write header for vary params output file """
        title = ("%-23s | %-23s | %-23s | %-23s | "
                 "%-23s | %-23s | %-23s | %-23s | %-26s | %-26s | "
                 "%-23s | %-23s | %-23s | %-23s | %-23s\n"
                 % ("Optical Throughput", "Optical Power",
                    "Telescope Temp", "Sky Temp",
                    "Photon NEP", "Bolometer NEP", "Readout NEP",
                    "Detector NEP", "Detector NET_CMB",
                    "Detector NET_RJ",  "Array NET_CMB",
                    "Array NET_RJ", "Correlation Factor",
                    "CMB Map Depth", "RJ Map Depth"))
        f.write(title)
        return

    def _write_vary_header_units(self, f):
        """ Write header units for output vary file """
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
        """ Draw a horizontal line in the output file """
        width = int(405 + sum(self._param_widths) + len(self._params))
        f.write(("-" * width + "\n"))
        return

    def _write_output(self, data, fout):
        """ Write formatted output to output file """
        with open(fout, 'w') as fwrite:
            data_write = np.transpose(data)
            for row in data_write:  # params
                wrstr = ""
                for val in row:
                    wrstr += ("%-9.4f " % (val))
                fwrite.write(wrstr)
                fwrite.write("\n")
        return

    def _write_vary_row(self, it, data, fch):
        """ Write row of data to the output file """
        with open(fch, 'a') as f:
            f.write(self._fmt_ind % (int(it)))
            f.write(self._fmt_str % (*self._set_arr[it],))
            spreads = [self._spread(dat) for dat in data]
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
                    % (*np.array(spreads).flatten(),))
            f.write(wstr)
        return

    def _check_dir(self, dir_val):
        """ Check that the output directory exists, or make it """
        if not os.path.isdir(dir_val):
            os.mkdir(dir_val)
        return dir_val

    def _status(self, n, ntot):
        """ Print status bar """
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

    def _load_params(self):
        """ Load parameters to vary from input file """
        self._log.log(
            "Loading parameters to vary from %s" % (self._param_file))
        # Converted loaded paraemters to strings with whitespace stripped
        convs = {i: lambda s: s.strip() for i in range(8)}
        # Load data from vary file
        data = np.loadtxt(self._param_file, delimiter='|', dtype=str,
                          unpack=True, ndmin=2, converters=convs)
        # Skip the first line if it wasn't commented out
        if data[5][0].upper() == "MINIMUM":
            data = [d[1:] for d in data]
        self._tels, self._cams, self._chs, self._opts = data[:4]
        self._params, mins, maxs, stps = data[4:]
        params_upper = [param.replace(" ", "").strip().upper()
                        for param in self._params]
        # Store the units associated with the loaded parameters
        self._unit_strs = ["[" + self._sim.std_params[
            param.replace(" ", "").upper()].unit.name + "]"
            for param in self._params]
        # Array to manage table spacing - don't waste space!
        param_widths = [len(max(
            [self._tels[i], self._cams[i], self._chs[i],
             self._opts[i], self._params[i]], key=len))
            for i in range(len(self._params))]
        self._param_widths = [width if width > 10 else 10
                              for width in param_widths]
        # Check for consistency of number of parameters varied
        if len(set([len(d) for d in data])) == 1:
            self._num_params = len(self._params)
        else:
            self._log.err("Number of telescopes, parameters, mins, maxes, and "
                          "steps must match for parameters to be varied "
                          "in %s" % (self._param_file))
        # Check if any parameters use custom-defined inputs
        min_empty = (np.char.upper(mins) == self._cust_str)
        max_empty = (np.char.upper(maxs) == self._cust_str)
        stp_empty = (np.char.upper(stps) == self._cust_str)
        if np.any(min_empty) or np.any(max_empty) or np.any(stp_empty):
            if not np.any(np.logical_and(
               np.logical_and(min_empty, max_empty),
               np.logical_and(max_empty, stp_empty))):
                self._log.err(
                    "Either all of or none of (min, max, step) must be "
                    "defined as 'CUST' for each parameter to be varied "
                    "in %s" % (self._param_file))
            else:
                cust_inds = min_empty
        else:
            cust_inds = None
        # If min, max, and step is not defined, check for a custom file
        cust_params = [[] for n in range(self._num_params)]
        if cust_inds is not None:
            existing_files = os.listdir(self._cust_dir)
            existing_files_upper = np.char.upper(existing_files)
            cust_labels = np.array(
                [self._tels[cust_inds], self._cams[cust_inds],
                 self._chs[cust_inds], self._opts[cust_inds],
                 self._params[cust_inds]]).T
            for ii, cust_label in enumerate(cust_labels):
                lab_arr = [("%s" % (lab)).replace(" ", "").strip()
                           for lab in cust_label if lab != ""]
                fname = "%s.txt" % ("_".join(lab_arr))
                fname_upper = fname.upper()
                select_ind = np.argwhere(
                    fname_upper == existing_files_upper).flatten()
                if len(select_ind) == 1:
                    fload = np.take(existing_files, select_ind)[0]
                    fload_path = os.path.join(self._cust_dir, fload)
                    cust_param_arr = np.loadtxt(
                        fload_path, unpack=True, dtype=np.float)
                    cust_params[ii] = cust_param_arr.tolist()
                elif len(select_ind) > 1:
                    self._log.err("Duplicate custom parameter vary file %s detected"
                                  % (existing_files[select_ind].flatten()[0]))
                else:
                    fload = os.path.join(self._cust_dir, fname)
                    self._log.err("Could not locate custom parameter vary file %s"
                                  % (fload))
        # Store the parameter arrays
        set_arr = []
        for ii in range(self._num_params):
            min_val = mins[ii]
            max_val = maxs[ii]
            stp_val = stps[ii]
            if min_val.upper() == self._cust_str:
                set_arr.append(cust_params[ii])
            elif (float(max_val) - float(min_val)) < float(stp_val):
                self._log.err(
                    "Step value cannot be larger than max value minus min "
                    "value for parameters to be varied in %s"
                    % (self._param_file))
            else:
                set_arr.append(np.arange(
                    float(min_val), float(max_val)+float(stp_val),
                    float(stp_val)).tolist())

        # If vary together flag is set, move the parameters together
        # Transpose parameter arrays from wide-form to long-form
        if self._vary_tog:
            # Check that the parameter arrays are the same length
            arr_lens = [len(arr) for arr in set_arr]
            if not len(set(arr_lens)) == 1:
                self._log.err(
                    "Cannot vary parameters in '%s' together because array "
                    "because array lengths are different" % (self._param_file))
            self._set_arr = np.array(set_arr).T
        else:
            self._set_arr = self._wide_to_long(set_arr)

        # Special joint consideration of pixel size, spill efficiency,
        # and detector number
        if 'PIXELSIZE**' in params_upper:
            if not np.any(np.isin(
                params_upper, ['WAISTFACTOR', 'APERTURE', 'LYOT',
                               'STOP', 'NUMDETPERWAFER'])):
                self._pix_size_special = True
            else:
                self._log.err("Cannot pass 'Pixel Size**' as a parameter to "
                              "'%s' when 'Aperture', 'Lyot', 'Stop', or "
                              "'Num Det per Wafer' is also passed"
                              % (self._param_file))
        else:
            self._pix_size_special = False
        return

    def _vary_scope(self, ind):
        """ Find scope of the parameter vary """
        scope = ''
        ret_val = ''
        if self._tels[ind] != '':
            scope = 'tel'
            if self._cams[ind] != '':
                scope = 'cam'
                if str(self._chs[ind]) != '':
                    scope = 'ch'
                    if self._opts[ind] != '':
                        ret_val = 'opt'
                    elif ('PIXELSIZE' in
                          self._params[ind].replace(" ", "").upper() and
                          self._pix_size_special):
                        ret_val = 'pix'
                    else:
                        ret_val = 'ch'
                else:
                    if self._opts[ind] != '':
                        ret_val = 'opt'
                    else:
                        ret_val = 'cam'
            else:
                ret_val = 'tel'
        else:
            scope = 'exp'
            ret_val = 'exp'
        # Set a new global scope
        if scope == 'exp':
            self._scope == 'exp'
        elif (scope == 'tel' and (
             self._scope == '' or self._scope == 'cam' or 
             self._scope == 'ch')):
            self._scope = 'tel'
        elif (scope == 'cam' and (
             self._scope == '' or self._scope == 'ch')):
            self._scope = 'cam'
        elif (scope == 'ch' and self._scope == ''):
            self._scope = 'ch'
        else:
            pass
        # Return scope for this parameter
        return ret_val

    def _wide_to_long(self, inp_arr):
        """ Convert wide-form data to long-form data """
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
        """ Calculate parameter output distribution spread """
        pct_lo, pct_hi = self._sim.param("pct")
        if unit is None:
            unit = un.Unit("NA")
        lo, med, hi = unit.from_SI(np.percentile(
            inp, (float(pct_lo), 50.0, float(pct_hi))))
        return [med, abs(hi-med), abs(med-lo)]

    def _cap(self, inp):
        """ Captialize a string and strip spaces """
        return str(inp).replace(" ", "").strip().upper()
