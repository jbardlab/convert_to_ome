import os
import argparse
import warnings
from bioio import BioImage
import xml.dom.minidom

# Suppress specific warning messages
warnings.filterwarnings("ignore", message="ND2File file not closed before garbage collection.")

def convert_file_to_ome(file_path, overwrite=False):
    """Convert a single ND2 or CZI file to OME-TIFF and save metadata as a separate file."""
    try:
        bio_image = BioImage(file_path)
        ome_tiff_path = f"{os.path.splitext(file_path)[0]}.ome.tif"
        metadata_path = f"{os.path.splitext(file_path)[0]}_metadata.xml"

        if os.path.exists(ome_tiff_path) and not overwrite:
            print(f"File {ome_tiff_path} already exists. Skipping conversion. Use overwrite flag -o")
            return

        # Save the image as OME-TIFF
        bio_image.save(ome_tiff_path)

        # Extract metadata and pretty-print it
        metadata = str(bio_image.metadata.to_xml())  # Convert OME object to a string
        parsed_metadata = xml.dom.minidom.parseString(metadata)
        pretty_metadata = parsed_metadata.toprettyxml(indent="  ")

        with open(metadata_path, 'w') as metadata_file:
            metadata_file.write(pretty_metadata)

        print(f"Converted: {file_path} -> {ome_tiff_path}")
    except Exception as e:
        print(f"Failed to convert {file_path}: {e}")

def convert_directory_to_ome(directory_path, overwrite=False):
    """Convert all ND2 and CZI files in a directory to OME-TIFF and save metadata."""
    for file_name in os.listdir(directory_path):
        if file_name.lower().endswith(('.nd2', '.czi')):
            file_path = os.path.join(directory_path, file_name)
            convert_file_to_ome(file_path, overwrite)

def main():
    parser = argparse.ArgumentParser(description="Convert ND2 or CZI files to OME-TIFF format and save metadata.")
    parser.add_argument("path", help="Path to the file or directory to convert.")
    parser.add_argument("-d", "--directory", action="store_true",
                        help="Specify this flag if the path is a directory.")
    parser.add_argument("-o", "--overwrite", action="store_true",
                        help="Overwrite existing OME-TIFF files if they exist.")

    args = parser.parse_args()

    if args.directory:
        if os.path.isdir(args.path):
            convert_directory_to_ome(args.path, args.overwrite)
        else:
            print(f"Error: {args.path} is not a valid directory.")
    else:
        if os.path.isfile(args.path):
            convert_file_to_ome(args.path, args.overwrite)
        else:
            print(f"Error: {args.path} is not a valid file. If it's a directory, add the -d flag.")

if __name__ == "__main__":
    main()
