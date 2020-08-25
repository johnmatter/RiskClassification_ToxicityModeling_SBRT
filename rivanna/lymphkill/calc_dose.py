import argparse
import sys
import csv
import os

import numpy as np
import nrrd

from lymphkill.file_utils import find_postfixed_files

'''
Load masks files saved as NRRD
Parameters:
    masks - a list of masks to load
Returns:
    A dictionary whose keys are mask names, and values are boolean-valued ndarrays
'''
def load_masks(masks):
    mdict = {}
    for m in masks:
        key = os.path.splitext(os.path.basename(m))[0]
        mdict[key], hdr = nrrd.read(m)
        mdict[key] = mdict[key].astype(bool)

    return mdict

'''
Characterize the dose in each mask
Parameters:
    dose - ndarray containing delivered dose
    masks - a list of masks to use
Returns:
    A list of dictionaries characterizing the dose in each mask
'''
def calculate_dose(dose, masks):
    doses = []

    for m in masks:
        print('Calculating %s' % m)
        masked_img = dose[masks[m]]
        dose_dict = {}
        dose_dict['mask'] = m
        dose_dict['max'] = masked_img.max()
        dose_dict['mean'] = masked_img.mean()
        doses.append(dose_dict)

    return doses

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=str, help='The patient directory to look in')
    args = parser.parse_args()

    try:
        # Load masks
        mask_filenames = find_postfixed_files(os.path.join(args.directory, 'masks'), 'nrrd')
        masks = load_masks(mask_filenames)

        # Load dose
        dose, dose_header = nrrd.read(os.path.join(args.directory, "dose_in_CT_dimensions.nrrd"))

        # Calculate dose
        doses = calculate_dose(dose, masks)

        # Print dose summary
        filename = os.path.join(args.directory, 'dose.csv')
        with open(filename, mode='w') as csv_file:
            writer = csv.DictWriter(csv_file, doses[0].keys())
            writer.writeheader()
            writer.writerows(doses)


    except Exception as ex:
        print(type(ex), ex)
        print('Could not calculate doses')
        sys.exit(0)
