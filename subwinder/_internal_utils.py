from typing import Any, Tuple, Type, Union


def type_check(obj: Any, valid_classes: Union[Type, Tuple[Type, ...]]):
    if not isinstance(obj, valid_classes):
        raise TypeError(
            f"Expected `obj` to be type from {valid_classes} or a derived class, but"
            f" got type {type(obj)} instead"
        )
