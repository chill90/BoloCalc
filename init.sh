#Check which operating system you are on
if [ "$(uname)" -eq "Darwin" ]; then
    # Mac OSX
    OS='Linux'
    RM_CMD='rm'
elif [ "$(expr substr $(uname -s) 1 5)" -eq "Linux" ] 
then
    # Linux
    OS='Linux'
    RM_CMD='rm'
elif [ "$(expr substr $(uname -s) 1 10)" -eq "MINGW32_NT" ] 
then
    # Windows 32-bit
    OS='Windows'
    RM_CMD='del'
elif [ "$(expr substr $(uname -s) 1 10)" -eq "MINGW64_NT" ] 
then
    # Windows 64-bit
    OS='Windows'
    RM_CMD='del'
fi

#Install wget
if [ OS -eq 'Linux' ]
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
if [ -d "src/atmFiles/" ]
then
    echo
    echo "NOTE: src/atmFiles/ already exists. Do 'rm -r src/atmFiles/' to remove before re-downloading"
else
    if [ -f "atm.zip" ]
    then
	${RM_CMD} atm.zip
    fi
    wget http://pbfs.physics.berkeley.edu/BoloCalc/ATM/atm.zip
    unzip atm.zip -d src/
    ${RM_CMD} atm.zip
fi

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
