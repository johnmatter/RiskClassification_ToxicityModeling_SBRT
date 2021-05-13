#!/usr/bin/env bash
patient=$1

patients_dir=/scratch/jcm6fv/PrePost

python write_ct_as_nrrd.py $patients_dir/${patient}

python convert_velocity_resampled_dose.py $patients_dir/${patient}

python structure_loading.py $patients_dir/${patient} --prefix struct
python mask_generation_with_CT_dimensions.py $patients_dir/${patient}

# Flip and fill masks
python flip_and_fill_masks.py $patients_dir/$patient
mask_dir=$patients_dir/$patient/masks
for mask in $(ls $mask_dir/flipped_and_filled/*nrrd); do
    echo ln -s $mask $mask_dir/
    ln -s $mask $mask_dir/
done

# Create flipped versions that aren't filled
python flip_masks.py $patients_dir/$patient/ --subdirectory original --no-archive
