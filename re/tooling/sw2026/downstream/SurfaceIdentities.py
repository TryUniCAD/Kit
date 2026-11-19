from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import MakeFileConfig
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from para.Tracking import signed_dword
from para.concentric.CylinderFace import node, words


@dataclass(frozen=True)
class SurfaceIdentity:
    node_id: int
    representation: ArchiveNode


def clone_collected_surface(identity):
    representation = identity.representation
    fields = representation.FieldsValue
    base = fields["f10"]
    keeper = base["f10"]
    owner = keeper.FieldsValue["f08"]
    file_fields = owner.FieldsValue
    copied_owner = ArchiveNode(owner.ClassValue, {
        **file_fields,
        "f60": 0,
        "f78": -1,
        "refcfg": dict(file_fields["refcfg"]),
    })
    copied_keeper = ArchiveNode(keeper.ClassValue, {
        "f08": copied_owner,
        "f10": dict(keeper.FieldsValue["f10"]),
    })
    return ArchiveNode(representation.ClassValue, {
        **fields,
        "f10": {**base, "f10": copied_keeper},
    })


def cylinder_surface_identities(attachment, feature_file):
    candidate = attachment.candidate
    source_file = candidate.HeaderValue.FieldsValue["f38"]
    if not isinstance(feature_file, ArchiveNode) or feature_file.ClassValue.NameValue != "moExtObject_c":
        raise ValueError("surface identities require a typed feature file owner")
    owner = feature_file.FieldsValue
    if (owner["refcfg"] != MakeFileConfig(candidate.SystemValue.RootValue, candidate.CurrentConfig)
            or any(ReadFileText(owner["shared"][field]) != ReadFileText(source_file.FieldsValue["shared"][field])
                   for field in ("h10", "h18"))):
        raise ValueError("surface identities require their actual file and configuration owner")
    boss = candidate.BossValue.FeatureValue
    feature = boss.FieldsValue["f08"]
    birth = DatumTime(candidate.HeaderValue, feature)
    marker = candidate.ProfileValue.GeometryValue.ArcValue.FieldsValue["f08"]
    topology = attachment.projection.partition
    nodes = {item.index: item for item in topology.nodes}
    body, = (ent for ent in topology.nodes if ent.kind == 12)
    atom_id, = words(nodes, body, "ATOM_ID_2001", 1)
    attached_atoms = candidate.SystemValue.RootValue.FieldsValue["fd88"]["atoms"]
    if (atom_id != attachment.atom_id or boss.FieldsValue["f498"] != [{"v": atom_id}]
            or len(attached_atoms) != 1 or attached_atoms[0]["o"] is not boss.FieldsValue["f528"]["items"][0]["o"]):
        raise ValueError("surface identity requires the actual producing feature and its body atom")

    expected = feature, signed_dword(birth), 0
    cap_selectors = set()
    has_side = False
    result = []
    for face in (ent for ent in topology.nodes if ent.kind == 14):
        carrier = nodes[face.fields["surface"]]
        if carrier.fields["owner"] != face.index:
            raise ValueError("surface carrier has a foreign face owner")
        code, owner_id, creation, flags, *local = words(nodes, face, "FACE_ID_2001", 2)
        if (owner_id, creation, flags) != expected:
            raise ValueError("surface identity belongs to a different feature or creation epoch")
        keeper = node("moFR_c", {"f08": feature_file, "f10": {"f00": feature, "f08": birth}})
        fields = {"f10": {"f08": None, "f10": keeper}}
        if code == 74 and carrier.kind == 51 and local == [marker] and not has_side:
            representation = node("moFromSktEntSurfIdRep_c", {**fields, "f38": marker})
            has_side = True
        elif code == 40 and carrier.kind == 50 and len(local) == 2:
            selector, contour = local
            if selector not in (0, 1) or contour != 0 or selector in cap_selectors:
                raise ValueError("an ordinary cap requires its distinct native end selector")
            representation = node("moEndFaceSurfIdRep_c", {**fields, "f38": selector, "f3c": contour})
            cap_selectors.add(selector)
        else:
            raise ValueError("the generated face has no admitted cylinder surface identity")
        result.append(SurfaceIdentity(face.fields["node_id"], representation))

    if len(result) != 3 or not has_side or cap_selectors != {0, 1}:
        raise ValueError("cylinder surface identities require the actual side and two caps")
    return tuple(result)
