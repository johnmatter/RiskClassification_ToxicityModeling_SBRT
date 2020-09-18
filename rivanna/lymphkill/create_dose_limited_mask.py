import argparse
import sys
import os

import numpy as np
import nrrd

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=str, help='The patient directory to look in')
    parser.add_argument('mask', type=str, help='The name of the mask to use')
    parser.add_argument('dose_limit', type=str, help='The RHS to use for mask.where(dose>dose_limit)')
    args = parser.parse_args()

    try:
        # Check filename has nrrd extension
        mask_filename = args.mask
        mask_splitext = os.path.splitext(mask_filename)
        if mask_splitext[1] == '':
            mask_filename = mask_filename + '.nrrd'

        # Read mask and dose
        mask_filename = os.path.join(args.directory, 'masks', mask_filename)
        mask, hdr = nrrd.read(mask_filename)

        dose_filename = os.path.join(args.directory, "dose_in_CT_dimensions.nrrd")
        dose, hdr = nrrd.read(dose_filename)

        # Mask mask by dose
        new_mask = np.ma.masked_where(dose >= float(args.dose_limit), dose)
        new_mask = np.logical_and(new_mask.mask, mask)

        # Need to convert from bool to int for nrrd
        new_mask = new_mask * 1

        # Write mask to disk
        output_filename = mask_splitext[0] + '_GT_' + str(args.dose_limit) + mask_splitext[1]
        output_filename = os.path.join(args.directory, 'masks', output_filename)

        nrrd.write(output_filename, new_mask)

    except Exception as ex:
        print(type(ex), ex)
        print('Failed to create mask')
        sys.exit(0)
