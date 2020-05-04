import base64
import gzip
from pathlib import Path

from subwinder.exceptions import SubHashError


def extract(bytes, encoding):
    """
    Extract `bytes` from being gzip'd and base64 encoded.
    """
    compressed = base64.b64decode(bytes)
    return gzip.decompress(compressed).decode(encoding)


# As per API spec with some tweaks to make it a bit nicer
# https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
def special_hash(filepath):
    """
    The "special hash" used by opensubtitles representing a specific media file.
    """
    CHUNK_SIZE_BYTES = 64 * 1024
    FILE_MIN_SIZE = CHUNK_SIZE_BYTES * 2

    # Force `filepath` to be `Path`
    filepath = Path(filepath)

    with filepath.open("rb") as file:
        filesize = filepath.stat().st_size
        hasher = _SumHasher(filesize)

        if filesize < FILE_MIN_SIZE:
            raise SubHashError(f"Filesize is below minimum of {FILE_MIN_SIZE} bytes")

        # Hash the first chunk of the file
        hasher.update(file.read(CHUNK_SIZE_BYTES))
        # and the last chunk
        file.seek(-CHUNK_SIZE_BYTES, 2)
        hasher.update(file.read(CHUNK_SIZE_BYTES))

    return hasher.digest()


class _SumHasher:
    def __init__(self, filesize):
        self.hash = filesize
        self.digest_size = 8
        self.block_size = 8

    def update(self, values):
        for i in range(0, len(values), self.block_size):
            chunk = values[i : i + self.block_size]
            self.hash += int.from_bytes(chunk, byteorder="little")

    def digest(self):
        # Keep output in `self.digest_size`
        temp = self.hash & 2 ** (self.digest_size * 8) - 1
        return f"{temp:016x}"
