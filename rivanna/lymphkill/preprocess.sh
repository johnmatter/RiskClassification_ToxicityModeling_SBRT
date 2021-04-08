#!/usr/bin/env bash
patient=$1
patients_dir=/nv/vol141/phys_nrf/JohnMatter/patients/post_and_pre
python write_ct_as_nrrd.py $patients_dir/${patient}
python convert_velocity_resampled_dose.py $patients_dir/${patient}
python structure_loading.py $patients_dir/${patient} --prefix struct
python mask_generation_with_CT_dimensions.py $patients_dir/${patient}

mkdir -p $patients_dir/${patient}/masks/original
cp $patients_dir/${patient}/masks/*.nrrd $patients_dir/${patient}/masks/original

python fill_masks.py $patients_dir/${patient}
cp $patients_dir/${patient}/masks/filled/*.nrrd $patients_dir/${patient}/masks/

python flip_masks.py $patients_dir/${patient}
cp $patients_dir/${patient}/masks/flipped/*.nrrd $patients_dir/${patient}/masks/

mv $patients_dir/${patient}/masks/flipped/ $patients_dir/${patient}/masks/filled_then_flipped
