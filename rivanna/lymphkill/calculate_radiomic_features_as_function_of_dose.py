import os
import sys
import csv
import six
import argparse

import warnings

import numpy as np
import SimpleITK as sitk
import nrrd
from radiomics import featureextractor

def cleanup(radiomic_features):
    keys_to_remove = []
    keys_to_remove.append('diagnostics_Configuration_Settings')
    keys_to_remove.append('diagnostics_Configuration_EnabledImageTypes')
    keys_to_remove.append('diagnostics_Image-original_Spacing')
    keys_to_remove.append('diagnostics_Image-original_Size')
    keys_to_remove.append('diagnostics_Mask-original_Spacing')
    keys_to_remove.append('diagnostics_Mask-original_Size')
    keys_to_remove.append('diagnostics_Mask-original_BoundingBox')
    keys_to_remove.append('diagnostics_Mask-original_CenterOfMassIndex')
    keys_to_remove.append('diagnostics_Mask-original_CenterOfMass')

    for key in keys_to_remove:
        radiomic_features.pop(key, None)

    return radiomic_features

def write_mask(dose, mask, dose_limit, directory):
    # Mask mask by dose
    new_mask = np.ma.masked_where(dose >= float(dose_limit), dose)
    new_mask = np.logical_and(new_mask.mask, mask)

    # Need to convert from bool to int for nrrd
    new_mask = new_mask * 1

    # Write mask to disk
    mask_filename = args.mask
    mask_splitext = os.path.splitext(mask_filename)
    output_filename = mask_splitext[0] + '_GT_' + str(dose_limit) + 'Gy' + mask_splitext[1]
    output_filename = os.path.join(directory, output_filename)
    nrrd.write(output_filename, new_mask)

    return output_filename

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=str, help='The patient directory to look in')
    parser.add_argument('image', type=str, help='The patient CT to use (assumed to be in PATIENT/')
    parser.add_argument('mask', type=str, help='The name of the mask to use (assumed to be in PATIENT/masks/)')
    parser.add_argument('dose_range', type=int, nargs=3, help='[min max step]; the range to use for mask.where(dose>dose_limit)')
    parser.add_argument('--output_directory', type=str, help='Where to write output CSV')
    args = parser.parse_args()

    patient_initials = os.path.basename(args.directory)
    mask_name = os.path.splitext(args.mask)[0]

    # Try to load data
    try:
        # Read mask
        mask_directory = os.path.join(args.directory, 'masks')
        mask_filename = os.path.join(mask_directory, args.mask)
        mask, hdr = nrrd.read(mask_filename)
    except Exception as ex:
        print(type(ex), ex)
        print('Failed to load mask: ' + mask_filename)
        sys.exit(1)

    try:
        # Read dose
        dose_filename = os.path.join(args.directory, "dose_in_CT_dimensions.nrrd")
        dose, hdr = nrrd.read(dose_filename)
    except Exception as ex:
        print(type(ex), ex)
        print('Failed to load dose: ' + dose_filename)
        sys.exit(1)

    # Check if CT exists
    image_filename = os.path.join(args.directory, args.image)
    if not(os.path.exists(image_filename)):
        print('CT img does not exist')
        sys.exit(1)

    # Create feature extractor
    extractor = featureextractor.RadiomicsFeatureExtractor()

    # What dose values are we interested in?
    dose_range = range(args.dose_range[0], args.dose_range[1]+1, args.dose_range[2])

    # Loop over dose limits, create a mask, and then calculate radiomic features for it
    radiomic_features = {}
    for dose_limit in dose_range:
        dose_mask_filename = write_mask(dose, mask, dose_limit, mask_directory)
        print('Wrote ' + dose_mask_filename)
        try:
            radiomic_features[dose_limit] = extractor.execute(image_filename, dose_mask_filename)
            radiomic_features[dose_limit]['success'] = True
        except ValueError:
            print('ERROR PROCESSING DOSE LIMIT ' + str(dose_limit))
            radiomic_features[dose_limit] = {'success' : False}

        radiomic_features[dose_limit]['patient'] = patient_initials
        radiomic_features[dose_limit]['mask'] = args.mask
        radiomic_features[dose_limit]['dose_limit'] = dose_limit


    # Clean up the dictionary
    radiomic_features = cleanup(radiomic_features)

    # Save features to csv
    csv_filename = '_'.join([patient_initials, mask_name, 'radiomics.csv'])
    if args.output_directory is None:
        csv_filename = os.path.join(args.directory, 'radiomics', csv_filename)
    else:
        csv_filename = os.path.join(args.output_directory, csv_filename)

    # We need to get a list of the header names from one of the successful iterations
    # If non of the iterations were successful, warn user
    fieldnames=[]
    for dose_limit in dose_range:
        if radiomic_features[dose_limit]['success'] == False:
            continue
        else:
            fieldnames = list(radiomic_features[dose_limit].keys())
            break

    if len(fieldnames)>0:
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for dose_limit in dose_range:
                writer.writerow(radiomic_features[dose_limit])
    else:
        print('Could not write csvs because `fieldnames` is empty.')
        print('Check to see if your mask is empty!')
