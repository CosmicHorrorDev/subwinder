## Developer tools

Hello there! So this directory just houses some tools that might come in handy for developing on `subwinder`.

### `fake_media.py`

So this little script manages creating a fake media given the expected hash and size (note this will create a file with that given size). This is useful to generate files that seem to be the desired media for searching with `Media`. This script takes the entries from `media_entries.json` and generates the media to the specified output location (**Note:** this produces a GBs of data so just take that into account).

```text
Example Usages:
./fake_media.py fake_media_entries.json
./fake_media.py --entry 0 --output-dir /tmp fake_media_entries.json
```
