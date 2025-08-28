#!/bin/bash

# replace file paths below
repo_path="/Users/jbard/Library/CloudStorage/OneDrive-TexasA&MUniversity/repos/convert_to_ome"

file_path="/Users/jbard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents - Team - Bard Lab/Data/JaredB/Microscopy/test/"

# Iterate over dw_Sample files matching the pattern
for file1 in "${file_path}"/dw_Sample*.ome.tif_ch561*.tiff; do
    # Extract the file name from the path
    file1_name=$(basename "$file1")

    # Derive the corresponding Sample file name by replacing dw_Sample with Sample and 561 with 405
    file2_name="${file1_name/dw_Sample/Sample}"
    file2_name="${file2_name/561/405}"
    file2="${file_path}${file2_name}"

    # Check if the corresponding file exists
    if [[ -f "${file2}" ]]; then
        # Construct the output file name using only the file name
        output_file="$merged_${file1_name/dw_/}"

        # Run the Python script to merge the channels (use full paths)
        pixi run --manifest-path "$env_path/pixi.toml" python "${env_path}/scripts/merge_channels.py" "$file1" "$file2" "${file_path}/$output_file" -c "ch405,ch561_decon"
    else
        echo "Matching $file2_name for $file1_name not found."
    fi
done
