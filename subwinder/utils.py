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
    HASH_SIZE_BYTES = 8
    FILE_MIN_SIZE = CHUNK_SIZE_BYTES * 2

    with filepath.open("rb") as f:
        filesize = filepath.stat().st_size
        filehash = filesize

        if filesize < FILE_MIN_SIZE:
            raise SubHashError(f"Filesize is below minimum of {FILE_MIN_SIZE} bytes")

        for i in range(2):
            # Seek to 64KiB before the end on second pass
            if i == 1:
                f.seek(-CHUNK_SIZE_BYTES, 2)

            # Read the first 64 KiB summing every 8 bytes
            for _ in range(CHUNK_SIZE_BYTES // HASH_SIZE_BYTES):
                buffer = f.read(HASH_SIZE_BYTES)
                filehash += int.from_bytes(buffer, byteorder="little")

    # Keep output in `HASH_SIZE_BYTES`
    filehash &= 2 ** (HASH_SIZE_BYTES * 8) - 1
    return f"{filehash:016x}"
