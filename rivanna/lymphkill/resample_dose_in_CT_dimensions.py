import os
import argparse
from sys import exit
import numpy as np
import pickle
import pydicom
import nrrd

from lymphkill.file_utils import find_prefixed_file, find_dicom_directory, find_prefixed_files, load_rtdose_files
from lymphkill.calc_blood_dose import *

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
Generate a masks structure given a set of contours and information about the dose files
Parameters:
	ct_info - Header information from a CT file (from pydicom.read)
	dose_info - Header information from a DOSE file (from pydicom.read)
	dose_grids - dose obtained (from load_rtdose_files)
Returns:
	dose - the dose grid resampled in the CT's resolution
'''
def resample_dose(
	ct_infos,
	dose_info,
	dosegrids):

	dose_grids = np.sum(dosegrids,0)

	ct_info = get_first_CT_frame(ct_infos)
	dim_vol = np.array([ct_info.Rows, ct_info.Columns, len(ct_infos)])
	dim_dos = np.array([dose_info.Rows, dose_info.Columns, dose_info.NumberOfFrames])

	#Get voxel dimensions
	dim_voxd = np.array([dose_info.PixelSpacing[0], dose_info.PixelSpacing[1], dose_info.PixelSpacing[0]])
	dim_voxv = np.array([ct_info.PixelSpacing[0], ct_info.PixelSpacing[1], ct_info.SliceThickness])

	#Get image corners
	corner_d = np.array([dose_info.ImagePositionPatient])
	corner_v = np.array([ct_info.ImagePositionPatient])

	x, y, z = np.meshgrid(np.arange(dim_vol[0]), np.arange(dim_vol[1]), np.arange(dim_vol[2]))
	#xyz =  np.transpose(np.array([x, y, z]), (2, 1, 3, 0))
	xyz_v = np.transpose(np.array([y, x, z]), (1, 2, 3, 0))


	xyz_d = (xyz_v * dim_voxv + corner_v - corner_d)/dim_voxd
	# xyz_d = xyz_d.astype(int)

	valid_voxel = np.logical_and(xyz_d[:,:,:,0] >= 0, xyz_d[:,:,:,1] >= 0)
	valid_voxel = np.logical_and(valid_voxel, xyz_d[:,:,:,2] >= 0)
	valid_voxel = np.logical_and(valid_voxel, xyz_d[:,:,:,0] < dim_dos[1])
	valid_voxel = np.logical_and(valid_voxel, xyz_d[:,:,:,1] < dim_dos[0])
	valid_voxel = np.logical_and(valid_voxel, xyz_d[:,:,:,2] < dim_dos[2])

	xyz_v = xyz_v[valid_voxel]
	xyz_d = xyz_d[valid_voxel]
	dose_v = np.zeros(dim_vol)

	# Use trilinear interpolation with the nomenclature of https://en.wikipedia.org/wiki/Trilinear_interpolation
	for (i,posv) in enumerate(xyz_v):
		xd = xyz_d[i][1] % 1
		yd = xyz_d[i][0] % 1
		zd = xyz_d[i][2] % 1

		x0 = np.clip(int(xyz_d[i][1]), 0, dim_dos[0]-1)
		y0 = np.clip(int(xyz_d[i][0]), 0, dim_dos[1]-1)
		z0 = np.clip(int(xyz_d[i][2]), 0, dim_dos[2]-1)

		x1 = np.clip(int(xyz_d[i][1])+1, 0, dim_dos[0]-1)
		y1 = np.clip(int(xyz_d[i][0])+1, 0, dim_dos[1]-1)
		z1 = np.clip(int(xyz_d[i][2])+1, 0, dim_dos[2]-1)
		
		c00 = (1-xd)*dose_grids[x0,y0,z0] + (xd)*dose_grids[x1,y0,z0]
		c01 = (1-xd)*dose_grids[x0,y0,z1] + (xd)*dose_grids[x1,y0,z1]
		c10 = (1-xd)*dose_grids[x0,y1,z0] + (xd)*dose_grids[x1,y1,z0]
		c11 = (1-xd)*dose_grids[x0,y1,z1] + (xd)*dose_grids[x1,y1,z1]

		c0 = (1-yd)*c00 + c10*yd
		c1 = (1-yd)*c01 + c11*yd

		c = (1-zd)*c0 + c1*zd

		dose_v[posv[1],posv[0],posv[2]] = c

	return dose_v

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
	# dose = np.transpose(dose,(1,0,2))

	write_dose(dose, args.directory)
