import os
import json
import platform
import datetime
from pprint import pprint
from libraries.gen_class import Class
from PyQt5 import QtCore, QtGui

##################################################################################################
# Assign all the attriubtes from other settings files to the settings Class 
# Custom settings over written after all asignements 
##################################################################################################

settings = Class()
list_of_extra_settings = []

for extra_settings in list_of_extra_settings:
    for attribute in dir(extra_settings):
        if '__' not in attribute:
            setattr(settings, attribute, getattr(extra_settings, attribute))


##################################################################################################
# Defaults (likely overwritten by custom setting)
##################################################################################################

settings.experiments = {'LB': 'LiteBRID', 'SA': 'Simons Array', 'SO': 'Simons Observatory'}
settings.loaded_experiment = 'SA'

if 'Linux' in platform.platform():
    settings.platform = 'Linux'
    settings.load_still_image_as_camera = True
    settings.user = os.path.expanduser('~').split('/')[-1]
elif 'Windows' in platform.platform():
    settings.platform = 'Windows'
    settings.user = os.path.expanduser('~').split('\\')[-1]

# Query Stuff
today = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
settings.today = datetime.datetime.now()

# Layout Stuff
settings.title = 'BoloCalc Gui'
settings.small_font = QtGui.QFont("Times", 8)
settings.med_font = QtGui.QFont("Times", 11)
settings.large_font = QtGui.QFont("Times", 14)
settings.larger_font = QtGui.QFont("Times", 16)
settings.huge_font = QtGui.QFont("Times", 24)
settings.giant_font = QtGui.QFont("Times", 32)


# DICTIONARIES 
########################################################################################################################
##################################################################################################
# Custom settings over written after all asignements 
##################################################################################################
if os.path.exists('./all_settings/custom_settings.py'):
    from .custom_settings import custom_settings
    for attribute in dir(custom_settings):
        if hasattr(settings, attribute) and not '__' in attribute:
            setattr(settings, attribute, getattr(custom_settings, attribute))
