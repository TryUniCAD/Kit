from collections.abc import Mapping

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# independent wrapper transform caches must not share mutable embedded matrix storage with each other or the occurrence
def CopyPlacement(Fields: Mapping[str, object]) -> dict[str, object]:
    Result = {
        NameValue: Fields[NameValue]
        for NameValue in ("has_matrix", "f58", "f60", "f68", "f70", "f78")
    }
    if Fields["has_matrix"]:
        Matrix = RequireRecord(Fields.get("f08"))
        Result["f08"] = {f"m{Index}": Matrix[f"m{Index}"] for Index in range(9)}
    return Result
