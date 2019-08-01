# This script takes an input band and adjusts the integrated band
# efficiency to a user-defined value. The band shape is preserved,
# but the overall amplitude is altered.

# The "ideal efficiency" is assumed to be one of uniform admittance between
# the defined band's -3 dB points. In other words, it's assumed to be
# a top-hat band with the input efficiency

import numpy as np
import sys as sy
import os


# Global boolean to determine whether old file will be saved
SAVE_OLD_FILE = False

# Pass the band file band-integrated efficiency as a command-line argument
args = sy.argv[1:]
if not len(args) == 2:
    print("\nUsage: python3 adjust_band_eff.py [band file] [eff]")
    print("Efficiency must lie between 0.0 and 1.0\n")
else:
    try:
        fname = str(args[0])
        band_avg_tran = float(args[1])
    except:
        print("\nCould not understand command-line arguments '%s' and '%s'"
              % (str(args[0]), str(args[1])))
        print("First argument must be the band file to be altered")
        print("Second argument must be a float between 0.0 and 1.0\n")
        sy.exit(False)
    if not os.path.exists(fname):
        print("\nPassed file name '%s' does not exist\n" % (fname))
        sy.exit(False)
    if not (band_avg_tran <= 1.0 and band_avg_tran >= 0.):
        print("\nPassed efficiency '%.3f' does not lie between 0.0 and 1.0\n"
              % (band_avg_tran))
        sy.exit(False)

# Load the band file
if ".CSV" in fname.upper():
    old_data = np.loadtxt(fname, unpack=True, dtype=np.float, delimiter=',')
    use_csv = True
elif ".TXT" in fname.upper():
    old_data = np.loadtxt(fname, unpack=True, dtype=np.float)
    use_csv = False
else:
    print("\nFormat within band file '%s' not understood\n" % (fname))
    sy.exit(False)

# Unpack the data
if len(old_data) == 3:
    freqs, tran, err = old_data
elif len(old_data) == 2:
    freqs, tran = old_data
    err = None
else:
    print("\nFile '%s' contained more than 3 data colums or less than 1\n"
          % (fname))
    sy.exit(False)

# Find the -3 dB points
max_tran = np.amax(tran)
lo_point = np.argmin(
    abs(tran[:len(tran)//2] - 0.5 * max_tran))
hi_point = np.argmin(
    abs(tran[len(tran)//2:] - 0.5 * max_tran)) + len(tran)//2
f_lo = freqs[lo_point]
f_hi = freqs[hi_point]

# Check old band's band-averaged transmission for consistency
old_band_avg_tran = np.trapz(tran, freqs) / (f_hi - f_lo)
print("\nInput band-averaged transmission: %.5f" % (old_band_avg_tran))

# Define the top-hat band
top_hat_tran = [band_avg_tran
                if (f >= f_lo and f < f_hi)
                else 0.
                for f in freqs]

# Scale the input band
scale_fact = np.trapz(top_hat_tran, freqs) / np.trapz(tran, freqs)
print("Scaling the input band by factor = %.5f" % (scale_fact))
new_tran = tran * scale_fact
if err is not None:
    new_err = err * scale_fact
    new_data = np.transpose([freqs, new_tran, new_err])
else:
    new_data = np.transpose([freqs, new_tran])
old_data = np.transpose(old_data)

# Check new band's band-averaged transmission for consistency
new_band_avg_tran = np.trapz(new_tran.T, freqs) / (f_hi - f_lo)
print("New band-averaged transmission: %.5f" % (new_band_avg_tran))

# Save the new band, moving the old band a filename with the tag 'orig'
save_dir = os.path.dirname(fname)
f_head, f_tail = os.path.split(fname)
new_file = fname
if SAVE_OLD_FILE:
    old_file = os.path.join(
        f_head, f_tail.split(".")[0] + "_orig." + f_tail.split(".")[-1])
if use_csv:
    np.savetxt(new_file, new_data, delimiter=',', fmt='%.5f')
    if SAVE_OLD_FILE:
        np.savetxt(old_file, old_data, delimiter=',', fmt='%.5f')
else:
    np.savetxt(new_file, new_data, delimiter='\t', fmt='%.5f')
    if SAVE_OLD_FILE:
        np.savetxt(old_file, old_data, delimiter='\t', fmt='%.5f')

# Done
print("Finished!\n")
