from argparse import ArgumentParser
from base64 import b64decode, b64encode
from dataclasses import replace
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from subprocess import run
import sys
import zlib

ROOT = Path(__file__).resolve().parents[4]
TOOLS = Path(__file__).resolve().parent
ORIGINAL_RECEIPT_SHA = (
    "79210ac088a95b3c6d0913b8a056e678e8dbe14e9a861f178455ea0426f6e80c"
)


def refuse(route, document, options, case_name, reasons):
    from convert.adapters.registry.RegistryErrors import NotFoundError

    original = b"existing stream"
    sink = BytesIO(original)
    sink.seek(3)
    try:
        route(document, sink, options)
    except (ValueError, NotFoundError) as error:
        matched = tuple(text for text in reasons if text in str(error))
        assert len(matched) == 1, (route.__name__, case_name, str(error))
    else:
        raise ValueError("unqualified offset readback was published")
    assert sink.tell() == 3 and sink.getvalue() == original
    return matched[0]


def publish_all(cold, warm, options, expected, stale_report):
    from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
    from interchange.document.Models.DocumentModel import CadDocument
    from ProveOffsetPublication import (
        MEASUREMENT,
        publish_adapter,
        publish_direct,
        publish_public,
    )

    copies = (cold, CadDocument.from_json(cold.to_json(indent=None)))
    changed_source = replace(cold, source=replace(cold.source, sha256="0" * 64))
    changed_metadata = replace(
        cold, metadata={**cold.metadata, "unrepresented": "additional design state"}
    )
    stale_options = {
        **options,
        MEASUREMENT: {
            **options[MEASUREMENT],
            "receipt": {"native_report": stale_report},
        },
    }
    refusals = {
        "changed_source": (changed_source, options, ("cold readback differs",)),
        "changed_source_metadata": (
            changed_metadata,
            options,
            ("cold readback differs",),
        ),
        "stale_authenticated_receipt": (
            cold,
            stale_options,
            ("no matching native measurement",),
        ),
        "native_saved_history": (
            warm,
            options,
            (
                "unqualified SOLIDWORKS sketch support references",
                "does not support the destination",
                "unsupported plain part preparation options",
                "native-only feature definitions cannot be exported",
            ),
        ),
    }
    result = {}
    for route in (publish_public, publish_direct, publish_adapter):
        for model in copies:
            assert model.to_json(indent=None) == cold.to_json(indent=None)
            sink = BytesIO()
            report = route(model, sink, options)
            assert sink.getvalue() == expected
            assert report.vendor_loadable and report.application_usable
            assert GetDocumentCaps(model) == report.native_capabilities
            assert not report.dropped and not report.carrier_capabilities
        result[route.__name__] = {
            "whole_streams": len(copies),
            "refusals": {
                case_name: refuse(route, case, settings, case_name, reasons)
                for case_name, (case, settings, reasons) in refusals.items()
            },
        }
    return result


def worker(envelope):
    from codecs import lookup
    from CheckScopedPlainWriter import WriterAudit
    from CheckTypedOffset import check_linked, check_neutral, digest
    from DisclosedOffsetRequest import offset_inputs
    from ProveOffsetPublication import MEASUREMENT
    from convert import open_document
    from convert.adapters.solidworks.Core.Preparation.OffsetPlane.IsOffRead import (
        IsOffRead,
    )
    from convert.adapters.solidworks.Core.Writing.OffsetPlanes.OffsetOptions import (
        KOffsetWriteOpt,
        OffsetOptions,
    )

    for name in ("utf-8", "utf-16-le", "latin-1", "ascii", "cp1252"):
        lookup(name)
    for name in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Models.DocumentWalk",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    request = envelope["model_request"]
    raw = b64decode(envelope["cold"], validate=True)
    saved = b64decode(envelope["warm"], validate=True)
    _, recipe, point, event = offset_inputs(request)
    options = {
        "final_destination": recipe.OutputValue.PathName,
        "require_native_transfers": True,
        MEASUREMENT: {
            "written_at": event,
            "receipt": {"native_report": envelope["report"]},
        },
        KOffsetWriteOpt: OffsetOptions(recipe, point),
    }
    geometry = check_neutral(raw, request)
    linked = check_linked(raw)
    reports = {}
    audit = WriterAudit(ROOT / "src", ROOT / "unused-offset-readback.SLDPRT")
    sys.addaudithook(audit.observe)
    for mode, include in (("full", True), ("design_only", False)):
        audit.phase = "done"
        cold = open_document(
            raw, source_format="solidworks.sldprt", strict=True, include_brep=include
        )
        warm = open_document(
            saved, source_format="solidworks.sldprt", strict=True, include_brep=include
        )
        assert (
            IsOffRead(cold)
            and not IsOffRead(warm)
            and (cold.brep is not None) == include
        )
        audit.phase = "write"
        reports[mode] = publish_all(cold, warm, options, raw, envelope["stale_report"])
    audit.phase = "done"
    assert not audit.denied and not audit.target_opens
    assert not {"pythoncom", "win32com.client", "FreeCAD", "adsk"} & sys.modules.keys()
    return {
        "cold_sha256": digest(raw),
        "warm_sha256": digest(saved),
        "geometry": geometry,
        "linked_replay": linked,
        "logical_stream_count": 10,
        "publication": reports,
        "runtime_input_reads": len(audit.denied),
    }


def run_scope(disclosure):
    from CheckTypedOffset import CASES, METHOD_HASH, checked

    measurements = ROOT / "re/solidworks/measurements/2026"
    report = checked(
        measurements / "ReferencePlaneBlindMethod01.json", METHOD_HASH
    ).decode()
    stale = checked(
        measurements / "ReferencePlaneOriginalHeldouts01.json", ORIGINAL_RECEIPT_SHA
    ).decode()
    rows = {}
    for slot, name, request_sha, cold_sha, result_sha in CASES:
        home = disclosure / ("GeneratedReferencePlaneParity" + slot)
        request = loads(checked(home / "Request.json", request_sha))
        native = loads(
            checked(home / "Inspection/PairedReferencePlaneResults.json", result_sha)
        )
        assert (
            native["passed"]
            and native["controls_healthy"]
            and native["distinct_processes"] == 4
        )
        (phase,) = (phase for phase in native["phases"] if phase["role"] == "Generated")
        warm = phase["saved"]
        assert warm["filename"] == name + "Edited.SLDPRT"
        cold_data = checked(home / "FrozenGenerated" / (name + ".SLDPRT"), cold_sha)
        warm_data = checked(home / "Saved" / warm["filename"], warm["sha256"])
        envelope = dumps(
            {
                "model_request": request,
                "cold": b64encode(cold_data).decode(),
                "warm": b64encode(warm_data).decode(),
                "report": report,
                "stale_report": stale,
            }
        ).encode()
        results = []
        for _ in range(2):
            process = run(
                [sys.executable, "-I", "-B", __file__, "--worker"],
                input=envelope,
                capture_output=True,
                timeout=180,
            )
            if process.returncode:
                raise RuntimeError(process.stderr.decode())
            results.append(loads(process.stdout))
        first, second = results
        assert first == second
        rows[name] = {
            "disclosed_request_sha256": request_sha,
            "existing_native_result_sha256": result_sha,
            "isolated_workers": 2,
            **first,
        }
    return {
        "schema": "kit.sw2026.measured-offset-cold-readback.v1",
        "disclosed_receipt_sha256": METHOD_HASH,
        "stale_receipt_sha256": ORIGINAL_RECEIPT_SHA,
        "python": sys.version.split()[0],
        "zlib": zlib.ZLIB_RUNTIME_VERSION,
        "new_native_processes": 0,
        "new_heldout_cases": 0,
        "cases": rows,
    }


def main():
    syspath = (ROOT / "src", TOOLS, TOOLS.parent)
    sys.path[:0] = [str(p) for p in syspath]
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--worker", action="store_true")
    group.add_argument("--disclosure", type=Path)
    args = parser.parse_args()
    result = (
        worker(loads(sys.stdin.buffer.read()))
        if args.worker
        else run_scope(args.disclosure)
    )
    print(dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
