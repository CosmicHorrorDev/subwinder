## Developer tools

Hello there! So this directory just houses some tools that might come in handy for developing on `subwinder`.

### `fake_media.py`

So this little script manages creating a fake media given the expected hash and size (note this will create a file with that given size). This is useful to generate files that seem to be the desired media for searching with `Media`. This script takes the entries from `media_entries.json` and generates the media to the specified output location (**Note:** This will attempt to create the files as [sparse files](https://en.wikipedia.org/wiki/Sparse_file) by calling `.truncate({size})` meaning that the physical size on disk should be much smaller then perceived, but not all programs are aware of this so copying or moving the files may result in the actual size being occupied on disk). This is mostly meant to be used where you need to test off of physical files, if this is not the case then you can build the media using `Media.from_parts(...)` instead.

```text
Example Usages:
./fake_media.py fake_media_entries.json
./fake_media.py --entry 0 --output-dir /tmp fake_media_entries.json
```
