#!/usr/bin/env python
import base64
import gzip
import sys


def main():
    packed = pack(sys.stdin.buffer.read())
    sys.stdout.buffer.write(packed)


def pack(bytes):
    compressed = gzip.compress(bytes)
    encoded = base64.b64encode(compressed)

    return encoded


if __name__ == "__main__":
    main()
