import sys     as sy
import            os
import getpass as gp

def exit():
    print 
    print 'Usage: python importExperiments.py [ExperimentToImport]'
    print 'Available Experiments for download:'
    print '"EX": An simple example experiment'
    print '"SO": Simons Observatory files (password protected)'
    print '"SA": Simons Array files (password protected)'
    print
    sy.exit(1)
    
args = sy.argv[1:]
if len(args) == 0:
    exit()
else:
    while len(args) > 0:
        if 'EX' in args[0].upper():
            os.system("wget http://pbfs.physics.berkeley.edu/BoloCalc/EX/ex.zip")
            os.system("unzip ex.zip")
            os.system("rm ex.zip")
            del args[0]            
        elif 'SA' in args[0].upper():
            uname = raw_input( "Username: ")
            os.system("wget --user=%s --ask-password http://pbfs.physics.berkeley.edu/BoloCalc/SA/sa.zip" % (uname))
            os.system("unzip sa.zip")
            os.system("rm sa.zip")
            del args[0]
        elif 'SO' in args[0].upper():
            uname = raw_input( "Username: ")
            os.system("wget --user=%s --ask-password http://pbfs.physics.berkeley.edu/BoloCalc/SO/so.zip" % (uname))
            os.system("unzip so.zip")
            os.system("rm so.zip")
            del args[0]
        else:
            print ('Could not understand argument "%s"' % (args[0]))
            exit()
