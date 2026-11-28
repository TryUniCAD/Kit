from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Assembly.RootRequest import RootRequest
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)


# complete assembly inputs reuse independently authored metadata vocabulary while retaining a real neutral child document and explicit native target identities
def MakeAsmInput(NameValue: str, IsVariant: bool) -> dict[str, object]:
    ChildValue = BlindCaseInput(
        "SdkDatumPlateBeta" if IsVariant else "SdkDatumPlateAlpha", IsVariant
    )
    SourceValue = RootRequest(NameValue, 0.375 if IsVariant else 0.25)
    Presentation = CastValue(dict[str, object], SourceValue["presentation"])
    SystemValue = CastValue(dict[str, object], Presentation["assembly_features"])
    FolderNames = CastValue(dict[str, str], SystemValue["folder_names"])
    Provenance = dict(CastValue(dict[str, object], SourceValue["provenance"]))
    Provenance.update(updated_at=Provenance["modified_at"], cjk_saved=False)
    AssemblyValue = {
        "name": NameValue,
        "configuration_name": "Default",
        "manager_name": "Configurations",
        "styles": Presentation["styles"],
        "units": Presentation["units"],
        "system": {
            "folders": list(FolderNames.items()),
            "planes": SystemValue["plane_names"],
            "cabinet_name": "Annotations",
            "origin_name": "Origin",
            "mate_group_name": "Mates",
            "created_at": Provenance["created_at"],
        },
        "target": SourceValue["target"],
        "provenance": Provenance,
        "definition": Presentation["definition"],
        "output": {
            "path_name": "C:\\KitSdkCandidates\\" + NameValue + ".SLDASM",
            "saved_at": CastValue(int, Provenance["modified_at"]) + 75,
        },
    }
    return {"child": ChildValue, "assembly": AssemblyValue}
