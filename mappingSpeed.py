# Built-in modules
import time as tm
import sys as sy
import os

# BoloCalc modules
import src.simulation as sm


# Experiment files
try:
    exp_file = sy.argv[1]
except:
    print
    print('Usage: python mappingSpeed.py [Experiment Directory]')
    print('Example: python mappingSpeed.py Experiments' + os.sep +
          'ExampleExperiment' + os.sep + 'V0' + os.sep)
    print
    sy.exit(1)
# Simulation file
sim_file = os.path.join(os.path.dirname(os.path.normpath(__file__)),
                        'config', 'simulationInputs.txt')
# Logging file
log_file = os.path.join(os.path.dirname(os.path.normpath(__file__)),
                        'log', ('log_%d.txt' % (int(tm.time()))))
# Simulate experiment
sim = sm.Simulation(log_file, sim_file, exp_file)
sim.simulate()
