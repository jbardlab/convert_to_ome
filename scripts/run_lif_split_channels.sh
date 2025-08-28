#!/bin/bash

# Configuration variables - modify these paths and settings as needed
DOCKER_IMAGE_REMOTE="ghcr.io/jbardlab/convert_to_ome:latest"
DOCKER_IMAGE_LOCAL="convert_to_ome:latest"
SCRIPT_PATH="/Users/jbard/Library/CloudStorage/SynologyDrive-home/repos/convert_to_ome/functions/lif_split_channels_to_ome.py"
INPUT_LIF_FILE="/Users/jbard/Library/CloudStorage/SynologyDrive-Shared/Data/MaxineC/OMAP-Microscopy results/250820_leica/250820.lif"
OUTPUT_FOLDER="/Users/jbard/Library/CloudStorage/SynologyDrive-home/repos/convert_to_ome/test"
CHANNEL_NAMES="DAPI,Cy3,Cy5"  # Comma-separated channel names, or leave empty for auto-detection

# Optional parameters
BIGTIFF_FLAG=""              # Set to "--bigtiff" if you want to force BigTIFF writing
DTYPE="native"              # Options: native, uint16, uint8, float32
INCLUDE_EMPTY_FLAG=""       # Set to "--include-empty" to keep empty scenes

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to pull Docker image if it doesn't exist locally
pull_image_if_needed() {
    echo "Checking if Docker image exists locally..."
    if ! docker image inspect "$DOCKER_IMAGE_LOCAL" > /dev/null 2>&1; then
        echo "Docker image not found locally. Pulling from registry and renaming..."
        echo "Note: On Mac, pulling for linux/amd64 platform..."
        if ! docker pull --platform linux/amd64 "$DOCKER_IMAGE_REMOTE"; then
            echo "Error: Failed to pull Docker image. Please check your internet connection and Docker login."
            exit 1
        fi
        # Tag the pulled image with the local name
        if ! docker tag "$DOCKER_IMAGE_REMOTE" "$DOCKER_IMAGE_LOCAL"; then
            echo "Error: Failed to tag Docker image with local name."
            exit 1
        fi
        echo "Successfully pulled and tagged Docker image as: $DOCKER_IMAGE_LOCAL"
    else
        echo "Docker image found locally: $DOCKER_IMAGE_LOCAL"
    fi
}

# Function to validate input file exists
validate_input() {
    if [[ ! -f "$INPUT_LIF_FILE" ]]; then
        echo "Error: Input LIF file does not exist: $INPUT_LIF_FILE"
        echo "Please update the INPUT_LIF_FILE variable with the correct path."
        exit 1
    fi
    
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        echo "Error: Python script does not exist: $SCRIPT_PATH"
        echo "Please update the SCRIPT_PATH variable with the correct path."
        exit 1
    fi
    
    # Get the directory containing the input file (properly handle spaces)
    INPUT_DIR=$(dirname "$INPUT_LIF_FILE")
    INPUT_DIR=$(realpath "$INPUT_DIR")
    INPUT_FILENAME=$(basename "$INPUT_LIF_FILE")
    
    # Get the directory containing the script and script filename
    SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
    SCRIPT_DIR=$(realpath "$SCRIPT_DIR")
    SCRIPT_FILENAME=$(basename "$SCRIPT_PATH")
    
    echo "Input file: $INPUT_LIF_FILE"
    echo "Input directory: $INPUT_DIR"
    echo "Input filename: $INPUT_FILENAME"
    echo "Script file: $SCRIPT_PATH"
    echo "Script directory: $SCRIPT_DIR"
    echo "Script filename: $SCRIPT_FILENAME"
}

# Function to create output directory if it doesn't exist
prepare_output() {
    if [[ ! -d "$OUTPUT_FOLDER" ]]; then
        echo "Creating output directory: $OUTPUT_FOLDER"
        mkdir -p "$OUTPUT_FOLDER"
    fi
    
    # Get absolute path for output folder (properly handle spaces)
    OUTPUT_DIR=$(realpath "$OUTPUT_FOLDER")
    echo "Output directory: $OUTPUT_DIR"
}

# Function to build the Docker command
build_docker_command() {
    # Use arrays to properly handle spaces in paths
    local docker_args=(
        "run" "--rm" "-t" "--platform" "linux/amd64"
        "-v" "$INPUT_DIR:/input"
        "-v" "$OUTPUT_DIR:/output"
        "-v" "$SCRIPT_DIR:/scripts"
        "$DOCKER_IMAGE_LOCAL"
        "python" "-u" "/scripts/$SCRIPT_FILENAME"
        "/input/$INPUT_FILENAME"
        "--outdir" "/output"
    )
    
    # Add channel names if specified
    if [[ -n "$CHANNEL_NAMES" ]]; then
        docker_args+=("--channel-names" "$CHANNEL_NAMES")
    fi
    
    # Add optional flags
    if [[ -n "$BIGTIFF_FLAG" ]]; then
        docker_args+=("$BIGTIFF_FLAG")
    fi
    
    if [[ "$DTYPE" != "native" ]]; then
        docker_args+=("--dtype" "$DTYPE")
    fi
    
    if [[ -n "$INCLUDE_EMPTY_FLAG" ]]; then
        docker_args+=("$INCLUDE_EMPTY_FLAG")
    fi
    
    if [[ -n "$QUIET_FLAG" ]]; then
        docker_args+=("$QUIET_FLAG")
    fi
    
    # Store the command array globally for execution
    DOCKER_CMD_ARRAY=("${docker_args[@]}")
}

# Main execution
main() {
    echo "=== LIF Split Channels to OME Script ==="
    echo "Remote Docker Image: $DOCKER_IMAGE_REMOTE"
    echo "Local Docker Image: $DOCKER_IMAGE_LOCAL"
    echo "Script: $SCRIPT_PATH"
    echo ""
    
    # Check if configuration variables are set
    if [[ "$INPUT_LIF_FILE" == "/path/to/your/input/file.lif" ]] || [[ "$OUTPUT_FOLDER" == "/path/to/your/output/folder" ]]; then
        echo "Error: Please update the configuration variables at the top of this script:"
        echo "  - INPUT_LIF_FILE: path to your .lif file"
        echo "  - OUTPUT_FOLDER: directory where output files will be saved"
        echo "  - CHANNEL_NAMES: comma-separated channel names (optional)"
        exit 1
    fi
    
    # Run checks and preparations
    check_docker
    pull_image_if_needed
    validate_input
    prepare_output
    
    # Create log file path early and log initial info
    LOG_FILE="$OUTPUT_DIR/lif_split_$(date +%Y%m%d_%H%M%S).log"
    
    # Log initial configuration to file
    {
        echo "=== LIF Split Channels to OME - Log Started ==="
        echo "Date: $(date)"
        echo "Input file: $INPUT_LIF_FILE"
        echo "Output directory: $OUTPUT_DIR"
        echo "Script path: $SCRIPT_PATH"
        echo "Channel names: $CHANNEL_NAMES"
        echo "Docker image: $DOCKER_IMAGE_LOCAL"
        echo "=================================="
        echo ""
    } > "$LOG_FILE"
    
    # Build and execute the Docker command
    echo ""
    echo "Building Docker command..."
    build_docker_command
    
    echo "Executing command:"
    echo "docker ${DOCKER_CMD_ARRAY[*]}"
    echo "Log file: $LOG_FILE"
    echo ""
    echo "=== Docker Output ==="
    
    # Simple approach: run docker command and let it output directly to terminal
    # Then capture the exit code and append a summary to log file
    docker "${DOCKER_CMD_ARRAY[@]}"
    DOCKER_EXIT_CODE=$?
    
    # Log the command and exit code to file
    {
        echo "Command executed: docker ${DOCKER_CMD_ARRAY[*]}"
        echo "Exit code: $DOCKER_EXIT_CODE"
        echo "Completed at: $(date)"
    } >> "$LOG_FILE"
    
    # Log completion status
    {
        echo ""
        echo "=== Process completed at $(date) ==="
        echo "Exit code: $DOCKER_EXIT_CODE"
    } >> "$LOG_FILE"
    
    if [[ $DOCKER_EXIT_CODE -eq 0 ]]; then
        echo ""
        echo "=== Script completed successfully! ==="
        echo "Output files should be in: $OUTPUT_DIR"
        echo "Log file saved to: $LOG_FILE"
    else
        echo ""
        echo "=== Script failed with errors ==="
        echo "Check the log file for details: $LOG_FILE"
        exit 1
    fi
}

# Show usage if --help is passed
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0"
    echo ""
    echo "This script runs lif_split_channels_to_ome.py using the convert_to_ome Docker container."
    echo "The local Python script will be mounted and used instead of the container's version."
    echo ""
    echo "Configuration:"
    echo "  Edit the variables at the top of this script to set:"
    echo "  - SCRIPT_PATH: path to your local lif_split_channels_to_ome.py script"
    echo "  - INPUT_LIF_FILE: path to your input .lif file"
    echo "  - OUTPUT_FOLDER: directory for output files"
    echo "  - CHANNEL_NAMES: comma-separated channel names (optional)"
    echo "  - BIGTIFF_FLAG: set to '--bigtiff' to force BigTIFF writing"
    echo "  - DTYPE: data type conversion (native, uint16, uint8, float32)"
    echo "  - INCLUDE_EMPTY_FLAG: set to '--include-empty' to keep empty scenes"
    echo "  - QUIET_FLAG: set to '--quiet' to reduce logging"
    echo ""
    echo "The script will:"
    echo "  1. Check if Docker is running"
    echo "  2. Pull the Docker image if not present locally"
    echo "  3. Validate input file and script exist"
    echo "  4. Create output directory if needed"
    echo "  5. Mount and run your local lif_split_channels_to_ome.py script in the container"
    echo ""
    echo "Example configuration:"
    echo "  SCRIPT_PATH=\"/Users/username/repos/convert_to_ome/functions/lif_split_channels_to_ome.py\""
    echo "  INPUT_LIF_FILE=\"/Users/username/data/experiment.lif\""
    echo "  OUTPUT_FOLDER=\"/Users/username/output\""
    echo "  CHANNEL_NAMES=\"DAPI,GFP,RFP\""
    exit 0
fi

# Run the main function
main
