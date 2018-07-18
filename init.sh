#Install wget
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

#Download atm files
if [ -d "src/atmFiles/" ]
then
    echo
    echo "NOTE: src/atmFiles/ already exists. Do 'rm -r src/atmFiles/' to remove before re-downloading"
else
    wget http://pbfs.physics.berkeley.edu/BoloCalc/ATM/atm.zip
    unzip atm.zip -d src/
    rm atm.zip
fi

#Download example experiment
if [ -d "Experiments/ExampleExperiment/" ]
then
    echo
    echo "NOTE: Experiments/ExampleExperiment/ already exists. Do 'rm -r Experiments/ExampleExperiment/' to remove before re-downloading"
else
    wget http://pbfs.physics.berkeley.edu/BoloCalc/EX/ex.zip
    unzip ex.zip -d Experiments/
    rm ex.zip
fi

echo
