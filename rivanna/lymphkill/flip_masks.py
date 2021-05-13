import os
import argparse
import numpy as np
import nrrd

from file_utils import find_postfixed_files

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('directory', type=str, help='The patient directory to look in')
parser.add_argument('--subdirectory', type=str, help='Subdirectory containing masks to flip')
parser.add_argument('--archive', dest='archive', action='store_true')
parser.add_argument('--no-archive', dest='archive', action='store_false')
parser.set_defaults(archive=True)
args = parser.parse_args()

# Get mask directory and make a new one for the flipped masks if it doesn't exist yet
mask_directory = os.path.join(args.directory, "masks")
if args.subdirectory is not None:
    search_directory = os.path.join(mask_directory, args.subdirectory)
else:
    search_directory = mask_directory

flipped_mask_directory = os.path.join(mask_directory, "flipped")
unflipped_mask_directory = os.path.join(mask_directory, "original")

if not(os.path.exists(flipped_mask_directory)):
        os.mkdir(flipped_mask_directory)
if not(os.path.exists(unflipped_mask_directory)):
        os.mkdir(unflipped_mask_directory)

# These are full path locations of the original masks
all_masks = find_postfixed_files(search_directory, "nrrd")

for mask_filename in all_masks:
    # Get basename
    mask_basename = os.path.basename(mask_filename)
    print('Flipping ' + mask_basename)

    # Read file
    mask, header = nrrd.read(mask_filename)

    # Flip z axis
    flipped_mask = np.flip(mask, 2)

    # Write
    flipped_mask_filename = os.path.join(flipped_mask_directory, mask_basename)
    nrrd.write(flipped_mask_filename, flipped_mask)

    if args.archive:
        print("Archiving")
        # Move unflipped file to archive directory
        os.rename(mask_filename, os.path.join(unflipped_mask_directory, mask_basename))
