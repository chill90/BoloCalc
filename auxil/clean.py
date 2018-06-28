#Run this script from the top-most directory of the tree you want to clean.
#python Version 2.7.2
import os

targets = ('log_', 'sensitivity.txt', 'opticalpower.txt', '~', '.pyc', '.ds_store', 'mappingspeedvary')

for root, dirs, files in os.walk(os.getcwd()):
    for file in files:
        if any(target in file.lower() for target in targets):
            print "Deleting file: " + file
            os.remove(os.path.join(root, file))
