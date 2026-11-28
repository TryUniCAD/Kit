from argparse import ArgumentParser
import json
from pathlib import Path
import re
from struct import Struct, unpack_from
import sys
from uuid import UUID
from zlib import crc32

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveAssemblyContentIndex import (
    MEASUREMENTS,
    PROOF,
    PROOF_PIN,
    checked,
    fingerprint,
    require,
    wire,
)
from ProveConfigHeaderExchange import source_cases
from InspectPartEnvironmentSource import Image
from convert.adapters.solidworks.Container.Container import SldprtArchive

BASE = "2a088a36f9cb33f74b34fa8e90ed78e3489e41f9"
RADIAL_RECEIPT = "ConcentricRadialAssemblyNative01.json"
RADIAL_PIN = "d9cfb90dd07b62a49160d4d816328072767c979d89a801842add035dbcf37016"
MODULE_PIN = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
MOTION_WINDOWS = {
    "serialize_selection": (
        0x4CA29A9C,
        0x4CA29AC0,
        "3e52bc021a170cd6ec4263153280bb9f682a4aa2055d2da7ea5ad24bee81c635",
    ),
    "allocate_default_study": (
        0x4CA2FE7D,
        0x4CA2FEDB,
        "d00888b112f0a4a10a473135763138fdf9c91ea0ad14b57c17a038e2743ed294",
    ),
    "select_study": (
        0x4CA2FEDB,
        0x4CA2FF21,
        "dee8138c610a1b160b03579fa01b73f5c6652e55b4a51b9431d2d3d7f0dc4fcd",
    ),
}
DIB = Struct("<IIiiHHIIiiII")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MOTION_GUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")


def preview_dib(data):
    (
        size,
        header,
        width,
        height,
        planes,
        bits,
        compression,
        image,
        xres,
        yres,
        used,
        important,
    ) = DIB.unpack_from(data)
    palette_entries = used or 1 << bits
    require(
        size == len(data) - 4
        and header == 40
        and width > 0
        and height > 0
        and (planes, bits, compression) == (1, 8, 1)
        and palette_entries <= 256
        and DIB.size + 4 * palette_entries + image == len(data)
        and xres == yres == important == 0,
        "unexpected native palette-compressed preview framing",
    )
    return {
        "width": width,
        "height": height,
        "bytes": len(data),
        "bits_per_pixel": bits,
        "palette_entries": palette_entries,
        "compressed_pixels_bytes": image,
        "bi_compression": compression,
    }


def preview_png(data):
    require(data.startswith(PNG_SIGNATURE), "missing PNG stream signature")
    offset = len(PNG_SIGNATURE)
    sizes = []
    dimensions = None
    while offset < len(data):
        length, tag = unpack_from(">I4s", data, offset)
        last = offset + 8 + length
        require(
            last + 4 <= len(data)
            and crc32(data[offset + 4 : last]) == unpack_from(">I", data, last)[0],
            "preview PNG chunk has an invalid extent or CRC",
        )
        if not sizes:
            require(
                (tag, length) == (b"IHDR", 13), "preview PNG has a different header"
            )
            dimensions = unpack_from(">II", data, offset + 8)
        sizes.append((tag, length))
        offset = last + 4
        if tag == b"IEND":
            require(
                length == 0 and offset == len(data),
                "preview PNG does not end with its closing chunk",
            )
    require(
        sizes and sizes[-1] == (b"IEND", 0) and any(tag == b"IDAT" for tag, _ in sizes),
        "incomplete preview PNG",
    )
    return {
        "width": dimensions[0],
        "height": dimensions[1],
        "bytes": len(data),
        "chunks": len(sizes),
    }


def archive_class(data, offset, expected):
    tag, schema, count = unpack_from("<HHH", data, offset)
    name = data[offset + 6 : offset + 6 + count]
    require(
        (tag, schema, name) == (0xFFFF, 1, expected),
        "native motion archive class differs",
    )
    return offset + 6 + count


def motion_scope(data):
    require(
        len(data) == 342 and unpack_from("<I", data)[0] == 19000,
        "unexpected ordinary motion archive extent",
    )
    at = archive_class(data, 4, b"moAnimationManager_c")
    active, count = unpack_from("<iI", data, at)
    archive_class(data, at + 8, b"moAnimKeyData_c")
    require(
        (active, count) == (-1, 1), "native motion default manager inventory differs"
    )
    identities = tuple(MOTION_GUID.findall(data[1:-1].decode("utf-16-le", "replace")))
    (identity,) = identities
    require(
        UUID(identity).version == 4,
        "native motion study identity is outside the measured profile",
    )
    return {
        "bytes": len(data),
        "manager_active_selection": active,
        "study_count": count,
        "study_identity_sha256": fingerprint(identity.encode("ascii")),
    }


def describe(path, pin):
    archive = SldprtArchive.from_bytes(checked(path, pin))
    streams = archive.streams
    face_members = {
        name: len(payload)
        for name, payload in streams.items()
        if name.startswith("FaceTessellations/")
    }
    require(
        bool(face_members) == ("FaceTessellations/Directory" in face_members)
        and (not face_members or len(face_members) > 1),
        "face tessellation directory has no owned members",
    )
    return {
        "source_sha256": pin,
        "preview": preview_dib(streams["Preview"]) if "Preview" in streams else None,
        "preview_png": (
            preview_png(streams["PreviewPNG"]) if "PreviewPNG" in streams else None
        ),
        "face_tessellations": face_members,
        "animator": (
            motion_scope(streams["ThirdPty/Animator"])
            if "ThirdPty/Animator" in streams
            else None
        ),
    }


def native_motion(path):
    image = Image(path, MODULE_PIN)
    spans = {}
    for name, (start, end, pin) in MOTION_WINDOWS.items():
        require(
            fingerprint(image.read(start, end)) == pin,
            "native motion default owner changed",
        )
        spans[name] = {"start": hex(start), "end_exclusive": hex(end), "sha256": pin}
    return {"module_sha256": MODULE_PIN, "windows": spans}


def main():
    cli = ArgumentParser()
    cli.add_argument("--disclosures", type=Path, required=True)
    cli.add_argument("--model-module", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    properties = json.loads(checked(MEASUREMENTS / PROOF, PROOF_PIN))
    radial = json.loads(checked(MEASUREMENTS / RADIAL_RECEIPT, RADIAL_PIN))
    require(
        radial["passed"]
        and radial["controls_healthy"]
        and radial["oracle_file_version"] == "34.5.2.0604"
        and radial["distinct_native_processes"] == 4
        and radial["numeric_checks"] == 140,
        "comparison requires the healthy exact-build radial lifecycle",
    )
    cases = {
        label: describe(path, pin)
        for label, path, pin in source_cases(args.disclosures, properties)
    }
    require(
        len(cases) == 12
        and all(
            row["preview"] and row["preview_png"] and row["animator"]
            for row in cases.values()
        ),
        "source presentation or motion inventory differs",
    )
    for pair in ("D01", "D02", "D03"):
        require(
            cases[pair + "/Source"]["animator"] == cases[pair + "/Edited"]["animator"],
            "ordinary edited study identity changed",
        )
    radial_cases = {
        name: describe(
            args.disclosures
            / "RadialConcentric01"
            / folder
            / "RadialConcentricProbe.SLDASM",
            radial["archive_round_trip"][name]["parent"]["sha256"],
        )
        for name, folder in (("generated", "Frozen"), ("native_save", "Working"))
    }
    require(
        all(
            bool(radial_cases["native_save"][name])
            and not radial_cases["generated"][name]
            for name in ("preview", "preview_png", "face_tessellations", "animator")
        ),
        "radial cache lifecycle differs",
    )
    report = wire(
        {
            "schema": "kit.sw2026.assembly-presentation-caches.v1",
            "base": BASE,
            "native_receipt_sha256": RADIAL_PIN,
            "native_motion": native_motion(args.model_module),
            "existing_radial_controls": radial_cases,
            "disclosed_sources": cases,
            "native_launches": 0,
            "heldout_accesses": 0,
            "writer_outputs": 0,
            "runner_sha256": fingerprint(HERE.read_bytes()),
        }
    )
    with args.output.open("xb") as output:
        output.write(report)


if __name__ == "__main__":
    main()
