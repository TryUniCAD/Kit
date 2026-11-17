from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage


# callers need actual grammar usage without retaining source bytes or claiming semantic acceptance
def GetBodyReport(UsageValue: BodyUsage) -> Mapping[str, object]:
    return {
        "completed": UsageValue.IsComplete,
        "used_schemas": tuple(sorted(UsageValue.SchemaCalls)),
        "schema_calls": dict(sorted(UsageValue.SchemaCalls.items())),
        "field_calls": dict(sorted(UsageValue.FieldCalls.items())),
        "missing_schemas": tuple(sorted(UsageValue.MissingNames)),
        "provisional_schemas": (),
    }
