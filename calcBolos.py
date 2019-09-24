# Built-in modules
import sys as sy

# Verify the python version
if sy.version_info.major == 2:
    sy.stdout.write("\n***** Python 2 is no longer supported for "
                    "BoloCalc v0.10 (Sep 2019) and beyond *****\n\n")
    sy.exit()

# More built-in modules
import argparse as ap  # noqa: E42
import datetime as dt  # noqa: E42
import os  # noqa: E42

# BoloCalc modules
import src.simulation as sm  # noqa: E42


def date_time_str():
    now = dt.datetime.now()
    date_time_str = (
        "%02d%02d%02d_%02d_%02d_%02d"
        % (now.year, now.month, now.day,
           now.hour, now.minute, now.second))
    date_str = "%02d%02d%02d" % (now.year, now.month, now.day)
    return date_str, date_time_str


# String defining when this code is being run
dt_str, dt_tm_str = date_time_str()
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
    default=[dt_tm_str],
    help="Custom name for vary output")
ps.add_argument(
    "--log_name", dest="log_name", nargs=1, type=str,
    default=[dt_str],
    help="Custom name for logging file")
args = ps.parse_args()

# Simulation file
sim_file = os.path.join(this_path, 'config', 'simulationInputs.txt')
# Parameter vary file
vary_file = os.path.join(this_path, 'config', 'paramsToVary.txt')
# Logging file
log_file = os.path.join(this_path, 'log', ('log_%s.txt' % (args.log_name[0])))

# Simulate experiment
sim = sm.Simulation(log_file, sim_file, args.exp_dir)
if not args.vary:
    sim.simulate()
else:
    sim.vary_simulate(vary_file, args.vary_name[0], args.vary_tog)
