# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import math

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.Formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from InferenceInputs import read_file


def properties(shell):
    points, rings = shell.PointsCm, shell.Rings
    origin = points[0]
    volumes = []
    moments = [[], [], []]
    edges = set()
    for ring in rings:
        edges.update(
            tuple(sorted((v, ring[(i + 1) % len(ring)]))) for i, v in enumerate(ring)
        )
        for j in range(1, len(ring) - 1):
            a, b, c = [
                tuple(x - y for x, y in zip(points[i], origin))
                for i in (ring[0], ring[j], ring[j + 1])
            ]
            volume = (
                a[0] * (b[1] * c[2] - b[2] * c[1])
                + a[1] * (b[2] * c[0] - b[0] * c[2])
                + a[2] * (b[0] * c[1] - b[1] * c[0])
            ) / 6
            volumes.append(volume)
            for axis in range(3):
                moments[axis].append(volume * (a[axis] + b[axis] + c[axis]) / 4)
    total = math.fsum(volumes)
    if not total or not math.isclose(
        abs(total), shell.VolumeCm3, rel_tol=1e-9, abs_tol=1e-12
    ):
        raise ValueError("planar boundary does not reproduce the SDK volume")
    return {
        "points_cm": points,
        "face_vertex_indices": rings,
        "volume_cm3": abs(total),
        "faces": len(rings),
        "edges": len(edges),
        "vertices": len(points),
        "center_cm": [origin[i] + math.fsum(moments[i]) / total for i in range(3)],
        "min_cm": [min(v) for v in zip(*points)],
        "max_cm": [max(v) for v in zip(*points)],
    }


def snapshot_bodies(data):
    entities = ReadGeometry(data).Entities
    ids = tuple(range(len(entities)))
    table = LiveTable(-1, entities, ids, ids)
    return [
        properties(ReadPlacedBody(table, i))
        for i in ids
        if isinstance(entities[i], BodyNode)
    ]


def journal_bodies(data):
    journal = ReadJournal(data)
    states = Materialize(journal)
    if len(states) > 64:
        raise ValueError("planar replay exceeds 64 journal states")
    history = []
    active = None
    references = 0
    for state in states:
        shells = ReadPlanarState(journal, state.StateId)
        references += sum(len(ring) for shell in shells for ring in shell.Rings)
        if references > 262144:
            raise ValueError(
                "planar state geometry exceeds the vertex-reference budget"
            )
        bodies = [properties(shell) for shell in shells]
        history.append(
            {
                "state_id": state.StateId,
                "active": state.StateId == journal.Stream.CurrentStateId,
                "bodies": bodies,
            }
        )
        if history[-1]["active"]:
            active = bodies
    if active is None:
        raise ValueError("journal does not contain its active state")
    return active, history


def boundary(bodies):
    def oriented_ring(vertices):
        first = min(vertices)
        return min(
            tuple(vertices[i:] + vertices[:i])
            for i, v in enumerate(vertices)
            if v == first
        )

    return sorted(
        sorted(
            oriented_ring([body["points_cm"][i] for i in ring])
            for ring in body["face_vertex_indices"]
        )
        for body in bodies
    )


def planar_file(data, pin, root):
    states = None
    try:
        bodies = snapshot_bodies(data)
    except ValueError:
        bodies, states = journal_bodies(data)
    if not bodies:
        raise ValueError("no active planar solid")
    report = {
        "profile": "PlanarSnapshot" if states is None else "PlanarJournal",
        "status": "decoded_profile",
        "model": {"bodies": bodies},
        "native_witness": None,
    }
    if states is not None:
        report["model"]["states"] = states
    folder = root / "re/Fusion/LocalOracle/PlanarTopology"
    prep = folder / "ProductionPreparation.json"
    receipt = folder / "NativeAcceptance.json"
    if not prep.is_file() or not receipt.is_file():
        return report
    plans = json.loads(read_file(prep, 4 * 1024 * 1024))["authored"]
    for row in plans:
        if pin != row["sha256" if states is None else "historySha256"]:
            continue
        path = (root / row["history" if states is None else "target"]).resolve()
        if path.parent != folder.resolve() or not path.is_file():
            continue
        companion = read_file(path, 32 * 1024 * 1024)
        digest = hashlib.sha256(companion).hexdigest()
        if digest != row["historySha256" if states is None else "sha256"]:
            continue
        try:
            if states is None:
                other, history = journal_bodies(companion)
            else:
                other, history = snapshot_bodies(companion), states
        except ValueError as error:
            report["paired_geometry"] = {
                "companion_sha256": digest,
                "status": "companion_refused",
                "reason": str(error)[:250],
            }
            break
        agree = boundary(bodies) == boundary(other)
        report["paired_geometry"] = {
            "companion_sha256": digest,
            "oriented_boundaries_match": agree,
            **({"states": history} if states is None else {}),
        }
        if not agree or len(bodies) != 1:
            break
        raw = read_file(receipt, 4 * 1024 * 1024)
        observations = [
            r
            for r in json.loads(raw)["authored"]
            if r["source_sha256"] == row["sha256"] and r["status"] == "accepted"
        ]
        if len(observations) != 1:
            break
        expected = observations[0]["reopened"]
        b = bodies[0]
        ok = expected.get("is_solid") is True and all(
            expected[k] == b[k] for k in ("faces", "edges", "vertices")
        )
        ok &= math.isclose(
            expected["volume_cm3"], b["volume_cm3"], rel_tol=1e-8, abs_tol=1e-9
        )
        for key in ("center_cm", "min_cm", "max_cm"):
            ok &= len(expected[key]) == 3 and all(
                math.isclose(a, v, rel_tol=1e-8, abs_tol=1e-9)
                for a, v in zip(expected[key], b[key])
            )
        report["native_witness"] = {
            "geometry_matches": ok,
            "observations_sha256": hashlib.sha256(raw).hexdigest(),
            "source_sha256": row["sha256"],
            "stage": "reopened",
            "observed": expected,
        }
        break
    return report
