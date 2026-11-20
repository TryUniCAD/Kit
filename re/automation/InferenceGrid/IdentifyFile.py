# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import asdict
import hashlib
from io import BytesIO
import json
import math
from zipfile import ZipFile

from InferenceInputs import read_file

from convert.adapters.Fusion.ArchiveProbe import ProbeFusion
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Container.Format import (
    COMPONENT_TREE_STREAM,
    KEYWORDS_STREAM,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import KAsmWidths


def identify_file(data):
    if data[:15] in KAsmWidths:
        return "asm", ".smb"
    if ProbeFusion(data).confidence == 1:
        return "fusion", ".f3d"
    try:
        archive = SldprtArchive.FromBytes(data)
    except (ValueError, SldprtFormatError):
        return "unknown", ""
    if archive.GetAction(COMPONENT_TREE_STREAM) is not None:
        return "solidworks", ".sldasm"
    if archive.GetAction(KEYWORDS_STREAM) is not None:
        return "solidworks", ".sldprt"
    return "unknown", ""


def raw_scope(data, path, pin, application, root):
    report = {"status": "unidentified", "size": len(data)}
    if application == "asm":
        from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.ReadPrismSnap import (
            ReadPrismSnap,
        )
        from convert.Formats.Fusion.BrepCodec.ReadSnapshot import ReadSnapshot
        from convert.Formats.Fusion.BrepCodec.ReadHistory import ReadHistory
        from convert.Formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
        from convert.Formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import (
            ReadFrustumHist,
        )

        report.update(status="unresolved_profile", readers={})
        for reader in (
            ReadPrismSnap,
            ReadSnapshot,
            ReadHistory,
            ReadPrismHist,
            ReadFrustumHist,
        ):
            try:
                model = reader(data)
            except ValueError as error:
                report["readers"][reader.__name__] = {
                    "status": "refused",
                    "reason": str(error)[:250],
                }
                continue
            report["readers"][reader.__name__] = {"status": "decoded"}
            report["status"] = "decoded_profile"
            report["profile"] = type(model).__name__
            report["model"] = asdict(model)
            if report["profile"] == "PrismSnapshot":
                report["native_witness"] = prism_witness(root, data, pin, model)
            break
    else:
        report["length_prefix_candidates"] = frame_candidates(data)
    audit = {
        "source_sha256": pin,
        "source_name": path.name,
        "format": application,
        "reader_attempts": report.get("readers", {}),
        "member_count": 1,
        "features_without_experiment": [],
        "selected_experiments": [],
        "unattributed_stream_ranges": [["input", 0, len(data)]],
        "diagnostics": [],
        "whole_file_verified": False,
    }
    return {application: {"catalogue_sha256": pin, "features": {}}}, (
        audit,
        {"raw-structure": report},
    )


def frame_candidates(data):
    candidates = []
    for width in (1, 2, 4, 8):
        for endian in (("little",) if width == 1 else ("little", "big")):
            for includes_prefix in (False, True):
                for start in range(min(17, len(data))):
                    cursor = start
                    sample = []
                    varied = False
                    for count in range(1, 16385):
                        if cursor + width > len(data):
                            break
                        size = int.from_bytes(data[cursor : cursor + width], endian)
                        next_pos = cursor + size + (0 if includes_prefix else width)
                        if next_pos <= cursor + width or next_pos > len(data):
                            break
                        if sample and size != sample[0][1]:
                            varied = True
                        if len(sample) < 8:
                            sample.append((cursor, size))
                        cursor = next_pos
                        if cursor == len(data):
                            if count >= 3 and varied:
                                candidates.append(
                                    {
                                        "start": start,
                                        "width": width,
                                        "byte_order": endian,
                                        "includes_prefix": includes_prefix,
                                        "records": count,
                                        "sample_offsets_and_lengths": sample,
                                    }
                                )
                            break
    return candidates


def prism_witness(root, data, pin, model):
    folder = root / "re/Fusion/LocalOracle/PrismSnapshot"
    prep = folder / "Preparation.json"
    witness = folder / "NativeAcceptance.json"
    if not prep.is_file() or not witness.is_file():
        return None
    cases = json.loads(read_file(prep, 1024 * 1024))["cases"]
    raw = read_file(witness, 4 * 1024 * 1024)
    recorded = json.loads(raw)
    for case in cases:
        if case["snapshot_sha256"] != pin or case["snapshot_bytes"] != len(data):
            continue
        path = (root / case["output"]).resolve()
        if path.parent != folder.resolve() or not path.is_file():
            continue
        archive = read_file(path, 128 * 1024 * 1024)
        digest = hashlib.sha256(archive).hexdigest()
        if digest != case["output_sha256"]:
            continue
        with ZipFile(BytesIO(archive)) as zipped:
            entries = [
                i for i in zipped.infolist() if i.filename == case["snapshot_member"]
            ]
            if (
                len(entries) != 1
                or entries[0].file_size != len(data)
                or zipped.read(entries[0]) != data
            ):
                continue
        observations = [
            r
            for r in recorded["cases"]
            if r["source_sha256"] == digest and r["status"] == "accepted"
        ]
        if len(observations) != 1 or len(observations[0]["opened"]["bodies"]) != 1:
            continue
        body = observations[0]["opened"]["bodies"][0]
        axes = tuple(zip(*model.Frame.CornersCm))
        predicted = {
            "volume_cm3": model.Model.Width
            * model.Model.Height
            * model.Model.Depth
            / 1000,
            "min_cm": [min(axis) for axis in axes],
            "max_cm": [max(axis) for axis in axes],
            "faces": len(model.Frame.FaceOrder),
            "edges": len(model.Frame.Edges),
            "vertices": len(model.Frame.CornersCm),
        }
        matches = all(predicted[k] == body[k] for k in ("faces", "edges", "vertices"))
        for name in ("min_cm", "max_cm"):
            matches &= len(body[name]) == 3 and all(
                math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
                for a, b in zip(predicted[name], body[name])
            )
        matches &= math.isclose(
            predicted["volume_cm3"], body["volume_cm3"], rel_tol=1e-9, abs_tol=1e-9
        )
        return {
            "archive_sha256": digest,
            "observation_sha256": hashlib.sha256(raw).hexdigest(),
            "stage": "opened",
            "predicted": predicted,
            "observed": body,
            "geometry_matches": matches,
        }
    return None
