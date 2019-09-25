import sys as sy

# Verify the python version
if sy.version_info.major == 2:
    sy.stdout.write("\n***** Python 2 is no longer supported for "
                    "BoloCalc v0.10 (Sep 2019) and beyond *****\n\n")
    sy.exit()

import os  # noqa: E42

# Remove command is different on Windows
if sy.platform in ['win32']:
    rm_cmd = 'del'
else:
    rm_cmd = 'rm'


def exit():
    print("Usage: python importExperiments.py [ExperimentToImport]")
    print("Available Experiments for download:")
    print("'EX': An simple example experiment")
    print("'SO': Simons Observatory files (password protected)")
    print("'SA': Simons Array files (password protected)")
    sy.exit(1)


def check(inp_dir):
    isdir = os.path.isdir(inp_dir)
    if isdir:
        while True:
            answer = input(
                "Directory '%s' already exists. Overwrite data? [Y/N]: "
                % (inp_dir))
            answer = answer.upper()
            if answer == "" or answer == "N":
                return False
            elif answer == "Y":
                os.system("%s -r %s" % (rm_cmd, inp_dir))
                return True
            else:
                print("Could not understand answer '%s'\n" % (answer))
    else:
        return True


def get(inp_dir, rem_dir, inp_file, pwd=False):
    ch = check(inp_dir)
    if ch:
        if os.path.exists(inp_file):
            os.system("%s %s" % (rm_cmd, inp_file))
        if pwd:
            uname = input("Username: ")
            os.system(
                "wget --user=%s --ask-password "
                "http://pbfs.physics.berkeley.edu/BoloCalc/%s/%s"
                % (uname, rem_dir, inp_file))
        else:
            os.system(
                "wget http://pbfs.physics.berkeley.edu/BoloCalc/%s/%s"
                % (rem_dir, inp_file))
        os.system("unzip %s" % (inp_file))
        os.system("%s %s" % (rm_cmd, inp_file))
    return


# ***** MAIN *****
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
            print('Could not understand argument "%s"' % (args[0]))
            exit()
