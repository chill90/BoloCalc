# Built-in modules
import argparse as ap
import datetime as dt
import sys as sy
import os

# BoloCalc modules
import src.simulation as sm


def date_time_str():
    now = dt.datetime.now()
    date_time_str = (
        "%02d%02d%02d_%02d_%02d_%02d"
        % (now.year, now.month, now.day,
           now.hour, now.minute, now.second))
    return date_time_str


def usage():
    usage_str = ("\nUsage: python3 mappingSpeed.py Experiment"
                 "[--vary] [--vary_tog] [--vary_name vary_name]\n"
                 "Example: python3 mappingSpeed.py %s\n"
                 % (os.path.join("Experiments", "ExampleExperiment", "V0")))
    sy.exit(False)

# Check the python version
if sy.version_info.major == 2:
    print("\n***** Python 2 is not longer supported for "
          "BoloCalc v0.10 (Aug 2019) and beyond *****")
    usage()

# String defining when this code is being run
date_str = date_time_str()
# This file's path
this_path = os.path.dirname(os.path.normpath(__file__))

# Parse arguments
ps = ap.ArgumentParser()
# Positional arguments
ps.add_argument(
    "exp_dir", type=str, metavar="Experiment Directory",
    help="Experiment directory to be simulated")
# Keyword arguments
ps.add_argument(
    "--vary", action="store_true", dest="vary", default=False,
    help="Vary over parameter sets defined in config/paramsToVary.txt")
ps.add_argument(
    "--vary_tog", action="store_true", dest="vary_tog", default=False,
    help="Vary parameter sets defined in config/paramsToVary.txt together")
ps.add_argument(
    "--vary_name", dest="vary_name", nargs=1, type=str,
    default=date_str,
    help="Custom name for vary output")
args = ps.parse_args()

# Simulation file
sim_file = os.path.join(this_path, 'config', 'simulationInputs.txt')
# Parameter vary file
vary_file = os.path.join(this_path, 'config', 'paramsToVary.txt')
# Logging file
log_file = os.path.join(this_path, 'log', ('log_%s.txt' % (date_str)))
# Simulate experiment
sim = sm.Simulation(log_file, sim_file, args.exp_dir)
if not args.vary:
    sim.simulate()
else:
    sim.vary_simulate(vary_file, args.vary_name[0], args.vary_tog)
