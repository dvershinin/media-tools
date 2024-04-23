# src/pixwise/updater.py

import json
import os
import subprocess
import tempfile
from pathlib import Path
import pytz
import datetime
import logging
from openai import OpenAI
client = OpenAI()

log = logging.getLogger(__name__)

DEFAULT_TIMEZONE = pytz.timezone('Europe/Moscow')

def get_file_metadata(file_path):
    """
    Retrieves the metadata of a file in JSON format using exiftool.

    Args:
        file_path (str): The path to the file whose metadata is to be retrieved.

    Returns:
        dict: A dictionary containing the metadata of the file, or None if an error occurs.
    """
    try:
        # Adding '-json' flag to command
        cmd = ['exiftool', '-json', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # The output is a JSON string in a list, so parse it and get the first item
        metadata_list = json.loads(result.stdout)

        # if the file is a video file, extract audio to a temporary file
        if metadata_list[0].get("MIMEType") == "video/mp4":
            # using tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                audio_file_path = temp_audio.name
                cmd = ['ffmpeg', '-i', file_path, '-vn', '-acodec', 'libmp3lame', '-y', audio_file_path]
                subprocess.run(cmd, check=True)
                print(f"Extracted audio to {audio_file_path}")
                audio_file = open(audio_file_path, "rb")
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                print(transcription.text)

        if metadata_list:
            return metadata_list[
                0]  # Assuming there's only one file processed, return its metadata
        else:
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving metadata: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None


def load_google_json(json_path):
    """
    Load Google Photos JSON file and return the data as a dictionary
    with datetime formats acceptable by `exiftool`.

    Args:
        json_path (str): The path to the Google JSON file to load.

    Returns:
        dict: A dictionary containing the data from the Google JSON file.
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
        if 'imageViews' not in data:
            log.warning(
                f"JSON data for {json_path} does not contain imageViews fields. Likely not a Google export file. Skipping.")
            return None
        # This mostly confirms to original file's EXIF taken time
        taken_time = int(data.get('photoTakenTime', {}).get('timestamp'))
        print(f"Taken time: {taken_time}")
        # It is already time-aware, so no need to localize, just format for exiftool UTC (without timezone)
        # load this time into UTC timezone
        # format for exiftool
        data['normalized_taken_time_utc_no_tz'] = datetime.datetime.utcfromtimestamp(taken_time).strftime(
            "%Y:%m:%d %H:%M:%S"
        )
        return data

def update_media_metadata(directory, dry_run=False):
    """Updates media files metadata based on corresponding JSON files."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.endswith('.json'):
                continue
            print(f"===================================== Processing {file} =====================================")
            json_path = Path(root) / file
            media_path = json_path.with_suffix('')
            google_data = load_google_json(json_path)
            print(f"Google data: {google_data}")
            if not google_data:
                log.warning(f"Skipping {json_path}")
                continue

            if media_path.exists():
                print(f"Found media file for {json_path}")
                # Get current metadata from media file using exiftool
                current_metadata = get_file_metadata(media_path)
                if not current_metadata:
                    print(f"Could not retrieve any metadata for {media_path}")
                    continue
                # pretty print current metadata for media file
                print(f"Current metadata for {media_path}: {json.dumps(current_metadata, indent=4)}")

                # pretyprint json data alongside current metadata
                print(f"JSON data for {json_path}: {json.dumps(json_data, indent=4)}")

                update_metadata = {}
                if current_metadata.get("MIMEType") == "video/mp4":
                    pass
                elif current_metadata.get("MIMEType") == "image/png":
                    # DateCreated seems to be Apple convention for creation time of PNG files
                    # So we should use that
                    if 'DateCreated' not in current_metadata and 'photoTakenTime' in json_data:
                        # Assuming json_data['creationTime']['timestamp'] is a Unix timestamp
                        date_created_ts = int(json_data['photoTakenTime']['timestamp'])
                        # Convert Unix timestamp to datetime in UTC
                        utc_dt = datetime.datetime.utcfromtimestamp(date_created_ts)

                        # Convert UTC datetime to specified default timezone
                        adjusted_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(
                            DEFAULT_TIMEZONE)

                        # Format datetime for exiftool, and ensure timezone is included
                        date_created_ts_str = adjusted_dt.strftime(
                            "%Y:%m:%d %H:%M:%S%z"
                        )

                        # Update the metadata dictionary
                        update_metadata['DateCreated'] = date_created_ts_str
                    if "title" in json_data and json_data["title"] != current_metadata.get("FileName") and not current_metadata.get("Title"):
                        # Apple uses Title for "Title""
                        update_metadata['Title'] = json_data['title']
                print("Update metadata: ", update_metadata)

                # Implement JSON parsing and exiftool updating logic here
                # Placeholder for actual implementation
                if not dry_run:
                    if update_metadata:
                        log.info(f"Updating metadata for {media_path}")
                    else:
                        log.info(f"No metadata to update for {media_path}")
                    # unlink the JSON file
                    log.info(f"Deleting JSON file {json_path}")
                    # json_path.unlink()
                else:
                    print(f"Dry run: metadata for {media_path} would be updated")
            else:
                log.info(f"No corresponding media file for {json_path}. Deleting JSON file.")
                if not dry_run:
                    # json_path.unlink()
                    pass
            break


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Update media files metadata from JSON.")
    parser.add_argument("--directory", help="Directory to scan for JSON and media files.", required=False)
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate the update process.")
    args = parser.parse_args()

    # default to current directory
    if not args.directory:
        args.directory = os.getcwd()

    # set up logging
    logging.basicConfig(level=logging.INFO)

    update_media_metadata(args.directory, args.dry_run)


if __name__ == "__main__":
    main()
