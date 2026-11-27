from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from math import inf, isclose, isfinite, nextafter
from pathlib import Path, PureWindowsPath
import sys
from io import BytesIO

def setup(root):
    sys.path[:0] = [str(root/"src"),str(root/"re/automation"),str(root/"re"),str(root/"re/solidworks/EncoderBoundary")]

def demand(condition, description):
    if not condition:
        raise ValueError(description)

def digest(raw):
    return sha256(raw).hexdigest()

def point_words(point):
    demand(type(point.x) is float and type(point.y) is float, "coordinate words must be explicit real binary64 values")
    return point.x.hex(), point.y.hex()

def lines(sketch):
    order,=sketch.closed_profile_entity_ids
    members={e.id:e.geometry for e in sketch.entities}
    return tuple(members[key] for key in order)

def inherited_positions(sketch):
    rows = tuple(row["native_fields"]["pos"] for row in sketch.attributes["native_point_rows"])
    members={e.id:e for e in sketch.entities}
    order,=sketch.closed_profile_entity_ids
    edges = [members[key].attributes["native_point_indices"] for key in order]
    demand(all(edges[i][1] == edges[(i+1)%len(edges)][0] for i in range(len(edges))), "typed source endpoint aliases differ")
    return tuple((rows[a]["x"], rows[a]["y"]) for a,_ in edges)

def api_endpoint_words(observed):
    if observed["sketch_relations"] != 0:
        raise ValueError("the independently authored sketch has relations")
    records=[]
    for segment in observed["sketch_segments"]:
        if segment["kind"] != 0 or len(segment["points"]) != 2:
            raise ValueError("the independently authored sketch has an unsupported segment")
        edge=[]
        for point in segment["points"]:
            if len(point) != 3 or any(type(value) is not float or not isfinite(value) for value in point):
                raise ValueError("the independently authored endpoint is not a finite typed position")
            if point[2] != 0.0:
                raise ValueError("independent endpoint leaves the Front plane")
            edge.append(tuple(value.hex() for value in point[:2]))
        records.append(tuple(edge))
    return tuple(records)


def produce(args):
    setup(args.root)
    from ExactDepthIntent import read_witness
    from InspectVendorBodyOwners import cases

    args.case="BaselineSource"
    evidence=read_witness(args)
    from EncoderRoundTrip.Artifacts import canonical_json
    from EncoderRoundTrip.Source import encode_writer_input
    from convert import open_document
    from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Enums.EnumUnits import UnitSystem
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.Transform import KTransformIdentity
    from interchange.geometry.Models.VectorPlane import PlaneVector

    authored=CadDocument.from_json(args.authored.read_text(encoding="utf-8"))
    encode_writer_input(authored)
    PlanPartWrite(authored)
    _,path,archive_hash,record_hash,observed = next(row for row in cases(args.source_record) if row[0]==args.case)
    raw=path.read_bytes()
    demand(
        archive_hash==digest(raw)==evidence["source_archive_sha256"]
        and record_hash==evidence["author_record_sha256"],
        "source evidence changed before coordinate inspection",
    )
    view=open_document(raw,source_format="solidworks.sldprt",strict=True)
    source_sketch,=view.sketches
    plane,=tuple(row for row in view.support_planes if row.id==source_sketch.support_plane_id)
    demand(
        source_sketch.id==evidence["source_sketch_id"] and source_sketch.attributes.get("typed_line_loop") is True
        and not source_sketch.suppressed and not source_sketch.constraints
        and plane.name=="Front Plane" and plane.transform==KTransformIdentity,
        "source lacks the proven typed Front sketch and zero-origin identity frame",
    )
    points=inherited_positions(source_sketch)
    demand(3 <= len(points) <= 64,"typed source profile has an unsupported size")
    positions=tuple(PlaneVector(*pair) for pair in points)
    closed=positions[1:]+positions[:1]
    measured=api_endpoint_words(observed)
    native=tuple((point_words(a),point_words(b)) for a,b in zip(positions,closed,strict=True))
    findings=[
        {"edge":index,"stored_xy_words":stored,"api_xy_words":recorded}
        for index,(stored,recorded) in enumerate(zip(native,measured))
        if stored!=recorded
    ]
    demand(len(native)==len(measured) and not findings, f"source and independently measured directed endpoints differ: {findings!r}")
    base,=authored.sketches
    authored_points=tuple((item.start.x,item.start.y) for item in lines(base))
    api_points=tuple((segment["points"][0][0]*1000,segment["points"][0][1]*1000) for segment in observed["sketch_segments"])
    demand(authored_points==api_points,"authored reference does not match the independently measured directed profile")
    entities=tuple(
        replace(base.entities[0],id=f"{base.id}:line:{i}",geometry=LineGeometry(a,b))
        for i,(a,b) in enumerate(zip(positions,closed,strict=True),1)
    )
    sketch=replace(base,entities=entities,closed_profile_entity_ids=(tuple(x.id for x in entities),))
    driver,=authored.parameters
    feature,=authored.feature_timeline
    quantity=replace(driver.value,value=float.fromhex(evidence["native_driver_m_binary64"]),unit="m")
    document=replace(authored,units=UnitSystem.KMeter,sketches=(sketch,),parameters=(replace(driver,value=quantity),),
                     feature_timeline=(replace(feature,definition=replace(feature.definition,length=quantity)),))
    encode_writer_input(document)
    validate_si_plan(document)
    value={"schema":"kit.research.exact-sketch.v1","document":document.to_dict(),"display_units":"mm"}
    data=canonical_json(value)
    with args.request.open("xb") as target:
        target.write(data)
    return {
        "request_sha256":digest(data),"source_sha256":evidence["source_archive_sha256"],
        "author_record_sha256":evidence["author_record_sha256"],"dependency":evidence["reader_revision"],
        "directed_body_comparisons":evidence["directed_body_comparisons"],
        "exact_api_endpoint_xy_words":4*len(native),"zero_api_endpoint_z_values":2*len(native),
    }

def validate_si_plan(document):
    from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
    from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import ProjectBlind
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import ReadLineLoop
    from convert.Geometry.Extrude.Polygon.PrismRing import CheckSimpleRing, MeasureRing
    from convert.Geometry.Extrude.Polygon.RingPredicates import ToRingGrid
    from interchange.geometry.Models.VectorPlane import PlaneVector

    CheckPlainScope(document)
    demand(document.units=="m","the geometry document must declare metres")
    demand(document.capabilities <= KPartWriteCaps,"unsupported document capabilities")
    plan=ProjectBlind(document,ReadLineLoop)
    quantity=document.parameters[0].value
    demand(quantity.unit=="m" and type(quantity.value) is float and plan.DepthValue.hex()==quantity.value.hex(),"the exact D1 must declare a finite metre quantity")
    edges=lines(document.sketches[0])
    starts=tuple(point_words(edge.start) for edge in edges)
    ends=tuple(point_words(edge.end) for edge in edges)
    demand(starts[1:]+starts[:1]==ends,"shared endpoint binary64 words disagree")
    demand(tuple(tuple(c.hex() for c in point) for point in plan.VerticesValue)==starts,"SI projection changed coordinate words")
    demand(plan.PlaneName=="Front Plane","expected canonical Front support")
    grid,_=ToRingGrid(tuple(PlaneVector(*point) for point in plan.VerticesValue))
    CheckSimpleRing(grid)
    _,area,perimeter=MeasureRing(tuple(PlaneVector(x/0.001,y/0.001) for x,y in plan.VerticesValue))
    height=plan.DepthValue*1000
    demand(isfinite(area*height) and area*height>0 and isfinite(2*area+height*perimeter),"exact SI plan exceeds readable prism bounds")
    return plan

def make_mm_view(document):
    from interchange.Enums.EnumUnits import UnitSystem
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.VectorPlane import PlaneVector
    sketch,=document.sketches
    def mm(point):
        return PlaneVector(point.x/0.001,point.y/0.001)
    entities=tuple(replace(e,geometry=LineGeometry(mm(e.geometry.start),mm(e.geometry.end))) for e in sketch.entities)
    # The required Front frame is already exactly at the origin with unit axes.
    return replace(document,units=UnitSystem.KMillimeter,sketches=(replace(sketch,entities=entities),))

def generate(args):
    setup(args.root)
    from EncoderRoundTrip.Artifacts import canonical_json,read_record
    from EncoderRoundTrip.Source import encode_writer_input
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
    from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
    from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import ReadLineLoop as ReadNativeRing
    from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
    from interchange.document.Models.DocumentModel import CadDocument

    data=args.request.read_bytes()
    record=read_record(data)
    demand(set(record)=={"schema","document","display_units"} and record["schema"]=="kit.research.exact-sketch.v1" and record["display_units"]=="mm", "explicit mm display intent is required")
    document=CadDocument.from_dict(record["document"])
    demand(encode_writer_input(document)==canonical_json(record["document"]) and canonical_json(record)==data,"geometry request must round-trip exactly")
    for codec in ("ascii","latin-1","cp1252","utf-8","utf-16-le","utf-16-be"):lookup(codec)
    active,attempts=True,[]
    def audit(event,_):
        if active and (event in ("open","os.listdir","os.scandir","os.system","os.exec","os.startfile","os.spawn","os.posix_spawn","os.fork","os.forkpty")
                       or event.startswith(("subprocess.","socket.","ctypes.","winreg."))):
            attempts.append(event)
            raise RuntimeError("construction attempted external access " + event)
    sys.addaudithook(audit)
    try:
        plan=validate_si_plan(document)
        mm=make_mm_view(document)
        PlanPartWrite(mm)
        RequirePartPath(args.locator,args.epoch)
        settings=CheckPartOpts(WriteOptions(values={"final_destination":args.locator}))
        candidate=RunPartPrep(mm,BytesIO(),plan,MakePartRecipe(plan,args.epoch),settings)
    finally:
        active=False
    demand(not attempts and not any(x.startswith(("win32com","pythoncom")) for x in sys.modules),"offline boundary failed")
    raw=candidate.BytesValue
    archive=SldprtArchive.from_bytes(raw,"<generated SI sketch>")
    demand(not any(name.startswith("Kit/") or name.endswith("-Partition") for name in archive.streams), "candidate includes an opaque carrier")
    link=ReadNativeLink(archive,0)
    nodes=IndexFeatures(link)
    owner,=tuple(ReadExtrude(link,node,nodes) for node in nodes.values() if node.ClassValue.NameValue=="moExtrusion_c")
    native_ring=ReadNativeRing(owner.ProfileValue.FieldsValue["pd_f80"],link)
    start_indices=tuple(native_ring.LinesValue[i].StartValue for i in native_ring.OrderValue)
    ends=tuple(native_ring.LinesValue[i].EndValue for i in native_ring.OrderValue)
    words=tuple(tuple(native_ring.PointsValue[i].FieldsValue["pos"][k].hex() for k in ("x","y")) for i in start_indices)
    demand(start_indices[1:]+start_indices[:1]==ends and words==tuple(point_words(edge.start) for edge in lines(document.sketches[0])),"typed native coordinate bits or endpoint aliases differ")
    config=ReadPartConfig(archive).RootValue.FieldsValue
    tables=[]
    for field in ("f9b8","f9c0"):
        rows={r["o"].ClassValue.NameValue:r["o"].FieldsValue for r in config[field].FieldsValue["items"]}
        tables.append([rows["moLengthUserUnits_c"]["fb0"],rows["moUnitSysUnits_c"]["fb0"]])
    demand(tables==[[0,4],[2,1]],"typed display mmgs or analysis SI table differs")
    native_depth=owner.DepthValue.Parameter.FieldsValue["f58"]
    decoded=open_document(raw,source_format="solidworks.sldprt",strict=True)
    driver,=decoded.parameters
    boss,=tuple(r for r in decoded.feature_timeline if r.id==driver.owner_id)
    body,=decoded.bodies
    demand(native_depth.hex()==plan.DepthValue.hex()==driver.attributes["native_value"].hex() and driver.name=="D1" and driver.role=="driving"
           and boss.definition.length==driver.value and boss.parameter_ids==(driver.id,) and body.final_feature_id==boss.id,"strict or typed linked D1 differs")
    expected,volume,_,bounds=BuildPrism(body.id,mm.support_planes[0].transform,lines(mm.sketches[0]),0.0,plan.DepthValue/.001)
    observed=ReadMassRings(decoded.brep)
    target=ReadMassRings(expected)
    def matches(ring,other):
        return len(ring)==len(other) and any(ring==other[i:]+other[:i] for i in range(len(other)))
    binding=[tuple(i for i,ring in enumerate(target) if matches(actual,ring)) for actual in observed]
    count=[len(decoded.brep.faces),len(decoded.brep.edges),len(decoded.brep.vertices)]
    demand(body.topology.solid_count==1 and body.topology.bounding_box==bounds and isclose(body.topology.volume,volume,rel_tol=0,abs_tol=1e-7)
           and len(target)==len(observed) and all(len(row)==1 for row in binding) and len(set(binding))==len(target)
           and count==[len(expected.faces),len(expected.edges),len(expected.vertices)],"strict SDK solid geometry or topology differs")
    impossible=[]
    for ix,(x,y) in enumerate(plan.VerticesValue):
        for axis,v in (("x",x),("y",y)):
            q=v/.001
            if not any((p*.001).hex()==v.hex() for p in (q,nextafter(q,-inf),nextafter(q,inf))):
                impossible.append([ix,axis,v.hex()])
    demand(digest(args.request.read_bytes())==digest(data),"original request changed")
    args.output.mkdir()
    with (args.output/PureWindowsPath(args.locator).name).open("xb") as dest:dest.write(raw)
    result={"scope":"offline SI coordinate feasibility","request_sha256":digest(data),"candidate_sha256":digest(raw),"candidate_bytes":len(raw),
            "coordinate_words_m":words,"no_exact_mm_inverse":impossible,"native_unit_table_codes":tables,"d1_m_word":native_depth.hex(),
            "topology":count,"volume_mm3":body.topology.volume,"geometry_rings":len(observed),"external_access_attempts":len(attempts),"native_launches":0}
    with (args.output/"Evidence.json").open("xb") as dest:dest.write(canonical_json(result))
    return result

if __name__=="__main__":
    parser=ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[3])
    cmds=parser.add_subparsers(dest="mode",required=True)
    prep=cmds.add_parser("produce"); emit=cmds.add_parser("generate")
    for cmd in (prep,emit):cmd.add_argument("--request",type=Path,required=True)
    prep.add_argument("--authored",type=Path,required=True)
    prep.add_argument("--source-record",type=Path,required=True)
    prep.add_argument("--dependency-root",type=Path,required=True)
    emit.add_argument("--output",type=Path,required=True); emit.add_argument("--locator",required=True); emit.add_argument("--epoch",type=int,required=True)
    args=parser.parse_args()
    args.root=args.root.resolve()
    result=produce(args) if args.mode=="produce" else generate(args)
    print(json.dumps(result,sort_keys=True,allow_nan=False))
