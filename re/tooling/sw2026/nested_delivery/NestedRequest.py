from hashlib import sha256
from pathlib import Path, PureWindowsPath
from convert.adapters.solidworks.Archive.Construction.Geometry.MakePlaneFrame import MakePlaneFrame
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument, ComponentDoc
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.serialization.Deserialize import FromData

def digest(raw):
    return sha256(raw).hexdigest()


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def checked(path, expected):
    raw = path.read_bytes()
    require(digest(raw) == expected and not path.is_symlink(), f"disclosed nested identity differs: {path.name}")
    return raw


def authored_document(request):
    definitions = []
    parts = []
    occurrences = []
    configs = {}
    root = request["root"]
    source_rows = request["definitions"]
    root_settings = next(row["request"] for row in source_rows if row["id"] == root)
    root_planes = root_settings["system"]["planes"]
    for row in source_rows:
        identity, kind, settings = row["id"], row["kind"], row["request"]
        if kind == "part":
            part = FromData(settings["document"])
            document_id = "doc:" + identity
            parts.append(ComponentDoc(document_id, part))
            selected, = part.configurations
            definition = ComponentDef(identity, part.metadata["name"], kind, document_id=document_id,
                                      configuration_id=selected.id, configuration_name=selected.name,
                                      body_ids=tuple(body.id for body in part.bodies))
        else:
            require(kind == "assembly" and settings["system"]["planes"] == root_planes, "unexpected disclosed assembly datums")
            selected = Configuration("cfg:" + identity, settings["configuration_name"], active=True)
            definition = ComponentDef(identity, settings["name"], kind,
                                      configuration_id=selected.id, configuration_name=selected.name)
        configs[identity] = selected
        definitions.append(definition)
    for row in source_rows:
        owner = row["id"]
        for index, pair in enumerate(row.get("occurrences", ())):
            value, target = pair["occurrence"], pair["target"]
            frame = MakePlaneFrame(tuple(value["origin"]), tuple(value["u"]), tuple(value["v"]))
            pose = tuple(component for axis in range(3) for component in (
                frame.AxisU[axis], frame.AxisV[axis], frame.NormalValue[axis], 1000 * frame.OriginValue[axis])) + (0, 0, 0, 1)
            selected = configs[target]
            occurrences.append(ComponentInst(f"inst:{owner}:{index}", value["name"], target, owner,
                                             TransformMatrix(pose), order=index,
                                             configuration_name=selected.name, configuration_id=selected.id))
    planes = tuple(SupportPlane("plane:" + axis, name, Transform(*(SpaceVector(*vector) for vector in
                   (frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue))))
                   for axis, name in root_planes.items() for frame in (PrincipalFrame(axis),))
    doc = CadDocument(CadSource("neutral", "authored nested model", ""), (configs[root],), (), planes, (), (), (), (),
                      metadata={"name": root_settings["name"]},
                      assembly=AssemblyData(root, tuple(definitions), tuple(occurrences), tuple(parts)))
    return doc, root_settings["output"]
