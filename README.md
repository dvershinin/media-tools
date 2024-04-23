# media-tools

## Recipes

### Convert old MTS files to MP4

This is useful for e.g. importing to Apple Photos.
The command will convert all MTS files in the current directory to MP4.

```bash
for f in *; do 
    ffmpeg -i "$f" -c copy -map_metadata 0 "${f%.MTS}.mp4" && 
    exiftool -overwrite_original -tagsFromFile "$f" -time:all "${f%.MTS}.mp4"; 
done
```

It retains the original metadata and copies it to the new MP4 file.

## TODO

* Automatically enrich MP4 metadata using OpenAI [Speech to text](https://platform.openai.com/docs/guides/speech-to-text).
