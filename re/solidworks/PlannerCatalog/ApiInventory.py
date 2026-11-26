# references nested in pointer and array descriptors must retain their declared targets
def ReadReferences(TypeValue):
    if isinstance(TypeValue, dict):
        if TypeValue.get("reference_id"):
            yield TypeValue["reference_id"]
        for Value in TypeValue.values():
            yield from ReadReferences(Value)
    elif isinstance(TypeValue, list):
        for Value in TypeValue:
            yield from ReadReferences(Value)


# declared descriptor totals expose extraction failures without claiming absent declarations
def AddErrorsMut(Rows, Owner, SourceId, ItemId, CountPairs):
    for DeclaredKey, ValuesKey in CountPairs:
        if Owner.get(DeclaredKey) != len(Owner.get(ValuesKey, [])):
            Rows.AddGap(
                "descriptor_count_mismatch",
                SourceId,
                ItemId,
                {
                    "declared": Owner.get(DeclaredKey),
                    "extracted": len(Owner.get(ValuesKey, [])),
                    "collection": ValuesKey,
                },
            )
    for Error in Owner.get("errors", []):
        Rows.AddGap("descriptor_unavailable", SourceId, ItemId, Error)


# member accessors stay distinct because writable domains cannot be inferred from names
def AddFunctionMut(Rows, Function, TypeId, SourceId):
    Kind = {
        1: "api_method",
        2: "api_property_get",
        4: "api_property_put",
        8: "api_property_putref",
    }.get(Function["invkind"], "api_function")
    Details = {
        Name: Value
        for Name, Value in Function.items()
        if Name not in ("id", "name", "parameters")
    }
    Rows.AddItem(Function["id"], Kind, Function["name"], SourceId, TypeId, Details)
    for Param in Function.get("parameters", []):
        ParamId = Function["id"] + "/parameter/" + str(Param["ordinal"])
        Rows.AddItem(
            ParamId, "api_parameter", Param["name"], SourceId, Function["id"], Param
        )


# all declarations remain visible even when they lie outside feature data interfaces
def AddTypeMut(Rows, TypeInfo, SourceId):
    TypeId = TypeInfo["id"]
    Details = {
        Name: Value
        for Name, Value in TypeInfo.items()
        if Name not in ("functions", "variables", "errors", "bases", "id", "name")
    }
    Rows.AddItem(TypeId, "api_type", TypeInfo["name"], SourceId, Details=Details)
    for Function in TypeInfo.get("functions", []):
        AddFunctionMut(Rows, Function, TypeId, SourceId)
    for Variable in TypeInfo.get("variables", []):
        Kind = "api_constant" if Variable.get("kind") == 2 else "api_variable"
        Rows.AddItem(Variable["id"], Kind, Variable["name"], SourceId, TypeId, Variable)
    AddErrorsMut(
        Rows,
        TypeInfo,
        SourceId,
        TypeId,
        (
            ("declared_function_count", "functions"),
            ("declared_variable_count", "variables"),
            ("declared_base_count", "bases"),
        ),
    )


# dangling external types are evidence gaps rather than invented local definitions
def AddRefMut(Rows, OwnerId, TargetId, Kind, SourceId, Details=None):
    if TargetId in Rows.Items:
        Rows.AddRelation(OwnerId, TargetId, Kind, SourceId, Details)
    else:
        Rows.AddGap(
            "external_type_unresolved",
            SourceId,
            OwnerId,
            {"target_id": TargetId, "relation": Kind, "reference": Details},
        )


# typed links preserve inheritance and parameter dependencies across library boundaries
def AddTypeRefsMut(Rows, TypeInfo, SourceId):
    BaseKind = {3: "inherits", 4: "inherits", 5: "implements"}.get(
        TypeInfo.get("kind"), "declared_base"
    )
    for Base in TypeInfo.get("bases", []):
        AddRefMut(Rows, TypeInfo["id"], Base["id"], BaseKind, SourceId, Base)
    for Target in ReadReferences(TypeInfo.get("alias_type")):
        AddRefMut(Rows, TypeInfo["id"], Target, "alias_type", SourceId)
    for Function in TypeInfo.get("functions", []):
        for Target in ReadReferences(Function.get("return_type")):
            AddRefMut(Rows, Function["id"], Target, "return_type", SourceId)
        for Param in Function.get("parameters", []):
            ParamId = Function["id"] + "/parameter/" + str(Param["ordinal"])
            for Target in ReadReferences(Param.get("type")):
                AddRefMut(Rows, ParamId, Target, "parameter_type", SourceId)
    for Variable in TypeInfo.get("variables", []):
        for Target in ReadReferences(Variable.get("type")):
            AddRefMut(Rows, Variable["id"], Target, "variable_type", SourceId)


# collection provenance binds portable planner records to installed declaration hashes
def AddApiMut(Rows, Snapshot, Digest):
    SourceId = "source:api-snapshot"
    Rows.AddSource(
        SourceId,
        "api_snapshot",
        "Sources/ApiSnapshot.json",
        Digest,
        Snapshot.get("collection", {}),
    )
    for Error in Snapshot.get("errors", []):
        Rows.AddGap("library_unavailable", SourceId, Details=Error)
    for Library in Snapshot["libraries"]:
        LibraryId = Library["id"]
        Details = {
            Name: Value
            for Name, Value in Library.items()
            if Name not in ("types", "errors")
        }
        Rows.AddSource(
            LibraryId,
            "type_library",
            Library["source_leaf"],
            Library["source_sha256"],
            Details,
        )
        for TypeInfo in Library["types"]:
            AddTypeMut(Rows, TypeInfo, LibraryId)
        AddErrorsMut(
            Rows, Library, LibraryId, None, (("declared_type_count", "types"),)
        )
    for Library in Snapshot["libraries"]:
        for TypeInfo in Library["types"]:
            AddTypeRefsMut(Rows, TypeInfo, Library["id"])
    for Code in (
        "availability_unverified",
        "native_wire_schema_unobserved",
        "command_registration_unobserved",
        "parameter_domains_unverified",
        "api_to_wire_mapping_unverified",
    ):
        Rows.AddGap(Code, SourceId, Details={"scope": "entire declaration inventory"})
