import base64
import gzip

from subwinder.exceptions import SubHashError


def extract(bytes, encoding):
    compressed = base64.b64decode(bytes)
    return gzip.decompress(compressed).decode(encoding)


# As per API spec with some tweaks to make it a bit nicer
# https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
def special_hash(filepath):
    CHUNK_SIZE_BYTES = 64 * 1024
    # HASH_SIZE_BYTES = 8
    FILE_MIN_SIZE = CHUNK_SIZE_BYTES * 2

    with filepath.open("rb") as f:
        filesize = filepath.stat().st_size
        # filehash = filesize
        hasher = _SumHasher(filesize)

        if filesize < FILE_MIN_SIZE:
            raise SubHashError(f"Filesize is below minimum of {FILE_MIN_SIZE} bytes")

        for i in range(2):
            # Seek to 64KiB before the end on second pass
            if i == 1:
                f.seek(-CHUNK_SIZE_BYTES, 2)

            # Process each chunk of the file
            chunk = f.read(CHUNK_SIZE_BYTES)
            hasher.update(chunk)

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
