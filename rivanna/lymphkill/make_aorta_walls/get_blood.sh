#!/bin/bash
patient=$1

patients_dir=/home/jcm6fv/scratch/PrePost

masks_dir=$patients_dir/$patient/masks

aorta=$(ls $masks_dir | grep -i aorta | grep -i blood)

echo $aorta
