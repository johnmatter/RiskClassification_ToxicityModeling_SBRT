import os
import argparse
from sys import exit
import numpy as np
import pickle
import pydicom
import nrrd

from lymphkill.file_utils import find_prefixed_file, find_dicom_directory, find_prefixed_files, load_rtdose_files
from calc_blood_dose import *

basic_mask_dicts = [
	{'NameStrings': ['other', 'organs'], 'GV': False, 'Stationary': False, 'CardiacOutput': -1},
	{'NameStrings': ['lung', 'total'], 'GV': False, 'Stationary': False, 'CardiacOutput': 0.025},
	{'NameStrings': ['aorta'], 'GV': True, 'Stationary': False, 'CardiacOutput': 1.},
	{'NameStrings': ['pa'], 'GV': True, 'Stationary': False, 'CardiacOutput': 1.},
	{'NameStrings': ['vc'], 'GV': True, 'Stationary': False, 'CardiacOutput': 1.},
	{'NameStrings': ['thoracic', 'spine'], 'GV': False, 'Stationary': True, 'CardiacOutput': 0.},
	{'NameStrings': ['Heart'], 'GV':True, 'Stationary':False,'CardiacOutput':1.},
	{'NameStrings': ['Heart','AV'], 'GV':True, 'Stationary':False,'CardiacOutput':1.},
	{'NameStrings': ['pa','av'], 'GV':True, 'Stationary':False,'CardiacOutput':1.},
	{'NameStrings': ['vc', 'av'], 'GV':True, 'Stationary':False,'CardiacOutput':1.},
	{'NameStrings': ['aorta', 'av'], 'GV':True, 'Stationary':False,'CardiacOutput':1.},
	{'NameStrings': ['Great','Vessels'], 'GV':False, 'Stationary': False, 'CardiacOutput':0.},
	{'NameStrings': ['Chestwall'], 'GV':False, 'Stationary': False, 'CardiacOutput':0.},
	{'NameStrings': ['Lung','Lt'], 'GV':False, 'Stationary': False, 'CardiacOutput':0.012},
	{'NameStrings': ['Lung','Rt'], 'GV':False, 'Stationary': False, 'CardiacOutput':0.012},
	{'NameStrings': ['cord'], 'GV':False, 'Stationary': True, 'CardiacOutput':0.},
	{'NameStrings': ['brachial', 'plexus'], 'GV':False, 'Stationary': False, 'CardiacOutput':0.},
	{'NameStrings': ['T10'], 'GV':False, 'Stationary': False, 'CardiacOutput':0.},
	{'NameStrings': ['T5'], 'GV':False, 'Stationary': False, 'CardiacOutput':0.},	
]

'''
Find the index for a given organ in the contours structure
Parameters:
	contours - The contours structure to look in
	name_strings - A list of strings which must appear in the name (lowercase)
Returns:
	The index of the matching contour in the structure
'''
def find_matching_contour_idx(contours, name_strings):
	for i, nm in enumerate(contours['ROIName']):
		lnm = nm.lower()
		found = True
		for j in name_strings:
			if not j.lower() in lnm:
				found = False
		if found:
			return i
	
	return -1

'''
Get grids for converting between the CT image dimensions and the dose file dimensions
Parameters:
	ct_info - Information about the CT files
	dose_info - Information about the RTDOSE files
	dim_vol - The dimensions of the CT volume
	dim_dos - The dimensions of the dose volume
Returns:
	posv, posd - The valid in-body indices for the CT and RTDOSE volumes respectively
'''
def get_conversion_grids(ct_info, dose_info, dim_vol, dim_dos):
	#Get voxel dimensions
	dim_voxd = np.array([dose_info.PixelSpacing[0], dose_info.PixelSpacing[1], dose_info.SliceThickness])
	dim_voxv = np.array([ct_info.PixelSpacing[0], ct_info.PixelSpacing[1], ct_info.SliceThickness])

	#Get image corners
	corner_d = np.array([dose_info.ImagePositionPatient])
	corner_v = np.array([ct_info.ImagePositionPatient])

	x, y, z = np.meshgrid(
		np.arange(dim_vol[0]),
		np.arange(dim_vol[1]),
		np.arange(dim_vol[2]))
		
	posv = np.transpose(np.array([x, y, z]), (1, 2, 3, 0))
	yxz = np.transpose(np.array([y, x, z]), (1, 2, 3, 0))
	xyz = np.transpose(np.array([x, y, z]), (1, 2, 3, 0))

	# posd contains the voxel coordinates (in the dose volume's coordinate system)
	# for each of the 512x512x110 voxels of the CT image
	#
	# If the original mask generation script is to be believed, we have the following:
	#	posd[:,:,:,0] contains the dose-grid y coordinates of each voxel
	#	posd[:,:,:,1] contains the dose-grid x coordinates of each voxel
	#	posd[:,:,:,2] contains the dose-grid z coordinates of each voxel
	#
	# I'm not sure why the x and y need to be flipped.
	posd = (corner_v - corner_d + xyz * dim_voxv) / dim_voxd
	posd = posd.astype(int)

	valid_voxel = np.logical_and(posd[:,:,:,0] >= 0, posd[:,:,:,1] >= 0)
	valid_voxel = np.logical_and(valid_voxel, posd[:,:,:,2] >= 0)
	valid_voxel = np.logical_and(valid_voxel, posd[:,:,:,0] < dim_dos[0])
	valid_voxel = np.logical_and(valid_voxel, posd[:,:,:,1] < dim_dos[1])
	valid_voxel = np.logical_and(valid_voxel, posd[:,:,:,2] < dim_dos[2])

	return posv[valid_voxel], posd[valid_voxel]

'''
Calculate the average layer size in the z-direction of a given mask
Parameters:
	mask - The boolean mask for an organ
Returns:
	The average number of True values in each Z-slice
'''
def layer_size(mask):
	num = np.sum(mask, axis=(0, 1))
	num = num[num > 0]
	return np.sum(num) / len(num)

'''
Find the first CT frame in the z-direction
Parameters:
	ct_infos - A list of loaded CT dicom files
Returns:
	The index of the first CT slice in the z-direction
'''
def get_first_CT_frame(ct_infos):
	first = ct_infos[0]
	for i in ct_infos:
		if float(i.ImagePositionPatient[2]) < float(first.ImagePositionPatient[2]):
			first = i
	return first

'''
Print information about the mask structure
Parameters:
	mask - The mask structure to print information about
'''
def print_mask(mask):
	print('Organ %s' % (mask['Name']))
	for key in mask.keys():
		if isinstance(mask[key], np.ndarray) or key == 'Name':
			continue
		print('  %15s:\t%g' % (key, mask[key]))

'''
Generate a masks structure given a set of contours and information about the dose files
Parameters:
	ct_info - Header information from a CT file
	dose_info - Header information from a DOSE file
	dose_grids
Returns:
	dose - the dose grid resampled in the CT's resolution
'''
def resample_dose(
	ct_infos,
	dose_info,
	dose_grids):
	
	ct_info = get_first_CT_frame(ct_infos)

	dim_vol = np.array([ct_info.Rows, ct_info.Columns, len(ct_infos)])
	dim_dos = np.array([dose_info.Rows, dose_info.Columns, dose_info.NumberOfFrames])

	print(dim_dos, dim_vol)

	posv, posd = get_conversion_grids(ct_info, dose_info, dim_vol, dim_dos)

	posv = np.ravel_multi_index(posv.transpose(), dim_vol)
	posd = np.ravel_multi_index(posd.transpose(), dim_dos)

	dose_grids = np.sum(np.array(dose_grids), axis=0)
	dose_grids = dose_grids.flatten()

	dose = np.zeros(dim_vol.prod(), dtype=np.float64)
	dose[posv] = dose_grids[posd]
	dose = dose.reshape(dim_vol)

	return dose

'''
Write the dose grid in NRRD format
Parameters:
	dose - the dose grid
	directory - where to write the NRRD
'''
def write_dose(dose, directory):
	filename = os.path.join(directory, 'dose_in_CT_dimensions.nrrd')
	print('Writing ' + filename)
	nrrd.write(filename, dose)


if __name__=='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('directory', type=str, help='The patient directory to look in')
	args = parser.parse_args()

	try:
		dcm_directory = find_dicom_directory(args.directory)
		ct_prefix = 'CT'
		dose_prefix = 'RTDOSE'
		
		ct_infos = [pydicom.dcmread(f) for f in find_prefixed_files(dcm_directory, ct_prefix)]
		dose_info = pydicom.dcmread(find_prefixed_file(dcm_directory, dose_prefix))
		dose_grids = load_rtdose_files(find_prefixed_files(dcm_directory, dose_prefix))
	except Exception as ex:
		print(type(ex), ex)
		print('Could not load in ct/dose info')
		exit(0)
	
	dose = resample_dose(ct_infos, dose_info, dose_grids)

	write_dose(dose, args.directory)
