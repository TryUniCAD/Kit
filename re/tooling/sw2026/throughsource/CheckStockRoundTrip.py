from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from pathlib import Path
import sys

from CheckScopedPlainWriter import WriterAudit, reject
from SelectedStockModel import EPOCH, LOCATOR, NAME


FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stock_views(data):
    from convert import open_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from interchange.document.Models.DocumentModel import CadDocument

    full, design = (
        open_document(data, source_format=FORMAT, configuration="Default", strict=True, include_brep=geometry)
        for geometry in (True, False)
    )
    raw = SldprtAdapter().read(data, ReadOptions(configuration="Default", strict=True, extract_raw_brep=True))
    moving, result = full.bodies
    (selected,) = full.selections
    steady, other, cut = tuple(step for step in full.feature_timeline if step.operation is not None)
    require(moving.final_feature_id == other.id and result.final_feature_id == cut.id
            and selected.path[0].entity_id == steady.id and cut.selection_ids == (selected.id,),
            "typed stock body and historical selection ownership disagree")
    require(full.brep is not None and all(lite.brep is None and not lite.brep_payloads for lite in (design, raw))
            and all(len(lite.bodies) == 2 and lite.bodies == full.bodies and lite.parameters == full.parameters
                    and lite.support_planes == full.support_planes and lite.sketches == full.sketches
                    and lite.selections == full.selections and lite.feature_timeline == full.feature_timeline
                    for lite in (design, raw))
            and [sketch.support_plane_id for sketch in full.sketches]
            == [full.support_planes[index].id for index in (0, 2, 0)]
            and all(sketch.attributes["support_plane_source"] == "plane-reference" for sketch in full.sketches),
            "optional B-rep changed the independently linked stock design")
    transported = tuple(CadDocument.from_json(view.to_json()) for view in (full, design))
    require(all(original.to_json() == copy.to_json() for original, copy in zip((full, design), transported, strict=True)),
            "neutral JSON decode changed a canonical reader model")
    return {
        "full": full, "design_only": design, "raw_only": raw,
        "json_full": transported[0], "json_design_only": transported[1],
    }


def check_preserved(data, candidate, receipt, expected_digest, directory):
    from convert import extract_brep, write_document
    from convert.adapters.solidworks.Container.Container import SldprtFormatError
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import PrepStockPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    views = stock_views(data)
    extract_dir = directory / "missing-raw-payload"
    reject(lambda: extract_brep(data, extract_dir, source_format=FORMAT),
           SldprtFormatError, "SLDPRT contains no readable Parasolid payload")
    require(not extract_dir.exists(), "empty raw extraction created an output directory")
    root = Path(__file__).resolve().parents[4]
    target = directory / f"{NAME}.SLDPRT"
    values = {"final_destination": LOCATOR, OPTION: {"written_at": EPOCH, "receipt": receipt},
              "require_native_transfers": True}
    options = WriteOptions(values=values)
    writer = SldprtWriter()
    exact = sha256(data).hexdigest() == expected_digest

    def direct(document, output):
        return writer.write(document, output, options)

    def registry(document, output):
        return write_document(document, output, destination_format=FORMAT, values=values, allow_carrier=False)

    for name in ("interchange.brep.Validation.BrepValidate",
                 "interchange.document.Models.DocumentProvenance",
                 "interchange.document.Validation.DocumentAssemblyValidate",
                 "interchange.document.Validation.DocumentFeatureValidate",
                 "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(name)

    audit = WriterAudit(root / "src", target)
    sys.addaudithook(audit.observe)
    published = 0
    refusals = {}
    audit.phase = "write"
    try:
        for view in views.values():
            generated = PrepStockPart(view, BytesIO(), EPOCH, options)
            require(generated == candidate and generated.BytesValue == data,
                    "unchanged readback did not reproduce every stream and the exact container")
            for route in (direct, registry):
                sink = BytesIO()
                if not exact:
                    reject(lambda: route(view, sink), ValueError, "no exact native measurement")
                    require(not sink.getvalue(), "an unverified physical digest wrote to the caller sink")
                    continue
                result = route(view, sink)
                require(sink.getvalue() == data and result.bytes_written == len(data) and result.vendor_loadable
                        and result.application_usable and not result.dropped
                        and result.native_capabilities == view.capabilities,
                        "measured readback did not preserve the actual destination and native transfer")
                published += 1
        for mode in ("full", "json_design_only"):
            view = views[mode]
            first, *tail = view.feature_timeline
            body, *bodies = view.bodies
            tests = {
                "opaque_metadata": replace(view, metadata={**view.metadata, "unrepresented_view": True}),
                "scaffold_history": replace(view, feature_timeline=(replace(first, name="Altered folder"), *tail)),
                "body_geometry": replace(view, bodies=(replace(body, topology=replace(body.topology, volume=123.0)), *bodies)),
            }
            for key, changed in tests.items():
                for route in (direct, registry):
                    sink = BytesIO()
                    refusals[f"{mode}.{key}"] = reject(lambda: route(changed, sink), ValueError,
                                                       "cold readback differs from its regenerated part")
                    require(not sink.getvalue(), "changed reader state reached publication")
    finally:
        audit.phase = "done"
    require(not audit.denied and not audit.target_opens and not target.exists(),
            "readback publication attempted runtime input or opened a path")
    return {"modes": list(views), "exact_regenerations": len(views),
            "publications": published, "strict_compressed_identity": exact,
            "geometry_free_body_counts": {key: len(views[key].bodies) for key in ("design_only", "raw_only")},
            "body_final_features": [body.final_feature_id for body in views["full"].bodies],
            "runtime_input_file_reads": len(audit.denied), "staged_output_opens": audit.target_opens,
            "refusals": refusals}
