from convert.adapters.solidworks.Assembly.Assembly import NativeAsm


# an unresolved cold graph may be deferred only when its physical occurrence inventory is unambiguous
def CheckColdShape(Native: NativeAsm) -> None:
    if len(Native.definitions) == len(Native.occurrences) == 2:
        RootValues = tuple(
            Value
            for Value in Native.definitions
            if Value.object_id == Native.root_definition_id
            and Value.document_type == "ASSEMBLY"
        )
        PartValues = tuple(
            Value
            for Value in Native.definitions
            if Value.object_id != Native.root_definition_id
            and Value.document_type == "PART"
        )
        if len(RootValues) == len(PartValues) == 1 and all(
            Value.definition_id == PartValues[0].object_id
            and Value.owner_definition_id == Native.root_definition_id
            and Value.configuration_id == 0
            and not (Value.suppressed or Value.virtual or Value.flexible)
            for Value in Native.occurrences
        ):
            return
    raise ValueError(
        "cold planar mate graph requires two qualified occurrences of one actual part"
    )
