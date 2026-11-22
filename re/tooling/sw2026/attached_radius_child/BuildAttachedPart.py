from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from json import dumps, loads
from math import pi
from pathlib import Path
import sys

sys.path.insert(0, str(Path(sys.argv[1]) / "src"))

from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import MakeFeatTime
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import MakeMgrHeader
from convert.adapters.solidworks.Archive.Construction.Nodes.InitConceptMut import InitConceptMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
from convert.adapters.solidworks.Archive.Construction.System.Members.MakeLightMut import MakeLightMut
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Partition.PartWrite.EncodePartXmt import EncodePartXmt
from convert.adapters.solidworks.Archive.Partition.PartWrite.PartXmtState import PartXmtState
from convert.adapters.solidworks.Archive.Partition.PartWrite.XmtMarkRow import XmtMarkRow
from convert.adapters.solidworks.Archive.Partition.PartWrite.XmtRollback import XmtRollback
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KConfigStream, KPartitionStream, KResolvedFeaturesStream
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadAttachAttr import ReadAttachAttrs
from interchange.brep.Validation import BrepValidate
from interchange.document.Models import DocumentProvenance
from interchange.document.Validation import DocumentFeatureValidate, DocumentReferenceValidate
from interchange.serialization.Deserialize import FromData


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def values(value):
    return tuple(map(values, value)) if isinstance(value, list) else value


def node(row):
    return XmtNode(row["index"], row["kind"], {name: values(value) for name, value in row["fields"].items()})


def mark_state(plan):
    active = tuple(node(row) for row in plan["nodes"])
    by_id = {record.IndexValue: record for record in active}
    require(len(by_id) == len(active), "neutral construction allocated duplicate indexes")
    marks = []
    for row in plan["history"]:
        prior = row["rollback"]
        rollback = None
        if prior:
            deleted = tuple(by_id[index] for index, _ in prior["deleted"])
            require(all(record.KindValue == kind for record, (_, kind) in zip(deleted, prior["deleted"], strict=True)),
                    "rollback references a different allocated kind")
            rollback = XmtRollback(deleted, node(prior["previous_world"]))
        marks.append(XmtMarkRow(node(row["mark"]), rollback))
    return PartXmtState(active, node(plan["root"]), tuple(marks))


def make_mark(state):
    return ArchiveNode(RuntimeClass("moPMarkRecord_c", 1), {"f18": state.Integer("id")})


def publish_body(candidate, state, epoch):
    root = candidate.SystemValue.RootValue.FieldsValue
    model_head = candidate.HeaderValue.FieldsValue
    manager = root["fd88"]
    boss = candidate.BossValue.FeatureValue
    feature = boss.FieldsValue
    require(not manager["atoms"] and manager["n6c"] == manager["fa8"] == 0 and not root["ffe0"]
            and root["fe38"] is None and not feature["has_f528"] and not feature["has_f3d0"]
            and KPartitionStream not in candidate.StreamsValue, "part is already attached")
    body_id = manager["f260"] + 1
    body_stamp = model_head["f44"] + 1
    feature_id = feature["f08"]
    body, = (record for record in state.ActiveValues if record.KindValue == 12)
    attrs = ReadAttachAttrs({record.IndexValue: record for record in state.ActiveValues}, body)
    tag, = attrs["BODY_MATCH"]
    require(attrs["ATOM_ID_2001"] == (body_id,) and attrs["LAST_BODY_MODIFYING_FEATURE_ID"] == (feature_id,)
            and attrs["ENT_TIME_STAMP_2001"] == (body_stamp,), "kernel state differs from real allocated body owners")
    atom = ArchiveNode(RuntimeClass("moAtom_c", 1), {})
    InitConceptMut(atom, candidate.PlanValue.FeatureName)
    atom.FieldsValue.update(f18=None, f140=body_id, f144=0, f130=feature_id, f12c=feature_id,
                            f158=0, body_kind=0, f170=0, f18c=1, f198=-1, f180=tag, f188=1, f1b0=tag, f19c=6)
    marks = {row.MarkValue.IndexValue: row.MarkValue for row in state.MarkValues}
    selected = marks[state.HistoryRoot.Integer("current_pmark")]
    activation = marks[selected.Integer("preceding")]
    owners = (candidate.SystemValue.OriginValue.ProfileValue, candidate.ProfileValue.ProfileValue, boss)
    initial_counter = model_head["f40"]
    update_mask = 0xFFFD7FF8
    for ordinal, member in enumerate(owners, 1):
        fields = member.FieldsValue
        fields.update(MakeFeatTime(FeatureInstant(epoch, ordinal)))
        fields.update(f29c=initial_counter + ordinal, f0c=fields["f0c"] & update_mask)
    root.update(f1300=root["f1300"] + len(owners), f0c=root["f0c"] & update_mask)
    row = [{"o": atom}]
    manager.update(f260=body_id, n6c=len(row), fa8=19000, atoms=row)
    root.update(fe38=make_mark(activation), f1010=1, nff4=1, ffe0=[{"k": atom, "v": 0}])
    feature.update(has_f528=1, f528={"n": 1, "items": row}, f498=[{"v": body_id}], n494=1,
                   has_f3d0=1, f3d0=make_mark(selected), f3c0=0, f3c8=0, f580=0, f540=3)
    update = initial_counter + len(owners)
    candidate.CurrentConfig.FieldsValue["f860"] = update
    for header in (candidate.HeaderValue, candidate.TopHeader):
        header.FieldsValue.update(f40=update, f44=body_stamp, f48=epoch)


def make_scene(candidate, spec, target):
    folder = candidate.SystemValue.RootValue.FieldsValue["f1e0"]
    require(not folder.FieldsValue["f60"]["list"]["items"], "expected an empty scene owner")
    allocator = PersistentIds(candidate.HeaderValue.FieldsValue["f08"])
    inputs = tuple(
        LightInput(**{name: values(value) for name, value in row.items()},
                   CreatedValue=FeatureInstant(spec["epoch"], ordinal))
        for ordinal, row in enumerate(spec["lights"], 1)
    )
    require(tuple(item.KindValue for item in inputs) == ("ambient", "directional", "directional", "directional"),
            "expected the disclosed authored scene input kinds")
    lights = [MakeLightMut(folder, row, target, allocator) for row in inputs]
    folder.FieldsValue["f60"] = {"list": {"n": len(lights), "items": [{"o": row} for row in lights]}, "tail": 0}
    for header in (candidate.HeaderValue, candidate.TopHeader):
        header.FieldsValue["f08"] = allocator.NextValue
    SetCfgStampMut(candidate.CurrentConfig, allocator)


def emit(candidate, partition):
    manager = candidate.SystemValue.ManagerValue
    config, graph = WriteConfigMut(candidate.SystemValue.RootValue, 19000, candidate.HeaderValue)
    resolved, _ = WriteResolMut(candidate.ResolvedValue.RootsValue, None, 19000, graph.MapValue,
                               {"model_compressed_stream": 1, "model_is_part": 1,
                                "cmgr_f658": manager.FieldsValue["f658"]})
    directory = MakeMgrHeader(manager, candidate.ManagerHeader.FieldsValue["f60"])
    streams = dict(candidate.StreamsValue) | {
        "Header2": WriteHeadGraph(candidate.TopHeader, 19000),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(candidate.HeaderValue, 19000),
        "Contents/CMgr": WriteCmgrMut(manager, 19000),
        "Contents/CMgrHdr2": WriteMgrHeader(directory, 19000)[0],
        KConfigStream: config, KResolvedFeaturesStream: resolved, KPartitionStream: partition,
    }
    output = BuildSldprt(streams, FormatVersion=4)
    require(SldprtArchive.from_bytes(output).streams == streams, "part container changed generated logical streams")
    return output, streams


def build(document, state, spec):
    epoch = spec["epoch"]
    plan = ProjectCircle(document)
    require(not plan.IsDiameter and plan.AxisValue == "z" and not plan.IsReversed,
            "only the forward Front radius profile is witnessed")
    recipe = MakePartRecipe(plan, epoch)
    folders = tuple((kind, spec["environment_name"] if kind == "moEnvFolder_c" else name)
                    for kind, name in recipe.SystemValue.FolderValues)
    bound = BindPartIntent(document, plan,
                           replace(recipe, SystemValue=replace(recipe.SystemValue, FolderValues=folders)),
                           SelfFileInput(spec["locator"], epoch))
    candidate = MakeCirclePart(document, bound)
    partition = EncodePartXmt(state)
    publish_body(candidate, state, epoch)
    make_scene(candidate, spec, bound.TargetValue)
    return emit(candidate, partition)


def strict_readback(data, source):
    checked = open_document(data, source_format="solidworks.sldprt", strict=True, include_tessellation=False)
    document = open_document(data, source_format="solidworks.sldprt", strict=True, include_brep=False,
                             include_tessellation=False)
    sketch, = checked.sketches
    profile, boss = (row for row in checked.feature_timeline if row.sketch_id == sketch.id)
    radial, depth = (checked.parameter(row.parameter_ids[0]) for row in (profile, boss))
    source_radial = source.parameter(source.sketches[0].parameter_ids[0])
    source_depth = source.parameter(source.feature_timeline[0].parameter_ids[0])
    geometry = source.sketches[0].entities[0].geometry
    body, = checked.bodies
    require((radial.value, depth.value) == (source_radial.value, source_depth.value)
            and (radial.owner_id, depth.owner_id) == (profile.id, boss.id)
            and (profile.name, boss.name) == (source.sketches[0].name, source.feature_timeline[0].name)
            and body.name == source.bodies[0].name and body.final_feature_id == boss.id
            and (body.topology.solid_count, body.topology.face_count) == (1, 3)
            and checked.parameters == document.parameters and checked.sketches == document.sketches
            and not checked.validate() and checked.brep.bodies[0].design_body_id == body.id,
            "generated child did not retain ordered editable owners and dimensions")
    radius_mm, depth_mm = geometry.radius, source_depth.value.value
    volume = pi * radius_mm ** 2 * depth_mm
    area = 2 * pi * radius_mm * (radius_mm + depth_mm)
    centre = body.attributes["solidworks.body_centroid_mm"]
    require(tuple(format(value, ".6g") for value in (volume, area, geometry.center.x, geometry.center.y, depth_mm / 2))
            == tuple(format(value, ".6g") for value in (body.topology.volume, body.topology.surface_area, *centre)),
            "generated physical shape did not reproduce independent neutral geometry")
    return {"read_depth_mm": depth.value.value, "read_radius_mm": radial.value.value,
            "body_name": body.name, "faces": body.topology.face_count,
            "centre_mm": centre, "native_driver_names": [f"{row.name}@{owner.name}" for row, owner in ((radial, profile), (depth, boss))],
            "area_mm2": body.topology.surface_area, "volume_mm3": body.topology.volume}


def main():
    request = loads(sys.stdin.read())
    source = FromData(request["spec"]["child"])
    source.AssertValid()
    GetDocumentCaps(source)
    plan = mark_state(request["producer"]["xmt"])
    for encoding in ("utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "cp1252"):
        lookup(encoding)
    active = True
    attempts = []

    def audit(event, _):
        if active and event in {"open", "subprocess.Popen", "socket.connect", "os.system", "ctypes.dlopen"}:
            attempts.append(event)
            raise RuntimeError("current attached radius SDK accessed unexpected external input")

    sys.addaudithook(audit)
    try:
        first, streams = build(source, plan, request["spec"])
        require((first, streams) == build(source, plan, request["spec"]),
                "current neutral construction did not deterministically repeat")
        readback = strict_readback(first, source)
    finally:
        active = False
    fingerprints = {name: digest(value) for name, value in streams.items()}
    require(digest(first) == request["producer"]["sha256"] and fingerprints == request["producer"]["streams"]
            and not attempts, "current SDK child differs from independent earlier construction")
    if len(sys.argv) == 3:
        with Path(sys.argv[2]).open("xb") as artifact:
            artifact.write(first)
    print(dumps({"sha256": digest(first), "bytes": len(first), "streams": fingerprints,
                 "repeated_builds": 2, "runtime_external_accesses": len(attempts),
                 "strict_readback": readback}, sort_keys=True))


if __name__ == "__main__":
    main()
