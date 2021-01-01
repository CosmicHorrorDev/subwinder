def type_check(obj, valid_classes):
    if not isinstance(obj, valid_classes):
        raise TypeError(
            f"Expected `obj` to be type from {valid_classes} or a derived class, but"
            f" got type {type(obj)} instead"
        )
