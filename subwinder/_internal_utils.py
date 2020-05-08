def type_check(obj, valid_classes):
    if not isinstance(obj, valid_classes):
        raise ValueError(
            f"Expected `obj` to be type from {valid_classes}, but got type {type(obj)}"
            " instead"
        )
