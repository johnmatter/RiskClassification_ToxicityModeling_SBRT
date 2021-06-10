#!/bin/bash
patient=$1
patients_dir=/home/jcm6fv/scratch/PrePost

aorta=$(./get_aorta.sh $patient)
blood=$(./get_blood.sh $patient)

python make_aorta_wall.py $patients_dir/$patient/masks --aorta $aorta --blood $blood
