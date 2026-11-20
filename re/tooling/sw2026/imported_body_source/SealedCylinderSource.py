from math import hypot
import os
import secrets

from AuthorCurves import require
from AuthorImportedBody import ImportedBodyAuthor
from ObserveCylinderExchange import measure_cylinder


SCHEMA = "kit.sw2026.sealed-cylinder-author-specification.v1"
SLOT_NAMES = ("CylinderSlot01", "CylinderSlot02")
SOURCE_PROFILE = "single_closed_periodic_cylinder"
OBSERVATIONS_PER_PHASE = 2


def sample_between(low, high):
    return low + secrets.randbelow(high - low + 1)


def sample_cylinder(coordinate_bands, signs, radius_band, height_band):
    axis_values = tuple(sign * sample_between(157, 991) for sign in signs)
    length = hypot(*axis_values)
    return {
        "face_center_m": tuple(sample_between(*band) / 1e6 for band in coordinate_bands),
        "axis": tuple(value / length for value in axis_values),
        "radius_m": sample_between(*radius_band) / 1e6,
        "height_m": sample_between(*height_band) / 1e6,
    }


def private_specification():
    require(os.name == "nt", "sample sealed cylinder specifications only inside Windows")
    return {
        "schema": SCHEMA,
        "profile": SOURCE_PROFILE,
        "source_author": "SOLIDWORKS IModeler::CreateBodyFromCyl and IPartDoc::CreateFeatureFromBody3",
        "nonce": secrets.token_hex(32),
        "cases": {
            SLOT_NAMES[0]: sample_cylinder(
                ((-58000, -39000), (24000, 42000), (11000, 26000)),
                (1, 1, -1),
                (5300, 9400),
                (32000, 47000),
            ),
            SLOT_NAMES[1]: sample_cylinder(
                ((41000, 61000), (-47000, -24000), (-30000, -13000)),
                (-1, 1, 1),
                (11500, 16400),
                (12000, 27600),
            ),
        },
    }


class SealedCylinderAuthor(ImportedBodyAuthor):
    def cylinder_topology(self, body, case):
        topology, owners = super().cylinder_topology(body, case)
        require(
            topology == {
                "vertices": 0,
                "edges": 2,
                "faces": 3,
                "planar_faces": 2,
                "cylindrical_faces": 1,
            },
            "sealed source is outside the closed periodic cylinder profile",
        )
        return topology, owners

    def observe(self, feature, case):
        observed = super().observe(feature, case)
        periodic_body = measure_cylinder(self, {"model": case})
        self.rec.data.setdefault("periodic_observations", []).append(periodic_body)
        self.rec.flush()
        return observed | {"periodic_body": periodic_body}
