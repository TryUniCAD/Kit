# sketch driver identities retain the existing public parameter namespace while names come from typed parameter nodes
def LineParamId(ProfileId: int, NameValue: str) -> str:
    return f"sldprt:parameter:{ProfileId}:{NameValue}"
