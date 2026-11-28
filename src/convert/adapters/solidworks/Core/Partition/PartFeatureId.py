# this definition exists because focused behavior needs one stable owner
def FeatureId(NativeId: int) -> str:
    return f"sldprt:feature:{NativeId}"
