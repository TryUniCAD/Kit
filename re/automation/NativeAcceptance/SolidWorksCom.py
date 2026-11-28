def Member(owner, name):
    from win32com.client.dynamic import CDispatch

    value = getattr(owner, name)
    if isinstance(value, CDispatch) or not callable(value):
        return value
    return value()
