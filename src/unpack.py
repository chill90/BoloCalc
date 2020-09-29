import numpy as np
import glob as gb
import sys as sy
import os

class Unpack:
    """
    Unpack is a post-processing class that unpacks BoloCalc output files
    into dictionaries, so that the user can generate tables and plots

    Attributes:
    sens_out_dict (dict): dictionary of sensitivity outputs
    vary_input_dict (dict): dictionary of parameters varied
    vary_summary_output_dict (dict): dictionary of (mean, lo, hi) values
                                     for the parameter sweep
    vary_hist_output_dict (dict): dictionary of arrays of all MC-simulated
                                  values for the parameter sweep
    """
    def __init__(self):
        # Formatting for the parameter spreads
        self._pm = '+/-'
        self._txt = '.txt'
        self._sens_file = 'sensitivity.txt'
        self._out_file = 'output.txt'
        self._pwr_file = 'optical_power.txt'
        self._exp_dir = 'Experiments'
        self._total_params = [
            'Num Det', 'Array NET_CMB', 'Array NET_RJ',
            'CMB Map Depth', 'RJ Map Depth']
        self._tot_str = 'Total'
        self._sens_str = 'Summary'
        self._pwr_str = 'Summary'
        self._out_str = 'All'
        self._num_det_str = 'Num Det'

    def unpack_sensitivities(self, inp_dir):
        """
        Generate self.sens_outputs from an input Experiment directory

        Args:
        inp_dir (str): input directory. Must be an absolute path, not relative
        """
        self.sens_outputs = {}
        self._inp_sens_dir = inp_dir
        self._gather_sens_files()
        return

    def unpack_parameter_vary(self, inp_dir, var_name):
        """
        Generate self.vary_inputs, self.vary_summary_dict, and
        self.vary_outputs_all given an input Experiment directory
        and a name for the parameter variation

        Args:
        inp_dir (str): input directory. Must be an absolute path, not relative
        """
        self.vary_inputs = {}
        self.vary_outputs = {}
        self._inp_vary_dir = inp_dir
        self._inp_vary_name = var_name
        # Gather the relevant files given the input directory
        self._gather_vary_files()
        # Store the inputs and summary outputs
        for i in range(len(self._exp_names)):
            input_dict = {}
            ch_summary_dict = {}
            ch_hist_dict = {}
            for j in range(self._num_bands):
                key = self._band_names[j].split(os.sep)[-1]
                fname = os.path.join(self._summary_files[j])
                input_dict, output_dict = self._unpack_vary_summary_file(fname)
                hist_dict = self._unpack_vary_hist_files(self._hist_files[j])
                input_dict.update(input_dict)
                ch_summary_dict.update({key: output_dict})
                ch_hist_dict.update({key: hist_dict})
            output_dict = {self._sens_str: ch_summary_dict,
                           self._out_str: ch_hist_dict}
            exp_key = self._exp_names[i]
            tel_key = self._tel_names[i]
            cam_key = self._cam_names[i]
            if exp_key not in self.vary_inputs.keys():
                self.vary_inputs.update(
                    {exp_key: {tel_key: {cam_key: input_dict}}})
                self.vary_outputs.update(
                    {exp_key: {tel_key: {cam_key: output_dict}}})
            elif tel_key not in self.vary_inputs[exp_key].keys():
                self.vary_inputs[exp_key].update(
                    {tel_key: {cam_key: input_dict}})
                self.vary_outputs[exp_key].update(
                    {tel_key: {cam_key: output_dict}})
            elif cam_key not in self.vary_inputs[exp_key][tel_key].keys():
                self.vary_inputs[exp_key][tel_key].update(
                    {cam_key: input_dict})
                self.vary_outputs[exp_key][tel_key].update(
                    {cam_key: output_dict})
            else:
                sy.exit("BoloCalc Unpack error: key error in "
                        "unpack_vary()")
        return

    def unpack_optical_powers(self, inp_dir):
        """
        Generate self.sens_outputs from an input Experiment directory

        Args:
        inp_dir (str): input directory. Must be an absolute path, not relative
        """
        self.pwr_outputs = {}
        self._inp_pwr_dir = inp_dir
        self._gather_pwr_files()
        return

    def _gather_sens_files(self):
        # Look for sensitivity files in the defined directory and below
        sens_files = [f for f in gb.iglob(
            os.path.join(self._inp_sens_dir, '**'+os.sep+'*'), recursive=True)
            if self._sens_file in f]
        out_files = [f for f in gb.iglob(
            os.path.join(self._inp_sens_dir, '**'+os.sep+'*'), recursive=True)
            if self._out_file in f]
        # For each file, build a label from the filepath
        # Start inspecting a the Experiments/ directory and below
        sens_loc_dirs = [f.split(self._exp_dir)[-1].split(os.sep)[1:]
                         for f in sens_files]
        out_loc_dirs = [f.split(self._exp_dir)[-1].split(os.sep)[1:]
                        for f in out_files]
        # Use the length of each filepath to determine the layer depth
        sens_loc_dir_lens = [len(loc_dir) for loc_dir in sens_loc_dirs]
        out_loc_dir_lens = [len(loc_dir) for loc_dir in out_loc_dirs]
        # sensitivity.txt is at three above the deepest depth
        path_lens = np.array([np.amax(sens_loc_dir_lens)-i for i in range(3)])
        # Loop over the levels
        for i, path_len in enumerate(path_lens):
            # Files at this level
            sens_args = np.argwhere(path_len == sens_loc_dir_lens)
            out_args = np.argwhere(path_len == out_loc_dir_lens)
            # Store the camera sensitivity files
            for j, sens_arg in enumerate(sens_args):
                sens_loc_dir = np.take(sens_loc_dirs, sens_arg)[0]
                sens_dict = self._unpack_sens_file(
                    np.take(sens_files, sens_arg)[0])
                if i == 0:  # Camera level
                    out_dict = self._unpack_out_file(
                        np.take(out_files, out_args[j])[0], 
                        list(sens_dict.keys()),
                        list(sens_dict[list(
                            sens_dict.keys())[0]].keys()))
                    key_exp = sens_loc_dir[-4]
                    key_tel = sens_loc_dir[-3]
                    key_cam = sens_loc_dir[-2]
                    dict_to_store = {self._sens_str: sens_dict, 
                                     self._out_str: out_dict}
                    if (key_exp not in self.sens_outputs.keys()):
                        self.sens_outputs.update(
                            {key_exp: {key_tel: {key_cam:
                             dict_to_store}}})
                    elif (key_tel not in
                          self.sens_outputs[key_exp].keys()):
                        self.sens_outputs[key_exp].update(
                            {key_tel: {key_cam: dict_to_store}})
                    elif (key_cam not in
                          self.sens_outputs[key_exp][key_tel].keys()):
                        self.sens_outputs[key_exp][key_tel].update(
                            {key_cam: dict_to_store})
                    else:
                        sy.exit("Camera-level storage error in "    
                                "Unpack._gather_sens_files()")
                elif i == 1:  # Telescope level
                    key_exp = sens_loc_dir[-3]
                    key_tel = sens_loc_dir[-2]
                    self.sens_outputs[key_exp][key_tel].update(
                        {self._sens_str: sens_dict})
                elif i == 2:  # Experiment level
                    key_exp = sens_loc_dir[-2]
                    self.sens_outputs[key_exp].update(
                        {self._sens_str: sens_dict})
                else:
                    sy.exit("Telescope-level storage error in "    
                            "Unpack._gather_sens_files()")
        return

    def _gather_vary_files(self):
        # All of the paramVary dirs associated with the input vary name
        var_dirs = [f for f in gb.glob(
            os.path.join(self._inp_vary_dir, "**"+os.sep), recursive=True)
            if f.rstrip(os.sep).split(os.sep)[-1] == self._inp_vary_name in f]
        # All all of the experiments, telescopes, and cameras
        self._exp_names, self._tel_names, self._cam_names = (
            np.transpose([d.split(os.sep)[-6:-3] for d in var_dirs]))
        # All of the summary files and histogram directories
        dir_list = np.array([
            gb.glob(os.path.join(d, "*")) for d in var_dirs]).flatten()
        # Get the summary files
        summary_files = [f for f in dir_list if self._txt in f]
        # Enforce alphabetical order
        args = np.argsort(summary_files)
        self._summary_files = np.take_along_axis(
            np.array(summary_files), args, 0)
        # Get the band names
        self._band_names = [os.path.split(f)[-1].rstrip(self._txt)
                            for f in self._summary_files]
        # Get the histogram dirs
        hist_dirs = [f for f in dir_list if os.path.isdir(f)]
        # Enforce alphabetical order
        args = np.argsort(hist_dirs)
        hist_dirs = np.take_along_axis(
            np.array(hist_dirs), args, 0)
        self._hist_files = []
        for d in hist_dirs:
            hist_files = [f for f in gb.glob(os.path.join(d, "*.txt"))
                          if 'output' in f]
            self._hist_files.append(hist_files)
        if len(self._band_names) == len(self._hist_files):
            self._num_bands = len(self._band_names)
        else:
            sy.exit("Error! Mistmatching number of varied bands in "
                    "Unpack._gather_vary_files()")
        return

    def _gather_pwr_files(self):
        # Look for optical_power files in the defined directory and below
        pwr_files = [f for f in gb.iglob(
            os.path.join(self._inp_pwr_dir, '**'+os.sep+'*'), recursive=True)
            if self._pwr_file in f]
        # For each file, build a label from the filepath
        # Start inspecting a the Experiments/ directory and below
        pwr_loc_dirs = [f.split(self._exp_dir)[-1].split(os.sep)[1:]
                        for f in pwr_files]
        for i, pwr_dir in enumerate(pwr_loc_dirs):
            pwr_dict = self._unpack_pwr_file(pwr_files[i])
            key_exp = pwr_dir[-4]
            key_tel = pwr_dir[-3]
            key_cam = pwr_dir[-2]
            dict_to_store = {self._pwr_str: pwr_dict}
            if (key_exp not in self.pwr_outputs.keys()):
                self.pwr_outputs.update(
                    {key_exp: {key_tel: {key_cam:
                        dict_to_store}}})
            elif (key_tel not in
                    self.pwr_outputs[key_exp].keys()):
                self.pwr_outputs[key_exp].update(
                    {key_tel: {key_cam: dict_to_store}})
            elif (key_cam not in
                    self.pwr_outputs[key_exp][key_tel].keys()):
                self.pwr_outputs[key_exp][key_tel].update(
                    {key_cam: dict_to_store})
            else:
                sy.exit("Camera-level storage error in "
                        "Unpack._gather_pwr_files()")
        return
    # Unpack sensitiviy files
    def _unpack_sens_file(self, fname):
        # Unpack the sensitiviy file
        with open(fname, 'r') as f:
            fread = f.readlines()[::2]
        param_labs = np.char.strip(fread[0].split('|'))
        total_raw = np.char.strip(fread[-1].split('|')[1:])
        # The camera sensitivity files only calculate totals for some values
        if len(total_raw) > 5:
            total_raw = np.delete(total_raw, [1, 4])
        totals = self._parse_spreads(total_raw)
        ch_labs = np.transpose([fr.split('|') for fr in fread[2:-1]])[0]
        data = [self._parse_spreads(arr)
                for arr in np.transpose(
                    [fr.split('|') for fr in fread[2:-1]])[1:]]
        num_chs = len(data[0])
        # Store the arrays into a dictionary
        out_dict = {}
        for i in range(num_chs):
            ch_lab = ch_labs[i].strip()
            out_dict[ch_lab] = {
                param_labs[j+1]: data[j][i]
                for j in range(len(param_labs[1:]))}
        out_dict[self._tot_str] = {
            self._total_params[i]: totals[i]
            for i in range(len(totals))}
        return out_dict

    # Unpack output files
    def _unpack_out_file(self, fname, ch_keys, sens_keys):
        # Remove the 'Total' label from the channel keys, if present
        tot_loc = np.argwhere(np.array(ch_keys) == self._tot_str)
        ch_keys = np.delete(ch_keys, tot_loc)
        # Remove number of detectors from the sensitivity keys, if present
        num_det_loc = np.argwhere(np.array(sens_keys) == self._num_det_str)
        sens_keys = np.delete(sens_keys, num_det_loc)
        # Unpack the output file
        with open(fname, 'r') as f:
            fread = f.readlines()[1:]
        # Divide the into channels
        ch_strs = np.transpose([l.split('|')[:-1] for l in fread])
        arr = np.transpose([[l.split() for l in ch]
                             for ch in ch_strs], (0, 2, 1)).astype(np.float)
        if len(arr) != len(ch_keys):
            sy.exit("BoloCalc Unpack error: error when unpacking 'output.txt' "
                    "in _unpack_out_file()")
        out_dict = {ch_keys[i]: {sens_keys[j]: arr[i][j]
                    for j in range(len(sens_keys))} 
                    for i in range(len(ch_keys))}
        return out_dict
    
    # Unpack a channel file
    def _unpack_vary_summary_file(self, fname):
        with open(fname, 'r') as f:
            finput = f.readlines()
        
        # Unpack the telescope, camera, channel, and optic labels
        lab_ids = finput[:4]
        tel_labs = np.char.strip(lab_ids[0].split('|'))[1:-1]
        cam_labs = np.char.strip(lab_ids[1].split('|'))[1:-1]
        ch_labs = np.char.strip(lab_ids[2].split('|'))[1:-1]
        opt_labs = np.char.strip(lab_ids[3].split('|'))[1:-1]
        self._num_inputs = len(tel_labs)
        # Unpack the parameter labels
        lab_ids = finput[4:5]
        param_labs = np.char.strip(lab_ids[0].split('|'))[1:]
        # Store the input parameter labels
        input_labs = []
        for i in range(self._num_inputs):
            labs_to_string = [
                cam_labs[i], ch_labs[i], opt_labs[i], param_labs[i]]
            lab_string = "_".join([("%s" % lab) for lab in labs_to_string 
                                   if lab != ""])
            input_labs.append(lab_string)
        # Store the output parameter labels
        self.output_labs = param_labs[self._num_inputs:]
        self.num_outputs = len(self.output_labs)
        # Unpack the unit labels
        lab_ids = finput[5:6]
        unit_labs = np.char.strip(lab_ids[0].split('|'))[1:]
        self.input_unit_labs = unit_labs[:self._num_inputs]
        self.output_unit_labs = unit_labs[self._num_inputs:]
        self.ind_lab = lab_ids[0].split('|')[0].strip()
        
        # Unpack the data
        data = np.char.strip([line.split('|') for line in finput[7:]]).T
        
        # Store the input data dictionary
        input_dict = {}
        #input_dict[self.ind_lab] = np.array(data[0]).astype(np.float)
        for i in range(self._num_inputs):
            ind = i + 1
            input_dict[input_labs[i]] = np.array(data[ind]).astype(np.float)
        
        # Store the output data dictionary
        output_dict = {}
        for i in range(self.num_outputs):
            ind = i + 1 + self._num_inputs
            output_dict[self.output_labs[i]] = np.array(
                self._parse_spreads(data[ind])).astype(np.float)
        return input_dict, output_dict
        
    # Unpack histogram files
    def _unpack_vary_hist_files(self, files):
        # Enforce that the files are ordered by index
        inds = [int(f.rstrip(self._txt).split('_')[-1]) for f in files]
        args = np.argsort(inds)
        inds = np.take_along_axis(np.array(inds), args, 0)
        files = np.take_along_axis(np.array(files), args, 0)
        
        # Unpack the raw data into a dictionary
        hist_dict = {}
        labs = self.output_labs
        data = []
        for fname in files:
            data_load = np.loadtxt(
                fname, unpack=True, dtype=np.float).tolist()
            # Handle the case of a single output
            if len(np.shape(data_load)) == 1:
                data_load = np.array([[d] for d in data_load]).tolist()
            data.append(data_load)
        save_data = np.transpose(data, (1, 0, 2))  
        hist_dict.update({labs[i]: save_data[i]
                          for i in range(self.num_outputs)})
        return hist_dict

    def _unpack_pwr_file(self, fname):
        # Unpack the sensitiviy file
        with open(fname, 'r') as f:
            fread = f.readlines()
        out_dict = {}
        ch_key = ''
        # Loop over lines
        for i, line in enumerate(fread):
            # Skip hline
            if '---' in line:
                continue
            # Skip the unit line
            elif '[pW]' in line:
                continue
            # Skip empty lines
            elif line.strip() == '':
                continue
            # Begnning a new channel
            elif '*****' in line:
                if ch_key is not '':
                    out_dict[ch_key] = opt_dict
                ch_key = line.strip().strip('*').strip()
                opt_dict = {}
                continue
            # Parameter label line
            elif 'Element' in line:
                params = line.split('|')[1:-1]
                param_names = [p.strip() for p in params]
            # Otherwise, store data
            else:
                # Loop over columns
                params = line.split('|')[1:-1]
                meds = []
                los = []
                his = []
                for j, param in enumerate(params):
                    if self._pm in param:
                        med, lo, hi = self._parse_spread(param)
                        meds.append(med)
                        los.append(lo)
                        his.append(hi)
                    else:
                        opt_key = str(param).strip()
                opt_dict[opt_key] = {
                    pn: [meds[j], los[j], his[j]]
                    for j, pn in enumerate(param_names[1:])}
        out_dict[ch_key] = opt_dict
        return out_dict

    # Store data with spreads
    def _parse_spreads(self, inp_arr):
        ret_arr = []
        for inp in inp_arr:
            if self._pm in inp:
                mean, spread = inp.strip().split(self._pm)
                lo, hi = spread.lstrip(' (').rstrip(' )').split(',')
                ret_arr.append([float(mean), float(lo), float(hi)])
            else:
                ret_arr.append([float(inp.strip()), 0, 0])
        return ret_arr

    def _parse_spread(self, inp):
        mean, spread = inp.strip().split(self._pm)
        lo, hi = spread.lstrip(' (').rstrip(' )').split(',')
        return [float(mean), float(lo), float(hi)]
