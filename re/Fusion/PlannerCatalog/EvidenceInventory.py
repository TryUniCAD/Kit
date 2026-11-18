import ast
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from CatalogRows import JsonText, ReadSource


# guid normalization joins captured identities without corrupting symbolic metatype identifiers
def NativeId(Value):
    try:
        return str(UUID(Value)).upper()
    except (ValueError, TypeError, AttributeError):
        return str(Value)


# only observed identities are created for references whose own schema has not been captured
def NativeRef(Rows, Value, SourceId):
    ItemId = "native:" + NativeId(Value)
    if ItemId not in Rows.Items:
        Rows.AddItem(
            ItemId,
            "native_reference",
            str(Value),
            SourceId,
            Details={"schema_status": "unresolved"},
        )
    return ItemId


# captured source versions remain distinct from the current installed application version
def ReadEvidence(Rows, SourceId, Kind, SourcePath, RootPath):
    Value = Rows.ReadJson(SourceId, Kind, SourcePath, RootPath)
    Version = Value.get(
        "expected_fusion_build",
        Value.get("applicationVersion", Value.get("fusion_version", "")),
    )
    Source = Rows.Sources[SourceId]
    Rows.Sources[SourceId] = (*Source[:4], str(Version), Source[5])
    return Value


# exact own schemas preserve absent and uninitialized lookups instead of fabricating empty fields
def CollectNative(Rows, RootPath):
    SourceId = "native:versions"
    Value = ReadEvidence(
        Rows,
        SourceId,
        "native_reflection",
        RootPath / "re/Fusion/LocalOracle/Reflection/Versions.json",
        RootPath,
    )
    Metatypes = Value["metatypes"]
    for MetaType in Metatypes:
        Details = {
            Key: MetaType.get(Key)
            for Key in (
                "category",
                "addin",
                "metatype_current_version",
                "lookup_supported",
                "lookup_limit_truncated",
            )
        }
        Rows.AddItem(
            "native:" + NativeId(MetaType["identifier"]),
            "native_type",
            MetaType["name"],
            SourceId,
            Details={
                **Details,
                "identifier": NativeId(MetaType["identifier"]),
                "wire_schema_complete": False,
            },
        )
    for MetaType in Metatypes:
        TypeId = "native:" + NativeId(MetaType["identifier"])
        if MetaType.get("base_identifier"):
            Rows.AddRelation(
                TypeId,
                NativeRef(Rows, MetaType["base_identifier"], SourceId),
                "native_inherits",
                SourceId,
            )
        Lookups = MetaType.get("member_set_lookups")
        if Lookups is None:
            Rows.AddGap(
                "native_lookup_unavailable",
                SourceId,
                TypeId,
                {"lookup_supported": MetaType.get("lookup_supported")},
            )
        for Lookup in Lookups or []:
            LookupVersion = Lookup["lookup_version"]
            SchemaId = TypeId + ":version:" + str(LookupVersion)
            Status = Lookup["lookup_status"]
            OwnSets = [
                Entry
                for Entry in Lookup.get("member_sets") or []
                if Entry.get("relation") == "own"
            ]
            OwnSet = OwnSets[0] if OwnSets else None
            Members = OwnSet.get("members") if OwnSet is not None else None
            Details = {
                "version": LookupVersion,
                "lookup_status": Status,
                "initialized": OwnSet.get("initialized") if OwnSet else None,
                "member_count": len(Members) if isinstance(Members, list) else None,
                "wire_schema_complete": False,
                "historical_base_version": None,
            }
            Rows.AddItem(
                SchemaId, "native_schema", MetaType["name"], SourceId, TypeId, Details
            )
            if Status != "initialized":
                Rows.AddGap("native_schema_" + Status, SourceId, SchemaId)
            if Status == "initialized" and not isinstance(Members, list):
                raise ValueError(
                    "Initialized native schema has no explicit member list"
                )
            for Member in Members or []:
                MemberId = SchemaId + ":member:" + Member["name"]
                Mask = Member.get("option_mask")
                MemberType = Member.get("metatype") or {}
                Details = {
                    "registration_index": Member.get("registration_index"),
                    "script_id": Member.get("script_id"),
                    "type_name": Member.get("debug_type_name"),
                    "option_mask": Mask,
                    "persisted": bool(Mask & 1) if isinstance(Mask, int) else None,
                    "category": (MemberType.get("category") or {}).get("name"),
                    "units": None,
                    "range": None,
                    "semantics_status": "unverified",
                }
                Rows.AddItem(
                    MemberId,
                    "native_member",
                    Member["name"],
                    SourceId,
                    SchemaId,
                    Details,
                )
                if MemberType.get("identifier"):
                    Rows.AddRelation(
                        MemberId,
                        NativeRef(Rows, MemberType["identifier"], SourceId),
                        "native_member_type",
                        SourceId,
                    )
    Rows.AddGap(
        "native_historical_base_versions_unknown",
        SourceId,
        Details={
            "reason": "Base pointers do not identify historical base schema versions"
        },
    )
    NameSource = "native:names"
    Names = ReadEvidence(
        Rows,
        NameSource,
        "native_names",
        RootPath / "re/Fusion/Reconstruction/BinaryClasses.json",
        RootPath,
    )
    for Entry in Names["classes"]:
        TargetId = NativeRef(Rows, Entry["identifier"], NameSource)
        AliasId = "native-name:" + Entry["class"] + ":" + NativeId(Entry["identifier"])
        Rows.AddItem(
            AliasId,
            "native_name",
            Entry["class"],
            NameSource,
            Details={"identifier": NativeId(Entry["identifier"])},
        )
        Rows.AddRelation(AliasId, TargetId, "names_native_type", NameSource)
    CorpusSource = "native:corpus"
    Corpus = ReadEvidence(
        Rows,
        CorpusSource,
        "historical_class_catalog",
        RootPath / "re/Fusion/Study/fusion-class-catalog.json",
        RootPath,
    )
    for Entry in Corpus["classes"]:
        TypeId = NativeRef(Rows, Entry["class_guid"], CorpusSource)
        ObservationId = "corpus:" + NativeId(Entry["class_guid"])
        Rows.AddItem(
            ObservationId,
            "corpus_class",
            NativeId(Entry["class_guid"]),
            CorpusSource,
            Details={
                "namespaces": Entry["namespaces"],
                "stored_versions_or_flags": Entry["stored_versions_or_flags"],
                "reported_semantics": Entry["observed_semantics"],
                "support_status": "unverified",
            },
        )
        Rows.AddRelation(ObservationId, TypeId, "observes_native_type", CorpusSource)


# command observations describe one captured session without claiming workspace or license completeness
def CollectCommands(Rows, SourcePath, SourceId, RootPath=None):
    if RootPath is not None:
        Value = ReadEvidence(Rows, SourceId, "command_capture", SourcePath, RootPath)
    else:
        from json import loads

        Content = Rows.AddSource(
            SourceId, "command_capture", SourcePath.name, SourcePath
        )
        Value = loads(Content)
        Source = Rows.Sources[SourceId]
        Rows.Sources[SourceId] = (
            *Source[:4],
            str(Value.get("fusion_version", "")),
            Source[5],
        )
    Source = Rows.Sources[SourceId]
    CaptureInfo = {
        Key: Value.get(Key)
        for Key in (
            "schema",
            "captured_at_utc",
            "capture_source_sha256",
            "scope",
            "status",
            "command_definition_count",
            "examined_count",
            "commands_executed",
            "documents_created",
            "document_count_before",
            "document_count_after",
        )
    }
    CaptureInfo["reported_error_count"] = len(Value.get("errors", []))
    Rows.Sources[SourceId] = (*Source[:5], JsonText(CaptureInfo))
    Records = Value.get("commands", Value.get("matches", []))
    for Record in Records:
        Details = {
            Key: Record.get(Key)
            for Key in (
                "isNative",
                "isApplicable",
                "isSubCommandDefinition",
                "objectType",
            )
        }
        Control = Record.get("control_definition")
        Details["control"] = (
            {Key: Control.get(Key) for Key in ("objectType", "isEnabled", "isVisible")}
            if isinstance(Control, dict)
            else None
        )
        Details["getter_error_fields"] = [
            Error.get("field") for Error in Record.get("getter_errors", [])
        ]
        ItemId = SourceId + ":command:" + Record["id"]
        Rows.AddItem(
            ItemId,
            "ui_command",
            Record["name"],
            SourceId,
            Details={"command_id": Record["id"], **Details},
        )
        if Details["getter_error_fields"]:
            Rows.AddGap(
                "ui_getter_unavailable",
                SourceId,
                ItemId,
                {"fields": Details["getter_error_fields"]},
            )
    for Workspace in Value.get("workspaces", []):
        Rows.AddItem(
            SourceId + ":workspace:" + Workspace["id"],
            "ui_workspace",
            Workspace["name"],
            SourceId,
        )
    Filtered = Value.get("filtered", "filter" in Value)
    Rows.AddGap(
        "ui_scope_current_session",
        SourceId,
        Details={
            "filtered": Filtered,
            "reported_status": Value.get("status"),
            "registered_count": Value.get("command_definition_count"),
            "retained_count": len(Records),
            "reason": "Captured context does not prove availability across all workspaces and licenses",
        },
    )
    if Filtered or Value.get("status") != "complete":
        Rows.AddGap(
            "ui_partial_capture",
            SourceId,
            Details={"filtered": Filtered, "status": Value.get("status")},
        )


# recipe and capture hashes expose evidence without promoting script presence to authoring qualification
def CollectRecipes(Rows, RootPath):
    StudyPath = RootPath / "re/Fusion/Study"
    Recipes = {}
    for SourcePath in sorted(StudyPath.glob("Generate*.py")):
        SourceId = "recipe:" + SourcePath.stem
        Label = SourcePath.relative_to(RootPath).as_posix()
        Content = Rows.AddSource(SourceId, "authoring_recipe", Label, SourcePath)
        ast.parse(Content, filename=Label)
        RecipeId = SourceId
        Rows.AddItem(
            RecipeId,
            "recipe",
            SourcePath.stem,
            SourceId,
            Details={"authoring_status": "unverified", "source_only": True},
        )
        Recipes.setdefault(sha256(Content).hexdigest(), []).append(RecipeId)
    for SourcePath in sorted(StudyPath.glob("*/ground_truth.json")):
        SourceId = "capture:" + SourcePath.parent.name
        Value = ReadEvidence(Rows, SourceId, "ground_truth", SourcePath, RootPath)
        Captures = Value.get("samples", [])
        if not isinstance(Captures, list):
            Rows.AddGap("capture_samples_unrecognized", SourceId)
            Captures = []
        ErrorCount = (
            len(Value.get("errors", []))
            if isinstance(Value.get("errors", []), list)
            else 1
        )
        Details = {
            "reported_status": Value.get("status"),
            "sample_count": len(Captures),
            "reported_error_count": ErrorCount,
            "terminal_marker_present": SourcePath.with_name("complete.txt").is_file(),
            "authoring_status": "unverified",
            "helper_binding_status": "unverified",
        }
        Rows.AddItem(
            SourceId, "capture", SourcePath.parent.name, SourceId, Details=Details
        )
        for RecipeId in Recipes.get(Value.get("executed_generator_sha256"), []):
            Rows.AddRelation(
                SourceId,
                RecipeId,
                "matches_entry_source_hash",
                SourceId,
                {"helper_bindings_verified": False, "proves_authoring_success": False},
            )
        if ErrorCount or Value.get("status") != "complete":
            Rows.AddGap(
                "capture_qualification_unverified",
                SourceId,
                SourceId,
                {
                    "reported_status": Value.get("status"),
                    "reported_error_count": ErrorCount,
                },
            )
        for Index, Sample in enumerate(Captures):
            if not isinstance(Sample, dict):
                Rows.AddGap(
                    "capture_sample_unrecognized", SourceId, SourceId, {"index": Index}
                )
                continue
            FileName = Sample.get("file")
            SafeName = (
                Path(FileName).name
                if isinstance(FileName, str)
                else "sample:" + str(Index)
            )
            Rows.AddItem(
                SourceId + f":sample:{Index}",
                "captured_sample",
                SafeName,
                SourceId,
                SourceId,
                {
                    "reported_kind": Sample.get("kind"),
                    "observed_keys": sorted(Sample),
                    "support_status": "unverified",
                },
            )
    for SourcePath in sorted(StudyPath.glob("commandinventory-*/ground_truth.json")):
        CollectCommands(
            Rows, SourcePath, "commands:" + SourcePath.parent.name, RootPath
        )
