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
import struct
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile
from zlib import error as InflateError

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


def raw_scope(data, path, pin, application, root, scratch, control_paths=()):
    patch = None
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
            from InferenceGrid.RoundReader import round_reader

            candidate, reason, patch = round_reader(root, data, pin, scratch)
            if candidate is None:
                report["readers"]["round_surface"] = {
                    "status": "refused",
                    "reason": reason,
                }
                from InferenceGrid.PlanarFile import planar_file

                try:
                    decoded = planar_file(data, pin, root)
                except ValueError as error:
                    report["readers"]["planar_shell"] = {
                        "status": "refused",
                        "reason": str(error)[:250],
                    }
                else:
                    report["readers"]["planar_shell"] = {"status": "decoded"}
                    report.update(decoded)
            else:
                report["readers"]["round_surface"] = {"status": "decoded"}
                report.update(candidate)
    else:
        package = inspect_zip(data) if not control_paths else None
        xml = xml_structure(data)
        if package is not None:
            report.update(status="inspected_zip", package=package)
        elif xml is not None:
            if control_paths:
                raise ValueError("binary comparison controls require a binary input")
            report.update(status="decoded_xml_structure", xml=xml)
        else:
            if len(control_paths) > 8:
                raise ValueError("raw stream comparison accepts up to eight controls")
            controls = []
            seen = {pin}
            remaining = 32 * 1024 * 1024
            layouts = frame_candidates(data)
            report["length_prefix_candidates"] = layouts
            viable = {
                (r["start"], r["width"], r["byte_order"], r["includes_prefix"])
                for r in layouts
            }
            comparisons = []
            for control in control_paths:
                blob = read_file(control, min(remaining, 16 * 1024 * 1024))
                digest = hashlib.sha256(blob).hexdigest()
                if (
                    not blob
                    or digest in seen
                    or identify_file(blob)[0] != "unknown"
                    or xml_structure(blob) is not None
                ):
                    raise ValueError(
                        "supply distinct nonempty raw binary comparison streams"
                    )
                seen.add(digest)
                controls.append(blob)
                found = frame_candidates(blob)
                viable &= {
                    (r["start"], r["width"], r["byte_order"], r["includes_prefix"])
                    for r in found
                }
                comparisons.append({"sha256": digest, "candidates": found})
            if controls:
                report["frame_comparisons"] = {
                    "controls": comparisons,
                    "shared_layouts": sorted(viable),
                }
            from InferenceGrid.RawScalarRule import raw_scalars

            scalar, patch = raw_scalars(root, data, pin, scratch, controls)
            if scalar:
                report["named_scalar_experiment"] = scalar
                report["status"] = scalar["status"]
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
    scalar = report.get("named_scalar_experiment", {})
    confirmed = sorted(scalar.get("native_measurement_offsets", []))
    if confirmed:
        width = struct.calcsize(scalar["encoding"])
        gaps = []
        cursor = 0
        for offset in confirmed:
            if cursor < offset:
                gaps.append(["input", cursor, offset])
            cursor = max(cursor, offset + width)
        if cursor < len(data):
            gaps.append(["input", cursor, len(data)])
        audit["unattributed_stream_ranges"] = gaps
    return {application: {"catalogue_sha256": pin, "features": {}}}, (
        audit,
        {"raw-structure": report, **({"reader-patch": patch} if patch else {})},
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


def inspect_zip(data):
    if not data.startswith(b"PK\x03\x04"):
        return None
    try:
        with ZipFile(BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 4096:
                return {"status": "member_limit"}
            names = {entry.filename for entry in entries if not entry.is_dir()}
            if len({entry.filename for entry in entries}) != len(entries):
                return {"status": "ambiguous_member_names"}
            remaining = 32 * 1024 * 1024
            binary_probes = 0
            members = {}
            for entry in sorted(entries, key=lambda e: e.filename):
                if entry.is_dir():
                    continue
                row = {"size": entry.file_size}
                members[entry.filename] = row
                if entry.compress_type not in (ZIP_STORED, ZIP_DEFLATED) or entry.flag_bits & 1 or entry.file_size > min(4 * 1024 * 1024, remaining):
                    row["status"] = "deferred"
                    continue
                remaining -= entry.file_size
                try:
                    with archive.open(entry) as stream:
                        blob = stream.read(entry.file_size + 1)
                except (BadZipFile, NotImplementedError, OSError, EOFError, InflateError):
                    row["status"] = "unreadable_member"
                    continue
                if len(blob) != entry.file_size:
                    row["status"] = "size_mismatch"
                    continue
                row["sha256"] = hashlib.sha256(blob).hexdigest()
                try:
                    xml = xml_structure(blob, names)
                except ValueError:
                    row["status"] = "refused_xml"
                    continue
                if xml:
                    row.update(status="decoded_xml_structure", xml=xml)
                else:
                    row["status"] = "opaque"
                    if binary_probes < 16 and len(blob) >= 6:
                        row["length_prefix_candidates"] = frame_candidates(blob)
                        binary_probes += 1
            return {"status": "inspected", "members": members}
    except (BadZipFile, OSError, EOFError):
        return None


def xml_structure(data, members=None):
    from xml.parsers.expat import ExpatError, ParserCreate

    if len(data) > 4 * 1024 * 1024 or not data.removeprefix(
        b"\xef\xbb\xbf"
    ).lstrip().startswith(b"<"):
        return None
    parser = ParserCreate()
    counts = {}
    references = {}
    depth = 0
    elements = 0
    root = None

    def enter(name, attrs):
        nonlocal depth, elements, root
        depth += 1
        elements += 1
        if depth > 256 or elements > 100000 or len(counts) > 4096:
            raise ValueError("XML structure budget exceeded")
        if root is None:
            root = name
        counts[name] = counts.get(name, 0) + 1
        if members:
            for attr, value in attrs.items():
                if value in members:
                    key = (name, attr, value)
                    if key not in references and len(references) >= 4096:
                        raise ValueError("XML reference budget exceeded")
                    references[key] = references.get(key, 0) + 1

    def leave(name):
        nonlocal depth
        depth -= 1

    def reject(*_):
        raise ValueError("DTD declarations are unsupported")

    parser.StartElementHandler = enter
    parser.EndElementHandler = leave
    parser.StartDoctypeDeclHandler = reject
    try:
        parser.Parse(data, True)
    except ExpatError:
        return None
    result = {"root": root, "element_count": elements, "elements": counts}
    if members is not None:
        result["member_name_matches"] = [
            {"element": element, "attribute": attr, "member": member, "occurrences": count}
            for (element, attr, member), count in sorted(references.items())
        ]
    return result
