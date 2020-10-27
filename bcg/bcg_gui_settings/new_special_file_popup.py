#from GuiBuilder.gui_builder import GenericClass
from gui_builder.gui_builder import GenericClass

new_special_file_popup_settings = GenericClass()
new_special_file_popup_settings.new_special_file_popup_build_dict = {
        '_common_settings': {'font': 'large'},
        '_BCG_new_special_file_popup_file_to_load_label': {
            'position': (0, 0, 1, 1)},
        '_BCG_new_special_file_popup_load_file_from_drive_pushbutton': {
            'text': 'Load file from Computer',
            'function': 'bcg_load_pdf_or_band_file_from_computer',
            'position': (1, 0, 1, 1)},
        '_BCG_new_special_file_popup_new_text_file_pushbutton': {
            'text': 'Start new text file',
            'function': 'bcg_start_new_txt_file',
            'position': (2, 0, 1, 1)},
        '_BCG_new_special_file_popup_new_csv_file_pushbutton': {
            'text': 'Start new csv file',
            'function': 'bcg_start_new_csv_file',
            'position': (3, 0, 1, 1)},
        '_BCG_new_special_file_popup_cancel_pushbutton': {
            'text': 'Cancel',
            'function': 'bcg_close_new_special_file',
            'position': (4, 0, 1, 1)},
        }
