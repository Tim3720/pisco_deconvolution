#! /usr/bin/env bash

set -e

# Script directory (where flake.nix should be)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
DEFAULT_PROCESSES=4
CONFIG_FILE=""
EXECUTABLE="./deconvolution.py"
NUM_PROCESSES=""
FLAKE_ATTR=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -e|--executable)
            EXECUTABLE="$2"
            shift 2
            ;;
        -n|--processes)
            NUM_PROCESSES="$2"
            shift 2
            ;;
        -f|--flake)
            FLAKE_ATTR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --config FILE      Configuration file (required)"
            echo "  -e, --executable PATH  Path to executable (default: ./config_parser)"
            echo "  -n, --processes NUM    Number of MPI processes (overrides config)"
            echo "  -f, --flake ATTR       Flake attribute (default: .#devShells.x86_64-linux.default)"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            if [[ -z "$CONFIG_FILE" ]]; then
                CONFIG_FILE="$1"
            fi
            shift
            ;;
    esac
done

# Check if config file is provided
if [[ -z "$CONFIG_FILE" ]]; then
    echo "Error: Configuration file is required."
    echo "Usage: $0 -c <config_file> [-n <num_processes>]"
    exit 1
fi

# Resolve config file path
if [[ ! "$CONFIG_FILE" = /* ]]; then
    CONFIG_FILE="$SCRIPT_DIR/$CONFIG_FILE"
fi

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Configuration file '$CONFIG_FILE' not found."
    exit 1
fi

# Resolve executable path
if [[ ! "$EXECUTABLE" = /* ]]; then
    EXECUTABLE="$SCRIPT_DIR/$EXECUTABLE"
fi

# Check if executable exists
if [[ ! -f "$EXECUTABLE" ]]; then
    echo "Error: Executable '$EXECUTABLE' not found."
    echo "Please build the project first."
    exit 1
fi

# Check if flake.nix exists
if [[ ! -f "$SCRIPT_DIR/flake.nix" ]]; then
    echo "Error: flake.nix not found in $SCRIPT_DIR"
    exit 1
fi

# Extract numProcesses from config file if not specified via command line
if [[ -z "$NUM_PROCESSES" ]]; then
    NUM_PROCESSES=$(grep -i "^numProcesses" "$CONFIG_FILE" | \
                   sed 's/.*=\s*//' | \
                   sed 's/\s*#.*//' | \
                   tr -d '[:space:]')
    
    if [[ -z "$NUM_PROCESSES" ]] || ! [[ "$NUM_PROCESSES" =~ ^[0-9]+$ ]]; then
        echo "Warning: numProcesses not found in config file. Using default: $DEFAULT_PROCESSES"
        NUM_PROCESSES=$DEFAULT_PROCESSES
    fi
fi

# Validate numProcesses
if ! [[ "$NUM_PROCESSES" =~ ^[0-9]+$ ]] || [[ "$NUM_PROCESSES" -lt 1 ]]; then
    echo "Error: Invalid number of processes: $NUM_PROCESSES"
    exit 1
fi

# Set default flake attribute if not specified
if [[ -z "$FLAKE_ATTR" ]]; then
    FLAKE_ATTR="$SCRIPT_DIR/flake.nix"
fi

echo "=== MPI Runner ==="
echo "Script directory: $SCRIPT_DIR"
echo "Config file: $CONFIG_FILE"
echo "Executable: $EXECUTABLE"
echo "Processes: $NUM_PROCESSES"
echo "Flake: $FLAKE_ATTR"
echo ""

# Run the program within the nix develop environment
nix develop "$FLAKE_ATTR" --command \
    python "$EXECUTABLE" "$CONFIG_FILE"

EXIT_STATUS=$?

if [[ $EXIT_STATUS -eq 0 ]]; then
    echo ""
    echo "Program completed successfully."
else
    echo ""
    echo "Program failed with exit status: $EXIT_STATUS"
fi

exit $EXIT_STATUS
