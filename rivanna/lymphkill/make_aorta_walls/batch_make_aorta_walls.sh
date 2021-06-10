#!/bin/bash
patients=(WJ HI MB LJ)
timepoints=(Pre Post1)
patients_dir=/scratch/jcm6fv/PrePost

for patient in ${patients[@]}; do
    for timepoint in ${timepoints[@]}; do
        echo Making aorta wall for $patient $timepoint
        ./make_aorta_wall.sh $patient/$timepoint
    done
done
