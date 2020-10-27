#from GuiBuilder.gui_builder import GenericClass
from gui_builder.gui_builder import GenericClass

main_panel_settings = GenericClass()

main_panel_settings.main_panel_build_dict = {
        '_common_settings': {'font': 'med'},
        '_cw_main_panel_select_experiment_label': {
            'position': (1, 0, 1, 1),
            'text': 'Select Experiment',
            },
        }

main_panel_settings.main_panel_combobox_dict = {
        '_cw_main_panel_select_experiment_combobox':  [],
        '_cw_main_panel_select_version_combobox': [],
        }

