from dataclasses import replace
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from sys import addaudithook
from argparse import ArgumentParser
from uuid import NAMESPACE_URL, uuid5

from convert import open_document
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Drawing.Construction.Linked.MakeLinkedFile import MakeLinkedFile
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Drawing.SdkLinked.MakeLinkedJob import MakeLinkedJob
from DrawingSdkLinkedInput import linked_input, part_settings
from downstream.PreparePrismCacheNative import candidate_streams
from downstream.Storage import cache_path
from para.DownstreamIds import allocate_fresh_downstream, owned_solid_chains
from para.Tracking import filetime_ticks
from para.prism.SdkPrismAttachment import attach_sdk_prism
from para.prism.SdkPrismPartition import design_geometry
from para.rectangle.Allocate import allocate_marks
from para.rectangle.ArchiveAttachment import FeatureUpdate
from para.rectangle.CheckProjection import schedule
from para.rectangle.Geometry import topology_nodes
from para.rectangle.RectangleAttributes import Appearance
from para.rectangle.RectanglePartition import complete_topology

def main():
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--windows-root", type=PureWindowsPath, required=True)
    parser.add_argument("--authored-light", type=Path, required=True)
    args = parser.parse_args()
    root = args.output
    root.mkdir()
    guest = args.windows_root
    if not guest.is_absolute():
        raise ValueError("the actual Windows destination directory must be absolute")
    case = "CachedChildDrawing"
    job = MakeLinkedJob(case, 36.3, 18.1, 9.8, "*Front", 1.0)
    part_path = guest / (case + "Child.SLDPRT")
    draw_path = guest / (case + ".SLDDRW")
    job["part"]["settings"]["output"]["path_name"] = str(part_path)
    job["native"]["output"]["path_name"] = str(draw_path)
    draw_intent = FromData(job["drawing_document"])
    ref, = draw_intent.ModelRefs
    job["drawing_document"] = ToData(replace(draw_intent, model_refs=(replace(ref,source_path=str(part_path)),)))
    file = root / "NeutralRequest.json"
    file.open("x",encoding="utf-8",newline="\n").write(dumps(job,indent=2,sort_keys=True)+"\n")
    light = loads(args.authored_light.read_bytes())
    for name in ("utf-8","utf-16-le","utf-16-be","latin-1","cp1252"):
        lookup(name)
    for name in ("convert.adapters.solidworks.Drawing.Definition.Projection.JoinConcept",
                 "convert.adapters.solidworks.Drawing.Definition.ReadConcept"):
        import_module(name)
    document = FromData(job["part"]["document"])
    AssertValid(document)
    active = True
    attempts = []
    def audit(event, values):
        if active and event in ("open","subprocess.Popen","os.system","os.posix_spawn","socket.connect"):
            attempts.append(event)
            raise RuntimeError("unexpected linked construction I/O: " + event)
    addaudithook(audit)
    try:
        inputs = linked_input(job)
        settings = part_settings(job)
        child = MakeBlindPart(document, settings)
        epoch = max(job["part"]["settings"]["provenance"][key] for key in ("created_at","modified_at","updated_at")) + 7
        fraction = 1516903
        session = schedule(3163, 32, 1, 0, 5, 2, 0, epoch, fraction)
        geometry, _, _, _, _ = design_geometry(child)
        topology, _ = complete_topology(topology_nodes(geometry, allocate_marks(session)))
        faces, edges = owned_solid_chains(topology)
        owner = uuid5(NAMESPACE_URL,"urn:kit:solidworks:cached-child:" + child.PlanValue.NameValue)
        allocation = allocate_fresh_downstream(faces,edges,owner,epoch,fraction,is_assembly=False)
        feature_events = (FeatureUpdate(1,epoch,240619,False),
                          FeatureUpdate(4,epoch,551183,True),
                          FeatureUpdate(8,epoch,911150,True))
        attached = attach_sdk_prism(child,session,feature_events,Appearance((86,133,147),0.1,1000.0),light,downstream=allocation)
        child = attached.candidate
        archive = SldprtArchive.from_bytes(child.BytesValue)
        cache = candidate_streams(archive,allocation,filetime_ticks(epoch+1,0))
        assert set(cache) - set(archive.streams) == {cache_path(0)}
        child = replace(child,StreamsValue=cache,BytesValue=BuildSldprt(cache,FormatVersion=4))
        drawing = MakeLinkedFile(inputs,child)
        assert drawing.ChildValue is child
        before = drawing.StreamsValue["Contents/Definition"]
        decoded = ReadNamedDef(before,19000,"*Front")
        assert WriteNamedDef(decoded.GraphValue).OutputValue == before
        read = open_document(drawing.BytesValue,source_format="solidworks.slddrw",strict=False)
        assert read.drawing.ModelRefs[0].SourcePath == str(part_path)
        view, = read.drawing.Sheets[0].Views
        assert view.OrientationName == "*Front"
        assert view.ConfigurationName == inputs.DrawingValue.Sheets[0].Views[0].ConfigurationName
    finally:
        active = False
    (root / draw_path.name).open("xb").write(drawing.BytesValue)
    (root / part_path.name).open("xb").write(child.BytesValue)
    proof = {
        "schema":"kit.sw2026.sdk-drawing-cached-child-host.v1",
        "native_acceptance":False,"heldout_inputs_read":0,"runtime_io_attempts":len(attempts),
        "drawing_sha256":sha256(drawing.BytesValue).hexdigest(),"part_sha256":sha256(child.BytesValue).hexdigest(),
        "part_cache_sha256":sha256(cache[cache_path(0)]).hexdigest(),
        "definition_round_trip":True,"actual_generated_child_identity":True,
        "body_atom_id":attached.prism.atom_id,
        "face_downstream_count":len(allocation.faces),"edge_downstream_count":len(allocation.edges),
        "model_reference":str(part_path),"view_orientation":view.OrientationName,
        "view_id":drawing.ViewValue.FieldsValue["f08"],
        "view_origin":[view.PositionValue.XCoord, view.PositionValue.YCoord],
        "partial_child_reference_matches":True,
    }
    (root / "HostProof01.json").open("x",encoding="utf-8",newline="\n").write(dumps(proof,sort_keys=True,indent=2)+"\n")
    print(dumps(proof,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
