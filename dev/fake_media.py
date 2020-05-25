#!/usr/bin/env python
import argparse
import json
from pathlib import Path


def main():
    HASH_SIZE = 8
    MAX_HASH = 2 ** (HASH_SIZE * 8) - 1
    MIN_FILE_SIZE = 128 * 10224

    args = parse_args()

    # Generate the fake media for each of the entries
    for entry_index in args.entry:
        entry = args.entry_file[entry_index]
        output_file = args.output_dir / entry["name"]
        hash = int(entry["hash"], 16)
        size = entry["size"]

        if size < MIN_FILE_SIZE:
            raise ValueError(
                f"Desired file is below minimum filesize of {MIN_FILE_SIZE} bytes"
            )

        # Determine the value for the first 8 bytes that will fake the desired hash
        if size > hash:
            contents = MAX_HASH - size + hash
        else:
            contents = hash - size

        with output_file.open("wb") as file:
            file.write(contents.to_bytes(HASH_SIZE, byteorder="little"))

            # Write the remaining as zeros, chunked to avoid crazy RAM usage
            remaining = size - HASH_SIZE
            chunk = 16 * 1024
            while remaining > chunk:
                file.write((0).to_bytes(chunk, byteorder="little"))
                remaining -= chunk

            file.write((0).to_bytes(remaining, byteorder="little"))


def _json_file_arg(file):
    with open(file) as f:
        return json.load(f)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--entry",
        action="append",
        help="[Default: all] Then entry file index to generate a media for",
        # Empty list is the magic value for all entries
        default=[],
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="[Default: current directory] Directory to store generated media in",
        default=Path.cwd(),
    )
    parser.add_argument(
        "entry_file", type=_json_file_arg, help="Location of the entry file"
    )

    args = parser.parse_args()

    # Deal with entries
    if len(args.entry) == 0:
        # Empty list means all entries
        args.entry = range(len(args.entry_file))
    else:
        entries = []
        for entry in args.entry:
            # Ensure entry is an int
            try:
                entry = int(entry)
            except ValueError:
                raise ValueError(f"Entry should be an int, got {entry}")

            # And within bounds
            if entry >= len(args.entry_file) or entry < 0:
                raise ValueError(
                    f"Entry {entry} extends outside entry_file bounds"
                    f" (0, {len(args.entry_file) - 1}"
                )

            entries.append(entry)
        args.entry = entries

    return args


if __name__ == "__main__":
    main()
