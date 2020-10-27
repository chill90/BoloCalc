#Install python packages
PYTHON_3=$(which python3)
if [ -z "$PYTHON_3" ]
then
    python auxil/install_packages.py
else
    python3 auxil/install_packages.py
fi

#Check which operating system you are on
if [ "$(uname)" == "Darwin" ]; then
    # Mac OSX
    OS='Linux'
    RM_CMD='rm'
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ] 
then
    # Linux
    OS='Linux'
    RM_CMD='rm'
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ] 
then
    # Windows 32-bit
    OS='Windows'
    RM_CMD='del'
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ] 
then
    # Windows 64-bit
    OS='Windows'
    RM_CMD='del'
else
    OS='Linux'
    RM_CMD='rm'
fi

#Install wget
if [ OS == 'Linux' ]
then
    WGETLOC=$(which wget)
    if [ -z "$WGETLOC" ]
    then
	echo
	echo "ERROR: wget needs to be installed to download auxiliary files"
	echo
	exit 1
    else
	echo "wget located at ${WGETLOC}"
    fi
fi

#Download atm files
./update_atm.sh
#if [ -d "src/atmFiles/" ]
#then
#    echo
#    echo "NOTE: src/atmFiles/ no longer used by BoloCalc. We suggest removing it."
#fi
#wget http://pbfs.physics.berkeley.edu/BoloCalc/ATM/atm.hdf5
#mv atm.hdf5 src/

#Download example experiment
if [ -d "Experiments/ExampleExperiment/" ]
then
    echo
    echo "NOTE: Experiments/ExampleExperiment/ already exists. Do 'rm -r Experiments/ExampleExperiment/' to remove before re-downloading"
else
    if [ -f "ex.zip" ]
    then
	${RM_CMD} ex.zip
    fi
    wget http://pbfs.physics.berkeley.edu/BoloCalc/EX/ex.zip
    unzip ex.zip -d Experiments/
    ${RM_CMD} ex.zip
fi

echo
