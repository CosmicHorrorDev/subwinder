import base64
import gzip


def auto_repr(cls):
    def __repr__(self):
        members = []
        for key, val in self.__dict__.items():
            members.append(f"{key}: {val.__repr__()}")
        members = ", ".join(members)

        return f"{self.__class__.__name__}({members})"

    cls.__repr__ = __repr__

    return cls


def extract(bytes, encoding):
    compressed = base64.b64decode(bytes)
    return gzip.decompress(compressed).decode(encoding)
