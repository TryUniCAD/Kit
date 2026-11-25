from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from zlib import ZLIB_RUNTIME_VERSION


CASES = (
    "BaselineReconstruction", "BaselineEdited",
    "HeldOutReconstruction", "HeldOutEdited",
)


def refuse(write, document, options, expected_error):
    protected = BytesIO(b"caller-owned output")
    protected.seek(4)
    try:
        write(document, protected, options)
    except ValueError as error:
        if expected_error not in str(error):
            raise
    else:
        raise ValueError(f"unqualified publication passed: {expected_error}")
    if protected.getvalue() != b"caller-owned output" or protected.tell() != 4:
        raise ValueError("refusal changed caller-owned output")


def check(root):
    sys.path[:0] = [str(root / "src"), str(root / "re")]
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.document.Models.DocumentModel import CadDocument
    from tooling.sw2026.PreparePlainPartEvidence import construct

    def registry(document, stream, options):
        return write_document(
            document, stream, destination_format="solidworks.sldprt",
            allow_carrier=False, values=options,
        )

    def direct(document, stream, options):
        return SldprtWriter().write(document, stream, WriteOptions(values=options))

    inputs = root / "re/solidworks/measurements/2026/EncoderRoundTrip"
    results = []
    for role in CASES:
        request = CadDocument.from_json((inputs / "Requests" / f"{role}.json").read_text(encoding="utf-8"))
        envelope = json.loads((inputs / f"{role}.json").read_bytes())
        receipt = envelope["receipt"]
        locator = rf"C:\KitEncoderRoundTrip\{request.metadata['name']}.SLDPRT"
        candidate = construct(request, locator, envelope["written_at"]).BytesValue
        expected = receipt["builds"][0]["candidate_sha256"]
        replay_sha = sha256(candidate).hexdigest()
        document = open_document(candidate, source_format="solidworks.sldprt", strict=True)
        document = CadDocument.from_json(document.to_json())
        options = {"final_destination": locator, "solidworks_native_measurement": envelope}
        edited_identity = deepcopy(envelope)
        edited_identity["receipt"]["oracle"]["sha256"] = "0" * 64
        accepted = 0
        for write in (registry, direct):
            refuse(
                write, document, {**options, "solidworks_native_measurement": edited_identity},
                "exact passing SOLIDWORKS",
            )
            if replay_sha != expected:
                if sys.platform == "win32" and "zlib-ng" in ZLIB_RUNTIME_VERSION:
                    raise ValueError(f"measured compression runtime failed to reproduce {role}")
                refuse(write, document, options, "no unique exact native measurement")
                continue
            stream = BytesIO()
            result = write(document, stream, options)
            measured = result.metadata["solidworks_native_measurement"]
            if (
                stream.getvalue() != candidate or result.dropped
                or not result.vendor_loadable or not result.application_usable
                or measured["oracle_build"] != receipt["oracle"]["build"]
            ):
                raise ValueError(f"publication lost archive or oracle binding: {role}")
            accepted += 1
        results.append({"role": role, "accepted": accepted, "unknown_identity_refused": 2})
    return {"results": results, "zlib_runtime": ZLIB_RUNTIME_VERSION}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.root.resolve()), sort_keys=True))
