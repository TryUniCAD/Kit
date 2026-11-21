from random import Random
from pathlib import Path
import os
import re
import secrets

from PatternEnvelopeSpec import measure, moved, specification


SLOTS = ("Slot01", "Slot02")
SCHEMA = "kit.sw2026.linear-pattern-datum-private-intent.v1"
ROLE_ORDER = ("original", "spacing", "instances")
RANGES_UM = (
    {"plate_x": (153000, 165000), "plate_y": (110000, 119000), "plate_z": (6750, 8250),
     "seed_x": (89000, 96000), "seed_y": (60000, 67000), "seed_dx": (8000, 11000),
     "seed_dy": (7000, 9500), "seed_z": (15500, 17400), "spacing": (17250, 19250), "spacing_edit": (26250, 31000)},
    {"plate_x": (131000, 142000), "plate_y": (79000, 84000), "plate_z": (4250, 5200),
     "seed_x": (42000, 48000), "seed_y": (55000, 60000), "seed_dx": (10000, 13000),
     "seed_dy": (4300, 6200), "seed_z": (24000, 27500), "spacing": (22250, 24750), "spacing_edit": (31500, 34250)},
)


def physical_state(plate, seed, pitch, count):
    copies = [moved(seed, index * pitch) for index in range(count)]
    if not all(plate[0][axis] < low[axis] < high[axis] < plate[1][axis]
               for low, high in copies for axis in (0, 1)):
        raise ValueError("all authored and repeated seed profiles must be over the joined plate")
    if not all(first[1][0] < second[0][0] for first, second in zip(copies, copies[1:])):
        raise ValueError("individual bosses must remain disjoint above the plate")
    return {"spacing_m": pitch, "count": count, "expected_final": measure((plate, *copies))}


def case_design(values, count):
    def m(name):
        return values[name] / 1_000_000

    stock = ((0.0, 0.0, 0.0), (m("plate_x"), m("plate_y"), m("plate_z")))
    seed = ((m("seed_x"), m("seed_y"), 0.0),
            ((values["seed_x"] + values["seed_dx"]) / 1_000_000,
             (values["seed_y"] + values["seed_dy"]) / 1_000_000, m("seed_z")))
    if not 0 < stock[1][2] < seed[1][2] or not m("spacing") < m("spacing_edit"):
        raise ValueError("require positive raised seeds and a substantive spacing edit")
    initial = physical_state(stock, seed, m("spacing"), count)
    spacing = physical_state(stock, seed, m("spacing_edit"), count)
    instances = physical_state(stock, seed, m("spacing"), count + 1)
    if all(initial["expected_final"]["centroid_m"][axis] == spacing["expected_final"]["centroid_m"][axis]
           for axis in (0, 1)) or instances["expected_final"]["volume_m3"] <= initial["expected_final"]["volume_m3"]:
        raise ValueError("both private driver edits must make a physical difference")
    return {"plate_box_m": stock, "seed_box_m": seed, "expected_before_pattern": measure((stock, seed)),
            "states": {"original": initial, "spacing": spacing, "instances": instances}}


def case_from_seed(seed):
    if os.name != "nt" or not re.fullmatch("[0-9a-f]{64}", seed):
        raise ValueError("private derivation requires a Windows custodian and a valid entropy seed")
    rng = Random(int(seed, 16))
    rows = []
    for slot, ranges in zip(SLOTS, RANGES_UM, strict=True):
        values = {key: rng.randint(*ends) for key, ends in ranges.items()}
        values["count"] = rng.randint(2, 3)
        stem = f"Pattern-{rng.getrandbits(128):032x}"
        names = {"original": stem + ".SLDPRT", "spacing": stem + "-Pitch.SLDPRT",
                 "instances": stem + "-Count.SLDPRT"}
        rows.append({"slot": slot, "case_values": values, "filenames": names,
                     "design": case_design(values, values["count"])})
    return rows


def new_intent(packet_sha256, revision, timestamp_ns):
    if os.name != "nt":
        raise ValueError("private generation runs only in the Windows guest")
    secret_seed = secrets.token_hex(32)
    return {"schema": SCHEMA, "cohort": "heldout", "packet_sha256": packet_sha256,
            "source_revision": revision, "sealed_at_unix_ns": timestamp_ns,
            "guest_seed": secret_seed, "cases": case_from_seed(secret_seed)}


def intent_spec(row, variant):
    recipe = specification()
    authored = row["design"]
    return {"hinge": recipe["hinge"], "direction_datum": recipe["direction_datum"], "pattern": recipe["pattern"],
            "plate_box_m": authored["plate_box_m"], "seed_box_m": authored["seed_box_m"],
            "expected_before_pattern": authored["expected_before_pattern"],
            "arms": [authored["states"][kind] for kind in ("original", variant)]}


def require_private_dir(path, root):
    if os.name != "nt" or path.drive.upper() != "C:" or not path.is_absolute() or not path.is_relative_to(root):
        raise ValueError("private data must remain in its reserved local C drive")
    for directory in (path, *path.parents):
        if directory.exists() and (directory.is_symlink() or directory.is_junction()):
            raise ValueError("private storage contains a link or junction")
    if path.resolve() != path or Path(root.anchor).resolve().drive.upper() != "C:":
        raise ValueError("private storage resolves outside its fixed local C drive")
