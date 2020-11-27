#!/bin/bash
patients=(FH HD PG RS VL)
patients_dir=/home/jcm6fv/phys_nrf/patients

for patient in ${patients[@]}; do
    # python flip_masks.py $patients_dir/$patient

    mask_dir=$patients_dir/$patient/masks
    mkdir $mask_dir/unflipped
    mv $mask_dir/*.nrrd $mask_dir/unflipped
    for mask in $(ls $mask_dir/flipped/*nrrd); do
        echo ln -s $mask $mask_dir/
        ln -s $mask $mask_dir/
    done
done
