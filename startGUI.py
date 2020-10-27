import sys
import os

bcg_fname = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'bcg', 'source', 'bolo_calc_gui.py'))
os.system('python %s' % (bcg_fname))
