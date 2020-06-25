import os
from pathlib import Path
import random
from tempfile import NamedTemporaryFile


class RandomTempFile:
    def __init__(self, size, seed=None):
        CHUNK_SIZE = 4096  # 4KiB
        random.seed(seed)

        self.temp_file = NamedTemporaryFile(delete=False)

        # Write in `size` bytes of psuedo-random data
        while size > CHUNK_SIZE:
            chunk = random.getrandbits(CHUNK_SIZE * 8).to_bytes(
                CHUNK_SIZE, byteorder="big"
            )
            self.temp_file.write(chunk)

            size -= CHUNK_SIZE

        # Finish off any remaining bytes
        if size > 0:
            remaining = random.getrandbits(size * 8).to_bytes(size, byteorder="big")
            self.temp_file.write(remaining)

        # self.temp_file.seek(0)
        self.temp_file.close()

    def __enter__(self):
        # Just return the path for the file
        return Path(self.temp_file.name)

    def __exit__(self, exc_type, exc_value, traceback):
        # Just like in real life even when stuff isn't going great, just ignore all the
        # problems and keep moving on
        os.remove(self.temp_file.name)
