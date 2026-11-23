from dataclasses import dataclass
from hashlib import sha256

from convert.adapters.freecad.BodyLineage.BoxPrismRoles import FindBoxRole
from convert.adapters.freecad.EditShape.Prism.PrismFaces import CheckFaceMut
from convert.adapters.freecad.EditShape.Prism.PrismProof import PrismProof
from convert.adapters.freecad.EditShape.Prism.PrismRaw import ReadPrismRaw
from convert.adapters.freecad.EditShape.PrismShape import HasUsedCarriers
from convert.Geometry.Opencascade import (
    BuildModel,
    PlacementState,
    PlaceRecordMut,
    Reference,
)
from FcstdRectangleOwners01 import require

KINDS = ("Edge", "Face", "Vertex")


@dataclass(frozen=True)
class Occurrence:
    entity_id: str
    role: str
    record: int
    chain: tuple[tuple[int, int], ...]


def first_occurrences(raw):
    pending = [(raw.RootRef, ())]
    seen = {}
    matrices = {}
    while pending:
        leaf, parent = pending.pop()
        chain = raw.Place(leaf, parent)
        key = (leaf.RecordA, chain)
        if key in seen:
            continue
        matrix_key = (leaf.RecordA, raw.Matrix(chain))
        require(
            matrix_key not in matrices,
            "distinct symbolic placements collapse to one matrix",
        )
        matrices[matrix_key] = key
        seen[key] = matrix_key
        children = raw.Records[leaf.RecordA].Children
        pending.extend((child, chain) for child in reversed(children))
    require({key[0] for key in seen} == raw.Records.keys(), "unowned placed Pad record")
    return seen


def boundary_roles(raw, expected):
    proof = PrismProof(raw, expected)
    (shell,) = raw.Records[raw.RootRef.RecordA].Children
    position = raw.Place(shell, raw.Place(raw.RootRef))
    faces = {}
    for reference in raw.Records[shell.RecordA].Children:
        key = (reference.RecordA, raw.Place(reference, position))
        require(key not in faces, "repeated placed Pad face")
        faces[key] = CheckFaceMut(proof, shell, reference, position)
    require(
        len(faces) == len(expected.Faces)
        and set(faces.values()) == expected.Faces.keys()
        and len(proof.Edges) == len(expected.Edges)
        and len(proof.Vertices) == len(expected.Points)
        and HasUsedCarriers(proof),
        "incomplete Pad prism incidence or shared carriers",
    )
    result = {
        key: ("Face", FindBoxRole(expected, vertices))
        for key, vertices in faces.items()
    }
    result.update(
        {
            key: ("Edge", FindBoxRole(expected, vertices))
            for key, vertices in proof.Edges.items()
        }
    )
    result.update(
        {
            key: ("Vertex", FindBoxRole(expected, (vertex,)))
            for key, vertex in proof.Vertices.items()
        }
    )
    require(len(set(result.values())) == len(result), "ambiguous Pad boundary roles")
    return result


def read_occurrences(payload, body_id, feature_id, expected):
    raw = ReadPrismRaw(payload.data, 4, True)
    occurrences = first_occurrences(raw)
    roles = boundary_roles(raw, expected)
    prefix = "freecad:occ:" + sha256(payload.id.encode()).hexdigest()[:20]
    matrices = tuple(raw.Matrix(chain) for chain in raw.Chains[1:])
    state = PlacementState(
        raw.Curves, raw.Surfaces, raw.Records, matrices, prefix, [], [], {}, {}, {}, {}
    )
    placed = PlaceRecordMut(
        state, raw.RootRef.RecordA, raw.Matrix(raw.Place(raw.RootRef))
    )
    require(
        set(occurrences.values()) == state.RecordCache.keys(),
        "strict placed graph loses a symbolic occurrence",
    )
    root = Reference(raw.RootRef.Orientation, placed)
    model = BuildModel(
        tuple(state.PlacedCurves),
        tuple(state.PlacedSurfaces),
        state.PlacedRecords,
        root,
        prefix,
        body_id,
        {"brep_payload_id": payload.id, "feature_id": feature_id},
    )
    grouped = {kind: [] for kind in KINDS}
    for key, matrix in occurrences.items():
        if key in roles:
            kind, role = roles[key]
            identity = f"{prefix}:{kind.lower()}:{state.RecordCache[matrix]}"
            grouped[kind].append(Occurrence(identity, role, key[0], key[1]))
    require(
        sum(map(len, grouped.values())) == len(roles), "unindexed placed Pad boundary"
    )
    return model, grouped
