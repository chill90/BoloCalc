import sys     as sy
import            os
import getpass as gp

#Python 2 uses raw_input(), Python 3 uses input()
PY2 = (sy.version_info[0] == 2)

#Remove command is different on Windows
if sy.platform in ['win32']:
    rm_cmd = 'del'
else:
    rm_cmd = 'rm'

def exit():
    print ()
    print ('Usage: python importExperiments.py [ExperimentToImport]')
    print ('Available Experiments for download:')
    print ('"EX": An simple example experiment')
    print ('"SO": Simons Observatory files (password protected)')
    print ('"SA": Simons Array files (password protected)')
    print ()
    sy.exit(1)

def check(dir):
    isdir = os.path.isdir(dir)
    if isdir:
        while True:
            if PY2:
                answer = raw_input("Directory '%s' already exists. Overwrite data? [Y/N]: " % (dir))
            else:
                answer = input("Directory '%s' already exists. Overwrite data? [Y/N]: " % (dir))
            if answer == "" or answer.upper() == "N":
                return False
            elif answer.upper() == "Y":
                os.system("%s -r %s" % (rm_cmd, dir))
                return True
            else:
                print ("Could not understand answer '%s'" % (answer))
                print ()
    else:
        return True

def get(dir, rem_dir, file, pwd=False):
    ch = check(dir)
    if ch:
        if os.path.exists(file): os.system("%s %s" % (rm_cmd, file))
        if pwd:
            if PY2:
                uname = raw_input("Username: ")
            else:
                uname = input("Username: ")
            os.system("wget --user=%s --ask-password http://pbfs.physics.berkeley.edu/BoloCalc/%s/%s" % (uname, rem_dir, file))
        else:
            os.system("wget http://pbfs.physics.berkeley.edu/BoloCalc/%s/%s" % (rem_dir, file))
        os.system("unzip %s" % (file))
        os.system("%s %s" % (rm_cmd, file))
    return

args = sy.argv[1:]
if len(args) == 0:
    exit()
else:
    while len(args) > 0:
        if 'EX' in args[0].upper():
            dir = "ExampleExperiment"
            rem_dir = "EX"
            file = "ex.zip"
            get(dir, rem_dir, file, pwd=False)
            del args[0]            
        elif 'SA' in args[0].upper():
            dir = "SimonsArray"
            rem_dir = "SA"
            file = "sa.zip"
            get(dir, rem_dir, file, pwd=True)
            del args[0]            
        elif 'SO' in args[0].upper():
            dir = "SimonsObservatory"
            rem_dir = "SO"
            file = "so.zip"
            get(dir, rem_dir, file, pwd=True)
            del args[0]            
        else:
            print ('Could not understand argument "%s"' % (args[0]))
            exit()
