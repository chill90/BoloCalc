#from GuiBuilder.gui_builder import GenericClass
from gui_builder.gui_builder import GenericClass


set_to_popup_settings = GenericClass()

set_to_popup_settings.set_to_popup_base_build_dict = {
    '_common_settings': {'font': 'large'},
    '_BCG_set_to_popup_parameter_header_label': {
        'text': 'Parameter To Edit:',
        'position': (0, 0, 1, 1)},
    '_BCG_set_to_popup_parameter_label': {
        'position': (0, 1, 1, 1)},
    '_BCG_set_to_popup_parameter_description_header_label': {
        'text': 'Parameter Description:',
        'position': (1, 0, 1, 1)},
    '_BCG_set_to_popup_parameter_description_label': {
        'position': (1, 1, 1, 1)},
    '_BCG_set_to_popup_parameter_input_type_header_label': {
        'text': 'Parameter Input Type:',
        'position': (2, 0, 1, 1)},
    '_BCG_set_to_popup_parameter_input_type_label': {
        'position': (2, 1, 1, 1)},
    '_BCG_set_to_popup_parameter_input_range_header_label': {
        'text': 'Parameter Input Range:',
        'position': (3, 0, 1, 1)},
    '_BCG_set_to_popup_parameter_input_range_label': {
        'position': (3, 1, 1, 1)},
    '_BCG_set_to_popup_edit_value_header_label': {
        'text': 'Current Value with Spread',
        'position': (4, 0, 1, 1)},
    '_BCG_set_to_popup_current_value_label': {
        'position': (4, 1, 1, 1)},
    '_BCG_set_to_popup_edit_mode_label': {
        'text': 'Edit Modes:',
        'position': (5, 0, 1, 1)},
    '_BCG_set_to_popup_edit_single_float_pushbutton': {
        'text': 'Edit Float',
        'function': 'bcg_edit_single_float',
        'position': (5, 1, 1, 1)},
    '_BCG_set_to_popup_edit_single_pdf_pushbutton': {
        'text': 'Load PDF',
        'function': 'bcg_edit_single_special_file',
        'position': (5, 2, 1, 1)},
    '_BCG_set_to_popup_edit_by_band_pushbutton': {
        'text': 'Edit Float/PDF per Band ID',
        'function': 'bcg_edit_each_band_as_float_or_pdf',
        'position': (6, 1, 1, 1)},
    '_BCG_set_to_popup_edit_single_band_pushbutton': {
        'text': 'Load BAND',
        'function': 'bcg_edit_single_special_file',
        'position': (6, 2, 1, 1)},
    '_BCG_set_to_popup_edit_panel': {
        'layout': 'QGridLayout',
        'position': (7, 0, 1, 3)},
    '_BCG_set_to_popup_new_value_header_label': {
        'text': 'New Value',
        'position': (8, 0, 1, 1)},
    '_BCG_set_to_popup_new_value_label': {
        'font': 'large',
        'position': (8, 1, 1, 1)},
    '_BCG_set_to_popup_edit_special_file_1_pushbutton': {
        'text': 'Edit Special File',
        'function': 'bcg_edit_special_file',
        'position': (9, 1, 1, 2)},
    '_BCG_set_to_popup_delete_special_file_1_pushbutton': {
        'text': 'Delete Special File',
        'function': 'bcg_delete_special_file',
        'position': (10, 1, 1, 2)},
    '_BCG_set_to_popup_update_value_pushbutton': {
        'text': 'Update Value',
        'function': 'bcg_update_value',
        'position': (11, 1, 1, 2)},
    '_BCG_set_to_popup_close_pushbutton': {
        'text': 'Cancel',
        'function': 'bcg_close_set_to_popup',
        'position': (12, 1, 1, 2)},
}

set_to_popup_settings.set_to_popup_combobox_entry_dict = {
    '_BCG_set_to_popup_edit_type_select_combobox': []
}
