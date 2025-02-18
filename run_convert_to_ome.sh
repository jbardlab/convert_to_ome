#!/bin/bash

# replace paths with those on your computer
repo_path="/Users/jbard/Library/CloudStorage/OneDrive-TexasA&MUniversity/repos/convert_to_ome"
pixi_path="${repo_path}/pixi.toml"
script_path="${repo_path}/convert_to_ome.py"
nd2_directory="/Users/jbard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents - Team - Bard Lab/Data/JaredB/Microscopy/test/"

pixi run --manifest-path "${pixi_path}" python "${script_path}" "${nd2_directory}" -d
