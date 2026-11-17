from __future__ import annotations

import codecs
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
for directory in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from Streams import StreamDoc, store_rooted
from builders.Assembly import initial_assembly_model
from builders.Metadata import header
from builders.Model import PersistentIds
from builders.Styles import detail_definitions
from builders.Units import unit_table_profile
from defs.ConfigPart import load_config, store_config_state
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt

REGISTRY = registry()
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
CONFIG = "Contents/Config-0"
HEADER = CONFIG + "-ModelHeader"


def inspect_root(request):
    name, presentation, provenance = (request[key] for key in ("name", "presentation", "provenance"))
    ids = PersistentIds()
    root = initial_assembly_model(name=name, allocator=ids, detail_definitions=detail_definitions(**presentation["styles"]), document_units=unit_table_profile(**presentation["units"]))
    created, modified = (provenance[key] for key in ("created_at", "modified_at"))
    rev = {"object_id": root["f08"], "name": name, "stamps": [{"status": 0, "user_index": 0, "company_index": 0, "timestamp": created, "comment": provenance["comment"]}]}
    history = header(next_id=ids.next_id, user_names=[provenance["author"]], company_names=[provenance["company"]], revision_logs=[rev], created_at=created, modified_at=modified, updated_at=modified, model_present=True, component_count=0, update_stamp=101, body_stamp=101, license_flags=0, license_type=0)
    config, state = store_config_state(StreamDoc(CONFIG, {"direct": 0}, [root]), REGISTRY, 19000)
    report_header = store_rooted(StreamDoc("rooted", {"base": 1}, [history]), REGISTRY, 19000)
    archive = SldprtArchive.from_bytes(build_sldprt({CONFIG: config, HEADER: report_header}))
    decoded, read = load_config(archive.require(CONFIG), REGISTRY, 19000, archive=archive, name=CONFIG)
    restored, replay = store_config_state(decoded, REGISTRY, 19000)
    model = decoded.roots[0]
    return {
        "model_class": model.cls, "name": model["f18"]["f08"],
        "root_bytes": len(config), "root_sha256": hashlib.sha256(config).hexdigest(),
        "reconstructed_bytes_identical": config == restored and not decoded.tail,
        "maps_consistent": state.count == read.count == replay.count,
        "component_model_binding": model["f990"]["owner"] is model,
        "unit_class": model["f9b8"].cls, "relation_class": model["f9d0"].cls,
        "analysis_units_missing": model["f9c0"] is None,
        "component_total": model["f1560"],
        "stream_count": len(archive.streams),
        "model_code_reads": AUDIT.ModuleReads, "denied_reads": AUDIT.DeniedReads,
        "complete_assembly_emitted": False, "native_acceptance": False,
    }


REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()
print(json.dumps(inspect_root(REQUEST), allow_nan=False))
