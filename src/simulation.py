# Built-in modules
import datetime as dt
import numpy as np
import sys as sy
import glob as gb
import os

# BoloCalc modules
import src.experiment as ex
import src.display as dp
import src.log as lg
import src.loader as ld
import src.parameter as pr
import src.standardParam as sp
import src.unit as un
import src.physics as ph
import src.noise as ns
# import src.profile as pf
import src.sensitivity as sn
import src.vary as vr


class Simulation:
    """
    Simulation object generates experiments, calculates their parameters,
    simulates their sensitivies, and displays the outputs

    Args:
    log_file (str): logging file
    sim_file (str): simulation input file
    exp_dir (str): experiment directory

    Attributes:
    exp_dir (str): input experiment directory
    senses (list): array of output sensitivities
    opt_pos (list): array of output optical power arrays

    Children:
    log (src.Log): Log object
    load (src.Load): Load object
    phys (src.Physics): Physics object
    noise (src.Noise): Noise object
    exp (src.Experiment): Experiment object
    sns (src.Sensitivity): Sensitivity object
    dsp (src.Display): Display object
    """
    def __init__(self, log_file, sim_file, exp_dir):
        # Store experiment input file
        self.exp_dir = exp_dir
        self._sim_file = sim_file

        # Set up logging
        self.log = lg.Log(log_file)

        # Latest atm file
        self._atm_log = 'atm_log.txt'
        self._check_atm()

        # Store standard parameter values
        self._store_standard_params()
        self._store_output_units()

        # Build simulation-wide objects
        self.log.log("Generating Simulation object")
        self.load = ld.Loader(self)
        self.phys = ph.Physics()
        self.noise = ns.Noise(self.phys)
        # Store parameter values
        self._store_param_dict()
        # Length of status bar
        self._bar_len = 100

        # Generate simulation objects
        self.log.log("Generating Experiment object")
        self.exp = ex.Experiment(self)
        self.log.log("Generating Sensitivity object")
        self.sns = sn.Sensitivity(self)
        self.log.log("Generating Display object")
        self.dsp = dp.Display(self)

        # Output arrays
        self.senses = []
        self.opt_pows = []

    # **** Public Methods ****
    # @pf.profiler
    def simulate(self):
        """ Run simulation """
        self._evaluate()
        self._display()
        return

    def vary_simulate(self, param_file, vary_name, vary_tog):
        """
        Run parameter vary simulation

        Args:
        param_file (str): file that contains the parameters to be varied
        vary_name (str): name of the vary output directory
        vary_tog (bool): whether or not to vary the parameter arrays together
        """
        vary = vr.Vary(self, param_file, vary_name, vary_tog)
        vary.vary()
        return

    def param(self, param):
        """
        Return parameter from param_dict

        Args:
        param (str): name of parameter, param_dict key
        """
        val = self._param_dict[param].get_val()
        if val is None:
            val = self._param_dict[param].get_med()
        return val

    # **** Helper Methods ****
    def _store_standard_params(self):
        """ Store dictionary of StandardParameter objects """
        # Functional minimum for zero-bounded parameters
        func_min = 1.e-3
        self.std_params = {
            "EXPERIMENTS": sp.StandardParam(
                "Experiments", un.Unit("NA"),
                0, np.inf, int),
            "OBSERVATIONS": sp.StandardParam(
                "Observations", un.Unit("NA"),
                0, np.inf, int),
            "DETECTORS": sp.StandardParam(
                "Detectors", un.Unit("NA"),
                0, np.inf, int),
            "RESOLUTION": sp.StandardParam(
                "Resolution", un.Unit("GHz"),
                0.01, np.inf, float),
            "FOREGROUNDS": sp.StandardParam(
                "Foregrounds", None,
                None, None, bool),
            "CORRELATIONS": sp.StandardParam(
                "Correlations", None,
                None, None, bool),
            "PERCENTILE": sp.StandardParam(
                "Percentile", None,
                None, None, list),
            "DUSTTEMPERATURE": sp.StandardParam(
                "Dust Temperature", un.Unit("K"),
                0.0, np.inf, float),
            "DUSTSPECINDEX": sp.StandardParam(
                "Dust Spec Index", un.Unit("NA"),
                -np.inf, np.inf, float),
            "DUSTAMPLITUDE": sp.StandardParam(
                "Dust Amplitude", un.Unit("MJy"),
                0.0, np.inf, float),
            "DUSTSCALEFREQUENCY": sp.StandardParam(
                "Dust Scale Frequency", un.Unit("GHz"),
                func_min, np.inf, float),
            "SYNCHROTRONSPECINDEX": sp.StandardParam(
                "Synchrotron Spec Index", un.Unit("NA"),
                -np.inf, np.inf, float),
            "SYNCHROTRONAMPLITUDE": sp.StandardParam(
                "Synchrotron Amplitude", un.Unit("K"),
                0.0, np.inf, float),
            "SYNCSCALEFREQUENCY": sp.StandardParam(
                "Sync Scale Frequency", un.Unit("GHz"),
                func_min, np.inf, float),
            "SKYTEMPERATURE": sp.StandardParam(
                "Sync Scale Frequency", un.Unit("K"),
                func_min, np.inf, float),
            "SITE": sp.StandardParam(
                "SITE", un.Unit("NA"),
                None, None, str),
            "ELEVATION": sp.StandardParam(
                "ELEVATION", un.Unit("deg"),
                20., 90., float),
            "PWV": sp.StandardParam(
                "PWV", un.Unit("mm"),
                0.0, 8.0, float),
            "OBSERVATIONTIME": sp.StandardParam(
                "Observation Time", un.Unit("yr"),
                func_min, np.inf, float),
            "SKYFRACTION": sp.StandardParam(
                "Sky Fraction", un.Unit("NA"),
                func_min, 1.0, float),
            "OBSERVATIONEFFICIENCY": sp.StandardParam(
                "Observation Efficiency", un.Unit("NA"),
                func_min, 1.0, float),
            "NETMARGIN": sp.StandardParam(
                "NET Margin", un.Unit("NA"),
                func_min, np.inf, float),
            "BORESIGHTELEVATION": sp.StandardParam(
                "Boresight Elevation", un.Unit("deg"),
                -40.0, 40.0, float),
            "OPTICALCOUPLING": sp.StandardParam(
                "Optical Coupling", un.Unit("NA"),
                func_min, 1.0, float),
            "FNUMBER": sp.StandardParam(
                "F Number", un.Unit("NA"),
                func_min, np.inf, float),
            "BATHTEMP": sp.StandardParam(
                "Bath Temp", un.Unit("K"),
                func_min, np.inf, float),
            "BANDCENTER": sp.StandardParam(
                "Band Center", un.Unit("GHz"),
                func_min, np.inf, float),
            "FRACTIONALBW": sp.StandardParam(
                "Fractional BW", un.Unit("NA"),
                func_min, 2.0, float),
            "PIXELSIZE": sp.StandardParam(
                "Pixel Size", un.Unit("mm"),
                func_min, np.inf, float),
            "PIXELSIZE**": sp.StandardParam(
                "Pixel Size", un.Unit("mm"),
                func_min, np.inf, float),
            "NUMDETPERWAFER": sp.StandardParam(
                "Num Det per Wafer", un.Unit("NA"),
                0.0, np.inf, float),
            "NUMWAFPEROT": sp.StandardParam(
                "Num Waf per OT", un.Unit("NA"),
                0.0, np.inf, float),
            "NUMOT": sp.StandardParam(
                "Num OT", un.Unit("NA"),
                0.0, np.inf, float),
            "WAISTFACTOR": sp.StandardParam(
                "Waist Factor", un.Unit("NA"),
                2.0, np.inf, float),
            "DETEFF": sp.StandardParam(
                "Det Eff", un.Unit("NA"),
                func_min, 1.0, float),
            "PSAT": sp.StandardParam(
                "Psat", un.Unit("pW"),
                func_min, np.inf, float),
            "PSATFACTOR": sp.StandardParam(
                "Psat Factor", un.Unit("NA"),
                func_min, np.inf, float),
            "CARRIERINDEX": sp.StandardParam(
                "Carrier Index", un.Unit("NA"),
                func_min, np.inf, float),
            "TC": sp.StandardParam(
                "Tc", un.Unit("K"),
                func_min, np.inf, float),
            "TCFRACTION": sp.StandardParam(
                "Tc Fraction", un.Unit("NA"),
                func_min, np.inf, float),
            "FLINK": sp.StandardParam(
                "Flink", un.Unit("NA"),
                func_min, np.inf, float),
            "G": sp.StandardParam(
                "G", un.Unit("pW"),
                func_min, np.inf, float),
            "YIELD": sp.StandardParam(
                "Yield", un.Unit("NA"),
                func_min, 1.000, float),
            "SQUIDNEI": sp.StandardParam(
                "SQUID NEI", un.Unit("pA/rtHz"),
                func_min, np.inf, float),
            "BOLORESISTANCE": sp.StandardParam(
                "Bolo Resistance", un.Unit("Ohm"),
                func_min, np.inf, float),
            "READNOISEFRAC": sp.StandardParam(
                "Read Noise Frac", un.Unit("NA"),
                0.0, np.inf, float),
            "RESPFACTOR": sp.StandardParam(
                "Resp Factor", un.Unit("NA"),
                func_min, np.inf, float),
            "ELEMENT": sp.StandardParam(
                "Element", un.Unit("NA"),
                None, None, str),
            "TEMPERATURE": sp.StandardParam(
                "Temperature", un.Unit("K"),
                0.1, np.inf, float),
            "ABSORPTION": sp.StandardParam(
                "Absorption", un.Unit("NA"),
                0.0, 1.0, float),
            "REFLECTION": sp.StandardParam(
                "Reflection", un.Unit("NA"),
                0.0, 1.0, float),
            "THICKNESS": sp.StandardParam(
                "Thickness", un.Unit("mm"),
                0.0, np.inf, float),
            "INDEX": sp.StandardParam(
                "Index", un.Unit("NA"),
                func_min, np.inf, float),
            "LOSSTANGENT": sp.StandardParam(
                "Loss Tangent", un.Unit("e-4"),
                0.0, np.inf, float),
            "CONDUCTIVITY": sp.StandardParam(
                "Conductivity", un.Unit("e+6"),
                0.0, np.inf, float),
            "SURFACEROUGH": sp.StandardParam(
                "Surface Rough", un.Unit("um RMS"),
                0.0, np.inf, float),
            "SPILLOVER": sp.StandardParam(
                "Spillover", un.Unit("NA"),
                0.0, 1.0, float),
            "SPILLOVERTEMP": sp.StandardParam(
                "Spillover Temp", un.Unit("K"),
                0.1, np.inf, float),
            "SCATTERFRAC": sp.StandardParam(
                "Scatter Frac", un.Unit("NA"),
                0.0, 1.0, float),
            "SCATTERTEMP": sp.StandardParam(
                "Scatter Temp", un.Unit("K"),
                0.1, np.inf, float),
            "NUMDET": sp.StandardParam(
                "Num Det", un.Unit("NA"),
                0, np.inf, int),
            "OPTICALTHROUGHPUT": sp.StandardParam(
                "Optical Throughput", un.Unit("NA"),
                0.0, 1.0, float),
            "POPT": sp.StandardParam(
                "Popt", un.Unit("pW"),
                0.0, np.inf, float),
            "NEP": sp.StandardParam(
                "NEP", un.Unit("aW/rtHz"),
                0.0, np.inf, float),
            "NET": sp.StandardParam(
                "NET", un.Unit("uK-rts"),
                0.0, np.inf, float),
            "CORRFACT": sp.StandardParam(
                "Corr Fact", un.Unit("NA"),
                1.0, np.inf, float),
            "MAPDEPTH": sp.StandardParam(
                "Map Depth", un.Unit("uK-amin"),
                0.0, np.inf, float)
        }

    def _store_output_units(self):
        """ Store units for output parameters """
        self.output_units = {
            "eff": self.std_params["OPTICALTHROUGHPUT"].unit,
            "popt": self.std_params["POPT"].unit,
            "Trcvr": self.std_params["TEMPERATURE"].unit,
            "Tsky": self.std_params["TEMPERATURE"].unit,
            "NEPph": self.std_params["NEP"].unit,
            "NEPg": self.std_params["NEP"].unit,
            "NEPrd": self.std_params["NEP"].unit,
            "NEPtot": self.std_params["NEP"].unit,
            "NETdet": self.std_params["NET"].unit,
            "NETrj": self.std_params["NET"].unit,
            "NETarr": self.std_params["NET"].unit,
            "NETarrRj": self.std_params["NET"].unit,
            "CorrFact": self.std_params["CORRFACT"].unit,
            "Depth": self.std_params["MAPDEPTH"].unit,
            "DepthRj": self.std_params["MAPDEPTH"].unit}
        return

    def _store_param_dict(self):
        """ Store input parameters in dictionary """
        # Check whether the simulation file exists
        if not os.path.isfile(self._sim_file):
            self.log.err(
                "Simulation file '%s' does not exist" % (self._sim_file))
        # Load the simulation file to a parameter dictionary
        self._inp_dict = self.load.sim(self._sim_file)
        # Store dictionary of Parameter objects
        self._param_dict = {
            "nexp": self._store_param("Experiments"),
            "nobs": self._store_param("Observations"),
            "ndet": self._store_param("Detectors"),
            "fres": self._store_param("Resolution"),
            "infg": self._store_param("Foregrounds"),
            "corr": self._store_param("Correlations"),
            }
        # On 2020-06-01, "Percentile" was replaced with "Percentile Lo"
        # and "Percentile Hi"
        if self._input_param_exists("Percentile"):
            self._param_dict.update({"pct": self._store_param("Percentile")})
        elif (self._input_param_exists("Percentile Lo") and
              self._input_param_exists("Percentile Hi")):
            # Store the list entries manually
            pct_lo = str(self._retrieve_input_param("Percentile Lo")).strip()
            pct_hi = str(self._retrieve_input_param("Percentile Hi")).strip()
            pct_val = "[%s, %s]" % (pct_lo, pct_hi)
            self._param_dict.update({"pct": pr.Parameter(
                self.log, pct_val,
                std_param=self.std_params["PERCENTILE"])})
        else:
            self.log.err(
                "Neither 'Percentile' not 'Percentile Lo' and 'Percentile Hi " 
                "were found in 'simulationInputs.txt")
        return

    def _input_param_exists(self, name):
        cap_name = name.replace(" ", "").strip().upper()
        if cap_name in self._inp_dict.keys():
            return True
        else:
            return False

    def _retrieve_input_param(self, name):
        cap_name = name.replace(" ", "").strip().upper()
        if cap_name in self._inp_dict.keys():
            return self._inp_dict[cap_name]
        else:
            self.log.err(
                "Passed parameter in simulationInputs.txt '%s' not "
                "recognized in _retrieve_input_param()" % (name))

    def _store_param(self, name):
        """ Helper method to store param dict """
        cap_name = name.replace(" ", "").strip().upper()
        if cap_name in self.std_params.keys():
            return pr.Parameter(
                self.log, self._inp_dict[cap_name],
                std_param=self.std_params[cap_name])
        else:
            self.log.err(
                "Passed parameter in simulationInputs.txt '%s' not "
                "recognized in _store_param()" % (name))

    def _evaluate(self):
        """ Evaluate experiment """
        tot_sims = self.param("nexp") * self.param("ndet") * self.param("nobs")
        self.log.out((
                "Simulting %d experiment realizations each with "
                "%d detector realizations and %d sky realizations. "
                "Total sims = %d"
                % (self.param("nexp"), self.param("ndet"),
                   self.param("nobs"), tot_sims)))
        for n in range(self.param("nexp")):
            self._evaluate_exp(n)
        self._done()
        return

    def _evaluate_exp(self, n):
        """ Evaluate and calculate sensitivity for a generated experiment """
        self._status(n)
        self.exp.evaluate()
        self.senses.append(self.sns.sensitivity())
        self.opt_pows.append(self.sns.opt_pow())
        return

    def _display(self):
        """ Display sensitivity output """
        self.dsp.display()
        return

    def _status(self, rel):
        """ Print status bar for realization 'rel' """
        frac = float(rel) / float(self.param("nexp"))
        sy.stdout.write('\r')
        sy.stdout.write(
            "[%-*s] %02.1f%%" % (int(self._bar_len), '=' * int(
                self._bar_len * frac), frac * 100.))
        sy.stdout.flush()
        return

    def _done(self):
        """ Print filled status bar """
        sy.stdout.write('\r')
        sy.stdout.write(
            "[%-*s] %.1f%%" % (self._bar_len, '='*self._bar_len, 100.))
        sy.stdout.write('\n')
        sy.stdout.flush()
        return

    def _check_atm(self):
        """ Check atmosphere file """
        # Check that the atmosphere file exists
        self._src_dir = os.path.dirname(os.path.abspath(__file__))
        self._atm_files = gb.glob(os.path.join(self._src_dir, 'atm*.hdf5'))
        if len(self._atm_files) == 0:
            self.log.err(
                "No atmosphere file found in %s" % (self._src_dir))
        elif len(self._atm_files) > 1:
            self.log.log(
                "Multiple atmosphere files found in %s: %s"
                % (self._src_dir, self._atm_files))
            fnames = [f.split(os.sep)[-1].strip('.hdf5')
                      for f in self._atm_files]
            dates = [int(f.split('_')[-1]) if '_' in f else 0 for f in fnames]
            args = np.argsort(dates)
            self.atm_file = np.take(self._atm_files, args)[-1]
        else:
            self.atm_file = self._atm_files[0]
        # Check for the latest atmosphere file
        auxil_dir = os.path.abspath(
            os.path.join(self._src_dir, '..', 'auxil'))
        self._atm_log_file = os.path.join(auxil_dir, 'atm_log.txt')
        if not os.path.isfile(self._atm_log_file):
            self.log.err(
                "No atmosphere log file found in %s. "
                "Run 'git checkout %s' before running 'calcBolos.py."
                % (auxil_dir, self._atm_log_file))
        self._atm_entries = open(self._atm_log_file, 'r').readlines()
        self._entries_str = '\n   * '.join(
            ['--'.join(f.split('--')[:2]) for f in self._atm_entries])
        self._latest_atm_file = self._atm_entries[0].split('--')[0].strip()
        if self._latest_atm_file not in self.atm_file:
            remind_date_str = self._atm_entries[0].split('--')[-1]
            self._remind_atm(remind_date_str)

    def _remind_atm(self, remind_date_str):
        """ Remind the user to download the latest atm file """
        ryear, rmonth, rday = (
            remind_date_str.lstrip(' [').rstrip('] \n').split('-'))
        now = dt.datetime.now()
        cyear = now.year
        cmonth = now.month
        cday = now.day
        # Remind the user if a reminder is due
        while True:
            if (cyear >= int(ryear) and cmonth >= int(rmonth) and
               cday >= int(rday)):
                inform_str = (
                    "Your atmosphere profile file '%s' is out of date. "
                    "Here is a record of 'atm.hdf5' files:\n"
                    "   * %s" % (self.atm_file, self._entries_str))
                options = (
                    "Would you like to...\n"
                    "   'D' -- download latest atmosphere file (~10 min)\n"
                    "   'P' -- proceed with existing file and remind me "
                    "again before next 'calcBolos.py' execution\n"
                    "   'R' -- proceed with existing file and remind me "
                    "again tomorrow\n")
                out_str = inform_str + '\n' + options
                sy.stdout.write(out_str)
                answer = input("Your selection [D]:")
                answer = answer.strip().upper()
                if answer == 'D' or answer == '':
                    os.system('python3 %s' % (os.path.join(
                        self._src_dir, '..', 'update_atm.py')))
                    write_str = (
                        "Updated to atmosphere file to %s"
                        % (self._latest_atm_file))
                    self.log.out(write_str)
                    self.atm_file = os.path.join(
                        self._src_dir, self._latest_atm_file)
                elif answer == 'P':
                    write_str = (
                        "Using old atmosphere file %s. "
                        "Update using update_atm.py"
                        % (self.atm_file))
                    self.log.wrn(write_str)
                elif answer == 'R':
                    write_str = (
                        "Using old atmosphere file %s. "
                        "Update using update_atm.py"
                        % (self.atm_file))
                    self.log.wrn(write_str)
                    # Update the atm log file with a new reminder date
                    new_date = now + dt.timedelta(days=1)
                    date_str = (
                        "[%04d-%02d-%02d]"
                        % (new_date.year, new_date.month, new_date.day))
                    self._atm_entries[0] = '--'.join(
                        self._atm_entries[0].split('--')[:2]
                        + [' '+date_str+'\n'])
                    open(self._atm_log_file, 'w').writelines(self._atm_entries)
                else:
                    write_str = (
                        "I could not understand your command %s"
                        % (answer))
                    sy.stdout.write(write_str)
                    continue
                break
            else:
                write_str = (
                        "Using old atmosphere file %s. "
                        "Update using update_atm.py"
                        % (self.atm_file))
                self.log.wrn(write_str)
                break
        return
