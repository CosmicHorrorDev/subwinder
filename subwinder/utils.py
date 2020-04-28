import base64
import gzip
from pathlib import Path


def extract(bytes, encoding):
    compressed = base64.b64decode(bytes)
    return gzip.decompress(compressed).decode(encoding)
