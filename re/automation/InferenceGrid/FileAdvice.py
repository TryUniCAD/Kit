# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from shutil import which

from CodexAdvice.Suggest import request_advice
from Pilot.PilotFiles import FileDigest, WriteRecord


def file_stall(audit, reports):
    if audit["whole_file_verified"]:
        return None
    dimension_layer = (
        "candidate-dimension-evidence"
        if "candidate-dimension-evidence" in reports
        else "dimension-evidence"
    )
    evidence = reports.get(dimension_layer, {})
    rows = evidence.get("keyword_evidence", {}).get("dimensions", [])
    missing = [
        row for row in rows if row["status"] in {"ambiguous", "no_matching_record"}
    ]
    if missing:
        focus = (
            "ambiguous_dimension"
            if any(row["status"] == "ambiguous" for row in missing)
            else "missing_dimension"
        )
        references = [
            {
                "feature_id": row["feature_id"],
                "parameter": row["name"],
                "status": row["status"],
            }
            for row in missing
        ]
        sources = ["FileScope.json", "Input-" + dimension_layer + ".json"]
    elif reports.get("raw-structure", {}).get("counted_text", {}).get("status") == "candidate_text_prefix" and (
        reports["raw-structure"]["counted_text"]["prefix_bytes"] < reports["raw-structure"]["size"]
    ):
        focus = "counted_text_gap"
        references = [{"offset": reports["raw-structure"]["counted_text"]["prefix_bytes"]}]
        sources = ["FileScope.json", "Input-raw-structure.json"]
    elif reports.get("edited-graph", {}).get("status") == "candidate_matches_native_graph":
        focus = "edited_graph_reopen"
        references = [{"feature_id": row["feature_id"], "parameter_id": row["parameter_id"]}
                      for row in reports["edited-graph"]["updates"]]
        sources = ["FileScope.json", "Input-native-edits.json", "Input-edited-graph.json"]
    elif reports.get("native-edits", {}).get("changes"):
        focus = ("edited_graph_reconciliation" if all(row.get("saved_geometry", {}).get("status") == "edited_prism_confirmed"
                 for row in reports["native-edits"]["changes"]) else "edited_extrusion_geometry")
        references = [{"feature_id": row["kit_feature_id"], "field": row["field"]}
                      for row in reports["native-edits"]["changes"]]
        sources = ["FileScope.json", "Input-native-edits.json"]
    elif reports.get("raw-structure", {}).get("status") == "decoded_profile":
        focus = "geometry_only" if (reports["raw-structure"].get("native_witness") or {}).get("geometry_matches") else "profile_validation"
        references = [{"reader_profile": reports["raw-structure"]["profile"]}]
        sources = ["FileScope.json", "Input-raw-structure.json"]
    elif audit["features_without_experiment"]:
        focus = "feature_semantics"
        references = [
            {"feature_id": row["id"]} for row in audit["features_without_experiment"]
        ]
        sources = ["FileScope.json"]
    elif audit["unattributed_stream_ranges"]:
        focus = "stream_layout"
        references = [
            {"stream": name, "start": start, "end": end}
            for name, start, end in audit["unattributed_stream_ranges"]
        ]
        sources = ["FileScope.json"]
    else:
        return None
    if "raw-structure" in reports and "Input-raw-structure.json" not in sources:
        sources.append("Input-raw-structure.json")
    shifted = (
        evidence.get("keyword_evidence", {}).get("extrusion_depth_evidence") or {}
    ).get("shifted_layout_experiments", [])
    exhausted_layout = bool(shifted) and all(
        row["search_complete"] and not row["candidate_layouts"] for row in shifted
    )
    return {
        "available_experiments": (
            ["vary blind boss depth", "vary blind cut depth"] if shifted else
            ["probe narrow counted text", "probe wide counted text"] if focus == "counted_text_gap" else []
        ),
        "signed_extrusion_layout_refuted_on_searched_fields": exhausted_layout,
        "source_sha256": audit["source_sha256"],
        "focus": focus,
        "targets": references,
        "evidence_files": sources,
        "control_edits": evidence.get("next_control_edits", []),
    }


def advise_file(directory, stall, options):
    summaries = {
        "ambiguous_dimension": "Multiple stored scalar locations fit a declared CAD dimension.",
        "missing_dimension": "No stored scalar location matches a declared CAD dimension.",
        "feature_semantics": "A native CAD feature has no mapped semantic experiment.",
        "edited_graph_reopen": "A reconstructed extrusion graph passes offline ownership and native geometry checks. Independent edit and reopen evidence is required.",
        "edited_graph_reconciliation": "The saved prism matches the edited depths. Reconciliation of the remaining embedded feature graph needs verification.",
        "edited_extrusion_geometry": "A saved native extrusion depth differs from its embedded model. The resulting solid and dependent features require independent verification.",
        "geometry_only": "Standalone solid geometry matches measured volume, bounds and topology counts. The parent document history is outside this input.",
        "profile_validation": "A standalone geometry reader recovered a typed profile. An independent measurement is needed to verify the recovered model.",
        "counted_text_gap": "A counted text sequence stopped at an opaque gap. Probe for the next two adjacent text records.",
        "stream_layout": "A native CAD stream contains ranges without a known semantic owner.",
    }
    destination = directory / "FileAdvice"
    destination.mkdir(mode=0o700)
    evidence = {
        name: FileDigest(directory / name)
        for name in ["FileStall.json", *stall["evidence_files"]]
    }
    packet = {
        "question": "Which controlled variation would distinguish competing explanations for this CAD reader gap?",
        "discovery_summary": summaries[stall["focus"]],
        "model": options.model or "cli-default",
    }
    if stall["available_experiments"]:
        packet["experiments"] = stall["available_experiments"]
        packet["question"] += (
            " Set controlled_change to one of: "
            + ", ".join(packet["experiments"])
            + "."
        )
    if stall["signed_extrusion_layout_refuted_on_searched_fields"]:
        packet[
            "discovery_summary"
        ] += " A local experiment shifted the entire learned signed extrusion-depth layout within feature boundaries. It produced no match on the searched fields."
    WriteRecord(
        destination / "Request.json",
        {"packet": packet, "evidence_sha256": evidence, "provider": options.provider},
    )
    attempts = []

    def current():
        return all(
            (directory / name).is_file() and FileDigest(directory / name) == digest
            for name, digest in evidence.items()
        )

    executable = which(options.provider) if options.provider != "ollama" else None
    if options.provider != "ollama" and not executable:
        attempts.append({"effort": "medium", "status": "launch_failed"})
        proposal = None
    else:
        proposal = request_advice(
            executable, packet, attempts, 90, destination, current, ("medium",), options
        )
    status = "stale" if not current() else "proposal" if proposal else "no_proposal"
    WriteRecord(
        destination / "Advice.json",
        {
            "status": status,
            "proposal": proposal if status == "proposal" else None,
            "attempts": attempts,
            "verified_rule": False,
            "evidence_sha256": evidence,
        },
    )
    return status, proposal["controlled_change"] if status == "proposal" else None
