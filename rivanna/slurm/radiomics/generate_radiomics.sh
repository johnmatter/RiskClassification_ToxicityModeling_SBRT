#!/bin/bash
patients=(WJ HI MB LJ)
timepoints=(Pre Post1)
patients_dir=/scratch/jcm6fv/PrePost

for patient in ${patients[@]}; do
    patient_dir=${patient}
    patient_str=${patient}
    filename=radiomics_${patient_str}.slurm

    cat ./radiomics_template_slurm.txt | \
    sed -e "s/PATIENTSTR/${patient_str}/" \
        -e "s/PATIENTDIR/${patient_dir}/" \
        > $filename
done
