# Built-in modules
import numpy as np
import glob as gb
import collections as cl
import os

# BoloCalc modules
import src.parameter as pr
import src.opticalChain as oc
import src.channel as ch


class Camera:
    def __init__(self, tel, inp_dir):
        # Store passed parameters
        self.tel = tel
        self.dir = inp_dir

        # Check whether this camera exists
        if not os.path.isdir(self.dir):
            self._log().err("Camera dir '%s' does not exist" % (self.dir))

        # Check whether configuration directory exists
        self.config_dir = os.path.join(self.dir, 'config')
        if not os.path.isdir(self.config_dir):
            self._log().err(
                "Camera config dir '%s' does not exist"
                % (self.config_dir))

        # Band and distribution directories
        self.band_dir = os.path.join(self.configDir, "Bands")
        self.dist_dir = os.path.join(self.configDir, "pdf")

        # Name the camera
        self.name = self.dir.rstrip(os.sep).split(os.sep)[-1]

        # Store camera parameters into a dictionary
        self.cam_file = os.path.join(self.configDir, 'camera.txt')
        if not os.path.isfile(self.cam_file):
            self._log().err(
                "Camera file '%s' does not exist" % (self.cam_file))
        self._store_param_dict(self._load().camera(self.cam_file))

        # Generate camera
        self.generate()

    # ***** Public Methods *****
    def generate(self):
        # Generate camera parameters
        self.param_vals = {}
        for k in self.param_dict:
            self.param_vals[k] = self._param_samp(self.params_dict[k])

        # Store optical chain
        self.opt_chain = oc.OpticalChain(self)
        
        # Store channel objects
        self._log().log("Generating channels for camera %s" % (self.name), 1)
        self.detBandDict = self._band_dict(
            os.path.join(self.bandDir, 'Detectors'))
        self.chnFile = os.path.join(
            self.configDir, 'channels.txt')
        if not os.path.isdir(self.configDir):
            raise Exception("BoloCalc FATAL Exception: Telescope configuration \
                            directory '%s' does not exist" % (self.configDir))
        chans = np.loadtxt(self.chnFile, dtype=np.str, delimiter='|')
        keyArr = chans[0]
        elemArr = chans[1:]
        self.chanDicts = [{keyArr[i].strip(): elem[i].strip()
                          for i in range(len(keyArr))} for elem in elemArr]
        self.channels = cl.OrderedDict({})
        for chDict in self.chanDicts:
            if chDict['Band ID'] in self.channels.keys():
                raise Exception(
                    'FATAL: Multiple bands with the same name "%s" defined in \
                    camera "%s", telescope "%s", experiment "%s"' %
                    (chDict['Band ID'], self.name, self.telName, self.expName))
            self.channels.update(
                {chDict['Band ID']: ch.Channel(
                    self._log(), chDict, self, self.optChain, self.sky, self.scn,
                    detBandDict=self.detBandDict, nrealize=self.nrealize,
                    nobs=self.nobs, clcDet=self.clcDet, specRes=self.specRes)})
        # Store pixel dictionary
        self._log().log("Generating pixels for camera %s" % (self.name), 2)
        self.pixels = cl.OrderedDict({})
        for c in self.channels:
            if self.channels[c].pixelID in self.pixels.keys():
                self.pixels[self.channels[c].pixelID].append(self.channels[c])
            else:
                self.pixels[self.channels[c].pixelID] = [self.channels[c]]

    # ***** Private Methods *****
    def _log(self):
        return self.tel.exp.sim.log

    def _load(self):
        return self.tel.exp.sim.ld

    # Collect band files
    def _band_dict(self, dir):
        bandFiles = sorted(gb.glob(os.path.join(dir, '*')))
        if len(bandFiles):
            nameArr = [os.path.split(nm)[-1].split('.')[0]
                       for nm in bandFiles if "~" not in nm]
            if len(nameArr):
                return cl.OrderedDict(
                    {nameArr[i]: bandFiles[i] for i in range(len(nameArr))})
            else:
                return None
        else:
            return None

    # Sample camera parameters
    def _param_samp(self, param):
        if not ('instance' in str(type(param)) or 'class' in str(type(param))):
            return np.float(param)
        if self.nrealize == 1:
            return param.getAvg()
        else:
            return param.sample(nsample=1)

    def _store_param_dict(self, params):
        self.param_dict = {
            "bore_elev": pr.Parameter(
                    self._log(), "Boresight Elevation",
                    params["Boresight Elevation"], min=-40.0, max=40.0),
            "opt_coup": pr.Parameter(
                    self._log(), "Optical Coupling",
                    params["Optical Coupling"], min=0.0, max=1.0),
            "fnum": pr.Parameter(
                    self._log(), "F Number",
                    params["F Number"], min=0.0, max=np.inf),
            "bath_temp": pr.Parameter(
                    self._log(), "Bath Temp",
                    params["Bath Temp"], min=0.0, max=np.inf)}
