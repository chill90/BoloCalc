import glob as gb
import pickle as pk

files = sorted(gb.glob("src/detCorrFiles/PKL/*"))

for f in files:
    stuff = pk.load(open(f, 'r'))
    pk.dump(stuff, open(f, 'wb'))
