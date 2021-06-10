#!/bin/bash
patients=(WJ HI MB LJ)
timepoints=(Pre Post1)
patients_dir=/scratch/jcm6fv/PrePost

for patient in ${patients[@]}; do
    for timepoint in ${timepoints[@]}; do
        patient_dir=${patient}\\/${timepoint}
        patient_str=${patient}_${timepoint}
        filename=preprocess_${patient_str}.slurm

        cat ./preprocess_template_slurm.txt | \
        sed -e "s/PATIENTSTR/${patient_str}/" \
            -e "s/PATIENTDIR/${patient_dir}/" \
            > $filename

    done
done
