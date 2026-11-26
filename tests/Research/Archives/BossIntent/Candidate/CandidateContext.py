from uuid import UUID as MakeUuid

from tests.Research.Archives.SolidWorksFreshBossTests import (
    KExchangeTime,
    KFreshContext,
)


# independent identities and save settings keep candidate synthesis separate from native source bytes
def MakeContext() -> tuple[dict[str, object], dict[str, object]]:
    Title = "P03IndependentRequestAudit"
    KeyValues = tuple(str(MakeUuid(int=Index, version=4)) for Index in range(200, 210))
    CaseValue: dict[str, object] = {
        "right": False,
        "title": Title,
        "dimensions_mm": [40.0, 20.0, 10.0],
        "density_kg_m3": 1000.0,
        "centre_m": [0.02, 0.01, 0.005],
        "ids": [57, 71, 91, 92, 93],
    }
    Package: dict[str, object] = {
        **KFreshContext,
        "saved_path": f"C:\\KitIndependentAudit\\{Title}.SLDPRT",
        "block_id": KeyValues[0],
        "config_exchange": {"id": KeyValues[1], "created": KExchangeTime},
        "object_exchange": {
            "folder": KeyValues[2],
            "planes": KeyValues[3:6],
            "document": KeyValues[6],
            "created": KExchangeTime,
            "index_order": [1, 2, 0],
        },
        "pmi": {"keys": KeyValues[7:10], "created": KExchangeTime},
        "content": {
            "material_name": "Material <not specified>",
            "material_id": "Steel",
            "body_visible": True,
        },
    }
    return CaseValue, Package
