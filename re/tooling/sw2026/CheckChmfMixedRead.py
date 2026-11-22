from hashlib import sha256
from json import dumps
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import fromstring, SubElement


HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
from convert import extract_brep, open_document
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Adapter import DecodePartBase
from interchange.Features.FeatureKinds import NativeFeature

sys.path.insert(0, str(HERE.parent))
from CheckMeasuredChamfer import FORMAT, demand
from CheckScopedPlainWriter import reject


SOURCE = ROOT / "re/automation/PairedCaptures/P04/solidworks-c1986308375a/P04-solidworks-baseline-a.SLDPRT"
PIN = "c1986308375aaf68ebac6f8de61e70a47b9b33535c94271bab2e4bd00504c59d"


def digest(raw):
    return sha256(raw).hexdigest()


def inspect_pair(actual, mixed, feature_id):
    contrast = None
    for include in (False, True):
        control = open_document(actual, source_format=FORMAT, strict=True, include_brep=include)
        warning = "SOLIDWORKS 2026 chamfer history requires the verified cold stock"
        reject(lambda: open_document(mixed, source_format=FORMAT, strict=True, include_brep=include),
               ValueError, warning)
        read = open_document(mixed, source_format=FORMAT, strict=False, include_brep=include)
        existing = tuple(row for row in read.feature_timeline if row.id != feature_id)
        (extra,) = tuple(row for row in read.feature_timeline if row.id == feature_id)
        (notice,) = tuple(row for row in read.diagnostics if row.code == "sldprt.chamfer_history_unresolved")
        demand(extra.kind.value == "chamfer" and isinstance(extra.definition, NativeFeature)
               and notice.severity.value == "warning" and existing == control.feature_timeline
               and read.parameters == control.parameters and read.sketches == control.sketches
               and read.support_planes == control.support_planes and read.brep == control.brep
               and read.brep_payloads == control.brep_payloads
               and (read.brep is not None) == include,
               "permissive mixed inspection changed independently supported history or cached geometry")
        modeled = tuple(row for row in existing if row.kind.value == "extrusion")
        demand([row.name for row in modeled] == ["BlindBoss", "BlindCut"]
               and all(row.provenance is not None and row.definition.length is not None for row in modeled),
               "control did not exercise both actual prior stock operations")
        contrast = [row.id for row in modeled]
    return contrast


def main():
    actual = SOURCE.read_bytes()
    demand(digest(actual) == PIN, "the independently authored stock and cut control changed")
    archive = SldprtArchive.from_bytes(actual)
    model = DecodePartBase(archive, None)[0]
    marker_id = max(feature.object_id for feature in model.features) + 100
    xml = fromstring(archive.require(KeywordsStream)[1:])
    (config,) = tuple(xml.iter("Configuration"))
    SubElement(config, "Feature", id=str(marker_id), Name="Supplemental unresolved chamfer", Type="Chamfer")
    mixed = BuildSldprt(dict(archive.streams) | {KeywordsStream: FrameKeywords(xml, False)}, FormatVersion=4)
    observed = SldprtArchive.from_bytes(mixed)
    changed = [
        name for name in archive.streams
        if archive.require(name) != observed.require(name)
    ]
    demand(changed == [KeywordsStream] and set(archive.streams) == set(observed.streams),
           "synthetic contrast changed physically saved support, method or body bytes")
    stock_ids = inspect_pair(actual, mixed, f"sldprt:feature:{marker_id}")
    with TemporaryDirectory(prefix="KitChmfMixed.") as folder:
        data = [
            [digest(path.read_bytes()) for path in extract_brep(raw, Path(folder) / label, source_format=FORMAT)]
            for raw, label in ((actual, "Control"), (mixed, "Supplemental"))
        ]
    demand(len(data[0]) == 4 and data[0] == data[1] and SOURCE.read_bytes() == actual,
           "mixed diagnostic path changed the original or a raw payload")
    print(dumps({"source_sha256": PIN, "boundary_kind": "synthetic_keyword_only",
                 "changed_streams": changed, "typed_stock_ids": stock_ids,
                 "strict_refusals": 2, "permissive_warnings": 2,
                 "raw_payload_sha256": data[0], "native_mixed_saves": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
