#python Version 2.7.2
import time            as tm
import sys             as sy
import os

import src.simulation  as sm
import src.vary        as vr

#Experiment Input files
try:
    args = sy.argv[1:]
    expFiles = args[0]
    args.remove(expFiles)
    if '-vt' in args: 
        varyTogether = True
        args.remove('-vt')
    else:             
        varyTogether = False
    if '-fh' in args: 
        fileHandle = sy.argv[sy.argv.index('-fh')+1]
        args.remove('-fh')
        args.remove(fileHandle)
    else:             
        fileHandle = None
    if not len(args) == 0:
        print 'Unrecognized arguments:', args
        raise Exception
except:
    print
    print 'Usage:   python mappingSpeed_vary.py [Experiment Directory]'
    print 'Example: python mappingSpeed_vary.py Experiments/ExampleExperiment/V0/'
    print 'Other options:'
    print '-fh [File Handle] (Example: -fh paramVary_20180629)'
    print '-vt [Vary parameters together] (Example: -vt)'
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
verbosity = None
#Parameter vary file
paramVaryFile = os.path.dirname(os.path.realpath(__file__))+'/config/paramsToVary.txt'
if not os.path.isfile(paramVaryFile):
    print
    print 'Could not find parameter vary file %s' % (paramVaryFile)
    print
    sy.exit(1)
#Generate simulation object
sim = sm.Simulation(expFiles, simFile, logFile, verbosity, genTables=False)
#Vary parameters
var = vr.Vary(sim, paramVaryFile, fileHandle=fileHandle, varyTogether=varyTogether)
var.vary()
var.save()
