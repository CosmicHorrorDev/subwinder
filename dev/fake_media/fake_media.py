#!/usr/bin/env python
import argparse
import json
import platform
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile


def _main():
    # TODO: add a warning here
    args = _parse_args()
    fake_media(args.entry_file, args.output_dir, args.entry)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--entry",
        action="append",
        help="[Default: all] Then entry index to generate a media for",
        # Empty list is the magic value for all entries
        default=[],
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="[Default: current directory] Directory to store generated media in",
        default=None,
    )
    parser.add_argument(
        "-f",
        "--entry-file",
        type=Path,
        help="[Default: default_entries.json] Entry file to use for fake media info",
        default=None,
    )

    args = parser.parse_args()

    # Make sure all entries are ints
    for i in range(len(args.entry)):
        try:
            args.entry[i] = int(args.entry[i])
        except ValueError:
            raise ValueError(f'Entry should be an int, got "{args.entry[i]}"')

    return args


# TODO: test that the hashes are right in unit testing
def fake_media(entry_file=None, output_dir=None, entry_indicies=[]):
    HASH_SIZE = 8
    MAX_HASH = 2 ** (HASH_SIZE * 8) - 1
    MIN_FILE_SIZE = 128 * 1024

    # No entry file defaults to default_entries.json
    if entry_file is None:
        entry_file = Path(__file__).resolve().parent / "default_entries.json"

    # No output dir defaults to cwd
    if output_dir is None:
        output_dir = Path.cwd()

    # Make the `output_dir` if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Attempt to read the entry file
    with entry_file.open() as f:
        entries = json.load(f)

    # Empty `entry_indicies` means all entries
    if len(entry_indicies) == 0:
        entry_indicies = range(len(entries))

    # Make sure all entries are within bounds
    for index in entry_indicies:
        if index >= len(entries) or index < 0:
            raise ValueError(
                f"Entry {index} extends outside entries' bounds (0, {len(entries) - 1})"
            )

    # Generate the fake media for each of the entries
    output_paths = []
    for entry_index in entry_indicies:
        entry = entries[entry_index]
        output_file = output_dir / entry["name"]
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

        write_sparse_file(
            output_file, contents.to_bytes(HASH_SIZE, byteorder="little"), size
        )
        output_paths.append(output_file)

    # Return the paths to all the dummy files
    return output_paths


def validate_sparse_support(directory):
    SIZE = 1024 * 1024  # 1 MiB temp file seems reasonable

    if not directory.exists():
        raise FileNotFoundError(f"No such file or directory: '{directory}'")
    elif not directory.is_dir():
        raise ValueError(f"Expected '{directory}' to be a directory")

    # Try to write a small sparse file in the same directory as `filepath` and then read
    # the actual size to check that it's sparse
    temp_file = NamedTemporaryFile(dir=directory, delete=False)
    temp_file.close()
    temp_file = Path(temp_file.name)

    write_sparse_file(temp_file, b"~Testing~", SIZE)
    temp_file_size = size_on_disk(temp_file)
    if temp_file_size is None:
        return False

    is_sparse = temp_file_size < SIZE
    temp_file.unlink()

    return is_sparse


def write_sparse_file(filepath, contents, size):
    with filepath.open("wb") as file:
        file.write(contents)

    if platform.system() == "Windows":
        # Workaround because `truncate` does not create sparse files on windows
        # https://bugs.python.org/issue39910
        subprocess_args = [
            ["FSUtil", "file", "setEOF", str(filepath), str(size)],
            ["FSUtil", "sparse", "setFlag", str(filepath)],
            [
                "FSUtil",
                "sparse",
                "setRange",
                str(filepath),
                str(len(contents)),
                str(size - len(contents)),
            ],
        ]

        for args in subprocess_args:
            subprocess.run(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    else:
        # Use truncate to set the remaining file size. On file systems that
        # support it this will create a sparse file
        # Note: even if the filesystem supports sparse files, copying or moving
        # the file may not keep it as a sparse file if the program used is not
        # aware
        with filepath.open("ab") as file:
            file.truncate(size)


def size_on_disk(filepath):
    # Mac supports rsize which is the "real size" of the file
    try:
        return filepath.stat().st_rsize
    except AttributeError:
        pass

    # Some unix systems support st_blocks which should be the number of 512-byte blocks
    # allocated for the file
    try:
        return filepath.stat().st_blocks * 512
    except AttributeError:
        pass

    return None


if __name__ == "__main__":
    _main()
