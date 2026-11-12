from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AssetFamily:
    SchemaName: str
    InstanceId: str
    DefinitionId: str
    AssetRole: str
    NameValue: str
