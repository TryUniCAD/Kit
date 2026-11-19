from dataclasses import dataclass

from downstream.PrismFaceConstructors import prism_face_constructor_fields
from downstream.SurfaceIdentities import clone_collected_surface
from para.Tracking import signed_dword


@dataclass(frozen=True)
class FaceKey:
    row_id: int
    original: int
    swapped: int


def ordinary_surface_description(representation):
    fields = representation.FieldsValue
    keeper = fields["f10"]["f10"].FieldsValue["f10"]
    id_and_time = (keeper["f00"], signed_dword(keeper["f08"]))
    name = representation.ClassValue.NameValue
    if name == "moEndFaceSurfIdRep_c":
        words = (40, *id_and_time, 0, fields["f38"], max(-1, fields["f3c"]))
    elif name == "moFromSktEntSurfIdRep_c":
        words = (74, *id_and_time, 0, fields["f38"])
    else:
        raise ValueError("ordinary face keys require a concrete cap or sketch-line representation")
    return ",".join(map(str, words))


def surface_key_hash(text):
    value = 0
    power = 1
    for byte in text.encode("ascii"):
        value = (value + byte * power) % 1_000_000_009
        power = (power * 32771) % 1_000_000_009
    return value


def prism_face_keys(rows):
    registered = set()
    keys = []
    for row in rows:
        component = row["object"].FieldsValue
        reference = component["fe8"].FieldsValue
        inline = tuple(slot["f08"] for slot in reference["f10"])
        if (component["f68"] or reference["fe8"] or reference["f70"] or len(inline) != 6
                or inline[-1] is not None or any(rep is None for rep in inline[:-1])):
            raise ValueError("face-key storage requires the ordinary direct one-loop constructor")
        primary, first, second, third, fourth = map(ordinary_surface_description, inline[:-1])
        original = surface_key_hash("s," + primary + first + second + third + fourth)
        swapped = surface_key_hash("s," + primary + second + first + third + fourth)
        if not original or original in registered or swapped in registered:
            raise ValueError("face-key storage requires the native noncollision path")
        keys.append(FaceKey(row["word"], original, swapped))
        registered.add(original)
    return tuple(keys)


def prism_face_store_fields(archive, allocation, *, special_id_map_present):
    fields = prism_face_constructor_fields(archive, allocation, special_id_map_present=special_id_map_present)
    rows = fields["f48"]
    collected = {}
    for row in rows:
        selected_surface = row["object"].FieldsValue["fe8"].FieldsValue["f10"][0]["f08"]
        description = ordinary_surface_description(selected_surface)
        if description in collected:
            raise ValueError("ordinary face collection requires distinct primary surface identities")
        collected[description] = clone_collected_surface(selected_surface)
    for row in rows:
        for slot in row["object"].FieldsValue["fe8"].FieldsValue["f10"]:
            representation = slot["f08"]
            if representation is not None:
                slot["f08"] = collected[ordinary_surface_description(representation)]
    return fields | {"f40": [{"object": surface} for surface in collected.values()]}, prism_face_keys(rows)
