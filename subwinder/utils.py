import hashlib
import os
# TODO: all this struct stuff can probably be swapped with
#       `int.from_bytes(bytes, byteorder="little")`, test and see
import struct

from subwinder.exceptions import SubHashError


# As per API spec with some tweaks to make it a bit nicer
# https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
def special_hash(filepath):
    # TODO: This is not min size, min size is actually 65536 * 2 * 8, right?
    FILE_MIN_SIZE = 65536 * 2
    LONGLONGFORMAT = "<q"  # little-endian long long
    try:
        # TODO: this is a const, name it as such (also is it always 8? Has to
        #       be for the hashes to be consistent right?)
        bytesize = struct.calcsize(LONGLONGFORMAT)

        with open(filepath, "rb") as f:
            filesize = os.path.getsize(filepath)
            filehash = filesize

            if filesize < FILE_MIN_SIZE:
                raise SubHashError(
                    "Filesize is below minimum of {FILE_MIN_SIZE} bytes"
                )

            for i in range(2):
                # Seek on second pass
                if i == 1:
                    # TODO: Could `filesize - 65536` even be negative? Min
                    #       condition above should catch it, test it
                    #       would not catch, min size is incorrect
                    # TODO: is this the same as `f.seek(-65536, filesize)`?
                    #       also last 0 defaults to 0 anyway
                    f.seek(max(0, filesize - 65536), 0)

                # Read the first 512 KiB summing every 8 bytes
                # TODO: can't this be read in similar way to `md5_hash`?
                for _ in range(int(65536 / bytesize)):
                    buffer = f.read(bytesize)
                    filehash += struct.unpack(LONGLONGFORMAT, buffer)[0]
                    # TODO: couldn't this be done once at the very end?
                    #       test on several files to verify
                    #       max size would be `8192 * 2 * 0xFFFFFFFFFFFFFFFF +
                    #       filesize` which seems fine for keeping as int
                    filehash &= 0xFFFFFFFFFFFFFFFF  # Keep as 64-bit int
    except IOError:
        raise SubHashError(f"Error on reading {filepath}")

    # TODO: Do f-string or .format for formatting?
    return "%016x" % filehash


# Kindly stolen from stackoverflow
def md5_hash(filepath):
    CHUNK_SIZE = 4096
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hash_md5.update(chunk)
    # TODO: is hexstring the correct return type?
    return hash_md5.hexdigest()
