def isoriginal(value):
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return True
    if isinstance(value, complex):
        return True
    if isinstance(value, str):
        return True
    if isinstance(value, list):
        return True
    if isinstance(value, tuple):
        return True

    return False
