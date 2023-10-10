#!/bin/bash
set -euo pipefail

# Check for Music Library argument
MUSIC_LIB="${1:$HOME/Music/Music}"

# Change to Music Library directory or exit
cd "$MUSIC_LIB" || { echo "Failed to cd to $MUSIC_LIB"; exit 1; }

DEST="$(pwd)/Media.localized/Automatically Add to Music.localized/"
if [ ! -d "$DEST" ]; then
  DEST=""
fi

find . -name "*.flac" -print0 | while IFS= read -r -d '' FLAC_FILE; do
  ALAC_FILE="$(dirname "$FLAC_FILE")/$(basename "$FLAC_FILE" .flac).m4a"
  echo -n "Converting $FLAC_FILE ..."

  # Run the ffmpeg command
  # Why need -nostdin: https://mywiki.wooledge.org/BashFAQ/089 
  ffmpeg -y -nostdin -i "$FLAC_FILE" -acodec alac -vcodec copy "$ALAC_FILE" >/dev/null 2>&1

  exit_status=$?  # store the exit status

  if [ $exit_status -eq 0 ]; then
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


