import os
import pickle
import argparse
import pydicom
import nrrd
import numpy as np
from scipy import ndimage

from sys import exit
from lymphkill.file_utils import find_prefixed_file, find_dicom_directory, implay, find_prefixed_files

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
Write a mask in NRRD format
Parameters:
	mask - a mask dictinoary whose keys are Name and Mask
	directory - where to write the mask
'''
def write_mask(mask, directory):
	# Generate filename
	filename = os.path.join(directory, mask['Name']+'.nrrd')

	# Remove trouble characters from filename
	filename = filename.replace(' ', '_')
	filename = filename.replace('(', '')
	filename = filename.replace(')', '')

	print('Writing ' + filename)
	nrrd.write(filename, 1*mask['Mask'])

'''
Generate a masks structure given a set of contours and information about the dose files
Parameters:
	contours - The result from structure_loading.load_structures
	ct_info - Header information from a CT file
	mask_dicts - Information about which masks to include
		Entries in mask_dicts have the format:
			NameStrings - search for ROIs in contours which have these name strings (use lowercase)
			GV - True if the organ is a great vessel
			Stationary - True if the organ is stationary (thoracic spine)
			Cardiac Output - Percentage of total cardiac output (0-1)
Returns:
	masks - A set of dictionaries, each containing:
		Name: The name of the organ
		GV: Whether the organ is a great vessel
		Stationary: Whether the organ is stationary
		CardiacOutput: The percent of total cardiac output for the organ (0-1)
		Mask: A boolean mask with the same dimensions as the dose files
		LayerSize: The average layer size of the organ
'''
def mask_generation(
	contours,
	ct_infos,
	mask_dicts=basic_mask_dicts):

	masks = []
	other_organs_ind = -1
	used_voxels = None
	z = 0
	for i, dct in enumerate(mask_dicts):
		print('dct', dct['NameStrings'])

		contour_idx = find_matching_contour_idx(contours, dct['NameStrings'])
		if contour_idx < 0:
			z += 1
			continue

		mdict = {}
		mdict['Name'] = contours['ROIName'][contour_idx]
		if 'heart' in dct['NameStrings']:
			print('HERE IS THE HEART')
			print(mdict['Name'])
			print(contour_idx)
		mdict['GV'] = dct['GV']
		mdict['Stationary'] = dct['Stationary']
		mdict['CardiacOutput'] = dct['CardiacOutput']

		print('Creating mask for organ %s' % mdict['Name'])

		mdict['Mask'] = contours['Segmentation'][contour_idx]
		mdict['Mask'] = ndimage.rotate(mdict['Mask'], -90, reshape=False)
		mdict['Mask'] = np.fliplr(mdict['Mask'])

		mdict['LayerSize'] = layer_size(mdict['Mask'])
		print('len bef', len(masks))
		masks.append(mdict)
		print('HERE is mdict', mdict['Name'])
		print('i:', i)
		print('len', len(masks))
		if masks[i-z]['CardiacOutput'] == -1:
			other_organs_ind = i
		else:
			if used_voxels is None:
				used_voxels = np.copy(masks[i-z]['Mask'])
			else:
				used_voxels = np.logical_or(used_voxels, masks[i-z]['Mask'])

	#Now remove duplicated voxels in other organs
	if other_organs_ind != -1:
		masks[other_organs_ind]['Mask'] = np.logical_and(
			masks[other_organs_ind]['Mask'], np.logical_not(used_voxels))

	return masks

if __name__=='__main__':

	# Parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('directory', type=str, help='The patient directory to look in')
	parser.add_argument('--output', type=str, help='Output directory for masks')
	args = parser.parse_args()

	# Where are we writing the masks?
	if args.output is None:
		mask_directory = os.path.join(args.directory, 'masks')
	else:
		mask_directory = args.output

	# Load the conouts.pickle file generated by structure_loading.py
	with open(os.path.join(args.directory, 'contours.pickle'), 'rb') as infile:
		contours = pickle.load(infile)

	# Remove any masks we don't want
	for i, nm in enumerate(contours['ROIName']):
		if nm == 'T10_POI_1' or nm == 'HeartMax_POI':
			contours['ROIName'].pop(i)

	# Generate mask_dicts containing EVERY contour in contours.pickle
	mask_dicts = []
	for roi in contours['ROIName']:
		mdict = {}
		mdict['NameStrings'] = roi
		mdict['GV'] = False
		mdict['Stationary'] = False
		mdict['CardiacOutput'] = -1
		mask_dicts.append(mdict)

	# Load CT info
	try:
		dcm_directory = find_dicom_directory(args.directory)
		ct_prefix = 'CT'
		ct_infos = [pydicom.dcmread(f) for f in find_prefixed_files(dcm_directory, ct_prefix)]
	except Exception as ex:
		print(type(ex), ex)
		print('Could not load ct info')
		exit(0)

	# Generate masks
	masks = mask_generation(contours, ct_infos, mask_dicts)

	# I'm commenting this paragraph out for now, because we're low on space on Rivanna
	# and I'm not currently using the pickle files.
	# ---------
	# # Dump masks as pickle
	# with open(os.path.join(args.directory, 'masks_in_CT_dimensions.pickle'), 'wb') as outfile:
	# 	pickle.dump(masks, outfile)

	# Write masks as NRRD for pyradiomics
	if (not(os.path.exists(mask_directory))):
		print('Creating directory ' + mask_directory)
		os.mkdir(mask_directory)
	for mask in masks:
		write_mask(mask, mask_directory)
