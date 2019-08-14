# Built-in modules
import time as tm
import sys as sy
import os

# BoloCalc modules
import src.simulation as sm


def usage():
    print('\nUsage: python3 mappingSpeed.py [Experiment Directory]')
    print('Example: python3 mappingSpeed.py Experiments' + os.sep +
          'ExampleExperiment' + os.sep + 'V0' + os.sep + '\n')
    sy.exit(False)

# Check the python version
if sy.version_info.major == 2:
    print("\n***** Python 2 is not longer supported for "
          "BoloCalc v0.10 (Aug 2019) and beyond *****")
    usage()

# Experiment files
try:
    exp_file = sy.argv[1]
except:
    usage()

# Simulation file
sim_file = os.path.join(os.path.dirname(os.path.normpath(__file__)),
                        'config', 'simulationInputs.txt')
# Logging file
log_file = os.path.join(os.path.dirname(os.path.normpath(__file__)),
                        'log', ('log_%d.txt' % (int(tm.time()))))
# Simulate experiment
sim = sm.Simulation(log_file, sim_file, exp_file)
sim.evaluate()
sim.display()
