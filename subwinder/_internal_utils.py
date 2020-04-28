from pathlib import Path


# TODO: paths can also be `bytes` as well which should be handled
def force_path(path):
    if type(path) == str:
        path = Path(path)

    return path
