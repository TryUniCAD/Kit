from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from os import getpid
from pathlib import Path
from struct import pack
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from Classes import registry
from Core import Obj
from FieldScan import FieldInventory
from RoundTrip import PLANS, REQUIRED, one, plan
from Streams import load_rooted, store_rooted
from defs.ConfigPart import store_config_state
from convert.adapters.solidworks.Container.Container import build_sldprt, SldprtArchive


def Digest(Value):
    return sha256(Value).hexdigest()


def JsonBytes(Value):
    return dumps(Value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def SaveReport(TargetPath, Value):
    with TargetPath.open("x", encoding="utf-8") as Output:
        Output.write(dumps(Value, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def SourceInput():
    CorpusPath = ROOT / "re/solidworks/v2026/corpus/curves-discovery"
    SourcePath = CorpusPath / "ControlRectangle.SLDPRT"
    ManifestPath = CorpusPath / "Manifest.json"
    if any(Item.is_symlink() for Item in (CorpusPath, SourcePath, ManifestPath)):
        raise ValueError("source fixtures must not be symbolic links")
    if not SourcePath.resolve().is_relative_to(ROOT):
        raise ValueError("source fixture escaped the checkout")
    ManifestRaw = ManifestPath.read_bytes()
    Entries = [Item for Item in loads(ManifestRaw)["records"] if Item["name"] == "ControlRectangle"]
    if len(Entries) != 1 or Entries[0]["split"] != "control" or Entries[0]["file"] != SourcePath.name:
        raise ValueError("expected exactly the public rectangle control")
    SourceRaw = SourcePath.read_bytes()
    if Digest(SourceRaw) != Entries[0]["sha256"]:
        raise ValueError("control fixture does not match its prepared manifest")
    Evidence = {
        "file": str(SourcePath.relative_to(ROOT)), "sha256": Digest(SourceRaw),
        "bytes": len(SourceRaw), "manifest_sha256": Digest(ManifestRaw),
        "original_sha256": Entries[0]["source_sha256"],
        "source_manifest_sha256": Entries[0]["source_manifest_sha256"],
    }
    return SourcePath, SourceRaw, SldprtArchive.from_bytes(SourceRaw, SourcePath), Evidence


def SourceProof():
    Files = [HERE / Item for Item in (
        "StringCorpus.py", "Core.py", "Schema.py", "Classes.py", "Streams.py",
        "RoundTrip.py", "FieldScan.py", "Dsl.py", "AnnotationWire.py", "MapBridge.py",
    )]
    Files.extend(sorted((HERE / "defs").glob("*.py")))
    for Folder in ("Archive/Counts", "Archive/Strings", "Archive/Tags", "Archive/Objects", "Archive/Maps", "Container"):
        Files.extend(sorted((ROOT / "src/convert/adapters/solidworks" / Folder).rglob("*.py")))
    return [{"file": str(Item.relative_to(ROOT)), "sha256": Digest(Item.read_bytes())} for Item in sorted(set(Files))]


def StrictPhase(Usage):
    if Usage["completed"] is not True or Usage["provisional_schemas"] or Usage["missing_schemas"]:
        raise ValueError("complete proven schema usage is required")
    if any(Item["completed"] is not True for Item in Usage["raw_operations"]):
        raise ValueError("raw schema operations must complete")


def LoadHeader(Archive, Registry):
    with Registry.track_usage("load", "Header2", role="cstring_archive", sources=Archive.streams) as Usage:
        Document, Reader = load_rooted(Archive.require("Header2"), Registry, 1, 19000)
        if Document.tail:
            raise ValueError("complete Header2 load is required")
    Snapshot = Usage.snapshot()
    StrictPhase(Snapshot)
    return Document, Reader, Snapshot


def StoreHeader(Document, Registry):
    with Registry.track_usage("store", "Header2", role="cstring_archive") as Usage:
        Result = store_rooted(Document, Registry, 19000)
    Snapshot = Usage.snapshot()
    StrictPhase(Snapshot)
    return Result, Snapshot


def StampOwner(Reader, Index=None):
    Candidates = [
        Key for Key, Entry in Reader.table.items()
        if Entry[0] == "obj" and type(Entry[1]) is Obj and Entry[1].cls == "moStamp_c"
    ]
    Selected = min(Candidates) if Index is None else Index
    if Selected not in Candidates:
        raise ValueError("documented revision stamp owner is absent")
    Target = Reader.table[Selected][1]
    if list(Target.f) != ["f08", "f0c", "f10", "f18", "f20"]:
        raise ValueError("revision comment must be the final documented field")
    return Target


def GraphProof(Document, Reader, Name="Header2", Dependency=None):
    Inventory = FieldInventory()
    SeedGraph = None
    if Dependency is not None:
        SeedGraph = Inventory.document("Contents/Config-0", Dependency["document"], Dependency["reader"])
    RootGraph = Inventory.document(Name, Document, Reader)
    Nodes = [
        {Key: Value for Key, Value in Node.items() if Key not in ("record_start", "record_end", "position_stream")}
        for Node in Inventory.nodes
    ]
    Graph = {"document": RootGraph, "dependency": SeedGraph, "nodes": Nodes, "tail_bytes": len(Document.tail), "tail_sha256": Digest(Document.tail)}
    return {
        "sha256": Digest(JsonBytes(Graph)), "node_count": len(Nodes),
        "reference_count": len(Inventory.references), "map_base": Reader.base,
        "map_count": Reader.count,
        "unresolved_references": sum(Item["type"] == "external-object-reference" for Item in Inventory.references),
    }


def LoadModel(Name, Archive, Registry, Models):
    Kind, Framing = plan(Name, {**PLANS, **Registry.plans})
    Options = {}
    if Name.endswith("-ResolvedFeatures"):
        if Kind != "custom":
            raise ValueError("resolved model generation requires the actual linked custom plan")
        Options["seed"] = Models["Contents/Config-0"]["reader"].map_state()
    with Registry.track_usage("load", Name, role="cstring_modeled_archive", sources=Archive.streams) as Usage:
        if Kind == "rooted":
            Document, Reader = load_rooted(Archive.require(Name), Registry, Framing, 19000)
        elif Kind == "custom":
            Document, Reader = Framing[0](Archive.require(Name), Registry, 19000, archive=Archive, name=Name, **Options)
        else:
            raise ValueError("unmodeled archive plans must not be emitted")
        if Document.tail:
            raise ValueError("modeled archive must consume the complete source stream")
    Snapshot = Usage.snapshot()
    StrictPhase(Snapshot)
    return {"document": Document, "reader": Reader, "kind": Kind, "framing": Framing, "load_usage": Snapshot}


def LoadModels(Archive, Registry):
    Models = {}
    for Name in (*REQUIRED, "Header2"):
        Models[Name] = LoadModel(Name, Archive, Registry, Models)
    return Models


def ModelGraphs(Models):
    return {
        Name: GraphProof(Model["document"], Model["reader"], Name, Models["Contents/Config-0"] if Name.endswith("-ResolvedFeatures") else None)
        for Name, Model in Models.items()
    }


def StoreModel(Name, Model, Registry, Seed=None):
    with Registry.track_usage("store", Name, role="cstring_modeled_archive") as Usage:
        if Name == "Contents/Config-0":
            Data, Seed = store_config_state(Model["document"], Registry, 19000)
        elif Model["kind"] == "rooted":
            Data = store_rooted(Model["document"], Registry, 19000)
        elif Model["kind"] == "custom":
            Options = {"seed": Seed} if Name.endswith("-ResolvedFeatures") else {}
            Data = Model["framing"][1](Model["document"], Registry, 19000, **Options)
        else:
            raise ValueError("unmodeled archive plans must not be emitted")
    Snapshot = Usage.snapshot()
    StrictPhase(Snapshot)
    return Data, Snapshot, Seed


def BuildModeled(Context, HeaderRaw, HeaderUsage, IsTainted=False, ModelHash=None):
    Streams, Proofs, Seed = {}, {}, None
    for Name, Model in Context["models"].items():
        if Name == "Header2":
            Data, Snapshot = HeaderRaw, HeaderUsage
        else:
            Data, Snapshot, Seed = StoreModel(Name, Model, Context["registry"], Seed)
            if Data != Context["archive"].require(Name):
                raise ValueError("another model did not regenerate its source archive identically")
        Streams[Name] = Data
        Proofs[Name] = {
            "bytes": len(Data), "sha256": Digest(Data), "store_usage": Snapshot,
            "model_sha256": ModelHash if Name == "Header2" and IsTainted else Digest(Data),
            "post_store_corruption": Name == "Header2" and IsTainted,
        }
    Items = [(Name, Streams[Name]) for Name in Context["order"]]
    return build_sldprt(Items), Proofs


def FrameBounds(Context):
    Document, Reader, Registry = Context["document"], Context["reader"], Context["registry"]
    Target = StampOwner(Reader)
    Original = Target.f["f20"]
    try:
        Target.f["f20"] = ""
        EmptyRaw, EmptyUsage = StoreHeader(Document, Registry)
        EmptyFile, _ = BuildModeled(Context, EmptyRaw, EmptyUsage)
        EmptyArchive = SldprtArchive.from_bytes(EmptyFile)
        _, EmptyReader, _ = LoadHeader(EmptyArchive, Registry)
        EmptyStamp = StampOwner(EmptyReader, Target.index)
    finally:
        Target.f["f20"] = Original
    Start = EmptyStamp.end - 4
    SourceRaw = Context["archive"].require("Header2")
    if EmptyRaw[Start:EmptyStamp.end] != bytes.fromhex("fffeff00"):
        raise ValueError("documented empty Unicode frame was not found")
    if SourceRaw[:Start] != EmptyRaw[:Start] or SourceRaw[Target.end:] != EmptyRaw[EmptyStamp.end:]:
        raise ValueError("comment mutation changed adjacent native data")
    if StoreHeader(Document, Registry)[0] != SourceRaw:
        raise ValueError("restoring the comment did not restore the entire source stream")
    return Target.index, Start, Target.end


def CaseValues():
    return {
        "UtfByte254": "x" * 254, "UtfWord255": "x" * 255,
        "UtfWord65533": "x" * 65533, "UtfLong65534": "x" * 65534,
        "NonBmp254": "\U0001f642" * 127, "NonBmp255": "\U0001f642" * 127 + "x",
        "LoneSurrogate": "head\ud800tail", "EmptyUnicode": "",
        "EmptyAnsi": ("A", ""), "AnsiBytes": ("A", "\x80\xff"),
    }


def BadFrames():
    return {
        "RepeatedUnicode": (bytes.fromhex("fffefffffeff"), "repeats the Unicode marker"),
        "ReservedUnicode": (bytes.fromhex("fffeffffffffffffffff"), "reserved double word length"),
        "ReservedAnsi": (bytes.fromhex("ffffffffffffff"), "reserved double word length"),
    }


def ExpectedFrame(Value):
    IsUnicode = type(Value) is str
    Text = Value if IsUnicode else Value[1]
    Payload = Text.encode("utf-16-le", "surrogatepass") if IsUnicode else Text.encode("latin-1")
    Units = len(Payload) // 2 if IsUnicode else len(Payload)
    if Units < 255:
        Length = pack("<B", Units)
    elif Units < 65534:
        Length = b"\xff" + pack("<H", Units)
    else:
        Length = b"\xff\xff\xff" + pack("<I", Units)
    Frame = (bytes.fromhex("fffeff") if IsUnicode else b"") + Length + Payload
    return Frame, {"unicode": IsUnicode, "units": Units, "frame_bytes": len(Frame), "frame_sha256": Digest(Frame)}


def StreamProof(Archive):
    return [{"name": Item.name, "bytes": len(Item.data), "sha256": Digest(Item.data)} for Item in Archive.records]


def WriteCase(OutputRoot, Name, HeaderRaw, Context, HeaderUsage, IsTainted=False, ModelHash=None):
    FileRaw, Generation = BuildModeled(Context, HeaderRaw, HeaderUsage, IsTainted, ModelHash)
    FilePath = OutputRoot / (Name + ".SLDPRT")
    with FilePath.open("xb") as Output:
        Output.write(FileRaw)
    return {
        "name": Name, "file": FilePath.name, "sha256": Digest(FileRaw), "bytes": len(FileRaw),
        "regenerated_streams": Generation, "negative_control_taint": IsTainted,
        "writer_output": False, "native_acceptance": False,
    }


def AuthorGood(OutputRoot, Name, Value, Context):
    Target = StampOwner(Context["reader"], Context["index"])
    Original = Target.f["f20"]
    try:
        Target.f["f20"] = Value
        ExpectedGraphs = ModelGraphs(Context["models"])
        HeaderRaw, Usage = StoreHeader(Context["document"], Context["registry"])
    finally:
        Target.f["f20"] = Original
    Frame, Shape = ExpectedFrame(Value)
    Start, End = Context["start"], Context["end"]
    SourceHeader = Context["archive"].require("Header2")
    if HeaderRaw != SourceHeader[:Start] + Frame + SourceHeader[End:]:
        raise ValueError("complete model storage changed more than the comment frame")
    return {**WriteCase(OutputRoot, Name, HeaderRaw, Context, Usage), "graphs": ExpectedGraphs, "shape": Shape, "schema_usage": Usage}


def AuthorBad(OutputRoot, Name, Value, Context):
    RegeneratedHeader, Usage = StoreHeader(Context["document"], Context["registry"])
    Frame, Reason = Value
    HeaderRaw = RegeneratedHeader[:Context["start"]] + Frame + RegeneratedHeader[Context["end"]:]
    return {**WriteCase(OutputRoot, Name, HeaderRaw, Context, Usage, True, Digest(RegeneratedHeader)), "reason": Reason, "frame_sha256": Digest(Frame)}


def AuditStream(Record, Archive, IsLinked):
    if not all(Record.get(Key) is True for Key in ("passed", "byte_identity_passed", "proven_schemas", "identical")) or Record["tail"] != 0:
        raise ValueError("strict stream compatibility failed")
    Usage = Record["schema_usage"]
    for Snapshot in (Usage["load"], Usage["store"], *Usage["dependencies"]):
        StrictPhase(Snapshot)
    for Snapshot in Usage["dependencies"]:
        Data = Archive.require(Snapshot["requested_stream"])
        if Snapshot["bytes"] != len(Data) or Snapshot["sha256"] != Digest(Data) or Snapshot["tail"] != 0:
            raise ValueError("linked source hash or complete consumption differs")
    if IsLinked:
        Seeds = [Item for Item in Usage["dependencies"] if Item["role"] == "linked_map_seed"]
        if len(Seeds) != 1 or Seeds[0]["requested_stream"] != "Contents/Config-0" or Record["seeded_map_count"] < 1:
            raise ValueError("resolved stream requires its actual configuration map seed")


def AuditArchive(FilePath, Archive):
    Registry = registry()
    Plans = {**PLANS, **Registry.plans}
    Reports = {}
    for Name, Selected, Linked in (
        ("primary", [*REQUIRED, "Header2"], False),
        ("linked", ["Contents/Config-0-ResolvedFeatures"], True),
    ):
        Report = one(FilePath, Selected, Registry, Plans, linked=Linked, require_proven=True)
        if not Report["passed"] or set(Report["streams"]) != set(Selected):
            raise ValueError("full archive critical stream audit failed")
        for StreamName, Record in Report["streams"].items():
            if Record["sha256"] != Digest(Archive.require(StreamName)) or Record["bytes"] != len(Archive.require(StreamName)):
                raise ValueError("reported stream identity differs from the container")
            AuditStream(Record, Archive, Linked)
        Reports[Name] = Report
    return Reports


def MakeContext():
    SourcePath, _, Archive, Source = SourceInput()
    Registry = registry()
    Models = LoadModels(Archive, Registry)
    HeaderModel = Models["Header2"]
    Document, Reader = HeaderModel["document"], HeaderModel["reader"]
    if StoreHeader(Document, Registry)[0] != Archive.require("Header2"):
        raise ValueError("unmodified control failed complete stream identity")
    Context = {
        "source": Source, "path": SourcePath, "archive": Archive, "models": Models,
        "registry": Registry, "document": Document, "reader": Reader,
        "order": [Item.name for Item in Archive.records if Item.name in Models],
        "load_usage": HeaderModel["load_usage"],
    }
    if len(Context["order"]) != 8 or set(Context["order"]) != set(Models):
        raise ValueError("all eight modeled archives must have unique source names")
    Context["index"], Context["start"], Context["end"] = FrameBounds(Context)
    Graphs = ModelGraphs(Models)
    if any(Graph["unresolved_references"] for Graph in Graphs.values()):
        raise ValueError("all emitted model graphs must resolve with their actual seeds")
    Context.update(baseline=AuditArchive(SourcePath, Archive), graphs=Graphs)
    return Context


def PrepareBatch(OutputRoot):
    if OutputRoot.exists() or OutputRoot.is_symlink():
        raise ValueError("preparation needs a new output directory")
    OutputRoot.mkdir(parents=True)
    Context = MakeContext()
    Records = [AuthorGood(OutputRoot, Name, Value, Context) for Name, Value in CaseValues().items()]
    Invalid = [AuthorBad(OutputRoot, Name, Value, Context) for Name, Value in BadFrames().items()]
    if SourceInput()[3] != Context["source"]:
        raise ValueError("immutable control or manifest changed during preparation")
    return {
        "source": Context["source"], "implementation": SourceProof(), "pid": getpid(),
        "owner": {"class": "moStamp_c", "field": "f20", "index": Context["index"]},
        "baseline": Context["baseline"], "baseline_graphs": Context["graphs"],
        "source_streams": StreamProof(Context["archive"]), "source_immutable": True,
        "emitted_modeled_streams": Context["order"],
        "omitted_source_streams": [Item for Item in StreamProof(Context["archive"]) if Item["name"] not in Context["models"]],
        "positive": Records, "negative": Invalid, "passed": True,
    }


def CheckFile(OutputRoot, Record, Context):
    FilePath = OutputRoot / Record["file"]
    if FilePath.name != Record["name"] + ".SLDPRT" or FilePath.is_symlink() or FilePath.resolve().parent != OutputRoot:
        raise ValueError("case file must remain in its owned flat output directory")
    FileRaw = FilePath.read_bytes()
    if Digest(FileRaw) != Record["sha256"] or len(FileRaw) != Record["bytes"]:
        raise ValueError("prepared complete container identity changed")
    Archive = SldprtArchive.from_bytes(FileRaw, FilePath)
    Source = Context["archive"]
    if [Item.name for Item in Archive.records] != Context["order"]:
        raise ValueError("output must contain only the eight regenerated modeled archives")
    if any(Item.data != Source.require(Item.name) for Item in Archive.records if Item.name != "Header2"):
        raise ValueError("comment preparation changed another container stream")
    return FilePath, Archive


def CheckGenerated(Record, Archive, Context, IsTainted):
    if Record["negative_control_taint"] is not IsTainted:
        raise ValueError("negative corruption must never inherit positive acceptance")
    Proofs = Record["regenerated_streams"]
    if set(Proofs) != set(Context["models"]):
        raise ValueError("every emitted stream requires its actual model store receipt")
    for Name, Proof in Proofs.items():
        StrictPhase(Proof["store_usage"])
        Data = Archive.require(Name)
        if Proof["bytes"] != len(Data) or Proof["sha256"] != Digest(Data):
            raise ValueError("regenerated model receipt differs from its emitted stream")
        Corrupted = Name == "Header2" and IsTainted
        if Proof["post_store_corruption"] is not Corrupted:
            raise ValueError("only the negative owned header may be corrupted after storage")
        ModelHash = Digest(StoreHeader(Context["document"], Context["registry"])[0]) if Corrupted else Digest(Data)
        if Proof["model_sha256"] != ModelHash:
            raise ValueError("a tainted header must retain the pristine model storage identity")


def CheckGood(OutputRoot, Record, Context):
    FilePath, Archive = CheckFile(OutputRoot, Record, Context)
    CheckGenerated(Record, Archive, Context, False)
    Models = LoadModels(Archive, Context["registry"])
    Document, Reader = Models["Header2"]["document"], Models["Header2"]["reader"]
    Value = CaseValues()[Record["name"]]
    Target = StampOwner(Reader, Context["index"])
    if Target.f["f20"] != Value or type(Target.f["f20"]) is not type(Value):
        raise ValueError("source string representation or text changed")
    Frame, Shape = ExpectedFrame(Value)
    Data, Before = Archive.require("Header2"), Context["archive"].require("Header2")
    if Data != Before[:Context["start"]] + Frame + Before[Context["end"]:] or Shape != Record["shape"]:
        raise ValueError("canonical comment frame or adjacent fields differ")
    if ModelGraphs(Models) != Record["graphs"] or Reader.count != Context["reader"].count:
        raise ValueError("complete emitted semantic graphs or archive maps changed")
    if StoreHeader(Document, Context["registry"])[0] != Data:
        raise ValueError("fresh process cannot preserve the complete edited stream")
    Audit = AuditArchive(FilePath, Archive)
    for Name in (Key for Key in Audit["primary"]["streams"] if Key != "Header2"):
        if Audit["primary"]["streams"][Name] != Context["baseline"]["primary"]["streams"][Name]:
            raise ValueError("an unchanged primary stream has different parser evidence")
    if Audit["linked"]["streams"] != Context["baseline"]["linked"]["streams"]:
        raise ValueError("linked configuration evidence or seed map changed")
    return {"name": Record["name"], "passed": True, "graphs": ModelGraphs(Models), "load_usage": Models["Header2"]["load_usage"], "audit": Audit}


def CheckBad(OutputRoot, Record, Context):
    FilePath, Archive = CheckFile(OutputRoot, Record, Context)
    CheckGenerated(Record, Archive, Context, True)
    Frame, Reason = BadFrames()[Record["name"]]
    Before = Context["archive"].require("Header2")
    if Archive.require("Header2") != Before[:Context["start"]] + Frame + Before[Context["end"]:]:
        raise ValueError("malformed control differs beyond its owned string frame")
    Registry = Context["registry"]
    Report = one(FilePath, ["Header2"], Registry, {**PLANS, **Registry.plans}, require_proven=True)
    Stream = Report["streams"].get("Header2", {})
    Error = Stream.get("error", "")
    if Report["passed"] or Stream.get("passed") or Reason not in Error:
        raise ValueError("archive CLI did not reject the exact malformed CString rule")
    if f"invalid archive string at {Context['start']}:" not in Error:
        raise ValueError("malformed control failed outside the owned comment field")
    Usage = Stream["schema_usage"]
    if Usage["load"]["completed"] is not False or Usage["store"] is not None:
        raise ValueError("malformed framing must stop the actual load before storage")
    if Usage["load"]["provisional_schemas"] or Usage["load"]["missing_schemas"]:
        raise ValueError("missing grammar cannot count as malformed string rejection")
    return {"name": Record["name"], "passed": True, "load_usage": Usage["load"], "error_sha256": Digest(Error.encode("utf-8")), "rejected_owned_field": True, "negative_control_taint": True, "writer_output": False, "native_acceptance": False}


def CheckCases(OutputRoot, Records, Context, Checker):
    Results = []
    for Record in Records:
        try:
            Results.append(Checker(OutputRoot, Record, Context))
        except Exception as Error:
            Results.append({"name": Record["name"], "passed": False, "error_type": type(Error).__name__, "error_sha256": Digest(str(Error).encode("utf-8", "surrogatepass"))})
    return Results


def VerifyBatch(OutputRoot):
    Prepared = loads((OutputRoot / "Prepared.json").read_bytes())
    if Prepared.get("passed") is not True:
        raise ValueError("preparation must complete before fresh process verification")
    if Prepared["implementation"] != SourceProof() or Prepared["pid"] == getpid():
        raise ValueError("verification needs identical source code and a fresh interpreter")
    Context = MakeContext()
    if Prepared["source"] != Context["source"] or Prepared["baseline_graphs"] != Context["graphs"]:
        raise ValueError("immutable native source graph or prepared manifest changed")
    if Prepared["source_streams"] != StreamProof(Context["archive"]) or Prepared["baseline"] != Context["baseline"]:
        raise ValueError("fresh interpreter baseline evidence differs from preparation")
    if Prepared["emitted_modeled_streams"] != Context["order"]:
        raise ValueError("modeled archive membership changed between actual processes")
    if [Item["name"] for Item in Prepared["positive"]] != list(CaseValues()) or [Item["name"] for Item in Prepared["negative"]] != list(BadFrames()):
        raise ValueError("all required complete archive cases must be present")
    Expected = {Item["file"] for Item in (*Prepared["positive"], *Prepared["negative"])}
    if {Item.name for Item in OutputRoot.glob("*.SLDPRT")} != Expected:
        raise ValueError("unexpected or missing source compatibility containers")
    Good = CheckCases(OutputRoot, Prepared["positive"], Context, CheckGood)
    Bad = CheckCases(OutputRoot, Prepared["negative"], Context, CheckBad)
    if SourceInput()[3] != Context["source"]:
        raise ValueError("immutable control changed during fresh process verification")
    return {
        "source": Context["source"], "implementation": SourceProof(), "pid": getpid(),
        "author_pid": Prepared["pid"], "prepared_sha256": Digest((OutputRoot / "Prepared.json").read_bytes()),
        "source_immutable": True, "positive": Good, "negative": Bad,
        "emitted_modeled_streams": Context["order"],
        "positive_count": len(Good), "negative_count": len(Bad),
        "primary_streams": len(REQUIRED) + 1, "linked_streams": 1,
        "passed": all(Item["passed"] for Item in (*Good, *Bad)),
    }


def MainEntry():
    Parser = ArgumentParser(description="Remote complete modeled archives for CString process compatibility")
    Parser.add_argument("mode", choices=("prepare", "verify"))
    Parser.add_argument("output", type=Path)
    Args = Parser.parse_args()
    OutputRoot = Args.output.resolve()
    ReportName = "Prepared.json" if Args.mode == "prepare" else "Checked.json"
    if Args.output.is_symlink() or OutputRoot.is_relative_to(ROOT) or (OutputRoot / ReportName).exists():
        Parser.error("output must be a fresh external task owned location")
    if Args.mode == "prepare" and OutputRoot.exists():
        Parser.error("preparation must not enter an existing directory")
    if Args.mode == "verify" and (not (OutputRoot / "Prepared.json").is_file() or (OutputRoot / "Prepared.json").is_symlink()):
        Parser.error("verification requires its completed owned preparation report")
    try:
        Result = PrepareBatch(OutputRoot) if Args.mode == "prepare" else VerifyBatch(OutputRoot)
    except Exception as Error:
        Result = {"passed": False, "error_type": type(Error).__name__, "error_sha256": Digest(str(Error).encode("utf-8", "surrogatepass"))}
    Result.update(
        schema="kit.sw2026.cstring-process.v2", scope="eight complete model regenerated archives only",
        writer_output=False, native_acceptance=False, native_field_length_acceptance=False,
        heldout_payloads_read=0, mode=Args.mode, complete_native_document=False,
        donor_template_used=False, saved_stream_passthrough=False,
    )
    if OutputRoot.is_dir():
        SaveReport(OutputRoot / ReportName, Result)
    print(dumps({"mode": Args.mode, "passed": Result["passed"]}))
    return 0 if Result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(MainEntry())
