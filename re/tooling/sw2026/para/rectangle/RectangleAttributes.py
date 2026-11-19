from dataclasses import dataclass
from math import isfinite

from .Allocate import Ref, positive_i32, require
from .AttributeChains import Install, register_attributes
from para.DownstreamIds import install_part_downstream
from builders.Model import logged_creation_time
from para.Tracking import signed_dword


FIRST_PROCESS_FACE_ID = 1
LOCAL_FEATURE_REFERENCE_FLAGS = 0
FIRST_CLOSED_CONTOUR_ID = 0


@dataclass(frozen=True)
class Appearance:
    rgb: tuple[int, int, int]
    transparency: float
    density_kg_m3: float | None = None

    def __post_init__(self):
        require(len(self.rgb) == 3 and all(type(c) is int and 0 <= c <= 255 for c in self.rgb),
                "appearance requires three RGB bytes")
        require(isfinite(self.transparency) and 0.0 <= self.transparency <= 1.0,
                "transparency must be in the unit interval")
        require(self.density_kg_m3 is None or (isfinite(self.density_kg_m3) and self.density_kg_m3 > 0),
                "present body density must be positive and finite")


def feature_created_at(model_header, feature):
    matches = [
        row["o"] for row in model_header["f20"]["items"]
        if row["o"]["f48"] == feature["f08"]
    ]
    require(len(matches) <= 1, "a feature cannot have multiple revision logs")
    timestamps = tuple(row["o"]["f18"] for row in matches[0]["items"]) if matches else ()
    return signed_dword(logged_creation_time(timestamps=timestamps))


def face_payload(role, feature_id, creation_second, unique_id):
    feature_ref = (feature_id, creation_second, LOCAL_FEATURE_REFERENCE_FLAGS)
    if role.cap:
        require(role.number in (0, 1), "ordinary blind boss cap role must select start or end")
        primary = (40, *feature_ref, role.number, FIRST_CLOSED_CONTOUR_ID)
    else:
        require(type(role.number) is int and role.number >= 0, "side face requires an allocated sketch line id")
        primary = (74, *feature_ref, role.number)
    return None, None, primary, (positive_i32(unique_id, "process face id"), 0)


def scalar_slots(slots):
    return tuple(v if v is None or isinstance(v, tuple) else (v,) for v in slots)


def prism_installs(brep, face_roles, tracking, feature_id, creation, appearance, previous_face_allocations):
    require(type(previous_face_allocations) is int and previous_face_allocations >= 0,
            "provide the count of earlier face-identification events")
    body = Ref(brep.bodies[0].id)
    caps = {role.number: name for name, role in face_roles.items() if role.cap}
    sides = tuple(name for name, role in face_roles.items() if not role.cap)
    attributed_faces = (caps[1], caps[0], *sides)
    for ordinal, name in enumerate(attributed_faces, FIRST_PROCESS_FACE_ID + previous_face_allocations):
        face = Ref(name)
        yield Install(face, "DOWNSTREAM_FACE_ID", tracking.face_fields[name]["DOWNSTREAM_FACE_ID"])
        yield Install(face, "FACE_ID_2001", face_payload(face_roles[name], feature_id, creation, ordinal))
    for name in ("ENT_TIME_STAMP_2001", "ATOM_ID_2001", "LAST_BODY_MODIFYING_FEATURE_ID", "SWIMPLICITBODYNAME_ID_U"):
        yield Install(body, name, scalar_slots(tracking.body_fields[name]))
    for name in face_roles:
        yield Install(Ref(name), "SWEntUnchanged", scalar_slots(tracking.face_fields[name]["SWEntUnchanged"]))
    yield Install(body, "BODY_MATCH", scalar_slots(tracking.body_fields["BODY_MATCH"]))
    yield Install(body, "BODY_RECIPE_2001", (None, None))
    if appearance.density_kg_m3 is not None:
        yield Install(body, "SDL/TYSA_DENSITY", ((appearance.density_kg_m3,), None))
    yield Install(body, "SDL/TYSA_COLOUR_2", (tuple(component / 255 for component in appearance.rgb),))
    yield Install(body, "SDL/TYSA_TRANSLUCENCY_2", ((appearance.transparency,),))
    yield Install(body, "BODY_IN_LIGHTWEIGHT_PERM", (None, (1,)))


def rectangle_installs(child, plan, appearance, previous_face_allocations):
    require(plan.archive.atom["f144"] == 0 and plan.archive.atom["f188"] == 1,
            "cache appearance requires a fresh visible solid atom")
    return prism_installs(plan.brep, plan.face_roles, plan.tracking, plan.archive.feature_id,
                          feature_created_at(child.model_header, child.extrusion.feature),
                          appearance, previous_face_allocations)


def append_rectangle_attributes(child, plan, topology, appearance, first_node_identifier, previous_face_allocations=0, *, downstream=None):
    body = Ref(plan.brep.bodies[0].id)
    installations = tuple(rectangle_installs(child, plan, appearance, previous_face_allocations))
    if downstream is not None:
        installations = install_part_downstream(topology, installations, downstream)
    return register_attributes(topology, body, installations, first_node_identifier)
