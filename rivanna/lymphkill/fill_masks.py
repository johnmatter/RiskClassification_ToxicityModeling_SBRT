import os
import argparse
import numpy as np
import nrrd

from scipy.ndimage import binary_fill_holes

from file_utils import find_postfixed_files

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('directory', type=str, help='The patient directory to look in')
args = parser.parse_args()

# Get mask directory and make a new one for the filled masks if it doesn't exist yet
mask_directory = os.path.join(args.directory, "masks")
new_mask_directory = os.path.join(mask_directory, "filled")
if not(os.path.exists(new_mask_directory)):
        os.mkdir(new_mask_directory)

# These are full path locations of the original masks
all_masks = find_postfixed_files(mask_directory, "nrrd")

for mask_filename in all_masks:
    # Get basename
    mask_basename = os.path.basename(mask_filename)
    print('Filling ' + mask_basename)

    # Read file
    mask, header = nrrd.read(mask_filename)

    # Fill holes
    filled_mask = binary_fill_holes(mask).astype(int)

    # Write
    new_mask_filename = os.path.join(new_mask_directory, mask_basename)
    nrrd.write(new_mask_filename, filled_mask)
