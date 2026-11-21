from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

import SdkDistanceMateProcess as worker
from HeaderEpochRecords import EPOCHS, author_history, header_fault
from SdkDistanceBridge import DistanceBridge
from SdkPlanarFaults import RejectedInput
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph


def main():
    envelope = json.load(sys.stdin)
    settings = envelope.pop("header_probe")
    if settings["view"] not in ("body", "sdk") or settings["case"] not in ("absent", "empty", "authored"):
        raise ValueError("declare the exact generated header view and epoch case")
    original_part = worker.AssemblyDocument.construct_part
    original_inspect = worker.inspect_distance

    def build_child(**values):
        return author_history(original_part(**values), settings)

    def inspect_result(link, graph, bundle):
        result = original_inspect(link, graph, bundle)
        mate, = graph.RootsValue
        epochs = [row["o"].FieldsValue["f58"].FieldsValue["ff0"]["f08"] for row in mate.FieldsValue["f410"]]
        expected = EPOCHS[0] if settings["case"] == "authored" else 2592000
        if epochs != [expected, expected]:
            raise ValueError("generated mate did not retain its actual first child datum event")
        result["selected_datum_epochs"] = epochs
        return result

    class HeaderBridge(DistanceBridge):
        def make_mate(self, **values):
            child = values["child"]
            if settings["view"] == "sdk":
                child = replace(child, model_header=ReadHeaderGraph(child.streams["Contents/Config-0-ModelHeader"], 19000))
                values["child"] = child
            datum, = (value for value in child.features if value.cls == "moRefPlane_c" and value["f18"]["f08"] == settings["datum"])
            header_fault(child.model_header, settings, datum["f08"])
            parent = values["assembly"]
            occurrences = values["occurrences"]
            snapshot = lambda: {"allocator_next": values["allocator"].next_id, "wrapper_counter": parent["fd48"], "fixed_flags": [value["f408"] for value in occurrences], "header_next": values["model_header"]["f08"]}
            before = snapshot()
            try:
                result = super().make_mate(**values)
            except (ValueError, TypeError) as error:
                if settings.get("fault") is None:
                    raise
                after = snapshot()
                if after != before:
                    raise ValueError("rejected header epoch mutated actual parent publication") from error
                self.rejection = {"fault": settings["fault"], "error": str(error), "error_type": type(error).__name__, "before": before, "after": after, "parent_state_unchanged": True}
                raise RejectedInput(str(error)) from error
            if settings.get("fault") is not None:
                raise ValueError("header epoch constructor admitted its malformed input")
            container = child.model_header.FieldsValue["f20"]
            fields = container.FieldsValue if hasattr(container, "FieldsValue") else container
            actual = tuple(value if hasattr(value, "FieldsValue") else value["o"] for value in fields["items"])
            retained = ReadLogItems(container, "moLogs_c")
            if len(actual) != len(retained) or any(first is not second for first, second in zip(actual, retained, strict=True)):
                raise ValueError("header epoch view replaced actual log identities")
            self.report["header_epoch"] = {"view": settings["view"], "case": settings["case"], "actual_log_identities_preserved": True, "native_log_count": len(actual)}
            return result

    worker.AssemblyDocument.construct_part = build_child
    worker.inspect_distance = inspect_result
    worker.DistanceBridge = HeaderBridge
    sys.stdin = StringIO(json.dumps(envelope))
    try:
        worker.main()
    finally:
        worker.AssemblyDocument.construct_part = original_part
        worker.inspect_distance = original_inspect


if __name__ == "__main__":
    main()
