# Utility Functions

This covers different functions that may be useful located in the `subwinder.utils` module.

```python
from subwinder.utils import extract, special_hash
```

---

### Table of Contents

* [`extract()`](#extractbytes-encoding)
* [`special_hash()`](#special_hashfilepath)

### `extract(bytes)`

Small helper function that base64 decodes and gzip decompresses `bytes`. This likely won't be useful to many people, but this is the format used to transfer subtitles and previews from the opensubtitles API.

```python
assert b"Hi!" == extract(b"H4sIAIjurl4C//PIVAQA2sWeeQMAAAA=")
```

### `special_hash(filepath)`

Hashes the file located at `filepath` using the [opensubtitles' special hash](https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes). This returns an 8 byte hex string representing the file's hash.

```python
from pathlib import Path


# Hash the provided file using the custom hash
filehash1 = special_hash("/path/to/some/file.mkv")
# Can also use a `Path`
filehash2 = special_hash(Path("/path/to/other/file.avi"))
```
