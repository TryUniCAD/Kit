from tests.Convert.Solidworks.Research.Construction.Nesting.NestedAsmInput import (
    NestedAsmInput,
)
from tests.Convert.Solidworks.Research.Construction.Nesting.NestedPartInput import (
    NestedPartInput,
)
from tests.Convert.Solidworks.Research.Construction.Nesting.NestedPoseInput import (
    NestedPoseInput,
)


# simple and repeated mixed hierarchies must vary direct definitions and expanded paths without reading any native source or held out design
def MakeNestedCase(IsMixed: bool, OutputRoot: str) -> dict[str, object]:
    PartsValue: list[dict[str, object]] = [
        {
            "id": "plate",
            "kind": "part",
            "request": NestedPartInput(
                "SdkNestedPlate", (28.65, 16.35, 7.45), OutputRoot
            ),
        }
    ]
    ModuleRows = [
        NestedPoseInput(
            "plate", "SdkNestedPlate-1", "x", 27.0, (0.0143, -0.0067, 0.0099)
        )
    ]
    RootRows = [
        NestedPoseInput("module", "SdkModule-1", "y", -41.0, (0.1087, 0.0521, -0.0133))
    ]
    if IsMixed:
        PartsValue.append(
            {
                "id": "gauge",
                "kind": "part",
                "request": NestedPartInput(
                    "SdkGaugePlate", (19.15, 24.55, 10.85), OutputRoot
                ),
            }
        )
        ModuleRows.append(
            NestedPoseInput(
                "plate", "SdkNestedPlate-2", "z", -33.0, (-0.0261, 0.0337, 0.0189)
            )
        )
        RootRows.extend(
            (
                NestedPoseInput(
                    "module", "SdkModule-2", "z", 19.0, (-0.0839, 0.0613, 0.0447)
                ),
                NestedPoseInput(
                    "gauge", "SdkGaugePlate-1", "x", -23.0, (0.0079, -0.0991, 0.0683)
                ),
            )
        )
    Assemblies = [
        {
            "id": "module",
            "kind": "assembly",
            "request": NestedAsmInput("SdkModule", OutputRoot),
            "occurrences": ModuleRows,
        },
        {
            "id": "frame",
            "kind": "assembly",
            "request": NestedAsmInput("SdkFrame", OutputRoot),
            "occurrences": RootRows,
        },
    ]
    return {"root": "frame", "definitions": [*PartsValue, *Assemblies]}
