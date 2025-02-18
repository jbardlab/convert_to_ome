# Example usage: python script.py file1.ome.tiff file2.ome.tiff output.ome.tiff --channel_names "My Channel 1,My Channel 2"


import os
import numpy as np
import argparse
from bioio import BioImage
from bioio.writers import OmeTiffWriter

def merge_channels(file1, file2, output_path, channel_names=None):
    """Merge two OME-TIFF files by stacking the channels together."""
    try:
        # Read both files using bioio
        im1 = BioImage(file1)  # Shape (Z, Y, X)
        im2 = BioImage(file2)  # Shape (Z, Y, X)
        data1 = im1.data.squeeze()  # Remove singleton dimensions
        data2 = im2.data.squeeze()

        # Check if both files have the same Z, Y, X dimensions
        if data1.shape != data2.shape:
            raise ValueError("The dimensions of the input files do not match.")

        # Stack the two channels along a new axis to get (C, Z, Y, X)
        merged_data = np.stack([data1, data2], axis=0)  # Shape (C, Z, Y, X)

        # Use provided channel names or default to names from input images
        if channel_names:
            channel_names_list = channel_names.split(",")
        else:
            channel_names_list = [im1.channel_names[0], im2.channel_names[0]]

        # Save the merged data as an OME-TIFF file using bioio
        OmeTiffWriter.save(
            merged_data,
            output_path,
            dim_order="CZYX",
            channel_names=channel_names_list
        )
        print(f"Merged files saved to {output_path}")
    except Exception as e:
        print(f"Failed to merge {file1} and {file2}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge two OME-TIFF channels into a single file.")
    parser.add_argument("file1", help="Path to the first OME-TIFF file.")
    parser.add_argument("file2", help="Path to the second OME-TIFF file.")
    parser.add_argument("output_path", help="Path to save the merged OME-TIFF file.")
    parser.add_argument("-c",
        "--channel_names",
        help="Comma-separated list of channel names (e.g., 'Channel 1,Channel 2'). If not provided, defaults to names from input files.",
        default=None
    )
    args = parser.parse_args()

    merge_channels(args.file1, args.file2, args.output_path, args.channel_names)
