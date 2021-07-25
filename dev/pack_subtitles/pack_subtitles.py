#!/usr/bin/env python
import base64
import gzip
import sys


def main() -> None:
    packed = pack(sys.stdin.buffer.read())
    sys.stdout.buffer.write(packed)


def pack(b: bytes) -> bytes:
    compressed = gzip.compress(b)
    encoded = base64.b64encode(compressed)

    return encoded


if __name__ == "__main__":
    main()
