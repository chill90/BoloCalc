#python Version 2.7.2
import time                as tm
import sys                 as sy
import os

import src.simulation      as sm

#Experiment Input files
try:
    expFiles = sy.argv[1]
except:
    print
    print 'Usage:   python mappingSpeed.py [Experiment Directory]'
    print 'Example: python mappingSpeed.py Experiments/ExampleExperiment/V0/'
    print
    sy.exit(1)
#Simulation input parameter file
simFile = os.path.dirname(os.path.realpath(__file__))+'/config/simulationInputs.txt'
if not os.path.isfile(simFile):
    print 
    print 'Could not find simulation input parameter file %s' % (simFile)
    print
    sy.exit(1)
#Logging file
logFile = os.path.dirname(os.path.realpath(__file__))+('/log/log_%d.txt' % (int(tm.time())))
verbosity = 0

#Simulate experiment
sim = sm.Simulation(expFiles, simFile, logFile, verbosity=verbosity, genTables=True)
sim.simulate()
