def isoriginal(value):
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return True
    if isinstance(value, complex):
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return True
    if isinstance(value, tuple):
        return True

    return False

def is_ref(value):
    res = False
    try:
        if (value._v_is_ref or value["_v_is_ref"]) or (value.__dict__._v_is_ref or value.__dict__["_v_is_ref"]):
            res = True
    except:
        pass
    
    return res
