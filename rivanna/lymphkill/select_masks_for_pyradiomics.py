import os
import argparse

from PyInquirer import prompt, style_from_dict, Token, Separator
from file_utils import find_postfixed_files

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('directory', type=str, help='The patient directory to look in')
args = parser.parse_args()

# Get all masks
all_masks = find_postfixed_files(os.path.join(args.directory,"masks"), "nrrd")

# Filter masks to heart and great vessels
mask_filters = ['pa', 'pulm', 'vc', 'vena', 'aorta', 'heart']
filtered_masks = []
for mask in all_masks:
    if any([substr in os.path.basename(mask).lower() for substr in mask_filters]):
        filtered_masks.append(mask)

# Basic info needed for PyInquirer prompt
questions = [{'type':'checkbox', 'message':'Select masks', 'name':'selected_masks'}]

questions[0]['choices'] = []
for mask in filtered_masks:
        questions[0]['choices'].append({'name': os.path.basename(mask)})

selected_masks = prompt(questions)

with open(os.path.join(args.directory,"selected_masks.txt"), "w") as txt_file:
    [txt_file.write(mask+'\n') for mask in selected_masks['selected_masks']]
    txt_file.close()
