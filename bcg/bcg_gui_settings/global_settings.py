import os
import json
import platform
import datetime
from pprint import pprint
from .main_panel import main_panel_settings
from .set_to_popup import set_to_popup_settings
from .new_special_file_popup import new_special_file_popup_settings
from .determine_special_file_popup import determine_special_file_popup_settings
from PyQt5 import QtCore, QtGui
from gui_builder.gui_builder import GenericClass

##################################################################################################
# Assign all the attriubtes from other settings files to the settings Class 
# Custom settings over written after all asignements 
##################################################################################################

settings = GenericClass()
list_of_extra_settings = [
        main_panel_settings, set_to_popup_settings,
        new_special_file_popup_settings, determine_special_file_popup_settings
        ]

settings.panels = {
    'cw_main_parameters_panel_widget': {
        'position': (5, 0, 1, 1),
        'layout': 'QGridLayout',
        },
    }

for extra_settings in list_of_extra_settings:
    for attribute in dir(extra_settings):
        if '__' not in attribute:
            setattr(settings, attribute, getattr(extra_settings, attribute))


settings.icon_size = 60

##################################################################################################
# Defaults (likely overwritten by custom setting)
##################################################################################################

settings.downloadable_experiment_dict = {
    'Simons Observatory': 'SO',
    'Simons Array': 'SA',
    'Example Experiment': 'EX'
    }

settings.experiment_dict = {
    'LiteBRID': 'LB',
    'Simons Observatory': 'SO',
    'Simons Array': 'SA',
    'Example Experiemt Observatory': 'EX'
    }

settings.sites =  [
    "ATACAMA",
    "POLE",
    "MCMURDO",
    "SPACE",
    "ROOM",
    "CUST"
    ]


settings.multiband_optical_properties = [
    'Absorption',
    'Reflection',
    'Spillover',
    'Scatter Frac'
    ]

settings.uneditiable_sweep_parameters = [
    'Telescope',
    'Camera',
    'Channel',
    'Optic',
    'Parameter'
    ]

settings.optics_column_order = [
    'Element',
    'Temperature',
    'Absorption',
    'Reflection',
    'Spillover',
    'Spillover Temp',
    'Scatter Frac',
    'Scatter Temp',
    'Thickness',
    'Index',
    'Loss Tangent',
    'Conductivity',
    'Surface Rough'
    ]


settings.preferred_output_names_dict = {
    'Telescope Temp':  "Telescope Temperature",
    'Sky Temp': "Sky Temperature",
    'Bolometer NEP': 'Thermal Carrier NEP'
    }

if 'Linux' in platform.platform():
    settings.platform = 'Linux'
    settings.user = os.path.expanduser('~').split('/')[-1]
elif 'Windows' in platform.platform():
    settings.platform = 'Windows'
    settings.user = os.path.expanduser('~').split('\\')[-1]
settings.bolo_calc_install_dir = os.path.abspath('.').replace('Gui', '')

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
settings.line_seperator_dict = {
    'telescope':  50,
    'foregrounds':  50,
    'site':  50,
    'pwv':  65,
    'camera':  75,
    'elevation':  50,
    'optics':  150,
    'channels':  100,
}

# DICTIONARIES 
settings.parameter_limits_json_path = './gui_settings/parameter_limits.json'

settings.optics_materials = ['Thickness', 'Index', 'Loss Tangent', 'Conductivity', 'Surface Rough']

settings.unit_dict = {
    'Num Det': '[NA]',
    'Optical Throughput': '[NA]',
    'Optical Power': '[pW]',
    'Telescope Temp': '[$\mathrm{K_{RJ}}$]',
    'Sky Temp': '[$\mathrm{K_{RJ}}$]',
    'Photon NEP': '[$\mathrm{aW / \sqrt{Hz}}$]',
    'Bolometer NEP': '[$\mathrm{aW / \sqrt{Hz}}$]',
    'Readout NEP': '[$\mathrm{aW / \sqrt{Hz}}$]',
    'Detector NEP': '[$\mathrm{aW / \sqrt{Hz}}$]',
    'Detector NET_CMB': '[$\mathrm{\mu K_{CMB} \sqrt{s}}$]',
    'Detector NET_RJ': '[$\mathrm{\mu K_{RJ} \sqrt{s}}$]',
    'Array NET_CMB': '[$\mathrm{\mu K_{CMB} \sqrt{s}}$]',
    'Array NET_RJ': '[$\mathrm{\mu K_{RJ} \sqrt{s}}$]',
    'Correlation Factor': '[NA]',
    'CMB Map Depth': '[$\mathrm{\mu K_{CMB} \; amin}$]',
    'RJ Map Depth': '[$\mathrm{\mu K_{RJ} \; amin}$]',
    'Psat': '[$pW$]',
    'Det Eff': ''
}


settings.label_dict = {
    'Num Det': '$\mathrm{N_{Det}}$',
    'Optical Throughput': '$\mathrm{\eta_{opt}}$',
    'Optical Power': '$\mathrm{P_{opt}}$',
    'Telescope Temp': '$\mathrm{T_{Tel}}$]',
    'Sky Temp': '$\mathrm{T_{Sky}}$',
    'Photon NEP': '$\mathrm{NEP_{ph}}$',
    'Bolometer NEP': '$\mathrm{NEP_{g}}$',
    'Readout NEP': '$\mathrm{NEP_{read}}$',
    'Detector NEP': '$\mathrm{NEP_{det}}$',
    'Detector NET_CMB': '$\mathrm{NET_{det}}$',
    'Detector NET_RJ': '$\mathrm{NET_{det}}$',
    'Array NET_CMB': '$\mathrm{NET_{arr}}$',
    'Array NET_RJ': '$\mathrm{NET_{arr}}$',
    'Correlation Factor': '$\mathrm{\Gamma_{corr}}$',
    'CMB Map Depth': '$\mathrm{\sigma_{map}}$',
    'RJ Map Depth': '$\mathrm{\sigma_{map}}$'
}

########################################################################################################################
##################################################################################################
# Custom settings over written after all asignements 
##################################################################################################
if os.path.exists('./all_settings/custom_settings.py'):
    from .custom_settings import custom_settings
    for attribute in dir(custom_settings):
        if hasattr(settings, attribute) and not '__' in attribute:
            setattr(settings, attribute, getattr(custom_settings, attribute))
