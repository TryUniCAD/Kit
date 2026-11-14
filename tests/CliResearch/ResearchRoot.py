from os import environ as KEnvironment
from pathlib import Path as FilePath


def ResearchRoot() -> FilePath:
    RootValue = KEnvironment.get("KIT_RESEARCH_CHECKOUT")
    if RootValue is None:
        raise ValueError("KIT_RESEARCH_CHECKOUT must identify the pinned PR94 checkout")
    RootPath = FilePath(RootValue)
    if not RootPath.is_absolute():
        raise ValueError("KIT_RESEARCH_CHECKOUT must be absolute")
    if not (RootPath / ".git").exists() or not (RootPath / "src/convert").is_dir():
        raise ValueError(
            "KIT_RESEARCH_CHECKOUT must contain the pinned repository and SDK"
        )
    return RootPath.resolve()
