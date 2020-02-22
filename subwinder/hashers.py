import hashlib
import os

from subwinder.exceptions import SubHashError


# As per API spec with some tweaks to make it a bit nicer
# https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
def special_hash(filepath):
    CHUNK_SIZE_BYTES = 64 * 1024
    HASH_SIZE_BYTES = 8
    FILE_MIN_SIZE = CHUNK_SIZE_BYTES * 2

    with open(filepath, "rb") as f:
        filesize = os.path.getsize(filepath)
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


# Kindly stolen from stackoverflow
def md5_hash(filepath):
    CHUNK_SIZE = 4096
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
