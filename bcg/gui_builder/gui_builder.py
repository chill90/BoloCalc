import os
import datetime
import simplejson
import numpy as np
from copy import copy
from PyQt5 import QtGui, QtCore, QtWidgets, QtSvg

class GuiBuilder():

    def __init__(self):
        super(GuiBuilder, self).__init__()
        self.widget_to_object_dict = {
            'checkbox': 'QCheckBox',
            'dial': 'QDial',
            'combobox': 'QComboBox',
            'imageviewer': 'QGraphicsView',
            'lineedit': 'QLineEdit',
            'label': 'QLabel',
            'panel': 'QWidget',
            'pixmap': 'QPixmap',
            'popup': 'QWidget',
            'pushbutton': 'QPushButton',
            'slider': 'QSlider',
            'textedit': 'QTextEdit',
            'toolbutton': 'QToolButton',
            'widget': 'QWidget',
        }
        self.tiny = QtGui.QFont("Times", 6)
        self.small_font = QtGui.QFont("Times", 8)
        self.med_font = QtGui.QFont("Times", 10)
        self.large_font = QtGui.QFont("Times", 14)
        self.larger_font = QtGui.QFont("Times", 16)
        self.huge_font = QtGui.QFont("Times", 24)
        self.giant_font = QtGui.QFont("Times", 32)
        for i in range(6, 128):
            setattr(self, 'size_{0}_font'.format(i), QtGui.QFont("Times", i))

    ##########################Generic Functions#####################################
    ################################################################################

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    def gb_dummy(self):
        return True

    def gb_get_now_str(self, time_format='%H:%M:%s'):
        now = datetime.datetime.now()
        now_str = datetime.datetime.strftime(now, time_format)
        return now_str

    def gb_is_float(self, str_):
        try:
            float(str_)
            return True
        except ValueError:
            return False

    def gb_initialize_panel(self, panel=None, exceptions=[]):
        if panel == 'self':
            panel = self
        else:
            panel = getattr(self, panel)
        for index in reversed(range(panel.layout().count())):
            widget = panel.layout().itemAt(index).widget()
            if widget.whatsThis() not in exceptions:
                widget.setParent(None)

    def gb_unpack_widget_function(self, function_text):
        if function_text is not None:
            if '.' in function_text:
                if len(function_text.split('.')) == 2:
                    base_function, attribute_function = function_text.split('.')
                    base_function = getattr(self, base_function)
                    widget_function = getattr(base_function, attribute_function)
            else:
                widget_function = getattr(self, function_text)
        else:
            widget_function = getattr(self, '_dummy')
        return widget_function

    def gb_get_image_size(self, image_name):
        '''
        '''
        q_process = QtCore.QProcess()
        get_image_size = q_process.execute('identify {0}'.format(image_name))
        identify_output = get_image_size.stdout.readlines()
        if 'PNG ' in str(identify_output[0]):
            identify_output = str(identify_output[0]).split('PNG ')[1]
        elif 'PDF ' in str(identify_output[0]):
            identify_output = str(identify_output[0]).split('PDF ')[1]
        image_size = identify_output.split(' ')[0].split('x')
        return image_size

    def gb_save_png_as_pdf(self, png_name):
        '''
        '''
        pdf_name = png_name.replace('png', 'pdf')
        if os.path.exists(pdf_name):
            os.remove(pdf_name)
        convert_command = 'convert -density 300 "{0}" -flatten -quality 90 "{1}"'.format(png_name, pdf_name)
        q_process = QtCore.QProcess()
        q_process.execute(convert_command)
        return pdf_name

    def gb_save_pdf_as_png(self, tex_name):
        '''
        '''
        if not 'tex' in tex_name:
            tex_name = '{0}.tex'.format(tex_name)
        pdf_name = tex_name.replace('tex', 'pdf')
        pdf_size = self.get_image_size(pdf_name)
        png_name = tex_name.replace('tex', 'png')
        if os.path.exists(png_name):
            os.remove(png_name)
        convert_command = 'convert -density 200  "{0}" -flatten -quality 80 "{1}"'.format(pdf_name, png_name)
        q_process = QtCore.QProcess()
        converted_image = q_process.execute(convert_command)
        image_size = self.get_image_size(png_name)
        return png_name, image_size
    ################################################################################

    ##########################Window Moving#########################################

    def gb_center_main_window(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

    def gb_move_window(self, center_window=True, widget=None):
        if widget is None:
            frame_geometry = self.frameGeometry()
        else:
            frame_geometry = widget.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        if center_window == True:
            center = frame_geometry.center()
        else:
            center = frame_geometry.topLeft()
        if widget is None:
            self.move(center)
        else:
            widget.move(center)
            return False

    ################################################################################

    ###########################Comboboxes###########################################

    def gb_get_all_widgets_from_self(self, filter_strings=[]):
        widgets = []
        for attribute in dir(self):
            if len(filter_strings) is 0:
                widget = getattr(self, attribute)
                if isinstance(widget, QtWidgets.QCheckBox):
                    widgets.append(attribute)
                    print(attribute)
                elif isinstance(widget, QtWidgets.QTextEdit):
                    widgets.append(attribute)
                    print(attribute)
                elif isinstance(widget, QtWidgets.QLineEdit):
                    widgets.append(attribute)
                    print(attribute)
                elif isinstance(widget, QtWidgets.QLabel):
                    widgets.append(attribute)
                    print(attribute)
                elif isinstance(widget, QtWidgets.QComboBox):
                    widgets.append(attribute)
                    print(attribute)
                elif isinstance(widget, QtWidgets.QPushButton):
                    widgets.append(attribute)
                    print(attribute)
                elif isinstance(widget, QtWidgets.QSlider):
                    widgets.append(attribute)
                    print(attribute)
            else:
                for filter_string in filter_strings:
                    if filter_string in attribute:
                        widgets.append(attribute)
        return widgets

    def gb_initialize_combobox(self, combobox_name):
        getattr(self, combobox_name).clear()

    def gb_populate_combobox(self, combobox_entry_dict):
        for unique_combobox_name, enteries in combobox_entry_dict.items():
            for entry in enteries:
                getattr(self, unique_combobox_name).addItem(entry)

    ################################################################################

    #######################Status, Menu, and Tool Bars##############################

    def gb_add_status_bar(self, permanant_messages=[], add_saved=False, custom_widgets=[]):
        self.status_bar = self.statusBar()
        for custom_widget in custom_widgets:
            self.status_bar.addPermanentWidget(custom_widget)
            setattr(self, custom_widget.whatsThis(), custom_widget)
        for permanant_message in permanant_messages:
            message_widget = QtWidgets.QLabel('', self)
            message_widget.setAlignment(QtCore.Qt.AlignBottom)
            message_widget.setText(permanant_message)
            self.status_bar.addPermanentWidget(message_widget)

    def gb_setup_menu_and_tool_bars(self, file_path):
        with open(file_path, 'r') as control_actions_handle:
            control_actions_dict = simplejson.load(control_actions_handle)
        with open(file_path, 'w') as control_actions_handle:
            simplejson.dump(control_actions_dict, control_actions_handle,
                            indent=4, sort_keys=True)
        self.main_menu = self.menuBar()
        for position, position_dict in reversed(sorted(control_actions_dict.items())):
            tool_bar_area = getattr(QtCore.Qt, '{0}ToolBarArea'.format(position))
            for menu, menu_dict in sorted(position_dict.items()):
                menu = menu.split('_')[-1]
                q_menu = self.main_menu.addMenu(menu)
                q_toolbar = QtWidgets.QToolBar(menu)
                q_toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
                self.addToolBar(tool_bar_area, q_toolbar)
                menu_attr_name = '_'.join(menu.split(' ')).lower()
                setattr(self, '{0}_qmw_tool_bar'.format(menu_attr_name), q_toolbar)
                setattr(self, '{0}_qmw_menu'.format(menu_attr_name), q_menu)
                for action, action_settings in menu_dict.items():
                    action = action.split('_')[-1]
                    q_action = QtWidgets.QAction(action, self)
                    q_action.setWhatsThis('action_{0}'.format(action))
                    setattr(self, 'action_{0}'.format(action), q_action)
                    if 'IconSize' in action_settings:
                        q_toolbar.setIconSize(QtCore.QSize(int(action_settings['IconSize']), int(action_settings['IconSize'])))
                    else:
                        q_toolbar.setIconSize(QtCore.QSize(self.icon_size, self.icon_size))
                    for action_attribute, action_attribute_value in action_settings.items():
                        if action_attribute == 'function':
                            q_action.triggered.connect(getattr(self, action_settings['function']))
                        elif action_attribute == 'icon':
                            icon_folder = os.path.join(os.path.dirname(__file__), 'icons')
                            if action_attribute_value in os.listdir(icon_folder):
                                icon_path = os.path.join(icon_folder, action_attribute_value)
                                q_icon = QtGui.QIcon(icon_path)
                                q_action.setIcon(q_icon)
                    if action == 'Quit':
                        q_quit_action = q_action
                        q_toolbar.addAction(q_quit_action)
                        q_toolbar.addSeparator()
                    else:
                        q_toolbar.addAction(q_action)
                        q_toolbar.addSeparator()
                        q_menu.addAction(q_action)
                if menu == 'File':
                    q_menu.addAction(q_quit_action)

    def gb_convert_icon(self, icon_path):
        return q_icon

    ################################################################################
    ##########################Popup Wrappers########################################
    ################################################################################

    def gb_quick_info_gather(self, title='', dialog=''):
        text, okPressed = QtWidgets.QInputDialog.getText(self, title, dialog, QtWidgets.QLineEdit.Normal, "")
        return str(text), okPressed

    def gb_quick_static_info_gather(self, title='', dialog='', items=[]):
        text, okPressed = QtWidgets.QInputDialog.getItem(self, title, dialog, items, editable=False)
        return str(text), okPressed

    def gb_quick_message(self,
                         msg='',
                         add_apply=False,
                         add_yes=False,
                         add_no=False,
                         add_save=False,
                         add_cancel=False,
                         add_discard=False,
                         add_yes_to_all=False,
                         msg_type=None):
        message_box = QtWidgets.QMessageBox(self)
        message_box.setText(msg)
        if add_save:
            save_button = QtWidgets.QMessageBox.Save
            message_box.addButton(save_button)
        if add_cancel:
            cancel_button = QtWidgets.QMessageBox.Cancel
            message_box.addButton(cancel_button)
        if add_yes:
            yes_button = QtWidgets.QMessageBox.Yes
            message_box.addButton(yes_button)
        if add_no:
            no_button = QtWidgets.QMessageBox.No
            message_box.addButton(no_button)
        if add_discard:
            discard_button = QtWidgets.QMessageBox.Discard
            message_box.addButton(discard_button)
        if add_apply:
            apply_button = QtWidgets.QMessageBox.Apply
            message_box.addButton(apply_button)
        if add_yes_to_all:
            yes_to_all_button = QtWidgets.QMessageBox.YesToAll
            message_box.addButton(yes_to_all_button)
        if msg_type == 'Question':
            message_box.setIcon(message_box.Question)
        if msg_type == 'Warning':
            message_box.setIcon(message_box.Warning)
        return message_box.exec_()

    def gb_scale_image_to_screen(self, q_pixmap, horizontal_screen_fraction=0.99, vertical_screen_fraction=0.8, expand_h=False, expand_v=False):
        if q_pixmap.width() > self.screen_resolution.width() or expand_h:
            q_pixmap = q_pixmap.scaled(int(horizontal_screen_fraction * self.screen_resolution.width()),
                                       int(vertical_screen_fraction * self.screen_resolution.height()),
                                       QtCore.Qt.KeepAspectRatio)
        if q_pixmap.height() > self.screen_resolution.height() or expand_v:
            q_pixmap = q_pixmap.scaled(int(horizontal_screen_fraction * self.screen_resolution.width()),
                                       int(vertical_screen_fraction * self.screen_resolution.height()),
                                       QtCore.Qt.KeepAspectRatio)
        return q_pixmap

    def gb_save_dialog(self, text='', image_path=None, add_caption_box=True, add_buttons=[]):
        save_dialog = QtWidgets.QDialog(self)
        save_dialog.setModal=True
        save_dialog.setLayout(QtWidgets.QGridLayout())
        if image_path is not None:
            q_image_to_display = QtGui.QPixmap(image_path)
            q_image_to_display = self.gb_scale_image_to_screen(q_image_to_display)
            image_label = QtWidgets.QLabel()
            image_label.setPixmap(q_image_to_display)
        if text is not None:
            text_label = QtWidgets.QLabel()
            text_label.setText(text)
        # Add text
        save_dialog.layout().addWidget(text_label, 0, 0, 1, 1)
        save_button = QtWidgets.QPushButton('Save')
        save_button.clicked.connect(save_dialog.accept)
        # Add Save and Cancel Buttons 
        save_dialog.layout().addWidget(save_button, 1, 0, 1, 1)
        cancel_button = QtWidgets.QPushButton('Cancel')
        cancel_button.clicked.connect(save_dialog.reject)
        save_dialog.layout().addWidget(cancel_button, 1, 1, 1, 1)
        # Dispaly image below
        qt_alignment = QtCore.Qt.AlignCenter
        image_label.setAlignment(qt_alignment)
        save_dialog.layout().addWidget(image_label, 2, 0, 1, 2)
        # Caption linedit below that 
        if add_caption_box:
            caption_lineedit = QtWidgets.QTextEdit()
            save_dialog.layout().addWidget(caption_lineedit, 3, 0, 1, 2)
            setattr(self, 'photo_caption_lineedit', caption_lineedit)
        if len(add_buttons) > 0:
            row = 3
            col = 0
            for i, add_button in enumerate(add_buttons):
                extra_button = QtWidgets.QPushButton(add_button)
                function = getattr(self, '_'.join(add_button.split(' ')).lower())
                extra_button.clicked.connect(function)
                if i % 2 == 0:
                    if i > 0:
                        col -= 2
                    row += 1
                save_dialog.layout().addWidget(extra_button, row, col, 1, 1)
                col += 1
        return save_dialog

    def gb_large_text_gather(self, text=''):
        large_text_dialog = QtWidgets.QDialog(self)
        large_text_dialog.setModal=True
        large_text_dialog.setLayout(QtWidgets.QGridLayout())
        feedback_textedit = QtWidgets.QTextEdit()
        feedback_textedit.setText(text)
        setattr(self, 'large_text_gather_textedit', feedback_textedit)
        # Add text
        large_text_dialog.layout().addWidget(feedback_textedit, 0, 0, 1, 2)
        # Add Save and Cancel Buttons 
        save_button = QtWidgets.QPushButton('Submit')
        save_button.clicked.connect(large_text_dialog.accept)
        large_text_dialog.layout().addWidget(save_button, 1, 0, 1, 1)
        cancel_button = QtWidgets.QPushButton('Cancel')
        cancel_button.clicked.connect(large_text_dialog.reject)
        large_text_dialog.layout().addWidget(cancel_button, 1, 1, 1, 1)
        return large_text_dialog

    ################################################################################

    ####################Direct Gui Management#######################################

    def gb_build_panel(self, build_dict, parent=None):
        for unique_widget_name, widget_settings in build_dict.items():
            widget_settings_copy = copy(build_dict['_common_settings'])
            if unique_widget_name != '_common_settings':
                widget_settings_copy.update(widget_settings)
                widget_settings_copy.update({'parent': parent})
                for widget_param, widget_param_value in widget_settings.items():
                    if 'function' == widget_param:
                        widget_function = self.gb_unpack_widget_function(widget_param_value)
                        widget_settings_copy.update({'function':  widget_function})
                self.gb_create_and_place_widget(unique_widget_name, **widget_settings_copy)

    def gb_create_popup_window(self, name, resize_overload=None):
        popup_window = QtWidgets.QWidget()
        popup_window.setGeometry(100, 100, 400, 200)
        popup_window.setLayout(QtWidgets.QGridLayout())
        if resize_overload is not None:
            popup_window.resizeEvent = resize_overload
        setattr(self, name, popup_window)

    def gb_create_and_place_widget(self,
                                   unique_widget_name,
                                   alignment=None,
                                   alignment_v=None,
                                   background=None,
                                   check_state=None,
                                   disabled=None,
                                   color=None,
                                   enabled=None,
                                   focus=None,
                                   font=None,
                                   frame_shadow=None,
                                   frame_shape=None,
                                   frame_linewidth=None,
                                   frame_midlinewidth=None,
                                   function=None,
                                   height=None,
                                   icon=None,
                                   keep_aspect_ratio=True,
                                   layout=None,
                                   orientation=None,
                                   parent=None,
                                   pixmap=None,
                                   style=None,
                                   text=None,
                                   tick_interval=None,
                                   tick_range=None,
                                   tool_tip=None,
                                   url=None,
                                   word_wrap=None,
                                   width=None,
                                   image_scale=None,
                                   widget_alignment=None,
                                   dial_min=None,
                                   dial_max=None,
                                   position=None,
                                   place_widget=True,
                                   **widget_setttings):
        widget_type = self.widget_to_object_dict[unique_widget_name.split('_')[-1]]
        if orientation is not None and widget_type == 'QSlider':
            widget = QtWidgets.QSlider(getattr(QtCore.Qt, orientation))
            widget.setTracking(True)
        else:
            if parent is not None:
                widget = getattr(QtWidgets, widget_type)(parent)
            else:
                widget = getattr(QtWidgets, widget_type)()
        if function is not None:
            if type(function) == str:
                function = self.gb_unpack_widget_function(function)
            if widget_type in ('QSlider', 'QDial'):
                widget.valueChanged.connect(function)
            elif widget_type in ('QPushButton', 'QCheckBox'):
                widget.clicked.connect(function)
            elif widget_type in ('QLineEdit', 'QTextEdit'):
                widget.textChanged.connect(function)
            elif widget_type in ('QComboBox',):
                widget.activated.connect(function)
                widget.currentIndexChanged.connect(function)
        if tool_tip is not None:
            widget.setToolTip(tool_tip)
        if text is not None:
            if url is not None:
                text = '<a href=\"{0}\">{1}</a>'.format(url, text)
                widget.setOpenExternalLinks(True)
            widget.setText(text)
        if pixmap is not None:
            image = QtGui.QPixmap(pixmap)
            if image_scale is not None:
                if keep_aspect_ratio:
                    image = image.scaled(image_scale[0], image_scale[1], QtCore.Qt.KeepAspectRatio)
                else:
                    image = image.scaled(image_scale[0], image_scale[1])
            if widget_type == 'QLabel':
                widget.setPixmap(image)
            elif widget_type == 'QGraphicsView':
                widget = GraphicsViewer()
                widget.scene.addPixmap(image)
        # Generic/simple in alphabetical order
        if alignment is not None:
            qt_alignment = getattr(QtCore.Qt, 'Align{0}'.format(alignment))
            widget.setAlignment(qt_alignment)
        if alignment_v is not None:
            qt_alignment = getattr(QtCore.Qt, 'Align{0}'.format(alignment))
            widget.setAlignment(qt_alignment)
        if background is not None:
            palette = QtGui.QPalette()
            palette.setColor(widget.backgroundRole(), QtGui.QColor(background))
            widget.setPalette(palette)
        #[jif contents_margin is not None:
            #[jwidget.setContentsMargin(contents_margin[0], contents_margin[1], contents_margin[2], contents_margin[3])
        if color is not None:
            widget.setStyleSheet('%s {color: %s}' % (widget_type, color))
        if check_state is not None:
            widget.setCheckState(check_state)
        if disabled is not None:
            widget.setDisabled(disabled)
        if dial_min is not None:
            widget.setMinimum(dial_min)
        if dial_max is not None:
            widget.setMaximum(dial_max)
        if enabled is not None:
            widget.setEnabled(enabled)
        if focus is not None:
            widget.setFocus(focus)
            widget.setFocusPolicy(QtCore.Qt.NoFocus)
        if font is not None:
            widget.setFont(getattr(self, '{0}_font'.format(font)))
        if frame_shadow is not None:
            if frame_linewidth is not None:
                widget.setLineWidth(frame_linewidth)
            else:
                widget.setLineWidth(3)
            if frame_midlinewidth is not None:
                widget.setLineWidth(frame_midlinewidth)
            else:
                widget.setMidLineWidth(1)
            widget.setFrameShadow(getattr(QtWidgets.QFrame, frame_shadow))
        if frame_shape is not None:
            widget.setFrameShape(getattr(QtWidgets.QFrame, frame_shape))
            if frame_linewidth is not None:
                widget.setLineWidth(frame_linewidth)
            else:
                widget.setLineWidth(3)
            if frame_midlinewidth is not None:
                widget.setLineWidth(frame_midlinewidth)
            else:
                widget.setMidLineWidth(1)
        if height is not None:
            widget.setFixedHeight(height)
        if icon is not None:
            if icon.endswith('.png') or icon.endswith('.jpg'):
                widget.setIcon(QtGui.QIcon(icon))
                widget.setIconSize(QtCore.QSize(50, 50))
            else:
                widget.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_{0}'.format(icon))))
        if style is not None:
            widget.setStyle(getattr(QtWidgets.QStyle, style)())
        if layout is not None:
            widget.setLayout(getattr(QtWidgets, layout)())
        if tick_interval is not None:
            widget.setTickInterval(1)
        if tick_range is not None:
            widget.setRange(tick_range[0], tick_range[1])
        if width is not None:
            widget.setFixedWidth(width)
        if word_wrap is not None:
            widget.setWordWrap(word_wrap)
        # After all settings are applied we place the widget
        if place_widget:
            row, col, row_span, col_span = position[0], position[1], position[2], position[3]
            widget.adjustSize()
            if 'widget' in unique_widget_name:
                if widget_alignment is not None:
                    self.centralWidget().layout().addWidget(widget, row, col, row_span, col_span,
                                        getattr(QtCore.Qt, widget_alignment))
                else:
                    self.centralWidget().layout().addWidget(widget, row, col, row_span, col_span)
            else:
                if 'panel' in unique_widget_name:
                    panel = '{0}_{1}'.format(unique_widget_name.split('_panel')[0][1:], 'panel_widget')
                if 'popup' in unique_widget_name:
                    panel = '{0}_{1}'.format(unique_widget_name.split('_popup')[0][1:], 'popup')
                if 'panel' in unique_widget_name and 'popup' in unique_widget_name and widget_type != 'QWidget':
                    panel = '_{0}_{1}'.format(unique_widget_name.split('_panel')[0][1:], 'panel')
                if widget_alignment is not None:
                    getattr(self, panel).layout().addWidget(widget, row, col, row_span, col_span,
                                                            getattr(QtCore.Qt, widget_alignment))
                else:
                    getattr(self, panel).layout().addWidget(widget, row, col, row_span, col_span)
        else:
            widget.close()
        setattr(self, unique_widget_name, widget)
        widget.setWhatsThis(unique_widget_name)
        return widget

    ################################################################################

class GenericClass(object):

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self.__dict__))
