from dataclasses import dataclass as DataClass, field as DataField


# physical readback carries the exact native identity and keeps unresolved scene domains explicit
@DataClass(frozen=True, slots=True)
class NamedMatRead:
    CfgName: str
    CatalogValue: str
    MaterialName: str
    NativeId: int
    DensityValue: float
    PendingDomains: tuple[str, str] = DataField(
        default=("appearance", "material_tree"), init=False
    )
