import re
import sys
import simplejson
import csv
import os
import shutil
import string
import operator
import subprocess
import platform
import time
import json
import glob
import datetime
import h5py as hp
import numpy as np
import pandas as pd
import pylab as pl
import seaborn as sns
import matplotlib
import decimal
from matplotlib import rc
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from pprint import pprint
from copy import copy, deepcopy
from PyQt5 import QtCore, QtGui, QtSvg, QtWidgets, Qt
from pdf2image import convert_from_path, convert_from_bytes

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from bcg_gui_settings.global_settings import settings
from src.unpack import Unpack
from gui_builder.gui_builder import GuiBuilder, GenericClass

# Globals for use between classes
timing = False
open_camera_window = True
run_timer = True
photo_taken = False

class BoloCalcGui(QtWidgets.QMainWindow, GuiBuilder):

    def __init__(self, screen_resolution, qt_app):
        '''
        '''
        super(BoloCalcGui, self).__init__()
        self.qt_app = qt_app
        self.splash_screen = QtWidgets.QSplashScreen()
        self.splash_screen_image = os.path.join(os.path.dirname(__file__), '..', 'bcg_gui_settings', 'SO_Site.jpeg')
        q_splash_image = QtGui.QPixmap(self.splash_screen_image)
        self.splash_screen.setPixmap(q_splash_image)
        self.splash_screen.show()
        self.splash_screen.showMessage('Connecting to Google', alignment=QtCore.Qt.AlignCenter, color=QtCore.Qt.white)
        self.bc_dir = os.path.join('..', 'BoloCalc')
        self.today = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
        self.count = 0
        self.row_start_index = 0
        self.row_end_index = 3
        self.n_enteries = 3
        self.col_start_index = 1
        self.n_col_enteries = 6
        self.col_end_index = 6
        self.current_channel_index = 0
        self.max_rows = 10
        self.splash_screen.showMessage('Welcome to BoloCaluCui!\nApplying Settings', alignment=QtCore.Qt.AlignCenter, color=QtCore.Qt.white)
        self.__apply_settings__(settings)
        # Set Scale Resolutions
        self.screen_resolution = copy(screen_resolution)
        self.title = 'Welcome to Bolo Calc!'
        self.setWindowTitle(self.title)
        # Set up grid and pallette
        grid = QtWidgets.QGridLayout()
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setWhatsThis('cw_panel')
        self.central_widget.setLayout(grid)
        self.setCentralWidget(self.central_widget)
        cw_main_parameters_panel_widget = QtWidgets.QWidget()
        self.cw_main_parameters_panel_widget = cw_main_parameters_panel_widget
        self.tool_and_menu_bar_json_path = os.path.join(os.path.dirname(__file__), '..', 'bcg_gui_settings', 'tool_and_menu_bars.json')
        self.bcg_setup_template()
        self.bcg_setup_status_bar()
        self.gb_setup_menu_and_tool_bars(self.tool_and_menu_bar_json_path)
        [x for x in self.main_menu.actions() if x.text() == 'Parameter'][0].setDisabled(True)
        self.parameter_qmw_tool_bar.setDisabled(True)
        palette_gray = self.palette()
        palette_gray.setColor(self.backgroundRole(), QtCore.Qt.gray)
        self.central_widget.setPalette(palette_gray)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.sizePolicy().setHorizontalPolicy(0)
        self.current_last_col = 0
        self.panel = 'channels'
        self.bcg_get_downloaded_experiments()
        self.has_loaded_experiment = False
        self.set_to_widget = None
        self.unpack = Unpack()
        datetime_str = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        self.splash_screen.showMessage('Welcome to BoloCaluCui!\nSettings Up Templates', alignment=QtCore.Qt.AlignCenter, color=QtCore.Qt.white)
        self.bolo_calc_dir = os.getcwd().replace('BoloCalcGui', 'BoloCalc')
        self.blank_cust_txt_file = os.path.join('templates', 'blank_cust_file.txt')
        self.blank_cust_csv_file = os.path.join('templates', 'blank_cust_file.csv')
        self.blank_pdf_txt_file = os.path.join('templates', 'blank_pdf_file.txt')
        self.blank_pdf_csv_file =  os.path.join('templates','blank_pdf_file.csv')
        self.blank_band_txt_file =  os.path.join('templates','blank_band_file.txt')
        self.blank_band_csv_file = os.path.join('templates', 'blank_band_file.csv')
        self.setWindowTitle('Welcome to BoloCalc!')
        self.setWindowIcon(QtGui.QIcon('../GuiBuilder/icons/bolo_calc.png'))
        self.splash_screen.showMessage('Welcome to BoloCaluCui!\nSettings Up Tabs',  alignment=QtCore.Qt.AlignCenter, color=QtCore.Qt.white)
        self.bcg_setup_tabs('experiment')
        self.bcg_setup_tabs('version')
        self.bcg_setup_tabs('telescope')
        self.bcg_setup_tabs('camera')
        self.bcg_setup_tabs('channel')
        self.splash_screen.showMessage('Welcome to BoloCaluCui!\nLoading Experiment', alignment=QtCore.Qt.AlignCenter, color=QtCore.Qt.white)
        self.saved = True
        self.bcg_load_experiment(experiment='ExampleExperiment')
        self.move(0, 10)
        self.splash_screen.showMessage('Welcome to BoloCaluCui!\nInitializing Gui',  alignment=QtCore.Qt.AlignCenter, color=QtCore.Qt.white)
        fig = plt.figure(figsize=(8,8))
        fig.savefig('temp.png')
        os.remove('temp.png')
        self.show()
        self.splash_screen.close()
        self.qt_app.processEvents()
        self.panel = 'channels'
        self.bcg_change_panel(panel=self.panel)
        self.resize(self.screen_resolution.width(), self.minimumSizeHint().height())
        self.show_bc_warnings = True
        #self.bcg_verify()
        self.show_descriptions = True
        show_descr_icon_path = os.path.join('..', 'GuiBuilder', 'icons', 'show_descr.png')
        self.q_show_descr_icon = QtGui.QIcon(show_descr_icon_path)
        hide_descr_icon_path = os.path.join('..', 'GuiBuilder', 'icons', 'hide.png')
        self.q_hide_descr_icon = QtGui.QIcon(hide_descr_icon_path)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setFocus()

    #################################################
    #################################################
    # #################GUI BUILDER AND DYNAMICS
    #################################################
    #################################################

    def bcg_setup_tabs(self, tab_bar, widget='central_widget'):
        '''
        '''
        if tab_bar == 'experiment':
            experiment_tab_bar = QtWidgets.QTabBar()
            tab_bar_name = '{0}_experiment_tab_bar'.format(widget)
            setattr(self, tab_bar_name, experiment_tab_bar)
            getattr(self, tab_bar_name).setWhatsThis('{0}_experiment_tab_bar'.format(widget))
            getattr(self, tab_bar_name).currentChanged.connect(self.bcg_change_experiment)
            getattr(self, tab_bar_name).tabCloseRequested.connect(self.bcg_remove_experiment)
            getattr(self, widget).layout().addWidget(experiment_tab_bar, 0, 0, 1, 1)
        #Versions
        if tab_bar == 'version':
            version_tab_bar = QtWidgets.QTabBar()
            tab_bar_name = '{0}_version_tab_bar'.format(widget)
            if hasattr(self, tab_bar_name):
                getattr(self, tab_bar_name).setParent(None)
            setattr(self, tab_bar_name, version_tab_bar)
            getattr(self, tab_bar_name).setWhatsThis('{0}_version_tab_bar'.format(widget))
            getattr(self, tab_bar_name).currentChanged.connect(self.bcg_change_version)
            getattr(self, widget).layout().addWidget(version_tab_bar, 1, 0, 1, 1)
        #Telescopes
        if tab_bar == 'telescope':
            telescope_tab_bar = QtWidgets.QTabBar()
            tab_bar_name = '{0}_telescope_tab_bar'.format(widget)
            if hasattr(self, tab_bar_name):
                getattr(self, tab_bar_name).setParent(None)
            setattr(self, tab_bar_name, telescope_tab_bar)
            getattr(self, tab_bar_name).currentChanged.connect(self.bcg_change_telescope)
            getattr(self, tab_bar_name).setWhatsThis('{0}_telescope_tab_bar'.format(widget))
            getattr(self, widget).layout().addWidget(getattr(self, tab_bar_name), 2, 0, 1, 1)
        #Cameras
        if tab_bar == 'camera':
            camera_tab_bar = QtWidgets.QTabBar()
            tab_bar_name = '{0}_camera_tab_bar'.format(widget)
            if hasattr(self, tab_bar_name):
                getattr(self, tab_bar_name).setParent(None)
            setattr(self, tab_bar_name, camera_tab_bar)
            getattr(self, tab_bar_name).currentChanged.connect(self.bcg_change_camera)
            getattr(self, tab_bar_name).setWhatsThis('{0}_camera_tab_bar'.format(widget))
            getattr(self, widget).layout().addWidget(getattr(self, tab_bar_name), 3, 0, 1, 1)
        if tab_bar == 'channel':
            channel_tab_bar = QtWidgets.QTabBar()
            tab_bar_name = '{0}_channel_tab_bar'.format(widget)
            if hasattr(self, tab_bar_name):
                getattr(self, tab_bar_name).setParent(None)
            setattr(self, tab_bar_name, channel_tab_bar)
            getattr(self, tab_bar_name).currentChanged.connect(self.bcg_change_channel)
            getattr(self, tab_bar_name).setWhatsThis('{0}_channels_tab_bar'.format(widget))
            getattr(self, widget).layout().addWidget(getattr(self, tab_bar_name), 4, 0, 1, 1)

    def bcg_change_experiment(self, clicked=True):
        '''
        '''
        experiment_index = self.sender().currentIndex()
        self.experiment = self.sender().tabText(experiment_index)
        self.bcg_change_version()
        self.bcg_configure_tab_bar('version')

    def bcg_change_version(self):
        '''
        '''
        version_index = self.sender().currentIndex()
        version = self.sender().tabText(version_index)
        if len(self.experiment) == 0:
            self.experiment = self.central_widget_experiment_tab_bar.tabText(0)
        if version in self.experiment_dict[self.experiment]:
            self.version = version
        else:
            self.version = list(self.experiment_dict[self.experiment].keys())[0]
        self.versions = list(self.experiment_dict[self.experiment].keys())
        self.bcg_change_telescope()
        self.bcg_configure_tab_bar('telescope')

    def bcg_change_telescope(self):
        '''
        '''
        telescope_index = self.sender().currentIndex()
        telescope = self.sender().tabText(telescope_index)
        if telescope in self.experiment_dict[self.experiment][self.version]:
            self.telescope = telescope
        else:
            self.telescope = list(self.experiment_dict[self.experiment][self.version].keys())[0]
        self.telescopes = list(self.experiment_dict[self.experiment][self.version].keys())[0]
        self.bcg_change_camera()
        self.bcg_configure_tab_bar('camera')

    def bcg_change_camera(self):
        '''
        '''
        camera_index = self.sender().currentIndex()
        camera = self.sender().tabText(camera_index)
        if camera in self.experiment_dict[self.experiment][self.version][self.telescope]:
            self.camera = camera
        else:
            self.camera = self.experiment_dict[self.experiment][self.version][self.telescope][0]
        self.cameras = self.experiment_dict[self.experiment][self.version][self.telescope]
        self.bcg_get_panel_parameter_path()
        prev_panel = self.panel
        self.bcg_setup_template()
        self.panel = prev_panel
        self.bcg_change_panel(panel=self.panel)
        self.bcg_configure_tab_bar('channel')
        self.channels = [str(x) for x in self.channels_dataframe['Band ID']]
        self.bcg_change_channel()

    def bcg_change_channel(self):
        '''
        '''
        channel_index = self.sender().currentIndex()
        channel = self.sender().tabText(channel_index)
        if ':' in channel:
            channel = channel.split(':')[1].strip()
            self.bcg_select_all_channel_values(channel)

    def bcg_configure_tab_bar(self, tab_bar_name, whatsThis=None):
        '''
        '''
        if whatsThis is None:
            if hasattr(self.sender(), 'whatsThis'):
                whatsThis = self.sender().whatsThis()
            else:
                whatsThis = ''
        if len(whatsThis) == 0:
            return None
        widget = None
        if 'central_widget' in whatsThis or 'action_' in whatsThis:
            widget = 'central_widget'
        elif 'analysis_popup' in whatsThis:
            widget = 'analysis_popup'
        if widget is None:
            return None
        tab_bar_full_name = '{0}_{1}_tab_bar'.format(widget, tab_bar_name)
        if not hasattr(self, '{0}s'.format(tab_bar_name)):
            return None
        else:
            getattr(self, '{0}s'.format(tab_bar_name))
        if not hasattr(self, tab_bar_full_name):
            return None
        else:
            getattr(self, tab_bar_full_name).setParent(None)
        self.bcg_setup_tabs(tab_bar_name)
        if tab_bar_name == 'version':
            new_tabs = list(self.experiment_dict[self.experiment].keys())
        elif tab_bar_name == 'telescope':
            new_tabs = list(self.experiment_dict[self.experiment][self.version].keys())
        elif tab_bar_name == 'camera':
            new_tabs = self.experiment_dict[self.experiment][self.version][self.telescope]
            camera = self.camera
        elif tab_bar_name == 'channel':
            new_tabs = []
            if self.panel == 'optics':
                new_tabs = ['Band ID: {0}'.format(str(x)) for x in self.channels_dataframe['Band ID']]
        else:
            return None
        tab_bar = getattr(self, tab_bar_full_name)
        for i, tab in enumerate(new_tabs):
            add = True
            for j, child in enumerate(tab_bar.children()):
                if tab_bar_name == 'channel':
                    tab_bar.setTabTextColor(j, QtGui.QColor('blue'))
                tab_text = tab_bar.tabText(j)
                if tab_text == tab:
                    add = False
            if add:
                tab_bar.addTab(tab)
                if tab_bar_name == 'channel':
                    tab_bar.setTabTextColor(i, QtGui.QColor('blue'))

    def bcg_set_tab_index(self, tab_bar_type):
        '''
        '''
        tab_bar = getattr(self, 'central_widget_{0}_tab_bar'.format(tab_bar_type))
        current_element = getattr(self, tab_bar_type)
        for i in range(tab_bar.count()):
            tab_text = tab_bar.tabText(i)
            if tab_text == current_element:
                current_tab_index = i
                break
        tab_bar.setCurrentIndex(current_tab_index)
        self.repaint()

    def bcg_download_experiment_popup(self):
        '''
        '''
        if hasattr(self, 'BCG_download_experiement_popup'):
            self.BCG_download_experiement_popup.close()
        BCG_download_experiement_popup = QtWidgets.QWidget()
        BCG_download_experiement_popup.setLayout(QtWidgets.QGridLayout())
        self.BCG_download_experiement_popup = BCG_download_experiement_popup
        q_download_combobox = QtWidgets.QComboBox(self.BCG_download_experiement_popup)
        self.q_download_combobox = q_download_combobox
        BCG_download_experiement_popup.layout().addWidget(q_download_combobox, 0, 0, 1, 2)
        for experiment in sorted(self.downloadable_experiment_dict):
            q_download_combobox.addItem(experiment)
        #Username
        q_username_label = QtWidgets.QLabel('Username:', self.BCG_download_experiement_popup)
        BCG_download_experiement_popup.layout().addWidget(q_username_label, 1, 0, 1, 1)
        q_username_lineedit = QtWidgets.QLineEdit(self.BCG_download_experiement_popup)
        self.q_username_lineedit= q_username_lineedit
        BCG_download_experiement_popup.layout().addWidget(q_username_lineedit, 1, 1, 1, 1)
        #PW
        q_password_label = QtWidgets.QLabel('Password:', self.BCG_download_experiement_popup)
        BCG_download_experiement_popup.layout().addWidget(q_password_label, 2, 0, 1, 1)
        q_password_lineedit = QtWidgets.QLineEdit(self.BCG_download_experiement_popup)
        self.q_password_lineedit= q_password_lineedit
        BCG_download_experiement_popup.layout().addWidget(q_password_lineedit, 2, 1, 1, 1)
        # Load?
        q_load_after_download_checkbox = QtWidgets.QCheckBox('Load after DL', self.BCG_download_experiement_popup)
        self.q_load_after_download_checkbox = q_load_after_download_checkbox
        q_load_after_download_checkbox.setChecked(True)
        BCG_download_experiement_popup.layout().addWidget(q_load_after_download_checkbox, 3, 0, 1, 1)
        # Download button
        q_download_pushbutton = QtWidgets.QPushButton('Download', self.BCG_download_experiement_popup)
        self.q_download_pushbutton = q_download_pushbutton
        q_download_pushbutton.clicked.connect(self.bcg_start_downloading_experiment)
        BCG_download_experiement_popup.layout().addWidget(q_download_pushbutton, 3, 1, 1, 1)
        # Download progress bar
        q_download_progress_bar = QtWidgets.QProgressBar(self.BCG_download_experiement_popup)
        self.download_progress_bar = q_download_progress_bar
        BCG_download_experiement_popup.layout().addWidget(q_download_progress_bar, 4, 0, 1, 2)
        # Run and set function
        experiment, wget_cmd, full_path, file_path = self.bcg_experiment_to_download_wget_command()
        q_download_combobox.currentIndexChanged.connect(self.bcg_experiment_to_download_wget_command)
        self.BCG_download_experiement_popup.show()

    def bcg_experiment_to_download_wget_command(self):
        '''
        '''
        experiment = self.q_download_combobox.currentText()
        short_name = self.downloadable_experiment_dict[experiment]
        directory = experiment.replace(' ', '')
        file_name = '{0}.zip'.format(short_name).lower()
        full_path = os.path.join(self.bolo_calc_install_dir, 'Experiments', directory)
        if experiment == 'Example Experiment':
            self.q_username_lineedit.setDisabled(True)
            self.q_password_lineedit.setDisabled(True)
            wget_cmd = "wget http://pbfs.physics.berkeley.edu/BoloCalc/{0}/{1}".format(short_name.upper(), file_name)
        else:
            self.q_username_lineedit.setDisabled(False)
            self.q_password_lineedit.setDisabled(False)
            username = self.q_username_lineedit.text()
            password = self.q_password_lineedit.text()
            wget_cmd = "wget --user {0} --password {1} http://pbfs.physics.berkeley.edu/BoloCalc/{2}/{3}".format(username, password, short_name, file_name)
        return experiment, wget_cmd, full_path, file_name

    def bcg_start_downloading_experiment(self):
        '''
        '''
        experiment, wget_cmd, full_path, file_name = self.bcg_experiment_to_download_wget_command()
        if os.path.exists(full_path):
            msg = '{0} Exists\nDelete and Proceed?'.format(full_path)
            response = self.gb_quick_message(msg, add_yes=True, add_cancel=True, msg_type='Warning')
            if response == QtWidgets.QMessageBox.Cancel:
                return None
            shutil.rmtree(full_path, ignore_errors=True)
        self.update_count = 0
        self.download_progress_bar.setValue(self.update_count)
        q_process = QtCore.QProcess()
        q_process.start(wget_cmd)
        q_process.finished.connect(lambda: self.bcg_finish_download(q_process))

    def bcg_update_download_progress_bar(self, q_process):
        '''
        '''
        self.update_count += 1
        q_process.readAllStandardOutput()
        self.download_progress_bar.setValue(self.update_count)

    def bcg_finish_download(self, q_process):
        '''
        '''
        experiment, wget_cmd, full_path, file_name = self.bcg_experiment_to_download_wget_command()
        experiment = experiment.replace(' ', '')
        if os.path.exists(file_name):
            self.download_progress_bar.setValue(100)
            if os.path.exists(experiment):
                shutil.rmtree(experiment, ignore_errors=True)
            q_process = QtCore.QProcess()
            q_process.readyReadStandardOutput.connect(lambda: self.bcg_update_download_progress_bar(q_process))
            q_process.start("unzip {0}".format(file_name))
            q_process.finished.connect(self.bcg_cleanup_download)
        else:
            self.download_progress_bar.setValue(0)
            msg = 'WGET failed to fetch the experiment. Please check for:\n'
            msg += '1) Username and/or Password\n'
            msg += '2) File Permission\n'
            msg += '3) Open File(s) (especially on Windows)\n'
            self.gb_quick_message(msg, msg_type='Warning')

    def bcg_cleanup_download(self):
        '''
        '''
        self.download_progress_bar.setValue(100)
        experiment, wget_cmd, full_path, file_name = self.bcg_experiment_to_download_wget_command()
        experiment = experiment.replace(' ', '')
        os.remove(file_name)
        shutil.move(experiment, full_path)
        self.bcg_get_downloaded_experiments()
        if self.q_load_after_download_checkbox.isChecked():
            self.bcg_load_experiment(experiment=experiment)
            self.bcg_change_panel(panel='channels')
        self.BCG_download_experiement_popup.close()

    def bcg_wget_experiment(self, inp_dir, rem_dir, inp_file, pwd=False):
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

    def bcg_load_experiment(self, clicked=True, experiment=None):
        '''
        '''
        experiment_dir = os.path.join(self.bc_dir, 'Experiments')
        if experiment is None:
            experiment_path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Wafer Folder', experiment_dir)
            if len(experiment_path) == 0:
                return None
            self.experiment = os.path.basename(experiment_path)
        else:
            self.experiment = experiment
        add_experiment = False
        if self.central_widget_experiment_tab_bar.count() == 0:
            add_experiment = True
        else:
            add_experiment = True
            for i in range(self.central_widget_experiment_tab_bar.count()):
                self.central_widget_experiment_tab_bar.tabText(i)
                if self.experiment == self.central_widget_experiment_tab_bar.tabText(i):
                    add_experiment = False
        if add_experiment:
            index = self.central_widget_experiment_tab_bar.addTab(self.experiment)
            self.central_widget_experiment_tab_bar.setCurrentIndex(index)
            if index >= 1:
                self.central_widget_experiment_tab_bar.setTabsClosable(True)
            self.versions = list(self.experiment_dict[self.experiment].keys())
            self.version = self.versions[0]
            self.bcg_configure_tab_bar('version')
            self.telescopes = list(self.experiment_dict[self.experiment][self.version].keys())
            self.telescope = self.telescopes[0]
            self.bcg_configure_tab_bar('telescope')
            self.cameras = self.experiment_dict[self.experiment][self.version][self.telescope]
            self.camera = self.cameras[0]
            self.bcg_configure_tab_bar('camera')
            self.gb_initialize_panel('cw_main_parameters_panel_widget')
            self.bcg_get_panel_parameter_path()
            self.bcg_setup_template()
            self.bcg_build_parameter_panel()
            self.parameter_qmw_tool_bar.setDisabled(False)
            [x.setDisabled(False) for x in self.main_menu.actions()]
            self.bcg_change_panel(panel='channels')

    def bcg_remove_experiment(self, tab_index):
        '''
        '''
        self.central_widget_experiment_tab_bar.removeTab(tab_index)
        active_experiment_count = 0
        for i in range(self.central_widget_experiment_tab_bar.count()):
            if not self.central_widget_experiment_tab_bar.tabRemoved(i):
                active_experiment_count += 1
        if active_experiment_count > 1:
            self.central_widget_experiment_tab_bar.setTabsClosable(True)
        else:
            self.central_widget_experiment_tab_bar.setTabsClosable(False)

    def bcg_setup_custom_status_bar_widgets(self):
        '''
        '''
        # N Display Rows
        custom_widgets = []
        n_display_label = QtWidgets.QLabel('N Display Rows:', self)
        n_display_label.setAlignment(QtCore.Qt.AlignRight)
        custom_widgets.append(n_display_label)
        n_display_label.setAlignment(QtCore.Qt.AlignBottom)
        custom_widgets.append(n_display_label)
        self.n_display_rows_lineedit = QtWidgets.QLineEdit('7', self)
        self.n_display_rows_lineedit.setValidator(QtGui.QIntValidator(1, self.max_rows, self.n_display_rows_lineedit))
        self.n_display_rows_lineedit.setFixedWidth(50)
        self.n_display_rows_lineedit.setAlignment(QtCore.Qt.AlignRight)
        self.n_display_rows_lineedit.setAlignment(QtCore.Qt.AlignBottom)
        self.n_display_rows_lineedit.returnPressed.connect(self.bcg_scroll_elements)
        custom_widgets.append(self.n_display_rows_lineedit)
        # Progress Bars
        for i, progress_type in enumerate(['sim', 'vary', 'write']):
            q_progress_label = QtWidgets.QLabel('{0} Progress:'.format(progress_type.title()), self)
            q_progress_label.setAlignment(QtCore.Qt.AlignRight)
            q_progress_label.setAlignment(QtCore.Qt.AlignBottom)
            custom_widgets.append(q_progress_label)
            q_progress_bar = QtWidgets.QProgressBar(self)
            q_progress_bar.setValue(0)
            q_progress_bar.setAlignment(QtCore.Qt.AlignBottom)
            q_progress_bar.setFixedWidth(150)
            custom_widgets.append(q_progress_bar)
            setattr(self, '{0}_progress_bar'.format(progress_type), q_progress_bar)
        # Working Saved Status
        q_saved_status_label = QtWidgets.QLabel('save_status_label', self)
        q_saved_status_label.setWhatsThis('saved_status_label')
        q_saved_status_label.setText('Last Saved at: Not Saved |')
        q_saved_status_label.setAlignment(QtCore.Qt.AlignBottom)
        self.saved_status_label = q_saved_status_label
        custom_widgets.append(q_saved_status_label)
        # Working Save Path
        q_save_path_label = QtWidgets.QLabel('save_path_label', self)
        q_save_path_label.setWhatsThis('save_path_label')
        q_save_path_label.setAlignment(QtCore.Qt.AlignBottom)
        custom_widgets.append(q_save_path_label)
        self.save_path_label = q_save_path_label
        return custom_widgets

    def bcg_setup_status_bar(self):
        '''
        '''
        custom_widgets = []
        custom_widgets = self.bcg_setup_custom_status_bar_widgets()
        #custom_widgets.append(custom_widget)
        permanant_messages = ['C.A.H and B.W. 2020']
        self.gb_add_status_bar(permanant_messages=permanant_messages , add_saved=True, custom_widgets=custom_widgets)
        #import ipdb;ipdb.set_trace()

    def bcg_close_hard(self):
        '''
        '''
        if not self.saved:
            message = 'You have unsaved changes, are you sure you want to quit BoloCalcGui?'
            result = self.gb_quick_message(msg=message, add_cancel=True, add_discard=True, add_save=True)
            if result == QtWidgets.QMessageBox.Save:
                self.bcg_save_changes()
                os._exit(0)
            elif result == QtWidgets.QMessageBox.Discard or result == QtWidgets.QMessageBox.Yes:
                os._exit(0)
        else:
            os._exit(0)

    def bcg_get_element_to_change_name(self, new_element, action):
        if new_element == 'Version':
            existing_elements = list(self.experiment_dict[self.experiment].keys())
        elif new_element == 'Telescope':
            existing_elements = list(self.experiment_dict[self.experiment][self.version].keys())
        elif new_element == 'Camera':
            existing_elements = self.experiment_dict[self.experiment][self.version][self.telescope]
        if len(existing_elements) == 1 and action == 'delete':
            msg = 'You must have at least one valid {0}'.format(new_element.lower())
            self.gb_quick_message(msg)
            return None, None
        dialog ='What {0} you like to delete?'.format(new_element.lower())
        name_to_delete, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=existing_elements)
        result = re.fullmatch('[A-Z0-9a-z-]*', name_to_delete)
        return name_to_delete, okPressed

    def bcg_get_new_element_name(self, new_element):
        '''
        '''
        new_name, okPressed = self.gb_quick_info_gather('{0}'.format(new_element), 'New {0} Name:'.format(new_element))
        if new_element == 'Experiment':
            existing_elements = list(self.experiment_dict.keys())
        elif new_element == 'Version':
            existing_elements = list(self.experiment_dict[self.experiment].keys())
        elif new_element == 'Telescope':
            existing_elements = list(self.experiment_dict[self.experiment][self.version].keys())
        elif new_element == 'Camera':
            existing_elements = self.experiment_dict[self.experiment][self.version][self.telescope]
            #import ipdb;ipdb.set_trace()
        result = re.fullmatch('[A-Z0-9a-z-]*', new_name)
        if result is None:
            self.gb_quick_message('Please use only alphanumerics and hypens')
            return '', False
        if new_name in existing_elements:
            msg = 'New name "{0}" exists!\n'.format(new_name)
            msg += 'New {0} cannot be in: {1}'.format(new_element.lower(), existing_elements)
            self.gb_quick_message(msg)
            new_name, okPressed = self.bcg_get_new_element_name(new_element)
        return new_name, okPressed

    def bcg_new(self):
        '''
        '''
        items = ['Experiment', 'Version', 'Telescope', 'Camera']
        new_element, okPressed = self.gb_quick_static_info_gather(title='', dialog='What would you like make a new one of?', items=items)
        if okPressed:
            new_name, okPressed = self.bcg_get_new_element_name(new_element)
        if okPressed:
            msg = 'You are creating a new {0} named {1}, '.format(new_element.lower(), new_name)
            msg += 'from a copy of {0} including all children\n'.format(getattr(self, new_element.lower()))
            msg += 'Would you like to proceed?'
            response = self.gb_quick_message(msg, add_yes=True, add_cancel=True)
        else:
            response = None
        if response == QtWidgets.QMessageBox.Yes:
            if new_element == 'Experiment':
                old_path = os.path.join(self.bc_dir, 'Experiments', self.experiment)
                new_path = os.path.join(self.bc_dir, 'Experiments', new_name)
                self.experiment = new_name
            elif new_element == 'Version':
                old_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, self.version)
                new_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, new_name)
                self.version = new_name
            elif new_element == 'Telescope':
                old_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, self.version, self.telescope)
                new_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, self.version, new_name)
                self.telescope = new_name
            elif new_element == 'Camera':
                old_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, self.version, self.telescope, self.camera)
                new_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, self.version, self.telescope, new_name)
                bands_path = os.path.join(new_path, 'config', 'Bands', 'Detectors')
            shutil.copytree(old_path, new_path)
            if new_element == 'Camera':
                for file_name in os.listdir(bands_path):
                    old_file_path = os.path.join(bands_path, file_name)
                    file_name = file_name.replace(self.camera, new_name)
                    new_file_path = os.path.join(bands_path, file_name)
                    shutil.move(old_file_path, new_file_path)
                self.camera = new_name
            self.bcg_get_downloaded_experiments()
            self.bcg_setup_template()
            if new_element == 'Experiment':
                self.bcg_load_experiment(experiment=new_name)
            else:
                self.bcg_setup_tabs(new_element.lower())
                self.bcg_configure_tab_bar(new_element.lower())
            if new_element == 'Experiment':
                self.experiment = new_name
            elif new_element == 'Version':
                self.version = new_name
            elif new_element == 'Telescope':
                self.telescope = new_name
            elif new_element == 'Camera':
                self.camera = new_name
            self.panel = 'channels'
            self.bcg_build_parameter_panel()
            self.bcg_set_tab_index(new_element.lower())
            self.repaint()
        elif response == QtWidgets.QMessageBox.Cancel:
            pass

    def bcg_delete_or_rename(self):
        '''
        '''
        action = self.sender().text().lower()
        items = ['Version', 'Telescope', 'Camera']
        new_element, okPressed = self.gb_quick_static_info_gather(title='', dialog='What would you like to {0}?'.format(action), items=items)
        if okPressed:
            old_name, okPressed = self.bcg_get_element_to_change_name(new_element, action)
        if okPressed:
            msg = 'You are deleting a {0} named {1}, '.format(new_element.lower(), old_name)
            msg += 'This is process is not undoable!!!\n'
            msg += 'Would you still like to proceed?'
            response = self.gb_quick_message(msg, add_yes=True, add_cancel=True)
        else:
            response = None
        if response == QtWidgets.QMessageBox.Yes:
            if new_element == 'Experiment':
                old_path = os.path.join(self.bc_dir, 'Experiments', new_name)
            elif new_element == 'Version':
                old_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, old_name)
            elif new_element == 'Telescope':
                old_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, self.version, old_name)
            elif new_element == 'Camera':
                old_path = os.path.join(self.bc_dir, 'Experiments', self.experiment, self.version, self.telescope, old_name)
            if action == 'delete':
                shutil.rmtree(old_path, ignore_errors=True)
            elif action == 'rename':
                new_name, okPressed = self.gb_quick_info_gather('{0}'.format(new_element), 'New Name:')
                result = re.fullmatch('[A-Z0-9a-z-]*', new_name)
                if result is None:
                    self.gb_quick_message('Please use only alphanumerics and hypens')
                    okPressed = False
                if not okPressed:
                    return None
                new_path = old_path.replace(old_name, new_name)
                if new_element.lower() == 'camera':
                    self.bcg_rename_cam_files(old_path, old_name, new_name)
                try:
                    shutil.move(old_path, new_path)
                except PermissionError:
                    self.gb_quick_message('You have an open file in the old directory!\nPlease close')
            self.bcg_get_downloaded_experiments()
            if getattr(self, '{0}'.format(new_element.lower())) == old_name:
                #import ipdb;ipdb.set_trace()
                if new_element == 'Version':
                    existing_elements = list(self.experiment_dict[self.experiment].keys())
                    self.version = existing_elements[0]
                elif new_element == 'Telescope':
                    existing_elements = list(self.experiment_dict[self.experiment][self.version].keys())
                    self.telescope = existing_elements[0]
                elif new_element == 'Camera':
                    existing_elements = self.experiment_dict[self.experiment][self.version][self.telescope]
                    self.camera = existing_elements[0]
            self.bcg_setup_template()
            self.bcg_setup_tabs(new_element.lower())
            self.bcg_configure_tab_bar(new_element.lower())
        elif response == QtWidgets.QMessageBox.Cancel:
            pass

    def bcg_rename_cam_files(self, old_path, old_name, new_name):
        '''
        '''
        detector_band_dir = os.path.join(old_path, 'config', 'Bands', 'Detectors')
        for file_name in os.listdir(detector_band_dir):
            new_file_name = file_name.replace(old_name, new_name)
            old_path = os.path.join(detector_band_dir, file_name)
            new_path = os.path.join(detector_band_dir, new_file_name)
            shutil.move(old_path, new_path)

    def bcg_delete_channel_from_optics_dataframe(self, dataframe, delete_channel):
        '''
        '''
        self.channel_dataframe = dataframe
        self.channels = [str(x) for x in self.channel_dataframe['Band ID']]
        for parameter in self.multiband_optical_properties:
            for element_index in self.optics_dataframe[parameter].index:
                element_data_dicts = self.optics_dataframe.loc[element_index, parameter]
                if type(element_data_dicts) == list:
                    for data_dict in element_data_dicts:
                        data_dict.pop(delete_channel)
        self.bcg_save_changes(panel='optics')
        self.bcg_save_changes(panel='channels')
        self.saved = True
        datetime_str = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        save_str = 'Last Saved at {0} |'.format(datetime_str)
        self.saved_status_label.setText(save_str)

    def bcg_change_channel_name_in_optics_dataframe(self, new_name):
        '''
        '''
        self.channels = [str(x) for x in self.channels_dataframe['Band ID']]
        for parameter in self.multiband_optical_properties:
            for element_index in self.optics_dataframe[parameter].index:
                element_data_dicts = self.optics_dataframe.loc[element_index, parameter]
                if type(element_data_dicts) == list:
                    for data_dict in element_data_dicts:
                        data_dict[new_name] = data_dict[self.previous_value]
                        data_dict.pop(self.previous_value)
        self.bcg_save_changes(panel='optics')
        self.bcg_save_changes(panel='channels')

    def bcg_add_channel_to_optics_dataframe(self, new_row, new_channel, copy_channel):
        '''
        '''
        self.channels = [str(x) for x in self.channels_dataframe['Band ID']]
        for parameter in self.multiband_optical_properties:
            for element_index in self.optics_dataframe[parameter].index:
                element_data_dicts = self.optics_dataframe.loc[element_index, parameter]
                if type(element_data_dicts) == list:
                    for data_dict in element_data_dicts:
                        data_dict[new_channel] = data_dict[copy_channel]
        self.saved = True
        datetime_str = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        save_str = 'Last Saved at {0} |'.format(datetime_str)
        self.saved_status_label.setText(save_str)

    def bcg_add_move_or_delete_element(self, clicked=False, start_row=6, delete=False, add_element=False):
        '''
        '''
        change_optics_order = False
        update_optics_dataframe = False
        self.channels = [str(x) for x in self.channels_dataframe['Band ID']]
        self.optical_elements = [str(x) for x in self.optics_dataframe['Element']]
        dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
        if self.panel == 'channels':
            if not ('delete' in self.sender().whatsThis() or 'move_down' in self.sender().whatsThis() or 'move_up' in self.sender().whatsThis()):
                msg = 'New Channel Name:'
                new_channel, okPressed_1 = self.gb_quick_info_gather(title='New Channel', dialog=msg)
                if new_channel in self.channels:
                    self.gb_quick_message('Channel {0} already exists!\nPlease choose a new name'.format(new_channel), msg_type='Warning')
                    return None
                msg = 'Copy from channel:'
                copy_channel, okPressed_2 = self.gb_quick_static_info_gather(title='New Channel', dialog=msg, items=self.channels)
                if okPressed_1 and okPressed_2:
                    update_optics_dataframe = True
                else:
                    return None
        if 'move_up' in self.sender().whatsThis():
            move_up = True
            move_down = False
        elif 'move_down' in self.sender().whatsThis():
            move_up = False
            move_down = True
        else:
            move_up = False
            move_down = False
        if 'New Element' in self.sender().text():
            row = len(dataframe) - 1
            add_element = True
        else:
            row = int(self.sender().whatsThis().split('row_')[1].split('_')[0])
        if move_up:
            new_row = row - 1
        else:
            new_row = row + 1
        if 'delete' in self.sender().whatsThis():
            message = 'Are you sure you want to delete this row?'
            message += '\nThis cannot be undone'
            result = self.gb_quick_message(msg=message, add_yes=True, add_cancel=True)
            delete = True
            if result == QtWidgets.QMessageBox.Yes:
                delete = True
            elif result == QtWidgets.QMessageBox.Cancel:
                return None
        elif new_row <= 0 or new_row == len(dataframe) + 1 and not '+' in self.sender().text():
            return None
        if move_up or move_down or delete:
            row_to_move = dataframe.loc[row, :]
        else: # Adding a new element
            blank_row = dataframe.loc[dataframe.index[0], :].apply(deepcopy)
            for key in blank_row.keys():
                if key in self.multiband_optical_properties:
                    values_dict_list = []
                    for i in range(2):
                        entry = '{'
                        for channel in self.channels:
                            entry += '{0}'.format(channel)
                        entry += '}'
                        values_dict_list.append(entry)
                else:
                    blank_row[key] = ''
            if add_element:
                dataframe = dataframe.append(blank_row, ignore_index=True)
                dataframe = dataframe.sort_index()
                dataframe.index = [x for x in range(1, len(dataframe) + 1)]
            else:
                start_df = dataframe[:row]
                end_df = dataframe[row:]
                start_df = start_df.append(blank_row, ignore_index=True)
                dataframe = start_df.append(end_df, ignore_index=True)
                dataframe = dataframe.sort_index()
                dataframe.index = [x for x in range(1, len(dataframe) + 1)]
            if self.panel == 'channels':
                dataframe.loc[new_row, 'Band ID'] = str(new_channel)
                for column in dataframe[dataframe['Band ID'] == copy_channel].keys():
                    if column != 'Band ID':
                        #import ipdb;ipdb.set_trace()
                        copy_channel_index = dataframe[dataframe['Band ID'] == copy_channel].index[0]
                        dataframe.loc[new_row, column] = dataframe[dataframe['Band ID'] == copy_channel][column][copy_channel_index]
        if delete:
            if self.panel == 'channels':
                delete_channel = self.channels_dataframe.loc[row, 'Band ID']
            dataframe = dataframe.drop(index=row)
            dataframe.index = [x for x in range(1, len(dataframe) + 1)]
            if self.panel == 'channels':
                self.bcg_delete_channel_from_optics_dataframe(dataframe, delete_channel)
        elif move_down or move_up:
            row_to_replace = dataframe.loc[new_row, :]
            row_to_move = dataframe.loc[row, :]
            dataframe = dataframe.drop(index=row)
            dataframe.loc[row] = row_to_replace
            dataframe.loc[new_row] = row_to_move
            dataframe = dataframe.sort_index()
            dataframe.index = [x for x in range(1, len(dataframe) + 1)]
        setattr(self, '{0}_dataframe'.format(self.panel), dataframe)
        if self.panel == 'channels' and not delete:
            self.bcg_add_channel_to_optics_dataframe(new_row, new_channel, copy_channel)
            self.bcg_save_changes(panel='optics')
            self.bcg_save_changes(panel='channels')
            datetime_str = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
            save_str = 'Last Saved at {0} |'.format(datetime_str)
            self.saved_status_label.setText(save_str)
            self.saved = True
        else:
            self.saved_status_label.setText('Not Saved')
            self.saved = False
        if self.panel in ('parameter', 'channels'):
            self.n_enteries = len(dataframe)
            self.row_end_index = self.n_enteries
        self.bcg_build_parameter_panel()

    def bcg_scroll_params(self):
        '''
        '''
        if self.panel not in ('optics', 'channels'):
            return None
        dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
        if 'Right' in self.sender().text():
            if self.col_end_index + 1 > len(dataframe.keys()):
                self.col_end_index = len(dataframe.keys())
                self.col_start_index = self.col_end_index - self.n_col_enteries
            else:
                self.col_start_index += 1
                self.col_end_index += 1
        elif 'Left' in self.sender().text():
            if self.col_start_index - 1 < 1:
                self.col_start_index = 1
                self.col_end_index = self.n_col_enteries - 1
            else:
                self.col_start_index -= 1
                self.col_end_index -= 1
        self.bcg_build_parameter_panel()
        self.status_bar.showMessage('Parameters {0} to {1} of {2}'.format(self.col_start_index, self.col_end_index, len(dataframe.keys()) - 1))
        self.repaint()

    def bcg_scroll_elements(self):
        '''
        '''
        if self.panel not in ('parameter', 'optics', 'channels'):
            return None
        dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
        n_lineedit_enteries = self.n_display_rows_lineedit.text()
        if len(n_lineedit_enteries) == 0:
            return None
        df_enteries = len(dataframe)
        n_lineedit_enteries = int(n_lineedit_enteries)
        if df_enteries > n_lineedit_enteries:
            self.n_enteries = n_lineedit_enteries
        else:
            self.n_enteries = df_enteries
        self.row_end_index = self.n_enteries
        if 'Down' in self.sender().text():
            self.row_start_index += 1
            self.row_end_index = self.row_start_index + self.n_enteries
            if self.row_end_index > df_enteries:
                self.row_end_index = df_enteries
                self.row_start_index = self.row_end_index - self.n_enteries
                if self.row_start_index < 0:
                    self.row_start_index = 0
        elif 'Up' in self.sender().text():
            self.row_start_index -= 1
            self.row_end_index = self.row_start_index + self.n_enteries
            if self.row_start_index < 0:
                self.row_start_index = 0
                self.row_end_index = self.n_enteries
        self.bcg_build_parameter_panel()
        self.status_bar.showMessage('Elements {0} to {1} of {2}'.format(self.row_start_index + 1, self.row_end_index, len(dataframe)))
        self.repaint()

    def bcg_change_panel(self, clicked=True, panel=None):
        '''
        '''
        if not self.n_display_rows_lineedit.text().isnumeric():
            return None
        if panel is None:
            sender_text = self.sender().text()
            if 'ameter' in sender_text:
                new_panel = 'parameter'
            else:
                new_panel = sender_text.lower()
        else:
            new_panel = panel
        self.panel = new_panel
        dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
        df_enteries = len(dataframe)
        if self.panel in ('optics', 'parameter', 'channels'):
            n_enteries = int(self.n_display_rows_lineedit.text())
            if n_enteries < df_enteries:
                self.n_enteries = n_enteries
            else:
                self.n_enteries = df_enteries
            self.n_display_rows_lineedit.setDisabled(False)
            if self.panel == 'parameter':
                self.col_end_index = len(dataframe.keys())
        else:
            self.n_enteries = len(dataframe)
            self.col_end_index = len(dataframe.keys())
            if self.panel == 'simulation':
                self.col_end_index -= 1
            self.n_display_rows_lineedit.setDisabled(True)
        display_init_dict = {
            'optics': (0, self.n_enteries, 1, 6),
            'channels': (0, self.n_enteries, 1, 6),
            'camera': (0, self.n_enteries, 0, self.col_end_index),
            'telescope': (0, self.n_enteries, 0, self.col_end_index),
            'foregrounds': (0, self.n_enteries, 0, self.col_end_index),
            'simulation': (0, self.n_enteries, 0, self.col_end_index),
            'parameter': (0, self.n_enteries, 0, self.col_end_index)
            }
        self.row_start_index, self.row_end_index, self.col_start_index, self.col_end_index = display_init_dict[self.panel]
        self.bcg_get_panel_parameter_path()
        populate = False
        if not self.saved:
            message = 'You have unsaved changes, changing panels without saving will result in lost data\n'
            message += 'What would you like to do?'
            result = self.gb_quick_message(msg=message, add_cancel=True, add_discard=True, add_save=True, msg_type='Warning')
            if result == QtWidgets.QMessageBox.Save:
                self.bcg_save_changes()
                populate = True
            elif result == QtWidgets.QMessageBox.Discard:
                populate = True
                self.saved = True
            elif result == QtWidgets.QMessageBox.Cancel:
                return None
        else:
            populate = True
        if populate:
            self.bcg_build_parameter_panel()

    def bcg_can_build(self):
        '''
        '''
        can_build = True
        if hasattr(self, 'panel') and len(self.panel) == 0:
            can_build = False
        if hasattr(self, 'experiment') and len(self.experiment) == 0:
            can_build = False
        if hasattr(self, 'version') and len(self.version) == 0:
            can_build = False
        if hasattr(self, 'telescope') and len(self.telescope) == 0:
            can_build = False
        if hasattr(self, 'camera') and len(self.camera) == 0:
            can_build = False
        return can_build

    def bcg_build_parameter_panel(self):
        '''
        '''
        self.build_dict = {'_common_settings': {}}
        self.start_row = 0
        self.start_col = 4
        has_site = False
        parameter_definition_path = os.path.join(os.path.dirname(__file__), '..', 'param_definitions', '{0}_paramDefs.json'.format(self.panel))
        with open(parameter_definition_path, 'r') as parameter_definition_file_handle:
            parameter_definition_dict = json.load(parameter_definition_file_handle)
        multiband_dict = {}
        uneditable_sweep_params_dict = {}
        if hasattr(self, '{0}_dataframe'.format(self.panel)) and self.bcg_can_build():
            self.bcg_add_panel_column_labels()
            self.start_row += 3
            dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
            lines = dataframe.to_numpy()[self.row_start_index:self.row_end_index]
            for i, line in enumerate(lines):
                if self.panel in ('optics', 'channels'):
                    columns = np.append(np.asarray([line[0]]), line[self.col_start_index:self.col_end_index])
                else:
                    columns = line[self.col_start_index:self.col_end_index]
                #if self.panel in ('camera', 'telescope', 'foregrounds'):
                    #import ipdb;ipdb.set_trace()
                for col_num, value in enumerate(columns):
                    row = self.start_row + i
                    position = (row, self.start_col + col_num, 1, 1)
                    if value is None:
                        str_value = ''
                    elif self.panel == 'simulation':
                        str_value = value.replace("+/-", '').strip()
                    elif self.column_dict[col_num] in ['Num OT', 'Num Waf per OT', 'Num Det per Wafer']:
                        str_value = str(value[0])
                    elif type(value) == str:
                        str_value = value.strip()
                    elif len(value) > 1 and type(value[0]) == list:
                        values = [x for x in value[0]]
                        spreads = [x for x in value[1]]
                        if len(values) == 1:
                            values = values[0]
                            spreads = spreads[0]
                        str_value = "{0} +/- {1}".format(values, spreads)
                    elif type(value) == list and type(value[0]) == dict:
                        value = [str(x) for x in value]
                        str_value =  ' +/- '.join(value)
                    elif type(value) == list:
                        value = [x.strip() for x in value]
                        str_value = ' +/- '.join(value)
                    unique_widget_settings = {
                        'position': position,
                        'text': str_value,
                        'height': 0.05 * self.screen_resolution.height(),
                        'font': 'size_12',
                        'parent': 'cw_main_parameters_panel_scrollarea'
                        }
                        #unique_widget_name = '_cw_main_parameters_panel_row_{0}_col_{1}_header_{2}_combobox'.format(self.row_start_index + i + 1, self.col_start_index + col_num - 1, self.column_dict[col_num])
                        #unique_widget_settings.update({'tool_tip': 'Edit Value', 'function': 'bcg_update_site_in_dataframe'})
                        #unique_widget_settings.pop('text')
                        ##has_site = True
                        #self.site_combobox_name = unique_widget_name
                        #saved_site = str_value
                    if self.panel == 'parameter' and self.column_dict[col_num] in self.uneditiable_sweep_parameters:
                        unique_widget_name = '_cw_main_parameters_panel_row_{0}_col_{1}_header_{2}_combobox'.format(self.row_start_index + i + 1, self.col_start_index + col_num, self.column_dict[col_num])
                        unique_widget_settings.update({'tool_tip': 'Edit Value'})
                        unique_widget_settings.pop('text')
                        uneditable_sweep_params_dict[unique_widget_name] = self.column_dict[col_num]
                    elif self.panel == 'optics' and self.column_dict[col_num] in self.multiband_optical_properties:
                        unique_widget_name = '_cw_main_parameters_panel_row_{0}_col_{1}_header_{2}_combobox'.format(self.row_start_index + i + 1, self.col_start_index + col_num - 1, self.column_dict[col_num])
                        unique_widget_settings.update({'tool_tip': 'Edit Value'})
                        unique_widget_settings.pop('text')
                        multiband_dict[unique_widget_name] = value
                    elif self.panel in ('parameter', 'channels', 'optics'):
                        unique_widget_name = '_cw_main_parameters_panel_row_{0}_col_{1}_header_{2}_pushbutton'.format(self.row_start_index + i + 1, self.col_start_index + col_num - 1, self.column_dict[col_num])
                        unique_widget_settings.update({'function': 'bcg_launch_set_to_popup', 'font': 'size_12', 'tool_tip': 'Edit Value'})
                    elif col_num == 1 and self.panel == 'simulation':
                        unique_widget_name = '_cw_main_parameters_panel_row_{0}_col_{1}_header_{2}_pushbutton'.format(self.row_start_index + i + 1, self.col_start_index + col_num - 1, line[0])
                        unique_widget_settings.update({'function': 'bcg_launch_set_to_popup', 'font': 'size_12', 'tool_tip': 'Edit Value'})
                    elif col_num == 2 and self.panel in ('foregrounds', 'telescope', 'camera'):
                        unique_widget_name = '_cw_main_parameters_panel_row_{0}_col_{1}_header_{2}_pushbutton'.format(self.row_start_index + i + 1, self.col_start_index + col_num - 1, line[0])
                        unique_widget_settings.update({'function': 'bcg_launch_set_to_popup', 'font': 'size_12', 'tool_tip': 'Edit Value'})
                        unique_widget_settings['position'] = (row, self.start_col + col_num, 1, 1)
                        if self.panel == 'telescope' and line[0] == 'Site' and col_num == 2:
                            self.site_button_name = unique_widget_name
                    elif col_num == 1 and self.panel in ('foregrounds', 'telescope', 'camera'):
                        unique_widget_name = None
                    elif col_num == 0 and self.panel in ('foregrounds', 'telescope', 'camera'):
                        unique_widget_name = '_cw_main_parameters_panel_row_{0}_col_{1}_header_{2}_label'.format(self.row_start_index + i + 1, self.col_start_index + col_num - 1, self.column_dict[col_num])
                        current_text = unique_widget_settings['text']
                        units = columns[col_num + 1]
                        if '[' in units:
                            new_text = '{0} {1}'.format(current_text, units)
                        else:
                            new_text = '{0} [{1}]'.format(current_text, units)
                        unique_widget_settings['text'] = new_text
                    else:
                        unique_widget_name = '_cw_main_parameters_panel_row_{0}_col_{1}_header_{2}_label'.format(self.row_start_index + i + 1, self.col_start_index + col_num - 1, self.column_dict[col_num])
                        if str(value) in parameter_definition_dict:
                            tool_tip = parameter_definition_dict[value]['descr']
                            unique_widget_settings.update({'tool_tip': tool_tip})
                    if unique_widget_name is not None:
                        self.build_dict[unique_widget_name] = unique_widget_settings
                if self.panel in ('parameter', 'optics', 'channels'):
                    self.bcg_add_control_buttons(i, line)
            if self.panel in ('optics', 'channels'):
                self.params_qmw_menu.setDisabled(False)
                self.params_qmw_menu.setDisabled(False)
            else:
                self.params_qmw_menu.setDisabled(True)
                self.params_qmw_menu.setDisabled(True)
        whatsThis = None
        if self.sender() is not None:
            whatsThis = copy(self.sender().whatsThis())
        if hasattr(self, 'cw_main_parameters_panel_widget'):
            getattr(self, 'cw_main_parameters_panel_widget').setParent(None)
            for unique_panel_name, unique_panel_settings in self.panels.items():
                self.gb_create_and_place_widget(unique_panel_name, **unique_panel_settings, parent=self.central_widget)
        self.gb_build_panel(self.build_dict)
        if whatsThis is not None:
            self.bcg_configure_tab_bar('channel', whatsThis)
        if self.panel == 'optics':
            self.bcg_configure_optics_comboboxes(multiband_dict)
        if self.panel == 'parameter' and whatsThis is not None:
            self.bcg_configure_parameter_comboboxes(uneditable_sweep_params_dict)
            self.bcg_update_sweep_parameters(whatsThis)
            self.bcg_update_sweep_parameter_valid_range(whatsThis)
        if self.panel in ('telescope', 'foregrounds'):
            self.bcg_add_plot_label(i)
            if self.panel == 'telescope' and hasattr(self, 'site_combobox_name'):
                self.bcg_show_atm_model_in_bcg()
            if self.panel == 'foregrounds':
                self.bcg_show_foreground_model_in_bcg()
        if self.panel == 'camera':
            self.bcg_add_edit_boresight_pdf()
        if self.panel != 'optics':
            self.central_widget_channel_tab_bar.setDisabled(True)
            self.central_widget_channel_tab_bar.setVisible(False)
        else:
            self.central_widget_channel_tab_bar.setDisabled(False)
            self.central_widget_channel_tab_bar.setVisible(True)
        self.qt_app.processEvents()
        self.setFixedHeight(self.minimumSizeHint().height())

    def bcg_add_plot_label(self, row_count):
        '''
        '''
        unique_widget_name = '_cw_main_parameters_panel_row_0_col_8_{0}_special_plot_label'.format(self.panel)
        if self.panel in 'telescope':
            position = (3, 7, 6, 1)
            btn_position = (9, 7, 1, 1)
            function = self.bcg_plot_atm_model
        if self.panel == 'foregrounds':
            position = (3, 7, 6, 1)
            btn_position = (9, 7, 1, 1)
            function = self.bcg_plot_foreground_model
        unique_widget_settings = {
            'position': position,
            }
        self.gb_create_and_place_widget(unique_widget_name, **unique_widget_settings, parent=self.cw_main_parameters_panel_widget)
        unique_widget_name = '_cw_main_parameters_panel_row_1_col_8_{0}_special_plot_pushbutton'.format(self.panel)
        unique_widget_settings = {
            'text': 'Show in Matplotlib (higher res)',
            'function': function,
            'position': btn_position,
            }
        self.gb_create_and_place_widget(unique_widget_name, **unique_widget_settings, parent=self.cw_main_parameters_panel_widget)
        self.repaint()

    def bcg_add_edit_boresight_pdf(self):
        '''
        '''
        unique_widget_name = '_cw_main_parameters_panel_row_5_col_2_header_boresight_pdf_label'
        unique_widget_settings = {
            'text': 'Boresight Elevation PDF',
            'font': 'size_12',
            'position': (7, 4, 1, 1)
            }
        self.gb_create_and_place_widget(unique_widget_name, **unique_widget_settings, parent=self.cw_main_parameters_panel_widget)
        unique_widget_name = '_cw_main_parameters_panel_row_5_col_2_header_boresight_pdf_pushbutton'
        unique_widget_settings = {
            'text': 'PDF',
            'font': 'size_12',
            'function': self.bcg_launch_set_to_popup,
            'position': (7, 6, 1, 1)
            }
        self.gb_create_and_place_widget(unique_widget_name, **unique_widget_settings, parent=self.cw_main_parameters_panel_widget)

    def bcg_add_panel_column_labels(self):
        '''
        '''
        self.column_dict = {}
        dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
        columns = dataframe.keys()
        if self.panel == 'channels':
            columns = np.append(np.asarray(['Band ID']), columns[self.col_start_index:self.col_end_index])
        elif self.panel == 'optics':
            columns = np.append(np.asarray(['Element']), columns[self.col_start_index:self.col_end_index])
        else:
            columns = list(columns[self.col_start_index:self.col_end_index])
        parameter_definition_path = os.path.join(os.path.dirname(__file__), '..', 'param_definitions', '{0}_paramDefs.json'.format(self.panel))
        with open(parameter_definition_path, 'r') as parameter_definition_file_handle:
            parameter_definition_dict = json.load(parameter_definition_file_handle)
        with open(parameter_definition_path, 'w') as parameter_definition_file_handle:
            simplejson.dump(parameter_definition_dict, parameter_definition_file_handle,
                            indent=4, sort_keys=True)
        for col_num, column_header in enumerate(columns):
            unique_widget_name = '_cw_main_parameters_panel_{0}_{1}_header_label'.format(col_num, column_header)
            position = (self.start_row, self.start_col + col_num, 1, 1)
            unique_widget_settings = {
                'position': position,
                'color': 'blue',
                'font': 'large',
                'word_wrap': True,
                'text': column_header
                }
            if column_header in parameter_definition_dict and self.panel in ('optics', 'channels'):
                name = parameter_definition_dict[column_header]['name']
                unique_widget_settings['text'] = name
                unique_widget_unit_name = '_cw_main_parameters_panel_{0}_{1}_unit_header_label'.format(col_num, column_header)
                unit_position = (self.start_row + 1, self.start_col + col_num, 1, 1)
                units = parameter_definition_dict[column_header]['unit']
                unique_unit_widget_settings = {'position': unit_position, 'text': '[{0}]'.format(units)}
                self.build_dict[unique_widget_unit_name] = unique_unit_widget_settings
                tool_tip = parameter_definition_dict[column_header]['descr']
                unique_widget_settings.update({'tool_tip': tool_tip})
            self.column_dict[col_num] = column_header
            if column_header != 'Unit':
                self.build_dict[unique_widget_name] = unique_widget_settings

    def bcg_configure_optics_comboboxes(self, multiband_dict):
        '''
        '''
        for unique_widget_name, value_spread_dict in multiband_dict.items():
            column = unique_widget_name.split('header_')[-1].split('_')[0]
            q_combobox = getattr(self, unique_widget_name)
            q_combobox.setCurrentIndex(self.current_channel_index)
            if value_spread_dict == 'NA':
                for i, channel_name in enumerate(self.channels):
                    item = 'Band ID {0}: NA'.format(channel_name)
                    q_combobox.addItem(item)
            else:
                value_dict = eval(value_spread_dict[0])
                spread_dict = eval(value_spread_dict[1])
                for i, channel_name in enumerate(self.channels):
                    if channel_name not in value_dict:
                        import ipdb;ipdb.set_trace()
                    if value_dict[channel_name] == 'BAND' or value_dict[channel_name] == 'PDF':
                        value_str = value_dict[channel_name]
                    else:
                        value_str = '{0} +/- {1}'.format(value_dict[channel_name], spread_dict[channel_name])
                    item = 'Band ID {0}: {1}'.format(channel_name, value_str)
                    q_combobox.addItem(item)
        for index in reversed(range(self.cw_main_parameters_panel_widget.layout().count())):
            widget = self.cw_main_parameters_panel_widget.layout().itemAt(index).widget()
            if isinstance(widget, QtWidgets.QComboBox):
                widget.setCurrentIndex(self.current_channel_index)
                widget.activated.connect(self.bcg_launch_set_to_popup)

    def bcg_set_all_sweeps_to_cust(self, row):
        '''
        '''
        getattr(self, '_cw_main_parameters_panel_row_{0}_col_4_header_Minimum_pushbutton'.format(row)).setText('CUST')
        getattr(self, '_cw_main_parameters_panel_row_{0}_col_5_header_Maximum_pushbutton'.format(row)).setText('CUST')
        getattr(self, '_cw_main_parameters_panel_row_{0}_col_6_header_Step Size_pushbutton'.format(row)).setText('CUST')

    def bcg_configure_parameter_comboboxes(self, uneditable_sweep_params_dict):
        '''
        '''
        for unique_widget_name, parameter in uneditable_sweep_params_dict.items():
            row = int(unique_widget_name.split('row_')[-1].split('_')[0])
            set_index = 0
            sweep_params = ['']
            if parameter == 'Channel':
                sweep_params.extend([str(x) for x in self.channels_dataframe['Band ID']])
            elif parameter == 'Optic':
                sweep_params.extend([str(x) for x in self.optics_dataframe['Element']])
                set_index = 1
            elif parameter in ('Telescope', 'Camera'):
                tels_or_cams = getattr(self, '{0}s'.format(parameter).lower())
                if type(tels_or_cams) != list:
                    tels_or_cams = [tels_or_cams]
                sweep_params.extend(tels_or_cams)
            elif parameter in ('Parameter'):
                sweep_params.extend(self.bcg_get_sweep_paramters(row))
            for i, sweep_param in enumerate(sweep_params):
                row = int(unique_widget_name.split('row_')[-1].split('_')[0])
                set_to_parameter = unique_widget_name.split('header_')[-1].split('_')[0]
                getattr(self, unique_widget_name).addItem(sweep_param)
                current_value = self.parameter_dataframe.loc[row, set_to_parameter]
                if sweep_param == current_value:
                    set_index = i
            getattr(self, unique_widget_name).setCurrentIndex(set_index)
            getattr(self, unique_widget_name).activated.connect(self.bcg_store_value)
            getattr(self, unique_widget_name).activated.connect(self.bcg_update_sweep_parameters)

    def bcg_get_sweep_paramters(self, row):
        '''
        '''
        telescope = getattr(self, '_cw_main_parameters_panel_row_{0}_col_0_header_Telescope_combobox'.format(row)).currentText()
        camera = getattr(self, '_cw_main_parameters_panel_row_{0}_col_1_header_Camera_combobox'.format(row)).currentText()
        channel = getattr(self, '_cw_main_parameters_panel_row_{0}_col_2_header_Channel_combobox'.format(row)).currentText()
        optic = getattr(self, '_cw_main_parameters_panel_row_{0}_col_3_header_Optic_combobox'.format(row)).currentText()
        if telescope == '' and camera == '' and channel == '' and optic == '':
            sweep_params = self.foregrounds_dataframe['Parameter'].to_list()
        elif camera == '' and channel == '' and optic == '':
            sweep_params = self.telescope_dataframe['Parameter'].to_list()
        elif channel == '' and optic == '':
            sweep_params = list(self.camera_dataframe['Parameter'].to_list())
        elif optic == '':
            sweep_params = list(self.channels_dataframe.keys()[1:])
            sweep_params.insert(2, 'Pixel Size**')
        else:
            sweep_params = list(self.optics_dataframe.keys()[1:])
        return sweep_params

    def bcg_update_sweep_parameters(self, whatsThis=None):
        '''
        '''
        if whatsThis is None:
            whatsThis = self.sender().whatsThis()
        else:
            return None
        if 'combobox' in whatsThis:
            row = int(whatsThis.split('row_')[-1].split('_')[0])
            sweep_params = self.bcg_get_sweep_paramters(row)
            q_combobox = getattr(self, '_cw_main_parameters_panel_row_{0}_col_4_header_Parameter_combobox'.format(row))
            q_combobox.clear()
            for i, sweep_param in enumerate(sweep_params):
                q_combobox.addItem(sweep_param)
                if i == 1:
                    first_item = sweep_param
            self.parameter_dataframe.loc[row, 'Parameter'] = first_item
            self.bcg_update_sweep_parameter_valid_range()

    def bcg_add_control_buttons(self, i, line):
        width = 0.02 * self.screen_resolution.width()
        unique_widget_name = '_cw_main_parameters_panel_{0}_row_{1}_delete_pushbutton'.format(self.panel, self.row_start_index + i + 1)
        position = (self.start_row + i, 0, 1, 1)
        unique_widget_settings = {
            'width': width,
            'position': position,
            'function': 'bcg_add_move_or_delete_element',
            'tool_tip': 'Delete Row',
            'icon': 'DialogDiscardButton'
            }
        self.build_dict[unique_widget_name] = unique_widget_settings
        unique_widget_name = '_cw_main_parameters_panel_{0}_row_{1}_add_pushbutton'.format(self.panel, self.row_start_index +  i + 1)
        position = (self.start_row + i, 1, 1, 1)
        unique_widget_settings = {
            'text': '+',
            'color': 'green',
            'width': width,
            'position': position,
            'tool_tip': 'Add New Element or Channel',
            'function': 'bcg_add_move_or_delete_element'}
        self.build_dict[unique_widget_name] = unique_widget_settings
        unique_widget_name = '_cw_main_parameters_panel_{0}_row_{1}_move_down_pushbutton'.format(self.panel, self.row_start_index + i + 1)
        position = (self.start_row + i, 2, 1, 1)
        unique_widget_settings = {
            'width': width,
            'position': position,
            'function': 'bcg_add_move_or_delete_element',
            'tool_tip': 'Move Element or Channel Down',
            'icon': 'ArrowDown'}
        self.build_dict[unique_widget_name] = unique_widget_settings
        unique_widget_name = '_cw_main_parameters_panel_{0}_row_{1}_move_up_pushbutton'.format(self.panel, self.row_start_index + i + 1)
        position = (self.start_row + i, 3, 1, 1)
        unique_widget_settings = {
            'width': width,
            'position': position,
            'function': 'bcg_add_move_or_delete_element',
            'tool_tip': 'Move Element or Channel Up',
            'icon': 'ArrowUp'}
        self.build_dict[unique_widget_name] = unique_widget_settings

    def bcg_select_optics_channel(self):
        '''
        '''
        msg = 'Please select a channel'
        channel, okPressed = self.gb_quick_static_info_gather(msg, items=self.channels)
        if okPressed:
            self.bcg_select_all_channel_values(channel)

    def bcg_select_all_channel_values(self, channel):
        '''
        '''
        for index in reversed(range(self.cw_main_parameters_panel_widget.layout().count())):
            widget = self.cw_main_parameters_panel_widget.layout().itemAt(index).widget()
            if isinstance(widget, QtWidgets.QComboBox):
                for i in range(widget.count()):
                    entry_channel = widget.itemText(i)
                    entry_channel = entry_channel.split(':')[0].replace('Band ID ', '')
                    if entry_channel == channel:
                        widget.setCurrentIndex(i)
                        self.current_channel_index = i

    ######################################################################
    ######################################################################
    # Set to Popup Values
    ######################################################################
    ######################################################################

    def bcg_launch_set_to_popup(self):
        '''
        '''
        self.current_edit_band = None
        self.set_to_widget = self.sender().whatsThis()
        if hasattr(self.sender(), 'text'):
            self.current_value_as_str = self.sender().text()
        else:
            self.current_edit_index = self.sender().currentIndex()
            self.current_edit_band = self.sender().itemText(self.current_edit_index)
            self.current_value_as_str = self.current_edit_band.split(': ')[-1].upper()
            self.current_edit_band = self.current_edit_band.split(':')[0].replace('Band ID', '').strip()
        if 'PDF' in self.current_value_as_str and '+/-' in self.current_value_as_str:
            self.current_value_as_str = 'PDF'
        if 'BAND' in self.current_value_as_str and '+/-' in self.current_value_as_str:
            self.current_value_as_str = 'BAND'
        self.previous_value = self.current_value_as_str
        row = int(self.set_to_widget.split('row_')[-1].split('_')[0])
        if hasattr(self, 'BCG_set_to_popup'):
            self.BCG_set_to_popup.close()
        BCG_set_to_popup = QtWidgets.QMainWindow(self)
        BCG_set_to_popup.setWindowTitle('Set Parameter')
        BCG_set_to_popup.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        BCG_set_to_popup.setWindowModality(QtCore.Qt.WindowModal)
        self.BCG_set_to_popup = BCG_set_to_popup
        BCG_cw = QtWidgets.QWidget()
        # Tool bar 
        bottom_tool_bar_area = QtCore.Qt.BottomToolBarArea
        BCG_cw.setLayout(QtWidgets.QGridLayout())
        BCG_set_to_popup.setCentralWidget(BCG_cw)
        q_set_to_popup_tool_bar = QtWidgets.QToolBar()
        q_set_to_popup_tool_bar.setIconSize(QtCore.QSize(50, 50))
        q_set_to_popup_tool_bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        BCG_set_to_popup.addToolBar(bottom_tool_bar_area, q_set_to_popup_tool_bar)
        ### Actions
        # Cancel 
        q_cancel_action = QtWidgets.QAction('Cancel', BCG_set_to_popup)
        self.q_cancel_action = q_cancel_action
        close_icon_path = os.path.join(os.path.dirname(__file__), '..', 'gui_builder', 'icons', 'cancel.png')
        q_cancel_icon = QtGui.QIcon(close_icon_path)
        q_cancel_action.setIcon(q_cancel_icon)
        q_set_to_popup_tool_bar.addAction(q_cancel_action)
        # Save
        q_save_action = QtWidgets.QAction('Save', BCG_set_to_popup)
        save_icon_path = os.path.join(os.path.dirname(__file__), '..', 'gui_builder', 'icons', 'save.png')
        q_save_icon = QtGui.QIcon(save_icon_path)
        q_save_action.setShortcuts(['Return', 'ctrl+s'])
        q_save_action.setIcon(q_save_icon)
        q_save_action.triggered.connect(self.bcg_store_value)
        q_set_to_popup_tool_bar.addAction(q_save_action)
        self.q_save_action = q_save_action
        # Description
        q_show_descr_action = QtWidgets.QAction('Show Desciption', BCG_set_to_popup)
        q_show_descr_action.setIcon(self.q_show_descr_icon)
        q_show_descr_action.triggered.connect(self.bcg_show_description)
        self.q_show_descr_action = q_show_descr_action
        q_set_to_popup_tool_bar.addAction(q_show_descr_action)
        # New
        q_new_action = QtWidgets.QAction('New', BCG_set_to_popup)
        new_icon_path = os.path.join(os.path.dirname(__file__), '..', 'gui_builder', 'icons', 'new.png')
        q_new_icon = QtGui.QIcon(new_icon_path)
        q_new_action.setShortcut('N')
        q_new_action.setIcon(q_new_icon)
        q_new_action.triggered.connect(self.bcg_new_special_file)
        self.q_new_action = q_new_action
        q_set_to_popup_tool_bar.addAction(q_new_action)
        # Load 
        q_load_action = QtWidgets.QAction('Load', BCG_set_to_popup)
        load_icon_path = os.path.join(os.path.dirname(__file__), '..', 'gui_builder', 'icons', 'load.png')
        q_load_icon = QtGui.QIcon(load_icon_path)
        q_load_action.setShortcut('L')
        q_load_action.setIcon(q_load_icon)
        q_load_action.triggered.connect(self.bcg_load_pdf_or_band_file_from_computer)
        self.q_load_action = q_load_action
        q_set_to_popup_tool_bar.addAction(q_load_action)
        # Delete
        q_delete_action = QtWidgets.QAction('Delete', BCG_set_to_popup)
        delete_icon_path = os.path.join(os.path.dirname(__file__), '..', 'gui_builder', 'icons', 'delete.png')
        q_delete_icon = QtGui.QIcon(delete_icon_path)
        q_delete_action.setShortcut('N')
        q_delete_action.setIcon(q_delete_icon)
        q_delete_action.triggered.connect(self.bcg_delete_special_file)
        self.q_delete_action = q_delete_action
        q_set_to_popup_tool_bar.addAction(q_delete_action)
        # Edit PDF/Band
        q_edit_action = QtWidgets.QAction('Edit', BCG_set_to_popup)
        q_edit_action.setShortcut('E')
        self.q_edit_action = q_edit_action
        edit_icon_path = os.path.join(os.path.dirname(__file__), '..', 'gui_builder', 'icons', 'edit.png')
        q_edit_icon = QtGui.QIcon(edit_icon_path)
        q_edit_action.setIcon(q_edit_icon)
        q_set_to_popup_tool_bar.addAction(q_edit_action)
        # View PDF/Band
        q_view_action = QtWidgets.QAction('View', BCG_set_to_popup)
        self.q_view_action = q_view_action
        view_icon_path = os.path.join(os.path.dirname(__file__), '..', 'gui_builder', 'icons', 'view.png')
        q_view_icon = QtGui.QIcon(view_icon_path)
        q_view_action.setIcon(q_view_icon)
        q_set_to_popup_tool_bar.addAction(q_view_action)
        if 'pushbutton' in self.sender().whatsThis():
            parameter = self.sender().whatsThis().split('header_')[-1].replace('_pushbutton', '')
        elif 'combobox' in self.sender().whatsThis():
            parameter = self.sender().whatsThis().split('header_')[-1].replace('_combobox', '')
            current_index = self.sender().currentIndex()
            #import ipdb;ipdb.set_trace()
        parameter_definition_path = os.path.join(os.path.dirname(__file__), '..', 'param_definitions', '{0}_paramDefs.json'.format(self.panel))
        with open(parameter_definition_path, 'r') as parameter_definition_file_handle:
            parameter_definition_dict = json.load(parameter_definition_file_handle)
        if parameter in parameter_definition_dict:
            if self.panel == 'parameter' and parameter in ('Minimum', 'Maximum'):
                self.valid_range, self.unit, self.description = self.bcg_update_sweep_parameter_valid_range()
            else:
                self.valid_range = parameter_definition_dict[parameter]['range']
                self.description = parameter_definition_dict[parameter]['descr']
                self.unit = parameter_definition_dict[parameter]['unit']
            self.edit_types = parameter_definition_dict[parameter]['type']
            self.name = parameter_definition_dict[parameter]['name']
            self.trumpedBy = 'None (Required)'
            if 'trumpedBy' in parameter_definition_dict[parameter]:
                self.trumpedBy = parameter_definition_dict[parameter]['trumpedBy']
            self.trumps = 'None'
            if 'trumps' in parameter_definition_dict[parameter]:
                self.trumps = parameter_definition_dict[parameter]['trumps']
            self.idn = parameter
        self.edit_types = self.edit_types.strip('[]').split(', ')
        edit_tab_bar = QtWidgets.QTabBar()
        edit_tab_bar.setWhatsThis('edit_tab_bar')
        setattr(self, 'edit_tab_bar', edit_tab_bar)
        for tab_index in range(self.edit_tab_bar.count()):
            self.edit_tab_bar.removeTab(tab_index)
        self.edit_tab_index = 0
        for i, edit_type in enumerate(self.edit_types):
            if i == 0:
                self.edit_type = edit_type.upper()
            edit_tab_bar.addTab(edit_type.upper())
            if edit_type.upper() == self.current_value_as_str:
                self.edit_tab_index = i
                self.edit_type = edit_type.upper()
        BCG_cw.layout().addWidget(edit_tab_bar, 2, 0, 1, 1)
        # New value
        new_value_label = QtWidgets.QLabel()
        self.new_value_label = new_value_label
        # Value Lineedit
        value_lineedit = QtWidgets.QLineEdit()
        value_lineedit.textChanged.connect(self.bcg_update_float)
        self.value_lineedit = value_lineedit
        self.BCG_set_to_popup.centralWidget().layout().addWidget(value_lineedit, 3, 0, 1, 1)
        # PM Label
        pm_label = QtWidgets.QLabel('+/-')
        self.BCG_set_to_popup.centralWidget().layout().addWidget(pm_label, 4, 0, 1, 1)
        self.pm_label = pm_label
        # Spread Lineedit
        spread_lineedit = QtWidgets.QLineEdit()
        spread_lineedit.textChanged.connect(self.bcg_update_float)
        self.spread_lineedit = spread_lineedit
        self.BCG_set_to_popup.centralWidget().layout().addWidget(spread_lineedit, 5, 0, 1, 1)
        BCG_cw.layout().addWidget(new_value_label, 6, 0, 1, 1)
        # Information Text Label
        information_text_label = QtWidgets.QLabel('', self.BCG_set_to_popup)
        information_text_label.setFont(self.size_12_font)
        self.information_text_label = information_text_label
        information_str = self.bcg_get_information_label(row)
        information_text_label.setText(information_str)
        BCG_cw.layout().addWidget(information_text_label, 0, 0, 1, 1)
        #
        ### Information PNG Label
        #
        q_information_png_label = QtWidgets.QLabel()
        self.q_information_png_label = q_information_png_label
        BCG_cw.layout().addWidget(q_information_png_label, 1, 0, 1, 1)
        #
        ### Information SVG Viewer Label
        #
        q_information_svg_widget = QtSvg.QSvgWidget()
        self.q_information_svg_widget = q_information_svg_widget
        BCG_cw.layout().addWidget(q_information_svg_widget, 1, 0, 1, 1)
        #
        # Add actions and funciont after placing
        edit_tab_bar.currentChanged.connect(self.bcg_set_edit_tab)
        edit_tab_bar.addTab('dummy')
        edit_tab_bar.setCurrentIndex(edit_tab_bar.count() - 1)
        edit_tab_bar.setCurrentIndex(self.edit_tab_index)
        edit_tab_bar.removeTab(edit_tab_bar.count() - 1)
        q_edit_action.triggered.connect(lambda: self.bcg_edit_pdf_or_band(edit_tab_bar))
        q_view_action.triggered.connect(lambda: self.bcg_view_pdf_or_band(edit_tab_bar))
        q_cancel_action.triggered.connect(self.bcg_cancel_edit)
        if self.panel == 'parameter':
            self.bcg_set_edit_tab(0)
        BCG_set_to_popup.move(100, 100)
        self.bcg_show_description()
        BCG_set_to_popup.show()

    def bcg_get_information_label(self, row):
        '''
        '''
        information = ''
        if self.panel == 'optics':
            optic = self.optics_dataframe.loc[row, 'Element']
            information += 'Optic: {0}\n'.format(optic)
            if self.current_edit_band is not None:
                information += 'Band ID: "{0}"\n'.format(self.current_edit_band)
        elif self.panel == 'channels':
            band_id = self.channels_dataframe.loc[row, 'Band ID']
            information += 'Band ID: "{0}"\n'.format(band_id)
        information += 'Parameter: {0}\n'.format(self.name)
        information += 'Valid Range: {0}\n'.format(self.valid_range)
        information += 'Unit: [{0}]\n'.format(self.unit)
        information += 'Description: {0}\n'.format(self.description)
        information += 'Trumps: {0}\n'.format(self.trumps)
        information += 'Trumped By: {0}\n'.format(self.trumpedBy)
        return information

    def bcg_update_sweep_parameter_valid_range(self, whatsThis=None):
        '''
        '''
        if whatsThis is None:
            whatsThis = self.sender().whatsThis()
        else:
            return None
        if 'action' in whatsThis:
            return None
        if hasattr(self, 'set_to_widget') and self.set_to_widget is not None:
            row = int(self.set_to_widget.split('row_')[-1].split('_')[0])
        else:
            row = int(whatsThis.split('row_')[-1].split('_')[0])
            getattr(self, '_cw_main_parameters_panel_row_{0}_col_4_header_Minimum_pushbutton'.format(row)).setText('')
            getattr(self, '_cw_main_parameters_panel_row_{0}_col_5_header_Maximum_pushbutton'.format(row)).setText('')
        sweep_param = self.parameter_dataframe.loc[row, 'Parameter']
        if sweep_param == '':
            return [], '', ''
        if 'combobox' in whatsThis:
            import ipdb;ipdb.set_trace()
            self.previous_value = self.sender().itemText(self.sender().currentIndex())
        for panel in ['channels', 'optics', 'camera', 'foregrounds', 'simulation', 'parameter',  'telescope']:
            parameter_definition_path = os.path.join(os.path.dirname(__file__), '..', 'param_definitions', '{0}_paramDefs.json'.format(panel))
            with open(parameter_definition_path, 'r') as parameter_definition_file_handle:
                parameter_definition_dict = json.load(parameter_definition_file_handle)
            if sweep_param in parameter_definition_dict:
                valid_range = parameter_definition_dict[sweep_param]['range']
                units = parameter_definition_dict[sweep_param]['unit']
                description = parameter_definition_dict[sweep_param]['descr']
                if self.panel == 'parameter':
                    current_min_val = getattr(self, '_cw_main_parameters_panel_row_{0}_col_4_header_Minimum_pushbutton'.format(row)).text()
                    current_max_val = getattr(self, '_cw_main_parameters_panel_row_{0}_col_5_header_Maximum_pushbutton'.format(row)).text()
                    if '(' in valid_range:
                        valid_range = valid_range.replace(']', ')')
                    elif '[' in valid_range:
                        valid_range = valid_range.replace(')', ']')
                    valid_range_as_list = eval(valid_range)
                    valid_range_as_list = list(valid_range_as_list)
                    if self.gb_is_float(current_max_val) and 'Minimum' in self.sender().whatsThis():
                        valid_range_as_list[1] = float(current_max_val)
                    if self.gb_is_float(current_min_val) and 'Maximum' in self.sender().whatsThis():
                        valid_range_as_list[0] = float(current_min_val)
                    valid_range = str(tuple(valid_range_as_list))
                return valid_range, units, description

    def bcg_toggle_show_descr(self):
        '''
        '''
        if self.show_descriptions:
            self.show_descriptions = False
            getattr(self, 'action_Hide Descriptions').setIcon(self.q_show_descr_icon)
            getattr(self, 'action_Hide Descriptions').setText('Show Descriptions')
        else:
            self.show_descriptions = True
            getattr(self, 'action_Hide Descriptions').setIcon(self.q_hide_descr_icon)
            getattr(self, 'action_Hide Descriptions').setText('Hide Descriptions')

    def bcg_show_description(self):
        '''
        '''
        if hasattr(self.sender(), 'text') and 'Show' in self.sender().text():
            self.show_descriptions = True
        if not self.show_descriptions:
            self.q_show_descr_action.setDisabled(True)
            return None
        self.q_show_descr_action.setDisabled(False)
        definition_svg_path = os.path.join(os.path.dirname(__file__), '..', 'templates', '{0}_definition.svg'.format(self.idn.replace(' ', '')))
        if os.path.exists(definition_svg_path):
            self.convertSVG(definition_svg_path)
            self.q_information_svg_widget.load(definition_svg_path)
            #if self.q_information_png_label.isVisible():
            if self.q_information_svg_widget.isVisible():
                self.q_information_svg_widget.setVisible(False)
                #self.q_information_png_label.setVisible(False)
                self.q_show_descr_action.setText('Show Description')
                self.q_show_descr_action.setIcon(self.q_show_descr_icon)
            else:
                self.q_information_svg_widget.setVisible(True)
                #self.q_information_png_label.setVisible(True)
                self.q_show_descr_action.setText('Hide Description')
                self.q_show_descr_action.setIcon(self.q_hide_descr_icon)
            self.qt_app.processEvents()
            self.BCG_set_to_popup.resize(self.BCG_set_to_popup.sizeHint())
            self.BCG_set_to_popup.move(100, 100)

    def bcg_cancel_edit(self):
        '''
        '''
        edit_type = self.edit_tab_bar.tabText(self.edit_tab_bar.currentIndex())
        self.BCG_set_to_popup.close()
        set_to_widget = getattr(self, self.set_to_widget)
        if hasattr(set_to_widget, 'setText'):
            set_to_widget.setText(self.previous_value)

    def bcg_update_float(self):
        '''
        '''
        if self.edit_type in ('PDF', 'BAND', 'NA'):
            new_value_as_string = self.edit_type
        elif self.edit_type in ('BOOL', 'NA', 'INT', 'STR') or self.panel in ('parameter', 'simulation'):
            new_value_as_string = '{0}'.format(self.value_lineedit.text())
        else:
            if len(self.spread_lineedit.text()) == 0:
                self.spread_lineedit.setText('0.0')
            new_value_as_string = '{0} +/- {1}'.format(self.value_lineedit.text(), self.spread_lineedit.text())
        self.new_value_label.setText(new_value_as_string)

    def bcg_store_value(self):
        '''
        '''
        self.optical_elements = [str(x) for x in self.optics_dataframe['Element']]
        if hasattr(self, 'edit_tab_bar'):
            edit_type = self.edit_tab_bar.tabText(self.edit_tab_bar.currentIndex())
            if edit_type in ('PDF', 'BAND') and hasattr(self, 'special_file_path'):
                err, valid = self.bcg_verify_special_file(self.special_file_path)
                if not valid:
                    msg = 'File it not valid. Stack Trace:\n'
                    msg += '\t{0}'.format(err)
                    self.gb_quick_message(msg, msg_type='Warning')
                    return None
        if self.panel == 'parameter' and isinstance(self.sender(), QtWidgets.QComboBox):
            if 'Optic' in self.sender().whatsThis():
                self.bcg_update_sweep_parameters()
            row = int(self.sender().whatsThis().split('row_')[-1].split('_')[0])
            col = int(self.sender().whatsThis().split('col_')[-1].split('_')[0])
            col += 1
            column_key = self.parameter_dataframe.keys()[col]
            new_value_string = self.sender().itemText(self.sender().currentIndex())
            self.valid_range, self.unit, self.description = self.bcg_update_sweep_parameter_valid_range()
            self.parameter_dataframe[column_key][row] = new_value_string
            self.saved_status_label.setText('Not Saved')
            self.saved = False
            if hasattr(self, 'BCG_set_to_popup'):
                self.BCG_set_to_popup.close()
                if self.panel == 'telescope':
                    self.bcg_show_atm_model_in_bcg()
        elif self.panel == 'parameter' and hasattr(self, 'set_to_widget'):
            row = int(self.set_to_widget.split('row_')[-1].split('_')[0])
            col = int(self.set_to_widget.split('col_')[-1].split('_')[0]) + 1
            column_key = self.parameter_dataframe.keys()[col]
            new_value_string = self.new_value_label.text()
            valid_value_flag = self.value_lineedit.validator().validate(self.value_lineedit.text(), 0)[0]
            if valid_value_flag == 2 or new_value_string == 'CUST':
                if new_value_string == 'CUST':
                    for column in ['Minimum', 'Maximum', 'Step Size']:
                        self.parameter_dataframe[column][row] = new_value_string
                else:
                    self.parameter_dataframe[column_key][row] = new_value_string
                getattr(self, self.set_to_widget).setText(new_value_string)
                self.BCG_set_to_popup.close()
                if self.panel == 'telescope':
                    self.bcg_show_atm_model_in_bcg()
                if not self.previous_value == new_value_string:
                    self.saved_status_label.setText('Not Saved')
                    self.saved = False
                self.bcg_set_all_sweeps_to_cust(row)
            else:
                format_string = 'Please format values properly as\n'
                format_string += 'Type must be one of: {0}\n'.format(self.edit_types)
                format_string += 'Value must be in range: {0}\n'.format(self.valid_range)
                format_string += 'Note: Number of values must equal\n'
                format_string += 'Number of spreads for multiple bands'
                self.gb_quick_message(format_string, msg_type='Warning')
        elif hasattr(self, 'spread_lineedit'):
            if self.spread_lineedit.validator() is None:
                new_value_string = self.new_value_label.text()
                row = int(self.set_to_widget.split('row_')[-1].split('_')[0])
                col = int(self.set_to_widget.split('col_')[-1].split('_')[0])
                if self.panel in ('parameter', 'simulation', 'telescope', 'foregrounds', 'camera'):
                    col += 1
                dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
                column_key = dataframe.keys()[col]
                if new_value_string in self.channels and column_key == 'Band ID':
                    self.gb_quick_message('A channel named "{0}" already exists!\nPlease choose a new name'.format(new_value_string), msg_type='Warning')
                    return None
                if new_value_string in self.optical_elements and column_key == 'Element':
                    self.gb_quick_message('An optic named "{0}" already exists!\nPlease choose a new name'.format(new_value_string), msg_type='Warning')
                    return None
                set_to_widget = getattr(self, self.set_to_widget)
                if hasattr(set_to_widget, 'setText'):
                    set_to_widget.setText(new_value_string)
                    dataframe[column_key][row] = new_value_string
                else:
                    channel_name = self.channels[self.current_edit_index]
                    new_value_string = 'Band ID {0}: {1}'.format(channel_name, new_value_string)
                    set_to_widget.setItemText(self.current_edit_index, new_value_string)
                    if 'BAND' in new_value_string:
                        new_value_string = 'BAND'
                        dataframe[column_key][row][0][self.current_edit_band] = 'BAND'
                        dataframe[column_key][row][1][self.current_edit_band] = '0.0'
                    elif 'PDF' in new_value_string:
                        dataframe[column_key][row][0][self.current_edit_band] = 'PDF'
                        dataframe[column_key][row][1][self.current_edit_band] = '0.0'
                if not self.previous_value == new_value_string:
                    self.saved_status_label.setText('Not Saved')
                    self.saved = False
                self.BCG_set_to_popup.close()
                if self.panel == 'telescope':
                    self.bcg_show_atm_model_in_bcg()
                elif self.panel == 'foregrounds':
                    self.bcg_show_foreground_model_in_bcg()
                elif self.panel == 'channels' and column_key == 'Band ID':
                    new_name = dataframe[column_key][row]
                    self.bcg_change_channel_name_in_optics_dataframe(new_name)
                return None
            valid_spread_flag = self.spread_lineedit.validator().validate(self.spread_lineedit.text(), 0)[0]
            valid_value_flag = self.value_lineedit.validator().validate(self.value_lineedit.text(), 0)[0]
            if valid_spread_flag > 0 and valid_value_flag == 2:
                row = int(self.set_to_widget.split('row_')[-1].split('_')[0])
                col = int(self.set_to_widget.split('col_')[-1].split('_')[0])
                dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
                if self.panel in ('parameter', 'simulation', 'telescope', 'foregrounds', 'camera'):
                    col += 1
                column_key = dataframe.keys()[col]
                new_value_string = self.new_value_label.text()
                set_to_widget = getattr(self, self.set_to_widget)
                if hasattr(set_to_widget, 'setText'):
                    set_to_widget.setText(new_value_string)
                    if '+/-' in new_value_string:
                        dataframe[column_key][row] = new_value_string.strip().split('+/-')
                    else:
                        dataframe[column_key][row] = new_value_string
                else:
                    channel_name = self.channels[self.current_edit_index]
                    new_value_string = 'Band ID {0}: {1}'.format(channel_name, new_value_string)
                    set_to_widget.setItemText(self.current_edit_index, new_value_string)
                    set_to_widget.setItemText(self.current_edit_index, new_value_string)
                    value, spread = new_value_string.split(' +/- ')
                    value = value.split(':')[-1].strip()
                    spread = spread.strip()
                    dataframe[column_key][row][0][self.current_edit_band] = float(value)
                    dataframe[column_key][row][1][self.current_edit_band] = float(spread)
                if not self.previous_value == new_value_string:
                    self.saved_status_label.setText('Not Saved')
                    self.saved = False
                self.BCG_set_to_popup.close()
                if self.panel == 'telescope':
                    self.bcg_show_atm_model_in_bcg()
                elif self.panel == 'foregrounds':
                    self.bcg_show_foreground_model_in_bcg()
            else:
                format_string = 'Please format values properly as\n'
                format_string += 'Type must be one of: {0}\n'.format(self.edit_types)
                format_string += 'Value must be in range: {0}\n'.format(self.valid_range)
                format_string += 'Note: Number of values must equal\n'
                format_string += 'Number of spreads for multiple bands'
                self.gb_quick_message(format_string, msg_type='Warning')

    def bcg_set_edit_tab(self, edit_type_index):
        '''
        '''
        if type(edit_type_index) == int:
            edit_type = self.edit_tab_bar.tabText(edit_type_index)
            self.edit_tab_bar.setCurrentIndex(edit_type_index)
        else:
            edit_type = edit_type_index
        if edit_type == 'dummy':
            return None
        if edit_type == 'BAND' and self.panel == 'optics':
            self.gb_quick_message('Choosing Band Will override entries for all other bands!')
        self.edit_type = edit_type
        if self.edit_type == 'FLOAT':
            if self.current_value_as_str == 'PDF' or 'PDF' in self.current_value_as_str:
                self.current_value_as_str = ''
            if self.current_value_as_str == 'BAND' in 'BAND' in self.current_value_as_str:
                self.current_value_as_str = ''
        if self.edit_type == 'CUST':
            self.current_value_as_str = 'CUST'
        self.q_view_action.setDisabled(True)
        self.q_edit_action.setDisabled(True)
        self.q_delete_action.setDisabled(True)
        self.q_load_action.setDisabled(True)
        row = int(self.set_to_widget.split('row_')[-1].split('_')[0])
        information_str = self.bcg_get_information_label(row)
        self.information_text_label.setText(information_str)
        if self.edit_type == 'NA':
            self.current_value_as_str = self.edit_type
            self.new_value_label.setText(self.current_value_as_str)
            self.value_lineedit.setDisabled(True)
            self.spread_lineedit.setDisabled(True)
            self.pm_label.setVisible(False)
            self.value_lineedit.setVisible(False)
            self.spread_lineedit.setVisible(False)
            self.q_view_action.setDisabled(True)
            self.q_edit_action.setDisabled(True)
            self.q_new_action.setDisabled(True)
            self.q_delete_action.setDisabled(True)
            self.q_save_action.setDisabled(False)
        elif self.edit_type in ('PDF', 'BAND', 'CUST'):
            self.current_value_as_str = self.edit_type
            self.new_value_label.setText(self.current_value_as_str)
            self.spread_lineedit.setText('')
            self.value_lineedit.setDisabled(True)
            self.spread_lineedit.setDisabled(True)
            self.q_load_action.setDisabled(True)
            self.pm_label.setVisible(False)
            self.value_lineedit.setVisible(False)
            self.spread_lineedit.setVisible(False)
            if self.edit_type == 'CUST':
                special_file_dict = self.bcg_get_special_file_dict(file_type=self.edit_type, channel_row=row)
            else:
                special_file_dict = self.bcg_get_special_file_dict(file_type=self.edit_type)
            exists = False
            if type(special_file_dict) == dict:
                exists = np.asarray([x['exists'] for x in special_file_dict.values()]).any()
            #import ipdb;ipdb.set_trace()
            if not exists:
                self.q_view_action.setDisabled(True)
                self.q_edit_action.setDisabled(True)
                self.q_new_action.setDisabled(False)
                self.q_load_action.setDisabled(False)
                self.q_delete_action.setDisabled(True)
                self.q_save_action.setDisabled(True)
                information_text = self.information_text_label.text()
                information_text += '\nFile Name: Does not exists!'
                self.information_text_label.setText(information_text)
            else:
                self.q_new_action.setDisabled(True)
                self.q_view_action.setDisabled(False)
                self.q_edit_action.setDisabled(False)
                self.q_load_action.setDisabled(False)
                self.q_delete_action.setDisabled(False)
                self.q_save_action.setDisabled(False)
                path = [x['path'] for x in special_file_dict.values() if x['exists']][0]
                self.special_file_path = path
                self.save_path_label.setText(path)
                information_text = self.information_text_label.text()
                information_text += '\nFile Name: {0}'.format(os.path.basename(path))
                self.information_text_label.setText(information_text)
                self.BCG_set_to_popup.repaint()
        elif self.edit_type in ('BOOL', 'STR', 'INT', 'CUST') or self.panel == 'simulation':
            if '+/-' in self.current_value_as_str:
                self.current_value_as_str = self.current_value_as_str.split('+/-')[0].strip()
            self.value_lineedit.setText(self.current_value_as_str)
            self.new_value_label.setText(self.current_value_as_str)
            self.spread_lineedit.setDisabled(True)
            self.spread_lineedit.setVisible(False)
            self.pm_label.setVisible(False)
            self.spread_lineedit.setText('')
            self.value_lineedit.setText(self.current_value_as_str)
            self.q_save_action.setDisabled(False)
            self.q_new_action.setDisabled(True)
            self.q_load_action.setDisabled(True)
        else:
            self.q_save_action.setDisabled(False)
            self.q_new_action.setDisabled(True)
            self.q_load_action.setDisabled(True)
            self.new_value_label.setText(self.current_value_as_str)
            self.value_lineedit.setDisabled(False)
            self.spread_lineedit.setDisabled(False)
            self.value_lineedit.setVisible(True)
            self.pm_label.setVisible(True)
            self.spread_lineedit.setVisible(True)
            if '+/-' in self.current_value_as_str:
                value = self.current_value_as_str.strip().split('+/-')[0].strip()
                spread = self.current_value_as_str.strip().split('+/-')[1].strip()
            else:
                value = self.current_value_as_str.strip()
                spread = ''
            self.spread_lineedit.setText(spread)
            self.value_lineedit.setText(value)
        self.bcg_update_set_to_validator(edit_type)

    def bcg_update_set_to_validator(self, edit_type):
        '''
        '''
        parameter_definition_path = os.path.join(os.path.dirname(__file__), '..', 'param_definitions', '{0}_paramDefs.json'.format(self.panel))
        with open(parameter_definition_path, 'r') as parameter_definition_file_handle:
            parameter_definition_dict = json.load(parameter_definition_file_handle)
        param = self.set_to_widget.split('header_')[1].split('_')[0]
        #' and isinstance(self.sender(), QtWidgets.QPushButton):
        if edit_type in ('FLOAT', 'INT'):
            if self.panel == 'parameter':
                valid_range, unit, description = self.bcg_update_sweep_parameter_valid_range()
            else:
                valid_range = parameter_definition_dict[param]['range']
            if '(' in valid_range:
                valid_range = valid_range.replace(']', ')')
            elif '[' in valid_range:
                valid_range = valid_range.replace(')', ']')
            self.valid_range = eval(valid_range)
            if edit_type == 'FLOAT':
                self.value_lineedit.setValidator(QtGui.QDoubleValidator(self.valid_range[0], self.valid_range[1], 8, self.value_lineedit))
                self.spread_lineedit.setValidator(QtGui.QDoubleValidator(self.valid_range[0], self.valid_range[1], 8, self.spread_lineedit))
            elif edit_type == 'INT':
                self.value_lineedit.setValidator(QtGui.QIntValidator(self.valid_range[0], self.valid_range[1], self.value_lineedit))
                self.spread_lineedit.setValidator(QtGui.QIntValidator(self.valid_range[0], self.valid_range[1], self.spread_lineedit))
        elif edit_type == 'BOOL' or self.panel == 'simulation':
            self.value_lineedit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("True|False"), self.value_lineedit))
        elif param == 'Band ID':
            self.value_lineedit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[A-Z0-9a-z-]*"), self.value_lineedit))
        elif param == 'Site':
            #import ipdb;ipdb.set_trace()
            regex_str = 'Atacama|ATACAMA|atacama'
            regex_str += '|Pole|POLE|pole'
            regex_str += '|Cust|CUST|cust'
            regex_str += '|Space|SPACE|space'
            regex_str += '|McMurdo|MCMURDO|mcmurdo'
            self.value_lineedit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("{0}".format(regex_str)), self.value_lineedit))
        else:
            self.spread_lineedit.setValidator(None)

    ######################################################################
    ######################################################################
    # Loading Special files 
    ######################################################################
    ######################################################################

    def bcg_new_special_file(self):
        '''
        '''
        if hasattr(self, 'BCG_new_special_file_popup'):
            self.gb_initialize_panel('BCG_new_special_file_popup')
        else:
            self.gb_create_popup_window('BCG_new_special_file_popup')
        msg = 'What kind of file would you like to make?'
        extension, okPressed = self.gb_quick_static_info_gather(msg, items=['CSV', 'TXT', 'LOAD FROM COMPUTER'])
        if not okPressed:
            return None
        index = self.edit_tab_bar.currentIndex()
        if self.edit_type == 'CUST':
            channel_row = (self.set_to_widget.split('row_')[-1].split('_')[0])
            special_file_dict = self.bcg_get_special_file_dict(file_type=self.edit_type, channel_row=channel_row)
        else:
            special_file_dict = self.bcg_get_special_file_dict(file_type=self.edit_type)
        if extension in ['CSV', 'TXT']:
            template_path = getattr(self, 'blank_{0}_{1}_file'.format(self.edit_type, extension).lower())
            new_path = special_file_dict[extension.lower()]['path']
            shutil.copy(template_path, new_path)
            self.bcg_open_file(new_path)
            self.special_file_path = new_path
            self.save_path_label.setText(new_path)
        else:
            self.bcg_load_pdf_or_band_file_from_computer()
        self.edit_tab_bar.setCurrentIndex(0)
        self.edit_tab_bar.setCurrentIndex(index)

    def bcg_load_pdf_file(self, element_name=None, parameter=None, channel_name=None, panel=None, get_names_from_widget=True):
        '''
        '''
        if panel is None:
            panel = self.panel
        self.edit_type = 'PDF'
        if hasattr(self.sender(), 'text') and self.sender().text() in ('Verify', 'Show Warnings'):
            get_names_from_widget = False
        if get_names_from_widget and self.set_to_widget is not None:
            parameter = self.set_to_widget.split('header_')[1].split('_')[0]
            row = (self.set_to_widget.split('row_')[-1].split('_')[0])
            if panel == 'channels':
                element_name = self.channels_dataframe['Band ID'][int(row)]
            elif panel == 'optics':
                element_name = self.optics_dataframe['Element'][int(row)]
        parameter = str(parameter).replace(' ', '')
        if panel == 'optics':
            if self.set_to_widget is not None:
                set_to_widget = getattr(self, self.set_to_widget)
                if hasattr(set_to_widget, 'itemText'):
                    combobox_text = set_to_widget.itemText(set_to_widget.currentIndex())
                    channel_name = combobox_text.split(':')[0].replace('Band ID ', '')
            pdf_path = self.bcg_load_optics_pdf_file(element_name, parameter, channel_name)
        elif panel == 'channels':
            pdf_path = self.bcg_load_channels_pdf_file(parameter, element_name)
        elif panel == 'camera':
            pdf_path = self.bcg_load_camera_pdf_file(parameter)
        elif panel == 'telescope':
            pdf_path = self.bcg_load_telescope_pdf_file(parameter)
        elif panel == 'foregrounds':
            pdf_path = self.bcg_load_foregrounds_pdf_file(parameter)
        pdf_path = os.path.join(self.bolo_calc_dir, 'Experiments', pdf_path)
        return pdf_path

    def bcg_load_optics_pdf_file(self, element_name, parameter, channel_name=None):
        '''
        '''
        if channel_name is not None:
            pdf_name = '{0}_{1}_{2}'.format(element_name, parameter, channel_name)
        else:
            pdf_name = '{0}_{1}'.format(element_name, parameter.lower())
        pdf_path = os.path.join(self.experiment, self.version, self.telescope, self.camera, 'config', 'Dist', 'Optics', pdf_name)
        return pdf_path

    def bcg_load_channels_pdf_file(self, parameter, channel_name):
        '''
        '''
        pdf_name = '{0}_{1}'.format(parameter, channel_name)
        pdf_path = os.path.join(self.experiment, self.version, self.telescope, self.camera, 'config', 'Dist', 'Detectors', pdf_name)
        return pdf_path

    def bcg_load_camera_pdf_file(self, parameter):
        '''
        '''
        pdf_name = '{0}'.format(parameter)
        pdf_path = os.path.join(self.experiment, self.version, self.telescope, self.camera, 'config', 'Dist', pdf_name)
        return pdf_path

    def bcg_load_telescope_pdf_file(self, parameter):
        '''
        '''
        pdf_name = '{0}'.format(parameter)
        pdf_path = os.path.join(self.experiment, self.version, self.telescope, 'config', 'Dist', pdf_name)
        return pdf_path

    def bcg_load_foregrounds_pdf_file(self, parameter):
        '''
        '''
        pdf_name = '{0}'.format(parameter)
        pdf_path = os.path.join(self.experiment, self.version, 'config', 'Dist', pdf_name)
        return pdf_path

    def bcg_load_band_file(self, element_name=None, parameter=None, panel=None, get_names_from_widget=True):
        '''
        '''
        if panel is None:
            panel = self.panel
        self.edit_type = 'BAND'
        if hasattr(self.sender(), 'text') and self.sender().text() in ('Verify', 'Show Warnings'):
            get_names_from_widget = False
        if get_names_from_widget and self.set_to_widget is not None:
            parameter = self.set_to_widget.split('header_')[-1].replace('_pushbutton', '').replace('_combobox', '')
            row = (self.set_to_widget.split('row_')[-1].split('_')[0])
            if panel == 'channels':
                element_name = self.channels_dataframe['Band ID'][int(row)]
            elif panel == 'optics':
                element_name = self.optics_dataframe['Element'][int(row)]
            else:
                import ipdb;ipdb.set_trace()
        parameter = str(parameter).replace(' ', '')
        if panel == 'channels':
            band_name = '{0}_{1}'.format(self.camera, element_name)
        elif panel == 'optics':
            band_name = '{0}_{1}'.format(element_name, parameter.replace(' ', '').lower())
        if panel == 'channels':
            band_path = os.path.join(self.experiment, self.version, self.telescope, self.camera, 'config', 'Bands', 'Detectors', band_name)
        elif panel == 'optics':
            band_path = os.path.join(self.experiment, self.version, self.telescope, self.camera, 'config', 'Bands', 'Optics', band_name)
        band_path = os.path.join(self.bolo_calc_dir, 'Experiments', band_path)
        return band_path

    def bcg_load_pdf_or_band_file_from_computer(self):
        '''
        '''
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Band or PDF file')[0]
        extension = file_path.split('.')[-1]
        special_file_dict = self.bcg_get_special_file_dict(file_type=self.edit_type)
        if len(file_path) == 0:
            return None
        path = special_file_dict[extension.lower()]['path']
        shutil.copy(file_path, path)
        self.special_file_path = path
        self.save_path_label.setText(path)
        self.bcg_set_edit_tab(self.edit_type)
        return special_file_dict

    def bcg_load_custom_param_vary_file(self, row):
        '''
        '''
        names = []
        telescope = getattr(self, '_cw_main_parameters_panel_row_{0}_col_0_header_Telescope_combobox'.format(row)).currentText()
        if telescope != '':
            names.append(telescope)
        camera = getattr(self, '_cw_main_parameters_panel_row_{0}_col_1_header_Camera_combobox'.format(row)).currentText()
        if camera != '':
            names.append(camera)
        channel = getattr(self, '_cw_main_parameters_panel_row_{0}_col_2_header_Channel_combobox'.format(row)).currentText()
        if channel != '':
            names.append(channel)
        optic = getattr(self, '_cw_main_parameters_panel_row_{0}_col_3_header_Optic_combobox'.format(row)).currentText()
        if optic != '':
            names.append(optic)
        parameter = getattr(self, '_cw_main_parameters_panel_row_{0}_col_4_header_Parameter_combobox'.format(row)).currentText()
        if parameter != '':
            names.append(parameter.replace(' ', ''))
        path = '_'.join(names)
        path = os.path.join(self.bc_dir, 'config', 'customVary', path)
        return path

    def bcg_get_special_file_dict(self, file_type=None, element_name=None, parameter=None, channel_name=None, channel_row=None):
        '''
        '''
        if hasattr(self.sender(), 'tabText') and file_type is None:
            file_type = self.sender().tabText(self.sender().currentIndex())
            if file_type == 'NA':
                return 'NA'
        special_file_dict = {}
        special_file_path = self.bcg_get_exact_special_file_path(file_type=file_type, element_name=element_name, parameter=parameter, channel_name=channel_name, channel_row=channel_row)
        for extension in ['txt', 'csv']:
            full_path = special_file_path + '.' + extension
            data, valid = self.bcg_verify_special_file(full_path)
            special_file_dict[extension] = {
                'path': full_path,
                'exists': os.path.exists(full_path),
                'valid': valid,
                'file_type': file_type,
                'panel': self.panel,
                'data': data
                }
        return special_file_dict

    def bcg_get_exact_special_file_path(self, file_type, element_name=None, parameter=None, channel_name=None, channel_row=None):
        '''
        '''
        if file_type.lower() == 'cust':
            path = self.bcg_load_custom_param_vary_file(channel_row)
        elif file_type.lower() == 'band':
            path = self.bcg_load_band_file(element_name=element_name, parameter=parameter)
        elif self.set_to_widget is not None and 'boresight_pdf' in getattr(self, self.set_to_widget).whatsThis():
            path = os.path.join(self.experiment, self.version, self.telescope, self.camera, 'config', 'elevation')
            path = os.path.join(self.bolo_calc_dir, 'Experiments', path)
        elif file_type.lower() == 'pdf':
            path = self.bcg_load_pdf_file(element_name=element_name, parameter=parameter, channel_name=channel_name)
        return path

    def bcg_verify_special_file(self, file_path):
        '''
        '''
        if not os.path.exists(file_path):
            return 'File does not exist', False
        extension = file_path.split('.')[-1]
        data, valid = self.bcg_test_special_file(file_path, extension)
        return data, valid

    def bcg_test_special_file(self, file_name, extension):
        try:
            with open(file_name, 'r') as fh:
                lines = fh.readlines()
            if len(lines) == 1 and lines[0] == '\n':
                err = 'Emtpy file'
                data = np.asarray([])
            elif extension == 'csv':
                data = np.loadtxt(file_name, dtype=np.float, delimiter=',')
            else:
                data = np.loadtxt(file_name, dtype=np.float)
            if len(data.shape) == 1:
                data = np.reshape(data, (1, 2))
            if self.edit_type == 'PDF':
                if len(data) == 1 and self.gb_is_float(data[0][0]):
                    pass
                elif not data.shape[1] == 2:
                    err = 'Wrong number of columns for PDF, must be 2, found {0}'.format(data.shape[1])
                    return err, False
            if self.edit_type == 'BAND':
                if len(data) == 1 and self.gb_is_float(data[0][0]):
                    pass
                elif not data.shape[1] in (2, 3):
                    err = 'Wrong number of columns for BAND, must be 2 or 3, found {0}'.format(data.shape[1])
                    return err, False
            return data, True
        except ValueError as err:
            return err, False

    def bcg_delete_special_file(self):
        '''
        '''
        edit_type = self.edit_tab_bar.tabText(self.edit_tab_bar.currentIndex())
        special_file_dict = self.bcg_get_special_file_dict(file_type=edit_type)
        for extension in ['txt', 'csv']:
            path = special_file_dict[extension]['path']
            if os.path.exists(path):
                message = 'Are you want to delete this {0} file?\n\t{1}'.format(edit_type, path)
                result = self.gb_quick_message(msg=message, add_yes=True, add_cancel=True)
                if result == QtWidgets.QMessageBox.Yes:
                    try:
                        os.remove(path)
                        self.bcg_set_edit_tab(0)
                    except (PermissionError, OSError):
                        msg = 'File is open in another application!\nCannot delete it'
                        self.gb_quick_message(msg)
                        return None
                elif result == QtWidgets.QMessageBox.Cancel:
                    return None

    def bcg_edit_pdf_or_band(self, edit_tab_bar):
        '''
        '''
        edit_type_index = self.edit_tab_bar.currentIndex()
        edit_type = self.edit_tab_bar.tabText(edit_type_index)
        channel_row = None
        if self.panel == 'parameter':
            channel_row = int(self.set_to_widget.split('row_')[1].split('_')[0])
        special_file_dict = self.bcg_get_special_file_dict(file_type=edit_type, channel_row=channel_row)
        for extension in ['txt', 'csv']:
            path = special_file_dict[extension]['path']
            if os.path.exists(path):
                self.bcg_open_file(path)
                self.special_file_path = path
                self.save_path_label.setText(path)
                break

    def bcg_open_file(self, filename):
        '''
        '''
        self.special_file_path = filename
        self.save_path_label.setText(filename)
        if sys.platform == "win32":
            os.startfile(filename)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, filename])

    ######################################################################
    ######################################################################
    # View special files 
    ######################################################################
    ######################################################################

    def bcg_view_pdf_or_band(self, edit_tab_bar):
        '''
        '''
        edit_type_index = self.edit_tab_bar.currentIndex()
        edit_type = self.edit_tab_bar.tabText(edit_type_index)
        special_file_dict = self.bcg_get_special_file_dict(file_type=edit_type)
        valid = False
        for extension in ['txt', 'csv']:
            path = special_file_dict[extension]['path']
            data = special_file_dict[extension]['data']
            if special_file_dict[extension]['valid']:
                self.special_file_path = path
                self.save_path_label.setText(path)
                if data.shape[1] == 3:
                    xs = data.T[0]
                    ys = data.T[1]
                    errs = data.T[2]
                elif data.shape[1] == 2:
                    xs = data.T[0]
                    ys = data.T[1]
                    errs = None
                self.bcg_make_pdf_band_plot(xs, ys, errs, path)
                valid = True
                break
        if not valid:
            msg = 'File it not valid. Stack Trace:\n'
            msg += '\t{0}'.format(str(data))
            self.gb_quick_message(msg, msg_type='Warning')
            return None

    #################################################
    #################################################
    # #################SAVING 
    #################################################
    #################################################

    def bcg_update_site_in_dataframe(self):
        '''
        '''
        if len(self.sender().currentText()) > 0:
            self.telescope_dataframe['Value'][1] = self.sender().currentText().title()

    def bcg_save_changes(self, clicked=True, panel=None):
        '''
        '''
        # Retrieve data frame
        if panel is None:
            panel = self.panel
        dataframe = getattr(self, '{0}_dataframe'.format(panel))
        if panel == 'optics':
            dataframe = dataframe[self.bc_optics_order]
        self.bcg_get_panel_parameter_path()
        # Store data strings into lists
        data_entries = []
        titles = dataframe.columns.tolist()
        data_entries.append(dataframe.columns.tolist())
        # Parameters that should be saved as ints with no +/-
        param_ints = ["Num Det per Wafer", "Num Waf per OT", "Num OT"]
        column_ints = [True if title.strip() in param_ints else False for title in titles]
        for i, data in enumerate(dataframe.to_numpy()):
            data_lines = []
            for j, entry in enumerate(data):
                if entry is not None:
                    if type(entry) == list:
                        # Optics file
                        if type(entry[0]) == dict:
                            values = []
                            spreads = []
                            for k, entry_dict in enumerate(entry):
                                for channel_name in self.channels:
                                    if k == 0:
                                        values.append(entry_dict[channel_name])
                                    else:
                                        spreads.append(entry_dict[channel_name])
                            dat = '{0} +/- {1}'.format(str(values), str(spreads))
                            dat = dat.replace("'", '')
                            if 'PDF' in str(dat):
                                dat = '{0} +/- {1}'.format(str(values), str(spreads))
                                dat = dat.replace("'", '')
                            if 'BAND' in str(values):
                                dat = 'BAND'
                        # Not an optics file
                        else:
                            if column_ints[j]:
                                dat = "%d" % (np.round(float(entry[0].strip())))
                            else:
                                if type(entry[0]) == list:
                                    entry = [entry[0][0], entry[1][0]]
                                if entry[0].strip().upper() == 'PDF':
                                    med = 'PDF'
                                    spd = None
                                elif entry[0].strip().upper() == 'BAND':
                                    med = 'BAND'
                                    spd = "%s" % entry[1].strip()
                                else:
                                    med = "%s" % entry[0].strip()
                                    spd = "%s" % entry[1].strip()
                                if spd is not None:
                                    dat = "%s +/- %s" % (med, spd)
                                else:
                                    dat = "%s" % (med)
                    else:
                        dat = entry.strip()
                    data_lines.append(dat)
            data_entries.append(data_lines)
        self.bcg_save_pretty_file(self.panel_parameter_path, data_entries)
        datetime_str = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        save_str = 'Last Saved at {0} |'.format(datetime_str)
        self.saved_status_label.setText(save_str)
        self.repaint()
        self.saved = True

    def bcg_save_pretty_file(self, fname, data):
        # Open the file to write to
        fout = open(fname, 'w')
        # Data is organized row-wise
        # Get each column's width
        num_char = np.array([[len(str(dat)) for dat in row] for row in data])
        widths = np.amax(num_char.T, axis=1)
        # Construct strings to write
        for row in data:
            write_str = ''
            for i, dat in enumerate(row):
                fmt_str = ("%-" + str(int(widths[i])) + "s") % (dat)
                if i == 0:
                    write_str = fmt_str
                else:
                    write_str = (write_str + ' | ' + fmt_str)
            write_str += '\n'
            sep_str = '#' + '-' * (len(write_str) - 2) + '\n'
            fout.write(write_str)
            fout.write(sep_str)
        fout.close()
        return

    #################################################
    #################################################
    # ################# LOAIND DATA
    #################################################
    #################################################

    def bcg_setup_template(self):
        '''
        '''
        self.template_lines = {}
        for panel in ['channels', 'optics', 'camera', 'foregrounds', 'simulation', 'parameter',  'telescope']:
            self.panel = panel
            self.bcg_get_panel_parameter_path()
            if self.panel_parameter_path is None:
                return None
            else:
                self.bcg_load_panel()

    def bcg_load_panel(self):
        '''
        '''
        panel_lines = []
        with open(self.panel_parameter_path, 'r') as panel_parameter_handle:
            valid_lines = 0
            for i, line in enumerate(panel_parameter_handle.readlines()):
                if not line.startswith('#'):
                    line_as_list = [x.strip() for x in line.split('|')]
                    if valid_lines > 0:
                        line_as_list = self.bcg_parse_line(line_as_list)
                    valid_lines += 1
                    panel_lines.append(line_as_list)
        panel_dataframe = pd.DataFrame(panel_lines, columns=panel_lines[0])
        panel_dataframe = panel_dataframe[1:]
        if self.panel == 'optics':
            panel_dataframe = self.update_optics_dataframe_with_channels(panel_dataframe)
        if hasattr(self, '{0}_dataframe'.format(self.panel)):
            delattr(self, '{0}_dataframe'.format(self.panel))
        setattr(self, '{0}_dataframe'.format(self.panel), panel_dataframe)

    def update_optics_dataframe_with_channels(self, optics_dataframe):
        '''
        '''
        if not hasattr(self, 'channels'):
            return None
        self.bc_optics_order = optics_dataframe.keys()
        optics_dataframe = optics_dataframe[self.optics_column_order]
        for parameter in self.multiband_optical_properties:
            for column in optics_dataframe.keys():
                if parameter == column:
                    for row in optics_dataframe.index:
                        old_values = optics_dataframe[parameter][row]
                        if type(old_values) == list:
                            value_dict = dict(zip(self.channels, old_values[0]))
                            spread_dict = dict(zip(self.channels, old_values[1]))
                            new_values = [value_dict, spread_dict]
                        else:
                            if old_values in ('PDF', 'BAND'):
                                value_dict = dict(zip(self.channels, [old_values] * len(self.channels)))
                                spread_dict = dict(zip(self.channels, ['0'] * len(self.channels)))
                                new_values = [value_dict, spread_dict]
                            else:
                                new_values = old_values
                        optics_dataframe.loc[row, parameter] = new_values
        return optics_dataframe

    def bcg_scale_band_pass(self, freq, tran, eff):
        # Find the -3 dB points
        max_tran = np.amax(tran)
        max_tran_loc = np.argmax(tran)
        lo_point = np.argmin(
            abs(tran[:max_tran_loc] - 0.5 * max_tran))
        hi_point = np.argmin(
            abs(tran[max_tran_loc:] - 0.5 * max_tran)) + max_tran_loc
        flo = freq[lo_point]
        fhi = freq[hi_point]
        bw = fhi - flo
        # Scale the band
        scale_fact = (bw * eff) / np.trapz(tran, freq)
        return scale_fact * tran

    def bcg_get_band_pass_median(self, value, band_id, parameter):
        '''
        '''
        median = 0.7
        if self.gb_is_float(value[0]):
            median = float(value[0])
        elif value[0].strip() == 'PDF' or value == 'PDF':
            for extension in ['txt', 'csv']:
                pdf_path = self.bcg_load_pdf_file(element_name=band_id, parameter=parameter, panel='channels', get_names_from_widget=False)
                full_pdf_path = '{0}.{1}'.format(pdf_path, extension)
                if os.path.exists(full_pdf_path):
                    data = np.loadtxt(full_pdf_path, unpack=True)
                    vals = data[0]
                    probs = data[1]
                    median = self.bcg_pdf_median(vals, probs)
                    break
        else:
            self.gb_quick_message('error loading pdf setting Fractional BW to 0.3')
        return median

    def bcg_get_band_passes(self):
        '''
        '''
        band_pass_dict = {}
        channels = [x for x in self.channels_dataframe.index]
        data = np.asarray([[np.nan, np.nan, np.nan]])
        for channel in channels:
            band_id = self.channels_dataframe.loc[channel, "Band ID"]
            band_path = self.bcg_load_band_file(element_name=band_id, panel='channels', get_names_from_widget=False)
            band_center = self.channels_dataframe.loc[channel, "Band Center"]
            det_eff = self.channels_dataframe.loc[channel, "Det Eff"]
            det_eff_median = self.bcg_get_band_pass_median(det_eff, band_id, 'Det Eff')
            dict_key = os.path.basename(band_path)
            if band_center == 'BAND' or band_center[0] == 'BAND':
                for extension in ['txt', 'csv']:
                    full_band_path = '{0}.{1}'.format(band_path, extension)
                    if os.path.exists(full_band_path):
                        data = np.loadtxt(full_band_path, dtype=np.float, unpack=True)
                        # Scale the band to the desired efficiency
                        data[1] = self.bcg_scale_band_pass(data[0], data[1], det_eff_median)
                        break
            else:
                bc_median = self.bcg_get_band_pass_median(band_center, band_id, 'Band Center')
                fbw = self.channels_dataframe.loc[channel, "Fractional BW"]
                bw_median = self.bcg_get_band_pass_median(fbw, band_id, 'Fracitoinal BW')
                low_frequency = float(bc_median) * (1 - float(bw_median))
                high_frequency = float(bc_median) * (1 + float(bw_median))
                mid_frequency = (high_frequency + low_frequency) / 2
                data = np.array([
                    [low_frequency]*2 + [mid_frequency] + [high_frequency]*2,
                    [0] + [det_eff_median]*3 + [0]])
            band_pass_dict[dict_key] = data
        return band_pass_dict

    def bcg_parse_line(self, line_as_list):
        '''
        '''
        elements = []
        for i, element in enumerate(line_as_list):
            if 'BAND' in element:
                new_element = 'BAND'
            elif self.panel == 'parameter':
                new_element = str(element)
            elif self.panel == 'channels' and i == 0:
                new_element = str(element)
            elif self.panel == 'simulation' and i <= 2:
                new_element = str(element)
            elif self.gb_is_float(element):
                new_element = [element, '0.0']
            elif '+/-' in element:
                if self.panel == 'optics':
                    try:
                        if 'PDF' in element:
                            values = eval(element.split('+/-')[0].replace('PDF', "'PDF'"))
                            spreads = eval(element.split('+/-')[1].strip())
                        else:
                            values, spreads = self.bcg_eval(element)
                        if type(values) == list:
                            values = [str(x) for x in values]
                            spreads = [str(x) for x in spreads]
                        else:
                            values = str(values)
                            spreads = str(spreads)
                        new_element = [values, spreads]
                    except:
                        import ipdb;ipdb.set_trace()
                else:
                    new_element = element.split('+/-')
            elif 'PDF' in element:
                new_element = 'PDF'
            else:
                new_element = element
            elements.append(new_element)
        return elements

    def bcg_eval(self, element):
        '''
        '''
        values = [decimal.Decimal(x) for x in element.split(' +/- ')[0].strip('[]').strip().split(',')]
        spreads = [decimal.Decimal(x) for x in element.split(' +/- ')[1].strip('[]').strip().split(',')]
        #import ipdb;ipdb.set_trace()
        return values, spreads

    def bcg_get_downloaded_experiments(self):
        '''
        '''
        self.experiment_dict = {}
        self.experiments = []
        #experiment_menu = self.main_menu.addMenu('Experiments')
        bc_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Experiments')
        for experiment in os.listdir(bc_dir):
            if os.path.isdir(os.path.join(bc_dir, experiment)):
                self.experiment_dict[experiment] = {}
                self.experiments.append(experiment)
                self.bcg_get_experiment_versions(experiment)

    def bcg_get_experiment_versions(self, experiment):
        '''
        '''
        bc_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Experiments')
        experiment_dir = os.path.join(bc_dir, '{0}'.format(experiment))
        versions = os.listdir(experiment_dir)
        for version in versions:
            if os.path.isdir(os.path.join(experiment_dir, version)):
                self.experiment_dict[experiment][version] = {}
                self.bcg_get_telescopes_in_version(experiment, version)

    def bcg_get_telescopes_in_version(self, experiment, version):
        '''
        '''
        bc_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Experiments')
        version_dir = os.path.join(bc_dir, '{0}'.format(experiment),
                                   '{0}'.format(version))
        telescopes = [x for x in os.listdir(version_dir)]
        for telescope in telescopes:
            if (os.path.isdir(os.path.join(version_dir, telescope)) and
               telescope not in ['config', 'paramVary']):
                self.experiment_dict[experiment][version][telescope] = []
                self.bcg_get_cameras_in_telescope(experiment, version, telescope)

    def bcg_get_cameras_in_telescope(self, experiment, version, telescope):
        '''
        '''
        bc_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Experiments')
        telescope_dir = os.path.join(bc_dir, '{0}'.format(experiment),
                                     '{0}'.format(version), '{0}'.format(telescope))
        cameras = [x for x in os.listdir(telescope_dir)]
        for camera in cameras:
            if (os.path.isdir(os.path.join(telescope_dir, camera)) and
               camera not in ['config', 'paramVary']):
                self.experiment_dict[experiment][version][telescope].append(camera)

    def bcg_get_panel_parameter_path(self):
        '''
        '''
        self.panel_parameter_path = None
        bc_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Experiments')
        if self.bcg_can_load():
            if self.panel is None:
                panel_parameter_path = os.path.join(bc_dir, self.experiment)
            elif self.panel == 'foregrounds':
                panel_parameter_path = os.path.join(bc_dir, self.experiment, self.version,
                                                   'config', 'foregrounds.txt')
            elif self.panel in ['telescope', 'elevation', 'pwv']:
                panel_parameter_path = os.path.join(bc_dir, self.experiment, self.version, self.telescope,
                                                   'config', '{0}.txt'.format(self.panel))
            elif self.panel in ['camera', 'channels', 'optics']:
                panel_parameter_path = os.path.join(bc_dir, self.experiment, self.version, self.telescope,
                                                   self.camera, 'config', '{0}.txt'.format(self.panel))
                if not os.path.exists(panel_parameter_path):
                    print()
                    print('{0}\nNot Found'.format(panel_parameter_path))
                    print('Experiment Name:\n', self.experiment, '\nTelescope Name:\n', self.telescope, '\nCamera Name:\n', self.camera)
                    print(len(self.camera), self.camera)
            elif self.panel == 'simulation':
                panel_parameter_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'simulationInputs.txt')
            elif self.panel == 'parameter':
                panel_parameter_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'paramsToVary.txt')
            self.panel_parameter_path = panel_parameter_path
            self.save_path_label.setText('Working file: {0} |'.format(self.panel_parameter_path))

    def bcg_can_load(self):
        '''
        '''
        can_load = True
        if not hasattr(self, 'panel'):
            can_load = False
        if not hasattr(self, 'experiment') or len(self.experiment) == 0:
            can_load = False
        if not hasattr(self, 'version') or len(self.version) == 0:
            can_load = False
        if not hasattr(self, 'telescope') or len(self.telescope) == 0:
            can_load = False
        if not hasattr(self, 'camera') or len(self.camera) == 0:
            can_load = False
        if self.panel in ['simulation', 'parameter']:
            can_load = True
        return can_load

    #################################################
    #################################################
    # ################# Verification
    #################################################
    #################################################

    def bcg_verify_popup(self):
        '''
        '''
        if not hasattr(self, 'BCG_verify_popup'):
            self.gb_create_popup_window('BCG_verify_popup')
        else:
            self.gb_initialize_panel('BCG_verify_popup')
        q_report_label = QtWidgets.QTextEdit(self.BCG_verify_popup)
        q_report_label.setReadOnly(True)
        self.report_label = q_report_label
        self.BCG_verify_popup.layout().addWidget(q_report_label, 1, 0, 1, 2)
        self.BCG_verify_popup.setWindowModality(QtCore.Qt.WindowModal)
        # Warning check box
        q_show_warnings_checkbox = QtWidgets.QCheckBox('Show Warnings', self.BCG_verify_popup)
        q_show_warnings_checkbox.setChecked(True)
        q_show_warnings_checkbox.stateChanged.connect(self.bcg_verify)
        self.show_warnings_checkbox = q_show_warnings_checkbox
        self.BCG_verify_popup.layout().addWidget(q_show_warnings_checkbox, 0, 0, 1, 1)
        # Run bolo calc button
        q_run_bc = QtWidgets.QPushButton('Run BoloCalc', self.BCG_verify_popup)
        q_run_bc.clicked.connect(self.bcg_get_bolo_calc_run_options)
        self.run_bc_verify = q_run_bc
        self.BCG_verify_popup.layout().addWidget(q_run_bc, 0, 1, 1, 1)
        self.BCG_verify_popup.resize(0.4 * self.screen_resolution.width(), 0.6 * self.screen_resolution.height())
        report = self.bcg_verify()
        self.BCG_verify_popup.show()

    def bcg_verify(self):
        '''
        '''
        self.template_lines = {}
        report = ''
        current_panel = self.panel
        if hasattr(self, 'show_warnings_checkbox') and self.show_warnings_checkbox.isChecked():
            self.show_bc_warnings = True
        for panel in ['channels', 'optics', 'camera', 'foregrounds', 'simulation', 'parameter',  'telescope']:
            self.panel = panel
            panel_report = self.bcg_verify_panel()
            if len(panel_report) == 0:
                report += 'Checking {0}.........All Set\n'.format(panel.title())
            else:
                report += 'Checking {0}...\n\n{1}'.format(panel.title(), panel_report)
            report += '\n'
        self.panel = current_panel
        if 'Invalid' in report:
            self.action_Run.setDisabled(True)
            if hasattr(self, 'BCG_verify_popup'):
                self.run_bc_verify.setDisabled(True)
        else:
            self.action_Run.setDisabled(False)
            if hasattr(self, 'BCG_verify_popup'):
                self.run_bc_verify.setDisabled(False)
        if hasattr(self, 'report_label'):
            self.report_label.setText(report)
        if hasattr(self, 'BCG_verify_popup'):
            if not self.show_bc_warnings:
                self.BCG_verify_popup.resize(0.3 * self.screen_resolution.width(), 0.2 * self.screen_resolution.height())
            else:
                self.BCG_verify_popup.resize(0.4 * self.screen_resolution.width(), 0.6 * self.screen_resolution.height())
        return report

    def bcg_verify_trumping_parameter(self, panel_dataframe, row, element_name, parameter, override_parameter):
        '''
        '''
        valid = False
        override_parameter = override_parameter
        override_value = panel_dataframe.loc[row, override_parameter]
        overridden_parameter = parameter
        overridden_value = panel_dataframe.loc[row, overridden_parameter]
        if override_value == 'NA' and overridden_value != 'NA':
            report = 'OVER RIDE WARNING!\n'
            report += '\tParameter: "{0}"\n'.format(overridden_parameter)
            report += '\tValue: {0}\n'.format(overridden_value[0])
            report += '\tWILL OVER RIDE\n'
            report += '\tParameter: {0}\n'.format(override_parameter)
            report += '\tValue: {0}\n'.format(override_value)
            valid = True
        elif override_value != 'NA' and overridden_value != 'NA':
            valid = True
            report = 'OVER RIDE WARNING!\n'
            report += '\tParameter: "{0}"\n'.format(override_parameter)
            report += '\tValue: {0}\n'.format(override_value)
            report += '\tWILL OVER RIDE\n'
            report += '\tParameter: {0}\n'.format(overridden_parameter)
            report += '\tValue: {0}\n'.format(overridden_value)
            pass
        elif override_value == 'NA' and overridden_value == 'NA':
            valid = False
            report = '\tError: {0} cannot have both {1} and {2} be NA\n'.format(element_name, override_parameter, overridden_parameter)
        else:
            valid = True
            report = ''
        return report, valid

    def bcg_verify_panel(self):
        '''
        '''
        panel_dataframe = getattr(self, '{0}_dataframe'.format(self.panel))
        parameter_definition_path = os.path.join(os.path.dirname(__file__), '..', 'param_definitions', '{0}_paramDefs.json'.format(self.panel))
        with open(parameter_definition_path, 'r') as parameter_definition_file_handle:
            parameter_definition_dict = json.load(parameter_definition_file_handle)
        report = ''
        if hasattr(self, 'show_warnings_checkbox'):
            self.show_bc_warnings = self.show_warnings_checkbox.isChecked()
        special_file = False
        if self.panel in ('channels', 'optics'):
            for parameter in panel_dataframe.keys():
                for i, row in enumerate(panel_dataframe.index):
                    is_valid = True
                    element_name = panel_dataframe.loc[row, panel_dataframe.keys()[0]]
                    value = panel_dataframe.loc[row, parameter]
                    valid_types = parameter_definition_dict[parameter]['type']
                    valid_range = parameter_definition_dict[parameter]['range']
                    if value in ('PDF', 'BAND'):
                        is_valid, valid_value = self.bcg_get_and_verify_special_file(value, element_name, parameter)
                    elif type(value[0]) == dict:
                        for channel_name, test_value in value[0].items():
                            if test_value in ('PDF', 'BAND'):
                                is_valid, valid_value = self.bcg_get_and_verify_special_file(test_value, element_name, parameter, channel_name)
                            else:
                                is_valid, valid_value = self.bcg_verify_value_in_range(test_value, valid_types, valid_range)
                    else:
                        is_valid, valid_value = self.bcg_verify_value_in_range(value, valid_types, valid_range)
                    if not is_valid:
                        report += '\tInvalid parameter found in "{0}"\n'.format(self.panel.title())
                        if self.panel == 'channels':
                            report += '\tPlease correct "{0}" for channel "{1}"\n'.format(parameter, element_name)
                        elif self.panel == 'optics':
                            report += '\twhile checking the "{0}" of the optic "{1}"\n'.format(parameter, element_name)
                        if not value in ('PDF', 'BAND'):
                            report += '\t{0} is not in the range {1}\n\n'.format(valid_value, valid_range)
                        else:
                            report += '{0}\n'.format(valid_value)
                    elif 'trumpedBy' in parameter_definition_dict[parameter] and self.show_bc_warnings:
                        override_parameter = parameter_definition_dict[parameter]['trumpedBy'][0]
                        trumped_report, valid = self.bcg_verify_trumping_parameter(panel_dataframe, row, element_name, parameter, override_parameter)
                        report += trumped_report
                        if not valid:
                            is_valid = valid
                    else:
                        pass #import ipdb;ipdb.set_trace()
        elif self.panel not in ('parameter'):
            for row in panel_dataframe.index:
                parameter = panel_dataframe.loc[row, 'Parameter']
                element_name = None
                value = panel_dataframe.loc[row, 'Value']
                valid_types = parameter_definition_dict[parameter]['type']
                valid_range = parameter_definition_dict[parameter]['range']
                if value in ('PDF', 'BAND'):
                    is_valid, valid_value = self.bcg_get_and_verify_special_file(value, element_name, parameter)
                else:
                    is_valid, valid_value = self.bcg_verify_value_in_range(value, valid_types, valid_range)
                if not is_valid:
                    report += '\tInvalid Param Found in the "{0}" panel\n'.format(self.panel.title())
                    report += '\t{0} is not in the range {1}\n'.format(valid_value, valid_range)
                    report += '\tInvalid Param Found in {0}\n'.format(self.panel.title())
                    report += '\t{0}'.format(parameter)
                    report += '\t{0} is not in the range {1}\n\n'.format(value, valid_range)
                elif 'trumpedBy' in parameter_definition_dict[parameter] and self.show_bc_warnings:
                    override_parameter = parameter_definition_dict[parameter]['trumpedBy']
                    trumped_report, valid = self.bcg_verify_trumping_parameter(panel_dataframe, row, element_name, parameter, override_parameter)
                    report += trumped_report
                else:
                    pass #import ipdb;ipdb.set_trace()
            #import ipdb;ipdb.set_trace()
        return report

    def bcg_get_special_file_valid_count(self, special_file_dict, valid_value=''):
        '''
        '''
        valid_count = 0
        for extension in ('txt', 'csv'):
            if special_file_dict[extension]['exists']:
                path = special_file_dict[extension]['path']
                valid = special_file_dict[extension]['valid']
                if valid:
                    valid_count += 1
                else:
                    error = special_file_dict[extension]['data']
                    valid_value += '\t{0} for {1}\n'.format(str(error), os.path.basename(path))
        return valid_count, valid_value

    def bcg_get_and_verify_special_file(self, value, element_name, parameter, channel_name=None):
        '''
        '''
        value = value.lower()
        self.edit_type = value.upper()
        special_file_dict = self.bcg_get_special_file_dict(file_type=value, element_name=element_name, parameter=parameter, channel_name=channel_name)
        valid_count, valid_value = self.bcg_get_special_file_valid_count(special_file_dict)
        if valid_count == 0:
            valid_value += '\t:::Neither TXT nor CSV are valid for {0}\n'.format(value.upper())
            is_valid = False
        elif valid_count == 1:
            valid_value += '\n'
            is_valid = True
        elif valid_count == 2:
            valid_value += '\t\t:::Warning Both TXT and CSV exist for {0}\n'.format(value.upper())
            is_valid = True
        return is_valid, valid_value

    def bcg_verify_value_in_range(self, value, valid_types, valid_range):
        '''
        '''
        is_valid = False
        valid_value = None
        if valid_range == 'NA' and len(value) > 0:
            is_valid = True
            valid_value = value
        elif value == 'NA' and 'na' in valid_types:
            is_valid = True
            valid_value = value
        elif type(value) == list:
            central_value = value[0]
            if type(central_value) == list and len(central_value) == 1:
                if 'int' in valid_types and not 'float' in valid_types:
                    if float(value).is_integer():
                        is_valid = True
                else:
                    is_valid, valid_value = self.bcg_float_in_range(central_value[0], valid_range)
            elif type(central_value) == list:
                print('ma')
                import ipdb;ipdb.set_trace()
            elif type(central_value) == dict:
                for channel_name, test_value in central_value.items():
                    test_in_range, test_valid_value = self.bcg_float_in_range(float(test_value), valid_range)
                    if not test_in_range and is_valid:
                        is_valid = False
                        valid_value = 'Ch "{0}" has the value "{1}" which'.format(channel_name, test_value)
                    else:
                        is_valid = True
                if is_valid:
                    valid_value = test_valid_value
            else:
                if self.gb_is_float(value[0].strip()):
                    is_valid, valid_value = self.bcg_float_in_range(value, valid_range)
                elif value[0].strip() == 'PDF':
                    is_valid = True
                    valid_value = 'PDF'
                else:
                    print('pa')
                    import ipdb;ipdb.set_trace()
        elif valid_types == '[bool]':
            if value in ('False', 'True'):
                is_valid = True
        else:
            if self.gb_is_float(value):
                if 'int' in valid_types and not 'float' in valid_types:
                    if float(value).is_integer():
                        is_valid = True
                else:
                    is_valid, valid_value = self.bcg_float_in_range(value, valid_range)
            else:
                is_valid = False
                valid_value = 'Unknown'
        return is_valid, valid_value

    def bcg_float_in_range(self, value, valid_range):
        '''
        '''
        in_range = False
        if not type(value) == float:
            float_value = float(value[0].strip())
        else:
            float_value = value
        if '(' in valid_range:
            op_1 = np.greater
        elif '[' in valid_range:
            op_1 = np.greater_equal
            valid_range = valid_range.replace('[', '(')
        else:
            print('no valid 1 operator')
            import ipdb;ipdb.set_trace()
        if ')' in valid_range:
            op_2 = np.less
        elif ']' in valid_range:
            op_2 = np.less_equal
            valid_range = valid_range.replace(']', ')')
        else:
            print('no valid 2 operator')
            import ipdb;ipdb.set_trace()
        float_range = eval(valid_range)
        if op_1(float_value, float_range[0]):
            in_range = True
        if op_2(float_value, float_range[0]):
            in_range = True
        return in_range, str(float_value)

    #################################################
    #################################################
    # ################# Running
    #################################################
    #################################################

    def bcg_get_bolo_calc_run_options(self):
        if hasattr(self, 'BCG_verify_popup'):
            self.BCG_verify_popup.close()
        if not hasattr(self, 'BCG_run_options_popup'):
            self.gb_create_popup_window('BCG_run_options_popup')
        else:
            self.gb_initialize_panel('BCG_run_options_popup')
        ########## vary tog
        q_vary_tog_checkbox = QtWidgets.QCheckBox('vary_tog', self)
        setattr(self, 'vary_tog_checkbox', q_vary_tog_checkbox)
        q_vary_tog_checkbox.setChecked(False)
        q_vary_tog_checkbox.stateChanged.connect(self.bcg_update_run_command)
        self.BCG_run_options_popup.layout().addWidget(q_vary_tog_checkbox, 1, 1, 1, 1)
        ########## display run command
        q_vary_run_command_label = QtWidgets.QLabel()
        q_vary_run_command_label.setAlignment(QtCore.Qt.AlignCenter)
        setattr(self, 'vary_run_command_label', q_vary_run_command_label)
        self.BCG_run_options_popup.layout().addWidget(q_vary_run_command_label, 4, 0, 1, 3)
        ########## vary checkbox
        q_vary_checkbox = QtWidgets.QCheckBox('vary', self)
        setattr(self, 'vary_checkbox', q_vary_checkbox)
        q_vary_checkbox.setWhatsThis('vary_checkbox')
        self.BCG_run_options_popup.layout().addWidget(q_vary_checkbox, 0, 0, 1, 1)
        q_vary_checkbox.setChecked(False)
        ########## vary name 
        q_vary_name_label = QtWidgets.QLabel('SWEEP NAME')
        q_vary_name_label.setWhatsThis('vary_header_label')
        self.BCG_run_options_popup.layout().addWidget(q_vary_name_label, 2, 1, 1, 1)
        q_vary_name_lineedit = QtWidgets.QLineEdit()
        q_vary_name_lineedit.setWhatsThis('vary_lineedit')
        setattr(self, 'vary_name_lineedit', q_vary_name_lineedit)
        self.BCG_run_options_popup.layout().addWidget(q_vary_name_lineedit, 2, 2, 1, 1)
        ########## log name 
        q_log_name_label = QtWidgets.QLabel('LOG NAME')
        q_log_name_label.setWhatsThis('log_header_label')
        self.BCG_run_options_popup.layout().addWidget(q_log_name_label, 3, 0, 1, 1)
        q_log_name_lineedit = QtWidgets.QLineEdit()
        q_log_name_lineedit.setWhatsThis('log_lineedit')
        setattr(self, 'log_name_lineedit', q_log_name_lineedit)
        self.BCG_run_options_popup.layout().addWidget(q_log_name_lineedit, 3, 1, 1, 2)
        ########## run button
        q_run_pushbutton = QtWidgets.QPushButton('Run Bolo Calc')
        self.BCG_run_options_popup.layout().addWidget(q_run_pushbutton, 5, 0, 1, 3)
        ########## asssign function
        q_vary_checkbox.stateChanged.connect(self.bcg_update_run_command)
        q_vary_name_lineedit.textChanged.connect(self.bcg_update_run_command)
        q_log_name_lineedit.textChanged.connect(self.bcg_update_run_command)
        q_run_pushbutton.clicked.connect(self.bcg_run_bolo_calc)
        self.bcg_update_run_command()
        self.BCG_run_options_popup.show()

    def bcg_update_run_command(self):
        '''
        '''
        calc_bolos_path = os.path.join(self.bolo_calc_install_dir, 'calcBolos.py')
        experiment_path = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version)
        run_command = 'python '
        run_command += calc_bolos_path
        run_command += '  '
        self.vary = False
        if self.vary_checkbox.isChecked():
            run_command += '--vary '
            if self.vary_tog_checkbox.isChecked():
                run_command += ' --vary_tog '
            self.vary = True
        else:
            run_command = 'python '
            run_command += calc_bolos_path
            run_command += '  '
        if not self.vary_checkbox.isChecked():
            self.vary_tog_checkbox.setDisabled(True)
            self.vary_name_lineedit.setDisabled(True)
        else:
            self.vary_tog_checkbox.setDisabled(False)
            self.vary_name_lineedit.setDisabled(False)
        if len(self.vary_name_lineedit.text()) > 0 and self.vary_checkbox.isChecked():
            if len(self.sender().text()) > 0:
                run_command += ' --vary_name '
                run_command += self.vary_name_lineedit.text()
                self.vary_name = self.vary_name_lineedit.text()
                run_command += ' '
        if len(self.log_name_lineedit.text()) > 0:
            if len(self.sender().text()) > 0:
                run_command += ' --log_name '
                run_command += self.log_name_lineedit.text()
                run_command += ' '
        run_command += experiment_path
        self.vary_run_command_label.setText(run_command)

    def bcg_run_bolo_calc(self):
        '''
        '''
        calc_bolos_path = os.path.join(self.bolo_calc_install_dir, 'calcBolos.py')
        experiment_path = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version)
        if hasattr(self, 'vary_path'):
            vary_path = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version, self.telescope, self.camera, 'paramVary', self.vary_name)
            if os.path.exists(vary_path):
                msg = 'A paramVary folder named {0} exists!\nRunning calcBolos.py again will over write this data.\nDo you wish to continue?'.format(self.vary_name)
                response = self.gb_quick_message(msg, add_yes=True, add_no=True)
                if response == QtWidgets.QMessageBox.No:
                    return None
        self.BCG_run_options_popup.close()
        run_command = self.vary_run_command_label.text()
        self.status_bar.showMessage('Running BoloCalc!')
        self.repaint()
        self.bcg_step = 'Simulating Realizations'
        q_process = QtCore.QProcess()
        self.run_type = 'Sim'
        self.sim_progress_bar.setValue(0)
        self.vary_progress_bar.setValue(0)
        self.write_progress_bar.setValue(0)
        self.bc_error = False
        q_process.finished.connect(lambda: self.bcg_update_sim_finished(q_process))
        q_process.readyReadStandardOutput.connect(lambda: self.bcg_update_run_status(q_process))
        q_process.error.connect(lambda: self.bcg_bolo_calc_error(q_process))
        q_process.start(run_command)

    def bcg_bolo_calc_error(self, q_process):
        '''
        '''
        self.sim_progress_bar.setValue(0)
        self.vary_progress_bar.setValue(0)
        self.write_progress_bar.setValue(0)

    def bcg_update_sim_finished(self, q_process):
        '''
        '''
        exit_code = q_process.exitCode()
        if exit_code == 0:
            self.status_bar.showMessage('Finished Running Bolo Calc')
            self.write_progress_bar.setValue(100)
        else:
            error = q_process.readAllStandardError()
            msgs = error.split('\n')
            display_msg = 'Error with bolo calc'
            for msg in msgs:
                display_msg += '{0}\n'.format(msg)
            self.gb_quick_message(display_msg)
            self.bc_error = True

    def bcg_update_run_status(self, q_process):
        '''
        '''
        out = str(q_process.readAllStandardOutput())
        print(out)
        if 'Looping' in out:
            self.bcg_step = 'Looping over parameters to vary'
        if 'Writing' in out:
            self.bcg_step = 'Writing output to disk'
        if 'Looping' in out:
            self.run_type = 'Vary'
            self.sim_progress_bar.setValue(100)
        if 'Writing' in out:
            self.run_type = 'Write'
            self.vary_progress_bar.setValue(100)
        pct = out.split(' ')[-1]
        pct = pct.replace("\\r", '').strip()
        pct = pct.replace("\\n", '').strip()
        pct = pct.replace("%", '').strip()
        pct = pct.replace("'", '').strip()
        pct = pct.replace('"', '').strip()
        pct_as_float = float(pct)
        pct_as_int = int(pct_as_float)
        pct_complete = '{0} {1:.1f}% complete'.format(self.bcg_step, pct_as_float)
        pct_complete = pct_complete.replace("\\r\\n", '')
        if self.run_type == 'Sim':
            self.sim_progress_bar.setValue(pct_as_int)
        if self.run_type == 'Vary':
            self.vary_progress_bar.setValue(pct_as_int)
        if self.run_type == 'Write':
            self.write_progress_bar.setValue(pct_as_int)
        self.status_bar.showMessage(pct_complete)
        self.repaint()

    #################################################
    #################################################
    # ################# Analysis
    #################################################
    #################################################

    def bcg_analyze(self):
        if hasattr(self, 'BCG_analyze_popup'):
            self.BCG_analyze_popup.close()
        # Check for analysis finished
        experiment_dir = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version)
        bc_dir = os.path.join('..', 'BoloCalc', 'Experiments')
        sensitivity_file_path = os.path.join(bc_dir, self.experiment, self.version, 'sensitivity.txt')
        self.data_exists = {
            'Histogram and Summary': {
                'path': '',
                'msg': '',
                'exists': True},
            'Parameter Vary': {
                'path': '',
                'msg': '',
                'exists': True}
            }
        self.data_exists['Histogram and Summary']['path'] = sensitivity_file_path
        if not os.path.exists(sensitivity_file_path):
            msg = '{0} does not exists.\nPlease Run Bolo Calc first (w/o vary options)'.format(sensitivity_file_path)
            self.data_exists['Histogram and Summary']['exists'] = False
            self.data_exists['Histogram and Summary']['msg'] = msg
        param_vary_path = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version, self.telescope, self.camera, 'paramVary')
        self.data_exists['Parameter Vary']['path'] = param_vary_path
        if not os.path.exists(param_vary_path):
            msg = '{0} does not exists.\nPlease Run Bolo Calc first (w/o vary options)'.format(param_vary_path)
            self.data_exists['Parameter Vary']['exists'] = False
            self.data_exists['Parameter Vary']['msg'] = msg
        if self.data_exists['Histogram and Summary']['exists'] or self.data_exists['Parameter Vary']['exists']:
            BCG_analyze_popup = QtWidgets.QMainWindow(self)
            BCG_analyze_popup.setWindowTitle('Analyze')
            #BCG_analyze_popup.setWindowModality(QtCore.Qt.WindowModal)
            #BCG_analyze_popup.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, True)
            self.BCG_analyze_popup = BCG_analyze_popup
            BCG_analyze_cw = QtWidgets.QWidget()
            # Tool bar 
            bottom_tool_bar_area = QtCore.Qt.BottomToolBarArea
            BCG_analyze_cw.setLayout(QtWidgets.QGridLayout())
            BCG_analyze_popup.setCentralWidget(BCG_analyze_cw)
            q_analyze_tab_bar = QtWidgets.QTabBar()
            for i, tab in enumerate(['Histogram and Summary', 'Parameter Vary']):
                q_analyze_tab_bar.addTab(tab)
            q_analyze_tab_bar.currentChanged.connect(lambda: self.bcg_show_analysis_options(q_analyze_tab_bar))
            self.BCG_analyze_popup.centralWidget().layout().addWidget(q_analyze_tab_bar, 0, 0, 1, 4)
            q_analyze_tab_bar.setCurrentIndex(1)
            q_analyze_tab_bar.setCurrentIndex(0)
            self.qt_app.processEvents()
            self.BCG_analyze_popup.resize(0.5 * self.screen_resolution.width(),
                                          0.5 * self.screen_resolution.height())
            self.BCG_analyze_popup.move(100, 100)
            self.BCG_analyze_popup.show()
        else:
            full_msg = 'You need to run bolo calc first (with our without the vary option)'
            self.gb_quick_message(full_msg)

    def bcg_show_analysis_options(self, tab_bar):
        '''
        '''
        panel = self.BCG_analyze_popup.centralWidget()
        for index in reversed(range(panel.layout().count())):
            widget = panel.layout().itemAt(index).widget()
            if not isinstance(widget, QtWidgets.QTabBar):
                widget.setParent(None)
        analysis_type = tab_bar.tabText(tab_bar.currentIndex())
        experiment_dir = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version)
        if analysis_type == 'Histogram and Summary':
            self.unpack.sens_outputs = {}
            self.unpack.unpack_sensitivities(experiment_dir)
            self.bcg_configure_histogram_and_summary_analysis()
        else:
            self.bcg_analyze_param_vary()

    def bcg_show_analysis_table(self, index):
        '''
        '''
        if 'Version' in self.sender().whatsThis():
            sensitivity_dict = self.unpack.sens_outputs[self.version]['Summary']
            self.bcg_create_sensitivity_table(sensitivity_dict)
        if 'Telescope' in self.sender().whatsThis():
            sensitivity_dict = self.unpack.sens_outputs[self.version][self.telescope]['Summary']
            self.bcg_create_sensitivity_table(sensitivity_dict)
        if 'Camera' in self.sender().whatsThis():
            sensitivity_dict = self.unpack.sens_outputs[self.version][self.telescope][self.camera]['Summary']
            self.bcg_create_sensitivity_table(sensitivity_dict, is_camera=True)
        if 'Channel' in self.sender().whatsThis():
            import ipdb;ipdb.set_trace()

    def bcg_configure_histogram_and_summary_analysis(self):
        '''
        '''
        output_dict = self.unpack.sens_outputs[self.version]
        q_experiment_table_pushbutton = QtWidgets.QPushButton('Experiment Sumamry Table')
        q_experiment_table_pushbutton.setWhatsThis('Version Summary PushButton')
        q_experiment_table_pushbutton.clicked.connect(self.bcg_show_analysis_table)
        self.BCG_analyze_popup.centralWidget().layout().addWidget(q_experiment_table_pushbutton, 1, 0, 1, 4)
        for i, telescope in enumerate(self.unpack.sens_outputs[self.version].keys()):
            if telescope != 'Summary':
                q_telescope_pushbutton = QtWidgets.QPushButton('Telescope: {0} Summary Table '.format(telescope))
                q_telescope_pushbutton.setWhatsThis('Telescope {0} PushButton'.format(telescope))
                q_telescope_pushbutton.clicked.connect(self.bcg_show_analysis_table)
                self.BCG_analyze_popup.centralWidget().layout().addWidget(q_telescope_pushbutton, 2, i, 1, 4)
        for i, camera in enumerate(self.unpack.sens_outputs[self.version][self.telescope].keys()):
            if camera != 'Summary':
                q_camera_pushbutton = QtWidgets.QPushButton('Camera: {0} Summary Table '.format(camera))
                q_camera_pushbutton.setWhatsThis('Camera {0} PushButton'.format(camera))
                q_camera_pushbutton.clicked.connect(self.bcg_show_analysis_table)
                self.BCG_analyze_popup.centralWidget().layout().addWidget(q_camera_pushbutton, 3, i, 1, 4)
        for i, channel in enumerate(self.unpack.sens_outputs[self.version][self.telescope][self.camera]['All'].keys()):
            q_channel_check_box = QtWidgets.QCheckBox(channel)
            setattr(self, '{0}_checkbox'.format(channel), q_channel_check_box)
            q_channel_check_box.setChecked(True)
            q_channel_check_box.setWhatsThis('Channel: {0} Analysis CheckBox'.format(channel))
            self.BCG_analyze_popup.centralWidget().layout().addWidget(q_channel_check_box, 4, i, 1, 1)
        self.bcg_add_histogram_buttons(channel)

    def bcg_add_histogram_buttons(self, channel):
        '''
        '''
        for i, result in enumerate(self.unpack.sens_outputs[self.version][self.telescope][self.camera]['All'][channel].keys()):
            mc_realizations = self.unpack.sens_outputs[self.version][self.telescope][self.camera]['All'][channel][result]
            button_name = result
            if result in self.preferred_output_names_dict:
                button_name = self.preferred_output_names_dict[result]
            q_mc_histogram_pushbutton = QtWidgets.QPushButton(button_name)
            q_mc_histogram_pushbutton.clicked.connect(self.bcg_make_and_show_mc_histogram)
            self.BCG_analyze_popup.centralWidget().layout().addWidget(q_mc_histogram_pushbutton, 5 + i, 0, 1, 3)
            q_mc_histogram_descr_pushbutton = QtWidgets.QPushButton("?")
            q_mc_histogram_descr_pushbutton.setWhatsThis(result)
            q_mc_histogram_descr_pushbutton.clicked.connect(self.bcg_show_histogram_info)
            self.BCG_analyze_popup.centralWidget().layout().addWidget(q_mc_histogram_descr_pushbutton, 5 + i, 3, 1, 1)

    def bcg_show_histogram_info(self):
        '''
        '''
        hisotgram_type = self.sender().whatsThis()
        file_name = '{0}_definition.svg'.format(hisotgram_type.replace(' ', ''))
        histogram_descr_path = os.path.join(os.path.dirname(__file__), '..', 'templates', file_name)
        self.old_size = (-1, -1)
        if os.path.exists(histogram_descr_path):
            self.convertSVG(histogram_descr_path)
            self.gb_create_popup_window('BCG_histogram_description')
            self.gb_create_popup_window('BCG_histogram_description', resize_overload=self.bcg_resize_svg_event)
            self.BCG_histogram_description.move(150, 150)
            self.q_svg_widget = QtSvg.QSvgWidget(self.BCG_histogram_description)
            #self.q_svg_widget.resizeEvent = self.bcg_resize_svg_event
            self.BCG_histogram_description.layout().addWidget(self.q_svg_widget, 0, 0, 1, 1)
            self.histogram_svg_size = (self.q_svg_widget.size().width(), self.q_svg_widget.size().height())
            self.histogram_svg_aspect_ratio = float(self.histogram_svg_size[1]) / float(self.histogram_svg_size[0])
            self.q_svg_widget.load(histogram_descr_path)
            #[import ipdb;ipdb.set_trace()
            self.BCG_histogram_description.show()
            self.BCG_histogram_description.show()

    def bcg_resize_svg_event(self, event):
        '''
        '''
        if True:
            return None
        print()
        print()
        print()
        print(self.histogram_svg_size, self.sender())
        new_size = event.size()
        old_size = event.oldSize()
        print('new', new_size, 'old', self.old_size)
        print()
        if int(old_size.width()) == -1:
            old_size = new_size
        print('old', new_size)
        width_ratio = new_size.width() / old_size.width()
        print(width_ratio)
        #import ipdb;ipdb.set_trace()
        new_width = self.histogram_svg_size[0] * width_ratio
        new_height = self.histogram_svg_aspect_ratio * new_width
        self.q_svg_widget.resize(new_width, new_height)
        self.BCG_histogram_description.setFixedSize(new_width, new_height)
        self.histogram_svg_size = (new_width, new_height)
        self.old_size = new_size
        print('hi', old_size, new_size, new_width, new_height)

    def bcg_make_and_show_mc_histogram(self):
        '''
        '''
        parameter = self.sender().text()
        plt.close('all')
        for i, channel in enumerate(self.unpack.sens_outputs[self.version][self.telescope][self.camera]['All'].keys()):
            if getattr(self, '{0}_checkbox'.format(channel)).checkState():
                label = '{0} {1}'.format(channel, parameter)
                sns.distplot(self.unpack.sens_outputs[self.version][self.telescope][self.camera]['All'][channel][parameter], kde=False, label=label)
        unit = self.unit_dict[parameter].replace('[', '').replace(']', '')
        if unit.upper() == 'NA':
            plt.xlabel('{0}'.format(parameter))
        else:
            plt.xlabel('{0} [{1}]'.format(parameter, unit))
        plt.ylabel('# of Realizations')
        plt.legend()
        plt.show()

    def bcg_analyze_param_vary(self):
        '''
        '''
        param_vary_path = self.data_exists['Parameter Vary']['path']
        if not os.path.exists(param_vary_path):
            return None
        q_param_vary_select_combobox = QtWidgets.QComboBox()
        for i, param_vary in enumerate(os.listdir(param_vary_path)):
            q_param_vary_select_combobox.addItem(param_vary)
            self.BCG_analyze_popup.centralWidget().layout().addWidget(q_param_vary_select_combobox, i + 1, 0, 1, 1)
        q_param_vary_select_combobox.activated.connect(self.bcg_configure_plot_param_vary)
        experiment_path = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version)
        ########## scatter plot button
        q_run_param_vary_scatter_pushbutton = QtWidgets.QPushButton('Param Vary Scatter Plot')
        setattr(self, 'vary_scatter_pushubtton', q_run_param_vary_scatter_pushbutton)
        q_run_param_vary_scatter_pushbutton.setDisabled(True)
        q_run_param_vary_scatter_pushbutton.clicked.connect(self.bcg_plot_param_vary)
        self.BCG_analyze_popup.centralWidget().layout().addWidget(q_run_param_vary_scatter_pushbutton, i + 2, 0, 1, 1)
        ########## violin plot button
        q_run_param_vary_violin_pushbutton = QtWidgets.QPushButton('Param Vary Violin Plot')
        setattr(self, 'vary_violin_pushubtton', q_run_param_vary_violin_pushbutton)
        q_run_param_vary_violin_pushbutton.setDisabled(True)
        q_run_param_vary_violin_pushbutton.clicked.connect(self.bcg_plot_param_vary)
        self.BCG_analyze_popup.centralWidget().layout().addWidget(q_run_param_vary_violin_pushbutton, i + 3, 0, 1, 1)
        ########## violin plot button
        q_run_param_vary_heatmap_pushbutton = QtWidgets.QPushButton('Param Vary Heat Map Plot')
        setattr(self, 'vary_heatmap_pushubtton', q_run_param_vary_heatmap_pushbutton)
        q_run_param_vary_heatmap_pushbutton.setDisabled(True)
        q_run_param_vary_heatmap_pushbutton.clicked.connect(self.bcg_plot_param_vary)
        self.BCG_analyze_popup.centralWidget().layout().addWidget(q_run_param_vary_heatmap_pushbutton, i + 4, 0, 1, 1)
        self.BCG_analyze_popup.show()

    def bcg_configure_plot_param_vary(self):
        '''
        '''
        param_vary_path = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version, self.telescope, self.camera, 'paramVary')
        ########## param panel
        if hasattr(self, 'analyze_param_vary_panel'):
            self.analyze_param_vary_panel.setParent(None)
            delattr(self, 'analyze_param_vary_panel')
        q_run_param_panel = QtWidgets.QWidget()
        q_run_param_panel.setLayout(QtWidgets.QGridLayout())
        setattr(self, 'analyze_param_vary_panel', q_run_param_panel)
        self.BCG_analyze_popup.centralWidget().layout().addWidget(q_run_param_panel, 0, 1, len(os.listdir(param_vary_path)), 1)
        experiment_dir = os.path.join(self.bolo_calc_install_dir, 'Experiments', self.experiment, self.version)
        vary_name = self.sender().currentText()
        self.unpack.vary_inputs = {}
        self.unpack.vary_outputs = {}
        self.unpack.unpack_parameter_vary(experiment_dir, vary_name)
        self.vary_heatmap_pushubtton.setDisabled(False)
        self.vary_violin_pushubtton.setDisabled(False)
        self.vary_scatter_pushubtton.setDisabled(False)
        #self.unpack.vary_outputs[self.version][self.telescope][self.camera]['Summary']
        for i, swept_parameter in enumerate(self.unpack.vary_inputs[self.version][self.telescope][self.camera].keys()):
            q_swept_parameter_checkbox = QtWidgets.QCheckBox(swept_parameter)
            q_swept_parameter_checkbox.setChecked(True)
            setattr(self, '{0}_checkbox'.format(swept_parameter), q_swept_parameter_checkbox)
            self.BCG_analyze_popup.centralWidget().layout().addWidget(q_swept_parameter_checkbox, i + 1, 1, 1, 1)
        for i, swept_channel in enumerate(self.unpack.vary_outputs[self.version][self.telescope][self.camera]['Summary'].keys()):
            q_swept_channel_checkbox = QtWidgets.QCheckBox(swept_channel)
            setattr(self, '{0}_checkbox'.format(swept_channel), q_swept_channel_checkbox)
            self.BCG_analyze_popup.centralWidget().layout().addWidget(q_swept_channel_checkbox, i + 1, 2, 1, 1)
            if i == 1:
                q_swept_channel_checkbox.setChecked(True)
            if i == 0:
                for j, swept_result in enumerate(self.unpack.vary_outputs[self.version][self.telescope][self.camera]['Summary'][swept_channel].keys()):
                    q_swept_result_checkbox = QtWidgets.QCheckBox(swept_result)
                    if j == 0:
                        q_swept_result_checkbox.setChecked(True)
                    setattr(self, '{0}_checkbox'.format(swept_result), q_swept_result_checkbox)
                    self.BCG_analyze_popup.centralWidget().layout().addWidget(q_swept_result_checkbox, j + 1, 3, 1, 1)

    def bcg_plot_param_vary(self):
        '''
        '''
        input_vector_dict = {}
        swept_parameters = []
        for i, swept_parameter in enumerate(self.unpack.vary_inputs[self.version][self.telescope][self.camera].keys()):
            if getattr(self, '{0}_checkbox'.format(swept_parameter)).isChecked():
                input_vector_dict[swept_parameter] = np.unique(self.unpack.vary_inputs[self.version][self.telescope][self.camera][swept_parameter])
                swept_parameters.append(swept_parameter)
        output_vector_dict = {}
        for i, swept_channel in enumerate(self.unpack.vary_outputs[self.version][self.telescope][self.camera]['Summary'].keys()):
            if getattr(self, '{0}_checkbox'.format(swept_channel)).isChecked():
                for j, swept_result in enumerate(self.unpack.vary_outputs[self.version][self.telescope][self.camera]['Summary'][swept_channel].keys()):
                    if getattr(self, '{0}_checkbox'.format(swept_result)).isChecked():
                        size_1 = len(input_vector_dict[swept_parameters[0]])
                        size_2 = len(input_vector_dict[swept_parameters[1]])
                        swept_result_vector = self.unpack.vary_outputs[self.version][self.telescope][self.camera]['Summary'][swept_channel][swept_result]
                        shaped_swept_result_vector = np.reshape(swept_result_vector, (size_1, size_2, -1))
                        output_vector_dict['{0}{1}'.format(swept_channel, swept_result)] = swept_result_vector
                        output_vector_dict['{0}{1}_shaped'.format(swept_channel, swept_result)] = shaped_swept_result_vector
                        active_swept_channel = swept_channel
                        active_swept_result = swept_result
        # Overplot the median and spreads as shaded regions
        if self.sender().text() == 'Param Vary Scatter Plot':
            self.bcg_make_param_vary_scatter_plot(input_vector_dict, output_vector_dict, active_swept_channel, active_swept_result, swept_parameters)
        if self.sender().text() == 'Param Vary Violin Plot':
            self.bcg_make_param_vary_scatter_plot(input_vector_dict, output_vector_dict, active_swept_channel, active_swept_result, swept_parameters)
        if self.sender().text() == 'Param Vary Heat Map Plot':
            self.bcg_make_param_vary_heat_map_plot(input_vector_dict, output_vector_dict, active_swept_channel, active_swept_result, swept_parameters)

    #################################################
    # ################# Table and Plot Creator
    #################################################

    def bcg_create_sensitivity_table(self, sensitivity_dict, is_camera=False):
        '''
        '''
        param_row = ['Channel'] + [self.label_dict[k]
                                   for k in list(sensitivity_dict[
                                       list(sensitivity_dict.keys())[0]].keys())]
        unit_row = ['Units'] + [self.unit_dict[k]
                                for k in list(sensitivity_dict[
                                    list(sensitivity_dict.keys())[0]].keys())]
        header_sep = ['---'] * len(param_row)
        column_width = 11.0 / len(param_row)
        latex_table_format = '{' + ' '.join(['m{%sin}' % column_width] * len(param_row)) + '}'
        # Labels for the data rows, which should be the channel names and "Total"
        if is_camera:
            ch_labs = [[lab for lab in list(sensitivity_dict.keys())][:-1]]
            data_rows = np.concatenate([
                np.transpose(ch_labs),
                [[self.bcg_convert_spread(v[k])
                  for k in list(v.keys())]
                  for v in list(sensitivity_dict.values())[:-1]]], axis=-1).tolist()
        else:
            ch_labs = [[lab for lab in list(sensitivity_dict.keys())]]
            data_rows = np.concatenate([
                np.transpose(ch_labs),
                [[self.bcg_convert_spread(v[k])
                  for k in list(v.keys())]
                  for v in list(sensitivity_dict.values())]], axis=-1).tolist()
        # Data to populate the rows
        # Generate table string
        header_rows = [param_row, unit_row]
        table_rows = data_rows
        table_str = ""
        with open('temp.tex', 'w') as tex_handle:
            if is_camera:
                tex_handle.write('\\documentclass[9pt]{article}\n')
            else:
                tex_handle.write('\\documentclass[12pt]{article}\n')
            tex_handle.write('\\usepackage[landscape]{geometry}\n')
            tex_handle.write('\\usepackage[table]{xcolor}\n')
            tex_handle.write('\\newcolumntype{C}[1]{>{\centering\let\\newline\\\\\\arraybackslash\hspace{0pt}}m{\#1in}}\n')
            tex_handle.write('\\begin{document}\n')
            tex_handle.write('\\pdfpagewidth 50in\n')
            tex_handle.write('\\pdfpageheight 25in\n')
            tex_handle.write('\\thispagestyle{empty}\n')
            tex_handle.write('\\rowcolors{0}{gray!25}{white}\n')
            tex_handle.write('\\begin{tabular}' + latex_table_format + '\n')
            for row in header_rows:
                row_str = '& '.join(row)+'\\\\\n'
                tex_handle.write(row_str)
                tex_handle.write('\\hline\n')
                table_str += '\\hline\n'
                tex_handle.write('\\hline\n')
                table_str += '\\hline\n'
                table_str += row_str
            for row in data_rows:
                row_str = '  &  '.join(row)+'\\\\\n'
                row_str = row_str.replace('_', '\\_')
                row_str = row_str.replace('+/-', '\\newline$\pm$\\newline')
                tex_handle.write(row_str)
                table_str += row_str
            tex_handle.write('\\end{tabular}\n')
            tex_handle.write('\\end{document}\n')
        q_process = QtCore.QProcess()
        q_process.execute('pdflatex temp.tex')
        q_process.execute('pdf-crop-margins temp.pdf -p 0 -o temp_cropped.pdf')
        image = convert_from_path('temp_cropped.pdf')[0]
        image.save('temp.png')
        save_dialog = self.gb_save_dialog(image_path='temp.png', add_caption_box=False)
        response = save_dialog.exec_()
        if response == 1:
            save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Location', '.', "Image files (*.png *.jpg *.gif)")[0]
            shutil.move('temp.png', save_path)

    def bcg_convert_spread(self, spread_list):
        '''
        '''
        mean, lo, hi = spread_list
        if (float(lo) == 0) and (float(hi) == 0):
            spread_str = "%g" % (mean)
        else:
            spread_str = "%g +/- (%g, %g)" % (mean, hi, lo)
        return spread_str

    def bcg_make_param_vary_heat_map_plot(self, input_vector_dict, output_vector_dict, active_swept_channel, active_swept_result, swept_parameters):
        '''
        '''
        plt.close('all')
        fig = pl.figure()
        ax = fig.add_subplot(111)
        active_key = '{0}{1}'.format(active_swept_channel, active_swept_result)
        x, y = input_vector_dict[swept_parameters[0]], input_vector_dict[swept_parameters[1]]
        X, Y = np.meshgrid(x, y)
        Z1 = output_vector_dict['{0}_shaped'.format(active_key)]
        Z2 = output_vector_dict['{0}'.format(active_key)]
        contour_Z_mean = np.zeros((len(x), len(y)))
        contour_Z_lo = np.zeros((len(x), len(y)))
        contour_Z_hi = np.zeros((len(x), len(y)))
        for i, x_val in enumerate(input_vector_dict[swept_parameters[0]]):
            for j, y_val in enumerate(input_vector_dict[swept_parameters[1]]):
                contour_Z_mean[i][j] = Z1[j][i][0]
                contour_Z_lo[i][j] = Z1[j][i][1]
                contour_Z_hi[i][j] = Z1[j][i][2]
        cntr1 = ax.contourf(X, Y, contour_Z_mean)
        fig.colorbar(cntr1, ax=ax)
        ax.set_title('{0} {1}'.format(active_swept_result, self.unit_dict[active_swept_result]))
        ax.set_xlabel('{0} {1}'.format(swept_parameters[0], self.unit_dict[swept_parameters[0].replace(active_swept_channel + '_', '')]))
        ax.set_ylabel('{0} {1}'.format(swept_parameters[1], self.unit_dict[swept_parameters[1].replace(active_swept_channel + '_', '')]))
        plt.show(fig)

    def bcg_make_pdf_band_plot(self, x, y, errs, path, close=False):
        '''
        '''
        # Determine whether this is a distribution or a band
        path_items = path.split(os.sep)
        if "DIST" in [p.upper() for p in path_items]:
            plot_type = 'PDF'
        elif "BANDS" in [p.upper() for p in path_items]:
            plot_type = 'BAND'
        else:
            # I can't plot this...
            return
        # Generate a dictionary of display names
        def_files = glob.glob(os.path.join(os.path.dirname(__file__), '..', 'param_definitions', '*_paramDefs.json'))
        param_name_dict = {}
        for f in def_files:
            d = json.load(open(f, 'r'))
            for k, v in d.items():
                param_name_dict.update({k.replace(' ', '').upper(): v['name']})
        # Generate figure
        plt.close('all')
        fig = plt.figure(figsize=(8,8))
        sns.set(font_scale=1.5, style='whitegrid', font='serif')
        lw = 2
        ms = 8
        bot = -0.02
        # Plot a PDF
        if plot_type == "PDF":
            # Normalize the probabilities
            y = y / np.sum(y)
            # Plot the data
            plt.vlines(x, np.zeros(len(x)), y, linewidth=lw, linestyle='-', color='b')
            plt.plot(x, y, linewidth=0, marker='o', markersize=ms, color='b')
            # Generate the x label
            # If a detector, then label the band
            if path_items[-2].upper() == 'DETECTORS':
                fname = path_items[-1].split('.')[0]
                param, band_id = fname.split('_')
                param_name = param_name_dict[param.upper()]
                xlabel = "%s (Band ID: %s)" % (param_name, band_id)
            # If an optic, then label it and the band
            elif path_items[-2].upper() == 'OPTICS':
                fname = path_items[-1].split('.')[0]
                labs = fname.split('_')
                if len(labs) == 2:
                    optic, param = labs
                    param_name = param_name_dict[param.upper()]
                    xlabel = "%s %s" % (optic, param_name)
                elif len(labs) == 3:
                    optic, param, band_id = labs
                    param_name = param_name_dict[param.upper()]
                    xlabel = "%s %s (Band ID: %s)" % (optic, param_name, band_id)
                else:
                    # Something went wrong
                    return
            # If any other parameter, just label it
            else:
                param = path_items[-1].split('.')[0]
                param_name = param_name_dict[param.upper()]
                xlabel = "%s" % (param_name)
            plt.xlabel(xlabel)
            plt.ylabel("Probability")
            plt.ylim(bottom=bot)
        # Plot a BAND
        elif plot_type == "BAND":
            fig, ax1 = plt.subplots(1,1)
            fig.set_figwidth(8)
            fig.set_figheight(8)
            ax2 = ax1.twinx()
            ax2.grid(False)
            yticks = np.linspace(0, 1, 6)
            # Generate the labels
            # If a detector, then label the band
            if path_items[-2].upper() == 'DETECTORS':
                fname = path_items[-1].split('.')[0]
                band_id = fname.split('_')[-1]
                label = "Detector (Band ID: %s)" % (band_id)
                ylabel = "Efficiency"
                # Plot the atmosphere data
                atm_freq, atm_tran, atm_temp = self.bcg_get_atm_model(live=False)
                if not np.all(atm_tran == 0):
                    ax1.plot(atm_freq, atm_tran, label="Atmosphere", linewidth=lw)
            # If an optic, then label it and the band
            elif path_items[-2].upper() == 'OPTICS':
                # Overplot the band passes
                band_pass_dict = self.bcg_get_band_passes()
                x_plotted = []
                for band_name, data in band_pass_dict.items():
                    x_band = data[0]
                    y1 = np.zeros(len(x_band))
                    y2 = data[1]
                    ax2.fill_between(x_band, y1, y2, label=band_name, alpha=0.3)
                    x_plotted += np.array(x).tolist()
                if len(x_plotted) > 0:
                    xlo = np.amin(x_plotted) - 10
                    if xlo < 0:
                        xlo = 0
                    xhi = np.amax(x_plotted) + 10
                    ax2.set_xlim(xlo, xhi)
                ax2.set_ylabel("Channel Efficiency", rotation=270, labelpad=25)
                ax2.set_yticks(yticks)
                # Generate the optics label
                fname = path_items[-1].split('.')[0]
                optic, param = fname.split('_')
                param_name = param_name_dict[param.upper()]
                label = "%s" % (optic)
                ylabel = "%s" % (param_name)
            # Plot the band data
            if errs is not None:
                ax1.errorbar(x, y, yerr=errs, linewidth=lw,
                             marker='o', markersize=ms, label=label)
            else:
                ax1.plot(x, y, linewidth=4, label=label)
            # Set the y limits
            ymax = ((np.amax(y) * 10) // 1 + 1) / 10
            if ymax > 1:
                ymax = 1
            ax1.set_yticks(np.linspace(0, ymax, 6))
            ax1.set_xlabel("Frequency [GHz]")
            ax1.set_ylabel(ylabel)
            ax1.legend(loc='upper left')
            ax2.legend(loc='upper right')
        # Otherwise, nothing to plot
        else:
            return
        plt.show(fig)
        if close:
            plt.close()
        return

    def bcg_make_param_vary_scatter_plot(self, input_vector_dict, output_vector_dict, active_swept_channel, active_swept_result, swept_parameters):
        '''
        '''
        plt.close('all')
        active_key = '{0}{1}'.format(active_swept_channel, active_swept_result)
        for i, psat in enumerate(input_vector_dict[swept_parameters[0]]):
            xarr = input_vector_dict[swept_parameters[1]]
            #import ipdb;ipdb.set_trace()
            med, hi, lo = output_vector_dict['{0}_shaped'.format(active_key)][i].T
            p1 = plt.plot(xarr, med, linewidth=4, linestyle='-',
                          label="%d" % (psat))
            plt.fill_between(xarr, med-lo, med+hi,
                             color=p1[0].get_color(), linewidth=0, alpha=0.2)
        plt.xlabel(swept_parameters[0])
        plt.ylabel('{0} {1}'.format(active_swept_result, self.unit_dict[active_swept_result]))
        #plt.ylim(top=2000, bottom=0)
        leg = plt.legend(title='{0} {1}'.format(swept_parameters[0], self.unit_dict[swept_parameters[0].replace(active_swept_channel + '_', '')]))
        plt.setp(leg.get_title(), fontsize=26)

    def bcg_pdf_median(self, val, prob):
        # Sort the arrays by increasing value
        args_sorted = np.argsort(val)
        val = val[args_sorted]
        prob = prob[args_sorted]
        # Eliminate negative probabilities
        prob = np.array([0 if p < 0 else p for p in prob])
        # Normalize the probabilities
        if np.any(prob > 0):
            prob = prob / np.sum(prob)
        else:
            return None
        # Find the median value
        cum_prob = np.cumsum(prob)
        median_args = np.argwhere(cum_prob >= 0.5)
        median = val[median_args][0][0]
        return median

    def bcg_load_pdf_median(self, param_name, panel_name):
        for extension in ['txt', 'csv']:
            pdf_path = self.bcg_load_pdf_file(
                parameter=param_name, panel=panel_name, 
                get_names_from_widget=False)
            pdf_path = '{0}.{1}'.format(pdf_path, extension)
            if os.path.exists(pdf_path):
                data = np.loadtxt(pdf_path)
                median = self.bcg_pdf_median(data.T[0], data.T[1])
                if median is None:
                    return None
                else:
                    return median

    def bcg_get_atm(self, site, pwv, elev):
        # Load site
        atm_file = os.path.join(self.bolo_calc_install_dir, "src", "atm.hdf5")
        site = site.strip().lower().capitalize()
        if pwv == 'PDF' or pwv[0] == 'PDF':
            pwv_median = self.bcg_load_pdf_median('pwv', 'telescope')
            pwv = np.round(pwv_median, 1)
        else:
            pwv = np.round(float(pwv[0].strip()), 1)
        # Baloons don't care about PWV
        if site == "Mcmurdo":
            site = "McMurdo"
            pwv = 0
        # Convert pwv to um
        pwv = pwv * 1e3
        # Load elevation
        if elev == 'PDF' or elev[0] == 'PDF':
            elev_median = self.bcg_load_pdf_median('elevation', 'telescope')
            elev = np.round(elev_median, 0)
        else:
            elev = np.round(float(elev[0]), 0)
        if site in ("Space", "CUST", "Room"):
            freq = np.asarray([])
            temp = np.asarray([])
            tran = np.asarray([])
        else:
            # Load the atmospheric profile
            key = "%d,%d" % (pwv, elev)
            with hp.File(atm_file, "r") as hf:
                data = hf[site][key]
                freq = data[0]
                temp = data[2]
                tran = data[3]
        return (freq, tran, temp)

    def bcg_get_atm_model(self, live=True):
        '''
        '''
        # Load site, PWV, and elevation from window
        if live:
            site = getattr(self, self.site_button_name).text()
        else:
            site = self.telescope_dataframe.loc[
                self.telescope_dataframe['Parameter'] == 'Site', 'Value'].iloc[0]
        sky_temp = self.telescope_dataframe.loc[
                self.telescope_dataframe['Parameter'] == 'Sky Temperature', 'Value'].iloc[0]
        if sky_temp == 'NA':
            pwv = self.telescope_dataframe.loc[
                self.telescope_dataframe['Parameter'] == 'PWV', 'Value'].iloc[0]
            elev = self.telescope_dataframe.loc[
                self.telescope_dataframe['Parameter'] == 'Elevation', 'Value'].iloc[0]
            freq, tran, temp = self.bcg_get_atm(site, pwv, elev)
        else:
            if sky_temp == 'PDF':
                sky_temp = float(self.bcg_load_pdf_median('Sky Temperature', 'telescope'))
            else:
                sky_temp = float(sky_temp[0])
            freq = np.linspace(1, 600, 601) # GHz
            tran = np.zeros(len(freq))
            temp = np.ones(len(freq)) * sky_temp
            
        return (freq, tran, temp)

    def bcg_get_live_foreground_model(self):
        '''
        '''
        # Load the foreground parameters
        params = [self.foregrounds_dataframe.loc[i, 'Value'] for i in range(1, 8)]
        param_names = [
            'Dust Temperature', 'Dust Spec Index', 'Dust Amplitude', 'Dust Scale Frequency',
            'Synchrotron Spec Index', 'Synchrotron Amplitude', 'Sync Scale Frequency']
        # Load the median values
        medians = []
        for param, name in zip(params, param_names):
            if param == 'PDF' or param[0] == 'PDF':
                median = float(self.bcg_load_pdf_median(name, 'foregrounds'))
            else:
                if isinstance(param, list):
                    median = float(param[0])
                else:
                    median = float(param)
            medians.append(median)
        # Label the parameters
        dust_temp = medians[0]
        dust_index = medians[1]
        dust_amp = medians[2]
        dust_freq = medians[3]
        sync_index = medians[4]
        sync_amp = medians[5]
        sync_freq = medians[6]
        # Generate foreground spectra
        freq = np.linspace(1, 600, 600)
        dust_spec = self.bcg_dust_spectrum(
            freq, dust_amp, dust_temp, dust_freq, dust_index)
        sync_spec = self.bcg_sync_spectrum(
            freq, sync_amp, sync_freq, sync_index)
        cmb_spec = self.bcg_cmb_spectrum(freq)
        return (freq, dust_spec, sync_spec, cmb_spec)

    def bcg_dust_spectrum(self, freq, Adust, Tdust, fdust, ndust):
        h = 6.6e-34
        kB = 1.4e-23
        c = 3e8
        freq = freq * 1e9
        fdust = fdust * 1e9
        planck_spec = lambda nu, T: (h * nu) / (np.exp((h * nu) / (kB * Tdust)) - 1)
        planck_frac = planck_spec(freq, Tdust) / planck_spec(fdust, Tdust)
        dust_spec = (
            (Adust / 2) * (c / freq)**2 * (freq / fdust)**ndust * planck_frac * 1e-20)
        return dust_spec

    def bcg_sync_spectrum(self, freq, Tsync, fsync, nsync):
        kB = 1.4e-23
        sync_spec = (kB * Tsync / 2) * (freq / fsync)**nsync
        return sync_spec

    def bcg_cmb_spectrum(self, freq):
        h = 6.6e-34
        kB = 1.4e-23
        Tcmb = 2.725
        freq = freq * 1e9
        cmb_spec = (
            (h * freq) / (np.exp((h * freq) / (kB * Tcmb)) - 1))
        return cmb_spec

    def bcg_plot_foreground_model(self, freq=[], dust_spec=[], sync_spec=[], cmb_spec=[], band_pass_dict=None, show=False):
        sns.set(font_scale=2, style='whitegrid', font='serif')
        if hasattr(self.sender(), 'text') and 'Matplotlib' in self.sender().text():
            show = True
            freq, dust_spec, sync_spec, cmb_spec = self.bcg_get_live_foreground_model()
            band_pass_dict = self.bcg_get_band_passes()
            plt.close('all')
        fig = pl.figure(figsize=(12, 8))
        # Plot the spectra
        pl.plot(freq, dust_spec, label="Dust", linewidth=4, linestyle='-')
        pl.plot(freq, sync_spec, label="Synch", linewidth=4, linestyle='--')
        pl.plot(freq, cmb_spec, label="CMB", linewidth=4, linestyle=':')
        # Plot the bands
        x_plotted = []
        labeled_band = False
        if band_pass_dict is not None:
            for data in band_pass_dict.values():
                x = data[0]
                y = data[1]
                ymax = np.amax(y)
                ymax_loc = np.argwhere(y == ymax).flatten()
                if len(ymax_loc) > 1:
                    max_loc = len(ymax_loc)//2 + len(ymax_loc)%2
                    ymax_loc = ymax_loc[max_loc]
                else:
                    ymax_loc = ymax_loc[0]
                lo_point = np.argmin(
                    abs(y[:ymax_loc] - 0.5 * ymax))
                hi_point = np.argmin(
                    abs(y[ymax_loc:] - 0.5 * ymax)) + ymax_loc
                xlo = x[lo_point]
                xhi = x[hi_point]
                if labeled_band:
                    pl.axvspan(xlo, xhi, alpha=0.3)
                else:
                    pl.axvspan(xlo, xhi, label="Channels", alpha=0.3)
                    labeled_band = True
                x_plotted += [xlo, xhi]
            x_plotted += np.array(x).tolist()
            if len(x_plotted) > 0:
                xlo = np.amin(x_plotted) - 10
                if xlo < 0:
                    xlo = 0
                xhi = np.amax(x_plotted) + 10
                plt.xlim(xlo, xhi)
        pl.xlabel("Frequency [GHz]")
        pl.ylabel("Power Spectrum ($A \Omega = \lambda^{2}$) [W / Hz]")
        pl.yscale("log")
        pl.legend()
        if show:
            plt.show(fig)
        return fig

    def bcg_plot_atm_model(self, freq=[], tran=[], temp=[], band_pass_dict=None, show=False):
        '''
        '''
        sns.set(font_scale=2, style='whitegrid', font='serif')
        if hasattr(self.sender(), 'text') and 'Matplotlib' in self.sender().text():
            show = True
            freq, tran, temp = self.bcg_get_atm_model()
            band_pass_dict = self.bcg_get_band_passes()
            plt.close('all')
        fig, ax1 = pl.subplots(1, 1)
        fig.set_figwidth(12)
        fig.set_figheight(10)
        # First plot the sky temperature
        ax1.plot(freq, temp, linewidth=4)
        # If a flat temperature, then no CMB
        if np.all(np.diff(temp) == 0):
            ylab = "Sky brightness temperature"
        else:
            ylab = "ATM brightness temperature"
        max_temp = np.amax(temp)
        # Set the y range
        if max_temp <= 30:
            ymax = 30
        else:
            ymax = (int(max_temp) // 5 + 1) * 5
        ax1.set_ylim(0, ymax)
        ax1.set_yticks(np.linspace(0, ymax, 6))
        ax1.set_ylabel(ylab)
        # Then plot the bands
        ax2 = ax1.twinx()
        ax2.grid(False)
        x_plotted = []
        if band_pass_dict is not None:
            for band_name, data in band_pass_dict.items():
                x = data[0]
                y1 = np.zeros(len(x))
                y2 = data[1]
                ax2.fill_between(x, y1, y2, label=band_name, alpha=0.3)
                x_plotted += np.array(x).tolist()
            if len(x_plotted) > 0:
                xlo = np.amin(x_plotted) - 10
                if xlo < 0:
                    xlo = 0
                xhi = np.amax(x_plotted) + 10
                ax2.set_xlim(xlo, xhi)
        ax2.set_ylim(0, 1)
        ax2.set_yticks(np.linspace(0, 1, 6))
        ax2.set_xlabel("Frequency [GHz]")
        ax2.set_ylabel("Channel efficiency", rotation=270, labelpad=30)
        ax2.legend()
        if show:
            pl.show(fig)
        return fig

    def bcg_show_atm_model_in_bcg(self):
        '''
        '''
        # Get atmosphere profile
        atm_freq, atm_tran, atm_temp = self.bcg_get_atm_model()
        # Get band passes
        band_pass_dict = self.bcg_get_band_passes()
        # Generate the atmosphere figure
        plt.close('all')
        fig = self.bcg_plot_atm_model(atm_freq, atm_tran, atm_temp, band_pass_dict)
        # Display the plot
        fig.savefig('temp.png')
        q_pixmap = QtGui.QPixmap('temp.png')
        q_pixmap = q_pixmap.scaled(0.4 * self.screen_resolution.width(), 0.4 * self.screen_resolution.width(), QtCore.Qt.KeepAspectRatio)
        getattr(self, '_cw_main_parameters_panel_row_0_col_8_{0}_special_plot_label'.format(self.panel)).setPixmap(q_pixmap)
        os.remove('temp.png')

    def bcg_show_foreground_model_in_bcg(self):
        '''
        '''
        # Get the foreground spectra
        freq, dust_spec, sync_spec, cmb_spec = self.bcg_get_live_foreground_model()
        # Get the bands for this experiment
        band_pass_dict = self.bcg_get_band_passes()
        # Generate the foreground figure
        plt.close('all')
        fig = self.bcg_plot_foreground_model(freq, dust_spec, sync_spec, cmb_spec, band_pass_dict)
        # Display the plot
        fig.savefig('temp.png')
        unique_widget_name = '_cw_main_parameters_panel_row_0_col_8_header_{0}_label'.format(self.panel)
        #temp_png = os.path.join('gui_settings', 'SO_site.jpeg')
        #test_pixmap = QtGui.QPixmap(temp_png)
        q_pixmap = QtGui.QPixmap('temp.png')
        q_pixmap = q_pixmap.scaled(0.4 * self.screen_resolution.width(), 0.4 * self.screen_resolution.width(), QtCore.Qt.KeepAspectRatio)
        getattr(self, '_cw_main_parameters_panel_row_0_col_8_{0}_special_plot_label'.format(self.panel)).setPixmap(q_pixmap)
        self.repaint()
        os.remove('temp.png')

    #################################################
    # Feedback
    #################################################

    def bcg_gather_feedback(self):
        '''
        '''
        feedback_gather = self.gb_large_text_gather()
        feedback_gather.showMaximized()
        response = feedback_gather.exec_()
        if response:
            self.bcg_upload_feedback_to_drive()

    def bcg_upload_feedback_to_drive(self):
        '''
        '''
        feedback_str = str(self.large_text_gather_textedit.toPlainText())
        now = datetime.datetime.now()
        now_str = datetime.datetime.strftime(now, '%Y_%m_%d_%H_%M_%S')
        save_name = 'feed_back_{0}.txt'.format(now_str)
        with open(save_name, 'w') as feedback_handle:
            feedback_handle.write(feedback_str)
        self.google_drive.upload_file(save_name, wafer='New_BCG_Tickets', tool=None, fab_step=None,
                                      upload_for_dies=False, duplicate_action=0,
                                      infolder=True, is_image=False, wafer_type='BCG_Feedback',
                                      status_bar=self.status_bar)
        os.remove(save_name)

    #################################################
    # Remove Glyphs from SVG
    #################################################

    def convertSVG(self, file):
        dom = self._getsvgdom(file)
        self._switchGlyphsForPaths(dom)
        self._commitSVG(file, dom)

    def _commitSVG(self, file, dom):
        f = open(file, 'w')
        dom.writexml(f)
        f.close()

    def _getsvgdom(self, file):
        #print('getting DOM model')
        import xml.dom
        import xml.dom.minidom as mini
        f = open(file, 'r')
        svg = f.read()
        f.close()
        dom = mini.parseString(svg)
        return dom

    def _getGlyphPaths(self, dom):
        symbols = dom.getElementsByTagName('symbol')
        glyphPaths = {}
        for s in symbols:
            pathNode = [p for p in s.childNodes if 'tagName' in dir(p) and p.tagName == 'path']
            glyphPaths[s.getAttribute('id')] = pathNode[0].getAttribute('d')
        return glyphPaths

    def _switchGlyphsForPaths(self, dom):
        glyphs = self._getGlyphPaths(dom)
        use = self._getUseTags(dom)
        for glyph in glyphs.keys():
            nl = self.makeNewList(glyphs[glyph].split(' '))
            u = self._matchUseGlyphs(use, glyph)
            for u2 in u:
                self._convertUseToPath(u2, nl)

    def _getUseTags(self, dom):
        return dom.getElementsByTagName('use')

    def _matchUseGlyphs(self, use, glyph):
        matches = []
        for i in use:
            if i.getAttribute('xlink:href') == '#'+glyph:
                matches.append(i)
        return matches

    def _convertUseToPath(self, use, strokeD):
        # Extract the color for this glyph
        style = use.parentNode.getAttribute('style')
        color = '(' + str(style.split('(')[-1].split(')')[0]) + ')'
        ## strokeD is a list of lists of strokes to make the glyph
        newD = self.nltostring(self.resetStrokeD(strokeD, use.getAttribute('x'), use.getAttribute('y')))
        use.tagName = 'path'
        use.removeAttribute('xlink:href')
        use.removeAttribute('x')
        use.removeAttribute('y')
        use.setAttribute('style',
                         'fill: rgb%s; stroke-width: 0.5; stroke-linecap: round; stroke-linejoin: round; '
                         'stroke: rgb%s; stroke-opacity: 1;stroke-miterlimit: 10; '
                         'background-color: white;' % (color, color))
        use.setAttribute('d', newD)

    def makeNewList(self, inList):
        i = 0
        nt = []
        while i < len(inList):
            start = i + self.listFind(inList[i:], ['M', 'L', 'C', 'Z'])
            end = start + self.listFind(inList[start+1:], ['M', 'L', 'C', 'Z', '', ' '])
            nt.append(inList[start:end+1])
            i = end + 1
        return nt

    def listFind(self, x, query):
        for i in range(len(x)):
            if x[i] in query:
                return i
        return len(x)

    def resetStrokeD(self, strokeD, x, y):
        nsd = []
        for i in strokeD:
            nsd.append(self.resetXY(i, x, y))
        return nsd

    def resetXY(self, nl, x, y): # convert a list of strokes to xy coords 
        nl2 = []
        for i in range(len(nl)):
            if i == 0:
                nl2.append(nl[i])
            elif i%2: # it's odd 
                nl2.append(float(nl[i]) + float(x))
            elif not i%2: # it's even 
                nl2.append(float(nl[i]) + float(y))
            else:
                print(i, nl[i], 'error')
        return nl2

    def nltostring(self, nl): # convert a colection of nl's to a string 
        col = []
        for l in nl:
            templ = []
            for c in l:
                templ.append(str(c))
            templ = ' '.join(templ)
            col.append(templ)
        return ' '.join(col)

if __name__ == '__main__':
    styles = ['QtCurve', 'Oxygen',  'Breeze', 'Windows', 'WindowsXP', 'WindowsVista', 'Fusion']
    styles = ['QtCurve', 'Oxygen',  'Breeze', 'Windows', 'WindowsXP', 'WindowsVista', 'Fusion', 'Plastique']
    style = styles[-2]
    qt_app = QtWidgets.QApplication([])
    display_style = Qt.QStyleFactory.create('{0}'.format(style))
    qt_app.setStyle(display_style)
    screen_resolution = qt_app.desktop().screenGeometry()
    gui = BoloCalcGui(screen_resolution, qt_app)
    gui.show()
    exit(qt_app.exec_())
