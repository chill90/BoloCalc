# Built-in modules
import numpy as np
import collections as cl
import os

# BoloCalc modules
import src.unit as un
import src.distribution as ds


class Display:
    def __init__(self, sim):
        # Store passed parameters
        self._sim = sim
        self._calcs = self._sim.calcs
        self._phys = self._sim.phys
        self._noise = self._sim.noise

        # Percentiles to be calculated
        self._pct_lo = 0.159
        self._pct_hi = 0.841

        # Extract means and standard deviations from calcs
        self._merge_exps(calcs)

        # Table titles
        self._table_format()

    # Generate sensitivities
    def sensitivity(self):
        self._init_exp_table()

        # Loop over telescopes
        self._exp_chs = {}
        self._exp_ndet = {}
        for i in range(len(exp.tels)):
            tel = list(self._exp.tels.values())[i]
            self._init_tel_table()

            # Loop over cameras
            self._tel_chs = {}
            self._tel_ndet = {}
            for j in range(len(tel.cams)):
                cam = list(tel.cams.values())[j]
                self._init_cam_table()

                # Loop over channels
                for k in range(len(cam.chs)):
                    ch = list(cam.chs.values())[k]
                    # Write channel sensitivity
                    self._write_cam_table_row(ch, (i, j, k))
                tel_chs.append(cam_chs)

                # Write camera sensitivity
                self._finish_cam_table((i, j))

            # Write telescope sensitivity
            self._write_tel_table()

        # Write experiment sensitivity
        self._write_exp_table()

        return

    # Generate opitcal power files
    def opt_pow_tables(self):
        for i in range(len(self._exp.tels)):
            tel = list(self._exp.tels.values())[i]
            for j in range(len(telescope.cameras)):
                cam = list(tel.cams.values())[j]
                self._opt_f = open(
                    os.path.join(cam.dir, 'optical_power.txt'), 'w')
                self._write_opt_table(band_title)
                for k in range(len(cam.chs)):
                    ch = list(cam.chs.values())[k]
                    self._write_opt_table(ch, (i, j, k))
                self._opt_f.close()
        return

    # ***** Helper Methods *****
    def _merge_exps(calcs):
        self._sns = np.concatenate(self._sim.senses, axis=-1)
        self._opts = np.concatenate(self._sim.opt_pows, axis=-1)
        self._exp = self._sim.exps[0]
        return

    def _table_format(self):
        # Camera file
        self._title_cam = ("%-10s | %-7s | %-23s | %-23s | %-23s | "
                           "%-23s | %-23s | %-25s | %-23s | %-23s\n"
                           % ("Chan", "Num Det", "Optical Power",
                              "Photon NEP", "Bolometer NEP", "Readout NEP",
                              "Detector NEP", "Detector NET", "Array NET",
                              "Map Depth"))
        self._unit_cam = ("%-10s | %-7s | %-23s | %-23s | %-23s | "
                          "%-23s | %-23s | %-25s | %-23s | %-23s\n"
                          % ("", "", "[pW]", "[aW/rtHz]",
                             "[aW/rtHz]", "[aW/rtHz]", "[aW/rtHz]",
                             "[uK-rts]", "[uK-rts]", "[uK-arcmin]"))
        self._break_cam = "-"*240+"\n"
        # Telescope and experiment files
        self._title_tel = ("%-10s | %-7s | %-23s | %-23s\n"
                           % ("Chan", "Num Det", "Array NET", "Map Depth"))
        self._unit_tel = ("%-10s | %-7s | %-23s | %-23s\n"
                          % ("", "", "[uK-rts]", "[uK-arcmin]"))
        self._break_tel = "-"*110+"\n"
        self._title_exp = self._title_tel
        self._unit_exp = self._unit_tel
        self._break_exp = self._break_tel
        # Optical power files
        self._title_opt = ("| %-15s | %-23s | %-23s | %-23s |\n"
                           % ("Element", "Power from Sky",
                              "Power to Detect", "Cumulative Eff"))
        self._unit_opt = ("| %-15s | %-23s | %-23s | %-23s |\n"
                          % ("", "[pW]", "[pW]", ""))
        self._break_opt = "-"*73+"\n"
        return

    def _init_exp_table(self):
        self._exp_f = open(
            os.path.join(self._sim.exp_dir, 'sensitivity.txt'), 'w')
        self._exp_f.write(self._title_exp)
        self._exp_f.write(self._break_exp)
        self._exp_f.write(self._unit_exp)
        self._exp_f.write(self._break_exp)
        return

    def _init_tel_table(self, tel_dir):
        self._tel_f = open(
            os.path.join(tel_dir, 'sensitivity.txt'), 'w')
        self._tel_f.write(self._title_tel)
        self._tel_f.write(self._break_tel)
        self._tel_f.write(self._unit_tel)
        self._tel_f.write(self._break_tel)
        return

    def _init_cam_table(self, cam_dir):
        self._cam_f = open(os.path.join(
            cam_dir, 'sensitivity.txt'), 'w')
        self._cam_f.write(self._title_cam)
        self._cam_f.write(self._break_cam)
        self._cam_f.write(self._unit_cam)
        self._cam_f.write(self._break_cam)
        return

    def _write_cam_table_row(self, ch, tup):
        # Write channel values to camera file
        # tup (i,j,k) = (tel,cam,ch) tuple
        sns = self._sns[tup[0]][tup[1]][tup[2]]
        ch_name = ch.param("ch_name")
        ndet = ch.param("ndet")
        wstr = ("%-10s | %-7d | "
                "%-5.2f +/- (%-5.2f,%-5.2f) | %-5.2f +/- (%-5.2f,%-5.2f) | "
                "%-5.2f +/- (%-5.2f,%-5.2f) | %-5.2f +/- (%-5.2f,%-5.2f) | "
                "%-5.2f +/- (%-5.2f,%-5.2f) | %-6.1f +/- (%-6.1f,%-6.1f) | "
                "%-5.1f +/- (%-5.2f,%-5.2f) | %-5.2f +/- (%-5.2f,%-5.2f)\n"
                % (ch_name, ndet,
                   *self._spread(sns[0], un.Unit("pW")),
                   *self._spread(sns[1], un.Unit("aW/rtHz")),
                   *self._spread(sns[2], un.Unit("aW/rtHz")),
                   *self._spread(sns[3], un.Unit("aW/rtHz")),
                   *self._spread(sns[4], un.Unit("aW/rtHz")),
                   *self._spread(sns[5], un.Unit("uK")),
                   *self._inv_var_spread(sns[5], un.Unit("uK")),
                   *self._map_depth(self._inv_var_spread(
                       sns[5], un.Unit("uK"))), ch.cam.tp))
        self._cam_f.write(wstr)
        self._cam_f.write(self._break_cam)
        # Store the detector number
        # Update telescope channel dictionary
        if ch_name in self._tel_chs.keys():
            self._tel_chs[ch_name] = np.concatenate(
                (self._tel_chs[ch_name], sns), axis=-1)
            self._tel_ndet[ch_name] += ndet
        else:
            self._tel_chs[ch_name] = [sns]
        # Update experiment channel dictionary
        if ch_name in self._exp_chs.keys():
            self._exp_chs[ch_name] = np.concatenate(
                (self._tel_chs[ch_name], sns), axis=-1)
            self._exp_ndet[ch_name] += ndet
        else:
            self._exp_chs[ch_name] = [sns]
        return

    def _map_depth(self, vals, fsky, tobs):
        return self._noise.sensitivity(vals, fksy, tobs)

    def _write_opt_table(self, ch, tup):
        # tup (i,j,k) = (tel,cam,ch) tuple
        opt = self._opts[tup[0]][tup[1]][tup[2]]
        band_name = ch.param("band_id")
        band_title = ("%s %11s %-12s %s\n"
                      % (ch.cam.param("cam_name"),
                         band_name, "*"*24, "*"*23))
        self._opt_f.write(band_title)
        self._opt_f.write(self._title_opt)
        self._opt_f.write(self._break_opt)
        self._opt_f.write(self._unit_opt)
        self._opt_f.write(self._break_opt)
        for m in range(len(ch.elem[0][0])):  # nelem
            elem_name = ch.elem[0][0][m]
            wstr = ("| %-15s | %-5.3f +/- (%-5.3f,%-5.3f) | "
                    "%-5.3f +/- (%-5.3f,%-5.3f) | "
                    "%-5.3f +/- (%-5.3f,%-5.3f) |\n"
                    % (elemName,
                       *self._spread(opt[0][m], un.Unit("pW")),
                       *self._spread(opt[1][m], un.Unit("pW")),
                       *self._spread(opt[2][m])))
            self._opt_f.write(wstr)
            self._opt_f.write(self._break_opt)
        self._opt_f.write("\n\n")
        return

    def _finish_cam_table(self, cam, tup):
        # Write cumulative sensitivity for all channels for camera
        # tup (i,j) = (tel,cam) tuple
        sns = self._sns[tup[0]][tup[1]]
        ndet = sum([ch.param("ndet") for ch in cam.chs.values()])
        wstr = ("%-10s | %-7d | %-156s | %-5.2f +/- (%-5.2f,%-5.2f) | "
                "%-5.1f +/- (%-5.1f,%-5.1f)\n"
                % ("Total", ndet, "",
                   *self._inv_var_spread(sns[5], un.Unit("uK")),
                   *self._map_depth(
                       self._inv_var_spread(sns[5], un.Unit("uK")),
                       cam.tp.param("fsky"),
                       cam.tp.param("tobs"))))
        self._cam_f.write(wstr)
        self._cam_f.close()

    def _write_tel_exp(self, chs, ndets, f):
        tot_det = 0
        tot_time = 0
        tot_fsky = 0
        for name, ch in chs.items():
            ndet = ndets[name]
            tot_det += ndet
            tot_time += ch.cam.tp.param("tobs")
            tot_fsky += ch.cam.tp.param("fsky")
            wstr = ("%-10s | %-7d | "
                    "%-5.2f +/- (%-5.2f,%-5.2f) | "
                    "%-5.1f +/- (%-5.1f,%-5.1f)\n"
                    % (name, ndet,
                       *self._inv_var_spread(ch[5], un.Unit("uK")),
                       *self._map_depth(
                           self._inv_var_spread(ch[5], un.Unit("uK")),
                           ch.cam.tp.param("fsky"), ch.cam.tp.param("tobs"))))
            f.write(wstr)
            f.write(self._break_tel)
        tot_fsky = tot_fsky / len(chs)
        # Write the cumulative sensitivity to finish the table
        sns = np.concatenate(list(chs.values()), axis=-1)
        wstr = ("%-10s | %-7d | "
                "%-5.2f +/- (%-5.2f,%-5.2f) | "
                "%-5.1f +/- (%-5.1f,%-5.1f)\n"
                % ("Total", tot_det,
                   *self._inv_var_spread(sns[5], un.Unit("uK")),
                   *self._map_depth(
                       self._inv_var_spread(sns[5], un.Unit("uK")),
                       tot_fksy, tot_time)))
        f.write(wstr)
        f.close()
        return

    def _write_tel_table(self):
        return self._write_tel_exp(self._tel_chs, self._tel_ndet, self._tel_f)

    def _write_exp_table(self):
        return self._write_tel_exp(self._exp_chs, self._exp.ndet, self._exp_f)

    def _spread(self, inp, unit=None):
        if unit is None:
            unit = un.Unit("NA")
        lo, med, hi = unit.from_SI(np.percentile(
            inp, (self._pct_lo, 0.50, self._pct_hi)))
        return [med, hi-med, med-lo]

    def _sum_spread(self, inp, unit=None):
        if unit is None:
            unit = un.Unit("NA")
        lo, med, hi = unit.from_SI(np.percentile(
            inp, (self._pct_lo, 0.50, self._pct_hi), axis=-1))
        return (np.sum(med),
                np.sqrt(np.sum((hi-med)**2)),
                np.sqrt(np.sum((med-lo)**2)))

    def _inv_var_spread(self, inp, unit=None):
        if unit is None:
            unit = un.Unit("NA")
        lo, med, hi = unit.from_SI(np.percentile(
            inp, (self._pct_lo, 0.50, self._pct_hi), axis=-1))
        return (self._phys.inv_var(med),
                self._phys.inv_var((hi-med)),
                self._phys.inv_var((med-lo)))
