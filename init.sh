#Install wget
WGETLOC=$(which wget)
if [ -z "$WGETLOC" ]
then
    echo "ERROR: wget needs to be installed to download auxiliary files"
else
    echo "wget located at ${WGETLOC}"
fi

#Download atm files
wget http://pbfs.physics.berkeley.edu/BoloCalc/ATM/atm.zip
unzip atm.zip -d src/
rm atm.zip

#Create Experiment/ directory if it doesn't already exist
if [ -d "$Experiments/" ]
then
    echo "Experiments/ directory already exists"
else
    mkdir Experiments/
fi

#Download example experiment
wget http://pbfs.physics.berkeley.edu/BoloCalc/EX/ex.zip
unzip ex.zip -d Experiments/
rm ex.zip