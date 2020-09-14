import os
import argparse
from sys import exit
import numpy as np
import pickle
import pydicom
import nrrd
import SimpleITK as sitk

from lymphkill.file_utils import find_prefixed_file, find_dicom_directory, find_prefixed_files, load_rtdose_files
from calc_blood_dose import *

'''
Generate a masks structure given a set of contours and information about the dose files
Parameters:
	ct_files - List of files that make up the CT
	dose_files - List of files containing dose info
Returns:
	dose - the dose grid resampled in the CT's resolution
'''
def resample_dose(
	ct_files,
	dose_files):
	
	# Sum dose info for dose grid resolution file
	dose_grids = load_rtdose_files(dose_files)
	dose = np.sum(np.array(dose_grids), axis=0)

	# Read CT as a SimpleITK image
	reader = sitk.ImageSeriesReader()
	reader.SetFileNames(ct_files)
	ct = reader.Execute()
	
	# CT spacing is in wrong units?
	ct_spacing = ct.GetSpacing()
	ct_spacing = [ct_spacing[0], ct_spacing[1], ct_spacing[2]/1e2]
	ct.SetSpacing(ct_spacing)


	# Set up the resampler
	resampler = sitk.ResampleImageFilter()
	resampler.SetOutputSpacing(ct.GetSpacing())
	resampler.SetSize(ct.GetSize())
	resampler.SetOutputDirection(ct.GetDirection())
	resampler.SetOutputOrigin(ct.GetOrigin())
	resampler.SetTransform(sitk.Transform())
	resampler.SetInterpolator(sitk.sitkNearestNeighbor)

	for dose_file in dose_files:
		print()
		print(dose_file)
		# Read dose as SimpleITK image so we can SetOrigin(), etc
		dose_sitk = sitk.ReadImage(dose_file)
		print('dose.any() before resample')
		print((sitk.GetArrayFromImage(dose_sitk)).any())

		# Resample
		resampled = resampler.Execute(dose_sitk)
		dose_resampled = sitk.GetArrayFromImage(resampled)
		dose_resampled = dose_resampled.transpose()
		print('dose.any() after resample')
		print(dose_resampled.any())

		# Add to total resampled

	return dose, dose_resampled

if __name__=='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('directory', type=str, help='The patient directory to look in')
	args = parser.parse_args()

	try:
		dcm_directory = find_dicom_directory(args.directory)
		ct_prefix = 'CT'
		dose_prefix = 'RTDOSE'
		
		ct_files = find_prefixed_files(dcm_directory, ct_prefix)
		dose_files = find_prefixed_files(dcm_directory, dose_prefix)

	except Exception as ex:
		print(type(ex), ex)
		print('Could not load in ct/dose info')
		exit(0)
	
	dose, dose_resampled = resample_dose(ct_files, dose_files)

	filename = os.path.join(args.directory, 'dose_in_CT_dimensions.nrrd')
	print('Writing ' + filename)
	nrrd.write(filename, dose_resampled)

	filename = os.path.join(args.directory, 'dose.nrrd')
	print('Writing ' + filename)
	nrrd.write(filename, dose)
