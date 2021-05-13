#!/usr/bin/env bash
patient=$1

# patients_dir=/nv/vol141/phys_nrf/JohnMatter/patients/post_and_pre
patients_dir=/scratch/jcm6fv/PrePost

timepoints=(Pre Post1)

for t in ${timepoints[@]}; do
    patient_dir=$patients_dir/$patient/$t
    mask_dir=$patient_dir/masks
    for mask in $(ls $mask_dir/Aorta*nrrd); do
        mask=$(basename $mask)
        python calculate_radiomic_features_by_dose_bin.py $patient_dir ct_img.nrrd $mask 0 30 50 60
    done
done
