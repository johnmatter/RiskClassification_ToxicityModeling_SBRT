#!/bin/bash
patients=(WJ HI)
timepoints=(Pre Post1)
patients_dir=/scratch/jcm6fv/PrePost

for patient in ${patients[@]}; do
    for t in ${timepoints[@]}; do
        python lymphkill/flip_and_fill_masks.py $patients_dir/$patient/$t

        mask_dir=$patients_dir/$patient/$t/masks
        for mask in $(ls $mask_dir/flipped_and_filled/*nrrd); do
            echo ln -s $mask $mask_dir/
            ln -s $mask $mask_dir/
        done
    done
done
