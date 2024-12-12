#!/bin/bash
set -euxo pipefail

# Function to display help message
print_help() {
  cat << EOF
Usage: alacify [OPTIONS] [FILE|DIRECTORY]

Options:
  --help      Show this help message and exit

Arguments:
  FILE        Convert a single FLAC file to ALAC
  DIRECTORY   Convert all FLAC files in the directory to ALAC (default: \$HOME/Music/Music)

Examples:
  alacify --help
  alacify /path/to/library
  alacify /path/to/file.flac
EOF
}

# Initialize variables
PROCESS_FILE=false
PROCESS_DIR=false
MUSIC_LIB="$HOME/Music/Music"

# Parse arguments
if [ $# -gt 0 ]; then
  case "$1" in
    --help)
      print_help
      exit 0
      ;;
    -*)
      echo "Unknown option: $1"
      print_help
      exit 1
      ;;
    *)
      ARG="$1"
      if [ -d "$ARG" ]; then
        MUSIC_LIB="$ARG"
        PROCESS_DIR=true
      elif [ -f "$ARG" ]; then
        FLAC_FILE="$ARG"
        PROCESS_FILE=true
      else
        echo "Error: '$ARG' is not a valid file or directory."
        exit 1
      fi
      ;;
  esac
fi

DEST=""

if [ "$PROCESS_DIR" = true ]; then
  # Change to Music Library directory or exit
  cd "$MUSIC_LIB" || { echo "Failed to cd to $MUSIC_LIB"; exit 1; }

  DEST="$(pwd)/Media.localized/Automatically Add to Music.localized/"
  if [ ! -d "$DEST" ]; then
    DEST=""
  fi
fi

# Function to convert a single FLAC file
convert_file() {
  local FLAC="$1"
  local ALAC="$(dirname "$FLAC")/$(basename "$FLAC" .flac).m4a"

  echo -n "Converting single '$FLAC' ... "

  if ffmpeg -y -nostdin -i "$FLAC" -acodec alac -vcodec copy "$ALAC"; then
    echo -e "Converted to '$ALAC' [✔]"
    rm -f "$FLAC"
  else
    echo -e "Conversion failed for '$FLAC' [✘]"
  fi
}

# Process a single file
if [ "$PROCESS_FILE" = true ]; then
  convert_file "$FLAC_FILE"
  exit 0
fi

find . -name "*.flac" -print0 | while IFS= read -r -d '' FLAC_FILE; do
  ALAC_FILE="$(dirname "$FLAC_FILE")/$(basename "$FLAC_FILE" .flac).m4a"
  echo -n "Converting $FLAC_FILE ..."

  # Run the ffmpeg command
  # Why need -nostdin: https://mywiki.wooledge.org/BashFAQ/089
  if ffmpeg -y -nostdin -i "$FLAC_FILE" -acodec alac -vcodec copy "$ALAC_FILE" >/dev/null 2>&1; then
    # Move to the beginning of the line, clear to the end of the line and print with a checkmark
    echo -e "\r\033[KConverted to $ALAC_FILE [✔]"
    # Delete the original .flac file
    rm -f "$FLAC_FILE"
    # If the FLAC file was in "/Not Added.localized/" then move the ALAC file
    if [[ -n "$DEST" && "$FLAC_FILE" == *"/Not Added.localized/"* ]]; then
      mv "$ALAC_FILE" "$DEST"
    fi
  else
    echo -e "\r\033[KConversion failed for $FLAC_FILE [✘]"
  fi
  # Break after the first iteration for testing
  # break
done
