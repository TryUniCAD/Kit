from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage


# each complete graph direction needs isolated evidence and an explicitly proven archive version
def NewBodyUsage(VersionValue: int, UsageValue: BodyUsage | None) -> BodyUsage:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            f"unsupported SOLIDWORKS ordinary body archive version {VersionValue}"
        )
    if UsageValue is None:
        return BodyUsage()
    if (
        UsageValue.IsComplete
        or UsageValue.SchemaCalls
        or UsageValue.FieldCalls
        or UsageValue.SchemaPath
        or UsageValue.FieldPath
        or UsageValue.MissingNames
        or UsageValue.ByteFields
    ):
        raise ValueError("SOLIDWORKS graph requires a fresh usage context")
    return UsageValue
