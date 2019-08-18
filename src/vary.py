# Built-in modules
import numpy as np
import sys as sy
import os
import copy as cp

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
        self._scope_enums = {
            'exp': 3, 'tel': 2, 'cam': 1, 'ch': 0,
            'opt': 0, 'pix': 0}

        # Name of parameter vary directory
        self._param_dir = "paramVary"

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

        # Loop over parameter set and adjust sensitivities
        adj_sns = []
        tot_adjs = self._nexp * len(self._set_arr)
        self._log.out((
                "Looping over %d parameter sets for %d realizations\n"
                "Total sims = %d"
                % (len(self._set_arr), tot_sims, tot_adjs)))
        for n, (exp, sens) in enumerate(zip(self._exps, self._sens)):
            adj_sns.append(self._vary_exp(exp, sens, n, tot_adjs))
        self._done()

        # Combine and save experiment realizations
        self.adj_sns = np.concatenate(adj_sns, axis=-1)
        self._save()
        return

    # ***** Helper Methods *****
    def _save(self):
        # Write parameter by parameter
        tot_writes = len(self.adj_sns)
        self._log.out((
                "Writing outputs for %d parameters" % (tot_writes)))
        for i in range(tot_writes):
            self._status(i, tot_writes)
            self._save_param_iter(i)
        self._done()
        return

    def _adjust_sens(self, arg, vary_scope, exp, sns):
        j = arg
        ret_sns = cp.deepcopy(sns)
        # Change experiment parameter
        if vary_scope is 'exp':
            for tel_ind, telescope in exp.tels.items():
                for cam_ind, camera in telescope.cams.items():
                    for ch_ind, channel in camera.chs.items():
                        channel.evaluate()
                        ret_sns[tel_ind][cam_ind][ch_ind] = (
                            self._sns.ch_sensitivity(channel))
        elif vary_scope is 'tel':
            tel = self._tels[j]
            tel_ind = list(exp.tels.keys()).index(tel)
            for cam_ind, camera in exp.tels[tel].cams.items():
                for ch_ind, channel in camera.chs.items():
                    channel.evaluate()
                    ret_sns[tel_ind][cam_ind][ch_ind] = (
                        self._sns.ch_sensitivity(channel))
        elif vary_scope is 'cam':
            tel = self._tels[j]
            cam = self._cams[j]
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            for ch_ind, channel in exp.tels[tel].cams[cam].chs.items():
                channel.evaluate()
                ret_sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                    channel)
        elif vary_scope is 'ch':
            tel = self._tels[j]
            cam = self._cams[j]
            ch = self._chs[j]
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            ch_ind = list(exp.tels[tel].cams[cam].chs.keys()).index(ch)
            channel = exp.tels[tel].cams[cam].chs[ch]
            channel.evaluate()
            ret_sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                channel)
        return ret_sns

        '''
        # Change telescope parameter
        elif vary_scope is 'tel':
            tel = exp.tels[self._tels[j]]
            changed = tel.change_param(
                self._params[j], self._set_arr[i][j])
        # Change camera parameter
        elif vary_scope is 'cam':
            tel = exp.tels[self._tels[j]]
            cam = tel.cams[self._cams[j]]
            changed = cam.change_param(
                self._params[j], self._set_arr[i][j])
        # Change channel parameter
        elif vary_scope is 'ch':
            tel = exp.tels[self._tels[j]]
            cam = tel.cams[self._cams[j]]
            ch = cam.chs[self._chs[j]]
            changed = ch.change_param(
                self._params[j], self._set_arr[i][j])
        # Change optic parameter
        elif vary_scope is 'opt':
            tel = exp.tels[self._tels[j]]
            cam = tel.cams[self._cams[j]]
            ch = cam.chs[self._chs[j]]
            opt = cam.opt_chn.optics[self._opts[j]]
            band_id = ch.param("band_id")
            changed = opt.change_param(
                self._params[j], self._set_arr[i][j], band_id=band_id)
        # Change the pixel size,
        # varying detector number also
        elif vary_scope is 'pix':
            tel = exp.tels[self._tels[j]]
            cam = tel.cams[self._cams[j]]
            ch = cam.chs[self._chs[j]]
            changed = self._set_new_pix_sz(cam, ch, (i,j))
        return changed
        # Recalculate specific channel
        if vary_scope is 'ch':
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            ch_ind = list(exp.tels[tel].cams[cam].chs.keys()).index(ch)
            channel = exp.tels[tel].cams[cam].chs[ch]
            sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                channel)
        # Re calculate specific camera
        elif vary_scope is 'cam':
            tel_ind = list(exp.tels.keys()).index(tel)
            cam_ind = list(exp.tels[tel].cams.keys()).index(cam)
            for ch_ind, channel in exp.tels[tel].cams[cam].chs.items():
                sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                    channel)
        # Recalculate specific telescope
        elif vary_scope is 'tel':
            tel_ind = list(exp.tels.keys()).index(tel)
            for cam_ind, camera in exp.tels[tel].cams.items():
                for ch_ind, channel in camera.chs.items():
                    sns[tel_ind][cam_ind][ch_ind] = self._sns.ch_sensitivity(
                        channel)
        # Recalculate entire experiment
        elif vary_scope is 'exp':
            for tel_ind, telescope in exp.tels.items():
                for cam_ind, camera in telescope.cams.items():
                    for ch_ind, channel in camera.chs.items():
                        sns[tel_ind][cam_ind][ch_ind] = (
                            self._sns.ch_sensitivity(channel))
        else:
            print("something bad...")

        return sns
        '''

    def _set_new_pix_sz(self, cam, ch, tup):
        i = tup[0]
        j = tup[1]
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
        opt_keys = list(cam.opt_chn.opts.keys())
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
        changed = []
        changed.append(
            ch.change_param('Pixel Size', new_pix_sz_mm))
        changed.append(ch.change_param(
            'Num Det per Wafer', new_ndet, band_id=band_id))
        changed.append(ap.change_param(
            'Absorption', new_ap, band_id=band_id))
        return np.any(changed)

    def _set_new_param(self, exp, tup, vary_scope):
        i = tup[0]
        j = tup[1]
        # Change experiment parameter
        if vary_scope is 'exp':
            changed = exp.change_param(
                self._params[j], self._set_arr[i][j])
        # Change telescope parameter
        elif vary_scope is 'tel':
            tel = exp.tels[self._tels[j]]
            changed = tel.change_param(
                self._params[j], self._set_arr[i][j])
        # Change camera parameter
        elif vary_scope is 'cam':
            tel = exp.tels[self._tels[j]]
            cam = tel.cams[self._cams[j]]
            changed = cam.change_param(
                self._params[j], self._set_arr[i][j])
        # Change channel parameter
        elif vary_scope is 'ch':
            tel = exp.tels[self._tels[j]]
            cam = tel.cams[self._cams[j]]
            ch = cam.chs[self._chs[j]]
            changed = ch.change_param(
                self._params[j], self._set_arr[i][j])
        # Change optic parameter
        elif vary_scope is 'opt':
            tel = exp.tels[self._tels[j]]
            cam = tel.cams[self._cams[j]]
            ch = cam.chs[self._chs[j]]
            opt = cam.opt_chn.optics[self._opts[j]]
            band_id = ch.param("band_id")
            changed = opt.change_param(
                self._params[j], self._set_arr[i][j], band_id=band_id)
        # Change the pixel size,
        # varying detector number also
        elif vary_scope is 'pix':
            tel = exp.tels[self._tels[j]]
            cam = tel.cams[self._cams[j]]
            ch = cam.chs[self._chs[j]]
            changed = self._set_new_pix_sz(cam, ch, (i, j))
        return changed

    def _vary_exp(self, exp, sns, n, ntot):
        # Sensitivity for every parameter combination
        sns_arr = []
        # Loop over long-form data
        for i in range(len(self._set_arr)):
            self._status((n * len(self._set_arr) + i), ntot)
            changes = []
            scopes = []
            # First adjust parameters
            for j in range(len(self._set_arr[i])):
                vary_scope = self._vary_scope(j)
                scopes.append(self._scope_enums[vary_scope])
                changed = self._set_new_param(exp, (i, j), vary_scope)
                # if changed:
                #    print(vary_scope)
                #    print(self._set_arr[i][j])
                changes.append(changed)
            # Then recalculate only where needed
            changed_args = np.argwhere(changes).flatten()
            scope_arg = np.argmax(np.array(scopes)[changes])
            arg = changed_args[scope_arg]
            vary_scope = scopes[arg]
            vary_scope = list(self._scope_enums.keys())[list(
                    self._scope_enums.values()).index(vary_scope)]
            out_sns = self._adjust_sens(arg, vary_scope, exp, sns)
            print(sns[0][0][0][1])
            print(out_sns[0][0][0][1])
            print("same output?", out_sns == sns)
            '''
            for j in changed_params:
                if changes[j]:
            changed_scopes = np.array(scopes)[changes]
            if len(changed_scopes) != 0:
                scope = np.amax(changed_scope)
                vary_scope = self._scope_enums.keys()[list(
                    self.scope_enums.values()).index(scope)]




            for j in range(len(self._set_arr[i])):
                if changes[i]:
                    vary_scope = self._vary_scope(j)

                self._set_new_param(vary_scope)
                # Change experiment parameter
                if vary_scope is 'exp':
                    changed = exp.change_param(
                        self._params[j], self._set_arr[i][j])
                    if changed:
                        exp.evaluate()
                        out_sns = self._adjust_sens(exp, sns)
                    else:
                        out_sns = sns
                # Change telescope parameter
                elif vary_scope is 'tel':
                    tel = exp.tels[self._tels[j]]
                    changed = tel.change_param(
                        self._params[j], self._set_arr[i][j])
                    if changed:
                        tel.evaluate()
                        sns = self._adjust_sens(
                            exp, sns, tel=self._tels[j])
                    else:
                        out_sns = sns
                # Change camera parameter
                elif vary_scope is 'cam':
                    tel = exp.tels[self._tels[j]]
                    cam = tel.cams[self._cams[j]]
                    changed = cam.change_param(
                        self._params[j], self._set_arr[i][j])
                    if changed:
                        cam.evalutate()
                        out_sns = self._adjust_sens(
                            exp, sns, tel=self._tels[j], cam=self._cams[j])
                    else:
                        out_sns = sns
                # Change channel parameter
                elif vary_scope is 'ch':
                    tel = exp.tels[self._tels[j]]
                    cam = tel.cams[self._cams[j]]
                    ch = cam.chs[self._chs[j]]
                    changed = ch.change_param(
                        self._params[j], self._set_arr[i][j])
                    if changed:
                        ch.evaluate()
                        out_sns = self._adjust_sens(
                            exp, sns, tel=self._tels[j],
                            cam=self._cams[j], ch=self._chs[j])
                    else:
                        out_sns = sns
                # Change optic parameter
                elif vary_scope is 'opt':
                    tel = exp.tels[self._tels[j]]
                    cam = tel.cams[self._cams[j]]
                    ch = cam.chs[self._chs[j]]
                    opt = cam.opt_chn.optics[self._opts[j]]
                    band_id = ch.param("band_id")
                    changed = opt.change_param(
                        self._params[j], self._set_arr[i][j], band_id=band_id)
                    if changed:
                        opt.evaluate(ch)
                        out_sns = self._adjust_sens(
                            exp, sns, tel=self._tels[j],
                            cam=self._cams[j], ch=self._chs[j])
                    else:
                        out_sns = sns
                # Change the pixel size,
                # varying detector number also
                elif vary_scope is 'pix':
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
                    changed = []
                    changed.append(
                        ch.change_param('Pixel Size', new_pix_sz_mm))
                    changed.append(ch.change_param(
                        'Num Det per Wafer', new_ndet, band_id=band_id))
                    changed.append(ap.change_param(
                        'Absorption', new_ap, band_id=band_id))
                    # Re-evaluate channel
                    if np.any(changed):
                        ch.evaluate()
                        out_sns = self._adjust_sens(
                            exp, sns, tel=self._tels[j],
                            cam=self._cams[j], ch=self._chs[j])
                    else:
                        out_sns = sns
            '''
            # Store new sensitivity values
            sns_arr.append(out_sns)
        return sns_arr

    def _save_param_iter(self, it):
        exp = self._exps[0]  # Just for retrieving names
        sns = self.adj_sns[it]
        print(np.shape(sns))
        # Write output files for every channel
        if self._scope is not 'exp':  # Overall scope of vary
            tel_names = list(set(self._tels))  # unique tels
            tels = [exp.tels[tel_name]
                    for tel_name in tel_names]
            tel_inds = [list(exp.tels.keys()).index(tel_name)
                        for tel_name in tel_names]
        else:  # Loop over all telescopes
            tel_names = list(exp.tels.keys())
            tels = exp.tels.values()
            tel_inds = range(len(tels))
        for i, tel in zip(tel_inds, tels):
            if (self._scope is 'cam' or self._scope is 'ch' or
               self._scope is 'pix'):
                valid_inds = np.argwhere(self._tels == tel_names[i]).flatten()
                cam_names = list(set(self._cams[valid_inds]))
                cams = [tel.cams[cam_name]
                        for cam_name in cam_names]
                cam_inds = [list(tel.cams.keys()).index(cam_name)
                            for cam_name in cam_names]
            else:  # Loop over all cameras
                cam_names = list(tel.cams.keys())
                cams = list(tel.cams.values())
                cam_inds = range(len(cams))
            for j, cam in zip(cam_inds, cams):
                param_dir = self._check_dir(
                    os.path.join(cam.dir, self._param_dir))
                vary_dir = os.path.join(param_dir, self._vary_name)
                if it == 0:
                    if not os.path.isdir(vary_dir):
                        os.mkdir(vary_dir)
                if (self._scope is 'ch' or self._scope is 'pix'):
                    valid_inds = np.argwhere(
                        (self._tels == tel_names[i]) *
                        (self._cams == cam_names[j])).flatten()
                    ch_names = list(set(self._chs[valid_inds]))  # uniqee chs
                    chs = [cam.chs[ch_name]
                           for ch_name in ch_names]
                    ch_inds = [list(cam.chs.keys()).index(ch_name)
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
                    self._write_output(sns[i][j][k], fout)
                    self._write_vary_row(it, sns[i][j][k], fch)
        return

    def _init_vary_file(self, fvary):
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
            f.write(("Index | " + (fmt_unit % (*self._units,))))
            self._write_vary_header_units(f)
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
        f.write(("-"*int(407 + sum(self._param_widths))+"\n"))
        return

    def _write_output(self, data, fout):
        with open(fout, 'w') as fwrite:
            for i in range(len(data)):  # params
                row = data[i]
                wrstr = ""
                for k in range(len(row)):
                    wrstr += ("%-9.4f " % (row[k]))
                fwrite.write(wrstr)
            fwrite.write("\n")
        return

    def _write_vary_row(self, it, data, fch):
        with open(fch, 'a') as f:
            f.write(self._fmt_ind % (int(it)))
            f.write(self._fmt_str % (*self._set_arr[it],))
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
        if not os.path.isdir(dir_val):
            os.mkdir(dir_val)
        return dir_val

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

    def _load_params(self):
        self._log.log(
            "Loading parameters to vary from %s" % (self._param_file))
        convs = {i: lambda s: s.strip() for i in range(8)}
        data = np.loadtxt(self._param_file, delimiter='|', dtype=str,
                          unpack=True, ndmin=2, converters=convs)
        self._tels, self._cams, self._chs, self._opts = data[:4]
        self._params, mins, maxs, stps = data[4:]
        self._units = ["[" + un.std_units[param].name + "]"
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
        print(self._set_arr)
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

    def _vary_scope(self, ind):
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
                        self._scope = 'ch'
                        return 'opt'
                    elif ('Pixel Size' in self._params[j] and
                          self._pix_size_special):
                        self._scope = 'ch'
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
