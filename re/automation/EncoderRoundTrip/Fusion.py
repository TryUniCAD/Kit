# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import io
import json
import math
import os
import re
import struct
import subprocess
import sys
from contextlib import ExitStack
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from unittest.mock import patch
from uuid import NAMESPACE_URL, UUID, uuid5

import convert
from convert import open_document, write_document
from convert.adapters.Fusion import MakeFusionDoc
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Projection.CompareNative import KUuidPattern
from convert.adapters.Fusion.Projection.NativeIndex import MakeIndex
from convert.adapters.Fusion.Projection.NativeProfile import NativeProfile
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange import CadDocument

AUTHORING = "fusion.authoring"
NATIVE = "fusion.native_state"
CODEC = "convert.Formats.Fusion.DocumentCodec."
UUID_ALLOCATORS = (
    "EmitDocument",
    "Model.CreateAuthor",
    "Materials.CreateMatIds",
    "PackDocument",
)
PROVENANCE_TIMES = {
    ("BodyIdentity", "AuthoredMicros"),
    ("GeometryStamp", "SavedAt"),
    ("PackageCore", "Created"),
    ("PackageCore", "Updated"),
    ("ResourceInfo", "Created"),
}
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
CHILD_MODE = "--kit-fusion-encoder-child"


def make_cuboid(
    title: str, width_mm: float, depth_mm: float, height_mm: float
) -> CadDocument:
    return MakeFusionDoc(
        DocumentSpec(
            title,
            "kitHeight",
            height_mm,
            ProfileKind="cuboid",
            SketchName="Encoder Rectangle",
            ExtrusionName="Encoder Extrusion",
            BodyName="Encoder Cuboid",
            WidthMm=width_mm,
            DepthMm=depth_mm,
            ConstrainRectangle=True,
            WidthParamName="kitWidth",
            DepthParamName="kitDepth",
        )
    )


def _write(document: CadDocument) -> bytes:
    output = io.BytesIO()
    result = write_document(
        document, output, destination_format="f3d", allow_carrier=False
    )
    if result.dropped or result.carrier_capabilities:
        raise ValueError("Fusion writer did not preserve the complete native graph")
    return output.getvalue()


def _native_model(document: CadDocument) -> DocumentModel:
    state = CheckContract(document.metadata[NATIVE], "model")
    if not isinstance(state, DocumentModel):
        raise ValueError("Fusion native-state contract requires a document model")
    return state


def _cuboid(spec: object) -> DocumentSpec:
    if (
        not isinstance(spec, DocumentSpec)
        or spec.ProfileKind != "cuboid"
        or not spec.ConstrainRectangle
        or spec.TaperDegrees != 0
        or spec.Features
    ):
        raise ValueError("Fusion encoder requires the supported plain constrained cuboid")
    return spec


def _authoring_spec(document: CadDocument) -> DocumentSpec:
    spec = _cuboid(CheckContract(document.metadata[AUTHORING], "spec"))
    if MakeFusionDoc(spec) != document:
        raise ValueError("Fusion authoring contract and neutral graph disagree")
    return spec


def _edit_height(spec: DocumentSpec, edit: dict[str, object] | None) -> DocumentSpec:
    if edit is None:
        return spec
    if (
        not isinstance(edit, dict)
        or set(edit) != {"dimension", "value_mm"}
        or edit["dimension"] != "depth"
    ):
        raise ValueError("Fusion supports a depth edit to the cuboid extrusion height")
    value = edit["value_mm"]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("Fusion extrusion height must be finite and positive")
    try:
        value_mm = float(value)
    except OverflowError as error:
        raise ValueError("Fusion extrusion height must be finite and positive") from error
    if not math.isfinite(value_mm) or value_mm <= 0:
        raise ValueError("Fusion extrusion height must be finite and positive")
    if value_mm == spec.LengthMm:
        raise ValueError("Fusion extrusion height edit must change the driving value")
    return replace(spec, LengthMm=value_mm)


def _seeded_write(
    document: CadDocument, *, native_locator: str, written_at: int
) -> tuple[bytes, frozenset[str]]:
    if type(written_at) is not int or not 0 <= written_at <= 253402300799:
        raise ValueError("Fusion encoder requires Unix seconds within the supported UTC range")
    basename = re.split(r"[/\\]", native_locator)[-1]
    if not basename:
        raise ValueError("Fusion encoder requires a logical candidate filename")
    spec_json = document.to_json(indent=None)
    command_input = json.dumps(
        [basename, written_at, spec_json], allow_nan=False
    ).encode("utf-8")
    environment = os.environ.copy()
    sdk = str(Path(convert.__file__).resolve().parents[1])
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (sdk, environment.get("PYTHONPATH")))
    )
    try:
        child = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), CHILD_MODE],
            input=command_input,
            capture_output=True,
            check=False,
            env=environment,
            timeout=60,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError("Fusion authored emitter exceeded 60 seconds") from error
    if child.returncode != 0:
        error = child.stderr.decode("utf-8", errors="replace").strip().splitlines()
        detail = f" ({error[-1][:500]})" if error else ""
        raise ValueError("Fusion authored emitter failed" + detail)
    if len(child.stdout) < 8:
        raise ValueError("Fusion authored emitter response is incomplete")
    count = struct.unpack_from("!I", child.stdout)[0]
    payload_at = 4 + 16 * count
    payload = child.stdout[payload_at:]
    if not 0 < count <= 256 or not payload.startswith(b"PK\x03\x04"):
        raise ValueError("Fusion authored emitter response does not frame a native ZIP")
    identities = frozenset(
        str(UUID(bytes=child.stdout[index : index + 16]))
        for index in range(4, payload_at, 16)
    )
    if len(identities) != count:
        raise ValueError("Fusion authored emitter produced duplicate identities")
    return payload, identities


def _emit_child() -> None:
    basename, written_at, spec_json = json.load(sys.stdin)
    document = CadDocument.from_json(spec_json)
    _authoring_spec(document)
    moment = EPOCH + timedelta(seconds=written_at)
    seed = sha256((basename + "\0" + spec_json).encode("utf-8")).hexdigest()
    identities = []

    def allocate_uuid() -> UUID:
        value = uuid5(NAMESPACE_URL, f"kit:fusion:encoder:{seed}:{len(identities)}")
        identities.append(value)
        return value

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return moment.replace(tzinfo=None) if tz is None else moment.astimezone(tz)

    # The short-lived process owns these aliases exclusively; public adapter calls in other processes retain their normal clocks and identity generators.
    with ExitStack() as patches:
        for name in UUID_ALLOCATORS:
            patches.enter_context(
                patch.object(import_module(CODEC + name), "MakeUuid", allocate_uuid)
            )
        for name in ("Materials.BuildMaterial", "Rectangle.BuildPrismPart"):
            patches.enter_context(
                patch.object(import_module(CODEC + name), "DateTime", FixedClock)
            )
        prism = import_module(CODEC + "Rectangle.BuildPrismPart")
        patches.enter_context(
            patch.object(prism, "ReadTimeNano", lambda: written_at * 1_000_000_000)
        )
        payload = _write(document)

    sys.stdout.buffer.write(struct.pack("!I", len(identities)))
    for identity in identities:
        sys.stdout.buffer.write(identity.bytes)
    sys.stdout.buffer.write(payload)


def _require_same_constructor_state(
    source: DocumentModel, generated: DocumentModel, identities: frozenset[str]
) -> None:
    aliases: dict[str, str] = {}
    allocated: set[str] = set()
    static_identities: set[str] = set()
    material_times: set[str] = set()

    def check_provenance(observed, expected, path: str) -> None:
        if type(observed) is type(expected):
            if (
                isinstance(observed, (int, float))
                and math.isfinite(observed)
                and observed >= 0
            ):
                return
            if isinstance(observed, str):
                try:
                    moment = datetime.fromisoformat(observed)
                except ValueError:
                    pass
                else:
                    if moment.utcoffset() == timedelta(0):
                        return
        raise ValueError(f"Invalid native Fusion provenance at {path}")

    def compare(observed, expected, path: str) -> None:
        if type(observed) is not type(expected):
            raise ValueError(f"Different native Fusion field type at {path}")
        if isinstance(expected, dict) and observed.keys() == expected.keys():
            if (
                expected.keys() == {"record", "fields"}
                and observed["record"] == expected["record"]
            ):
                record = expected["record"].rsplit(".", 1)[-1]
                got, wanted = observed["fields"], expected["fields"]
                if got.keys() == wanted.keys():
                    for field, value in wanted.items():
                        field_path = f"{path}.{record}.{field}"
                        if (record, field) not in PROVENANCE_TIMES:
                            compare(got[field], value, field_path)
                        else:
                            check_provenance(got[field], value, field_path)
                            if record in {"PackageCore", "ResourceInfo"}:
                                material_times.add(got[field])
                    return
            for key, value in expected.items():
                compare(observed[key], value, f"{path}.{key}")
            return
        if isinstance(expected, list) and len(observed) == len(expected):
            for index, value in enumerate(expected):
                compare(observed[index], value, f"{path}[{index}]")
            return
        if isinstance(expected, str):
            matches = list(KUuidPattern.finditer(expected))
            observed_matches = list(KUuidPattern.finditer(observed))
            if len(matches) == len(observed_matches):
                for wanted, got in zip(matches, observed_matches, strict=True):
                    key = wanted[0].lower()
                    actual = got[0].lower()
                    if key not in identities:
                        static_identities.add(key)
                        continue
                    if key in aliases:
                        continue
                    if actual in allocated:
                        raise ValueError(f"Native Fusion identity is not unique at {path}")
                    aliases[key] = actual
                    allocated.add(actual)

                def substitute(match):
                    guid = aliases.get(match[0].lower(), match[0])
                    return guid.upper() if match[0].isupper() else guid

                if observed == KUuidPattern.sub(substitute, expected):
                    return
        if observed != expected:
            raise ValueError(f"Different native Fusion field at {path}")

    compare(EncodeState(source), EncodeState(generated), "native state")
    if allocated & static_identities:
        raise ValueError("Native Fusion identity collides with static format vocabulary")
    if len(material_times) != 1:
        raise ValueError("Native Fusion material provenance has inconsistent timestamps")


def generate_candidate(
    document: CadDocument,
    edit: dict[str, object] | None = None,
    *,
    native_locator: str,
    written_at: int,
) -> bytes:
    if set(document.metadata) == {AUTHORING}:
        spec = _authoring_spec(document)
    elif set(document.metadata) == {NATIVE}:
        model = _native_model(document)
        if model.Configurations or model.Snapshots or model.Graphics is not None:
            raise ValueError("Fusion encoder requires constructor-profile native state")
        spec = _cuboid(NativeProfile(MakeIndex(model), model))
        _write(document)
        base, identities = _seeded_write(
            MakeFusionDoc(spec), native_locator=native_locator, written_at=written_at
        )
        base_projection = open_document(base, source_format="f3d")
        _require_same_constructor_state(
            model, _native_model(base_projection), identities
        )
        if edit is None:
            return base
    else:
        raise ValueError("Fusion encoder requires a complete versioned Fusion semantic contract")

    desired = MakeFusionDoc(_edit_height(spec, edit))
    candidate, _ = _seeded_write(
        desired, native_locator=native_locator, written_at=written_at
    )
    projected = open_document(candidate, source_format="f3d")
    if replace(desired, source=projected.source, metadata=projected.metadata) != projected:
        raise ValueError("Strict Fusion output projection and regenerated cuboid disagree")
    return candidate


if __name__ == "__main__":
    if sys.argv[1:] != [CHILD_MODE]:
        raise SystemExit(
            "Use the encoder round-trip research command to generate Fusion candidates"
        )
    _emit_child()
