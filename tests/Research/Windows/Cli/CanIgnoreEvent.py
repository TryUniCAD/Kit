# the console observer must survive native cancellation without changing control handling in its children
def CanIgnoreEvent(EventCode: int) -> bool:
    return EventCode in (0, 1)
