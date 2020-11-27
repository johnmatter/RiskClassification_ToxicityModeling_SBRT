patient=$1
patients_dir=/nv/vol141/phys_nrf/JohnMatter/patients
# python structure_loading.py $patients_dir/${patient}
# python write_ct_as_nrrd.py $patients_dir/${patient}
# python resample_dose_in_CT_dimensions.py $patients_dir/${patient}
# python mask_generation_with_CT_dimensions.py $patients_dir/${patient}
# python calc_dose.py $patients_dir/${patient}

mask_list=${patients_dir}/${patient}/selected_masks.txt
for mask in $(cat $mask_list); do
    echo
    echo $mask
    python calculate_radiomic_features_as_function_of_dose.py ${patients_dir}/$patient ct_img.nrrd $mask 0 60 5
done
