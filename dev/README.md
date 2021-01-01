## Developer tools

Hello there! So this directory just houses some tools that might come in handy for developing on `subwinder`.

### `fake_media.py`

So this little script manages creating a fake media given the expected hash and size (note this will create a file with that given size). This is useful to generate files that seem to be the desired media for searching with `MediaFile`. This script takes the entries from `media_entries.json` and generates the media to the specified output location (**Note:** This will attempt to create the files as [sparse files](https://en.wikipedia.org/wiki/Sparse_file) by calling `.truncate({size})` meaning that the physical size on disk should be much smaller then perceived, but not all programs are aware of this so copying or moving the files may result in the actual size being occupied on disk). This is mostly meant to be used where you need to test off of physical files, if this is not the case then you can build the media using `MediaFile.from_parts(...)` instead.

```text
Example Usages:
./fake_media.py
./fake_media.py --entry 0 --output-dir /tmp --entry-file /path/to/your/entry_file.json
```

### `pack_subtitles.py`

This script handles setting up subtitles in the way they get returned from the API. This involves gzipping then base64 encoding them. It just reads from stdin and then dumps the gzipped+base64 encoded contents to output.

```text
Example Usages:
echo 'Testing 1 2 3' | ./pack_subtitles.py
cat sample_subtitles.srt | ./pack_subtitles.py > packed_subtitles.srt
```
