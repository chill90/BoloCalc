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
wget http://pbfs.physics.berkeley.edu/BoloCalc/ATM/atm.hdf5
mv atm.hdf5 src/
