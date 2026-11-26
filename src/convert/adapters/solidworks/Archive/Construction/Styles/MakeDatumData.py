from convert.adapters.solidworks.Archive.Construction.Styles.MakeAnnoData import (
    MakeAnnoData,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeDatumData(*, FontName: str) -> dict[str, object]:
    return {
        "f8": 0,
        "fc": 0,
        "f10": 0,
        "f18": "",
        "f20": 0,
        "f24": 0,
        "f28": "",
        "f30": 0,
        "f34": 0,
        "f38": 0,
        "f40": MakeAnnoData(FontName=FontName),
    }
