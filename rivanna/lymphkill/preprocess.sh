patient=$1
# patients_dir=/nv/vol141/phys_nrf/JohnMatter/patients/pre_only
patients_dir=/nv/vol141/phys_nrf/JohnMatter/patients/post_and_pre
python write_ct_as_nrrd.py $patients_dir/${patient}
python convert_velocity_resampled_dose.py $patients_dir/${patient}
python structure_loading.py $patients_dir/${patient}
python mask_generation_with_CT_dimensions.py $patients_dir/${patient}
