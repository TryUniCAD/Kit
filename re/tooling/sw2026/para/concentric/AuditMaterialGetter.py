from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

from ObserveChildAppearanceContrast import (
    BUILD,
    GETTER_CALLS,
    GETTER_PROTOCOL,
    GETTER_ROUGHNESS,
    PART_NAME,
    PHASES,
    STOCK_COLOR,
)
from PrepareChildAppearanceContrast import change, f32, inspect_part, leaves, read_json, require

from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef


ROLE_FIELDS = ("f28", "f30", "f4c", "f80", "f88", "f90", "fe0", "f140", "f150", "f208", "f240")


def raw_definition(archive, publication):
    raw = archive.require("Contents/Definition")
    read = ReadModelDef(raw, 19000)
    write = WriteModelDef(read.GraphValue)
    require(
        write.OutputValue == raw and read.MapValue == write.MapValue
        and all(wire.UsageValue.IsComplete and not wire.UsageValue.ByteFields for wire in (read, write)),
        "appearance Definition replay is incomplete",
    )
    root = read.GraphValue.DocumentValue.FieldsValue
    manager = root.get("f1110")
    items = manager["list"]["items"] if manager is not None else ()
    if manager is not None:
        require(len(items) == manager["list"]["n"], "manager count differs from actual references")
    rows = []
    for item in items:
        node = item["o"]
        value = node.FieldsValue
        require(
            node.ClassValue.NameValue == "PWMaterialProperties_c"
            and node.ClassValue.SchemaValue == value["f20"] == 1 and len(value) == 98,
            "unexpected saved appearance record class or payload",
        )
        ids = [value["f2e8"] & 0xFFFFFFFF, value["f2ec"] & 0xFFFFFFFF]
        observed = {name: value[name] for name in ROLE_FIELDS}
        if value["f30"] == 0:
            role = "stock_original"
        elif value["f30"] == STOCK_COLOR and value["f4c"] == -1:
            role = "visual_reconstruction"
        else:
            role = "unclassified"
        rows.append(
            {
                "archive_slot": node.IndexValue, "start": node.StartOffset,
                "end_exclusive": node.EndOffset, "ids": ids,
                "matches_publication": ids == publication,
                "roughness_hex": value["f140"].hex(), "role": role, "fields": leaves(observed),
            }
        )
    return {
        "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
        "typed_replay": True, "manager_terminal_map": read.MapValue.CounterValue,
        "allocator_words": [manager["f08"], manager["f0c"]] if manager is not None else None,
        "ordered_records": rows,
    }


def audit(root, trial_hash, result_hash):
    job = read_json(root / "Trial.json", trial_hash)
    result = read_json(root / "Result.json", result_hash)
    require(
        job["authoring_protocol"] == GETTER_PROTOCOL
        and job["roughness"] == GETTER_ROUGHNESS
        and job["presave_material_enumerations"] == GETTER_CALLS
        and result["trial_sha256"] == trial_hash and result["passed"]
        and result["controls_healthy"] and result["native_processes"] == 6
        and result["heldout_credit"] == 0 and set(result["phases"]) == set(PHASES),
        "no healthy paired same-locator native measurement",
    )
    row_shas = {}
    for role, phase in result["phases"].items():
        raw = (root / "Inspection" / role / "Record.json").read_bytes()
        row = json.loads(raw)
        row_shas[role] = sha256(raw).hexdigest()
        require(
            row["job"] == {"trial_sha256": trial_hash, "phase": role}
            and row["result"] == phase and phase["passed"]
            and phase["open_errors"] == phase["open_warnings"] == 0
            and phase["oracle_identity"]["file_version"] == BUILD,
            f"native evidence differs: {role}",
        )
        calls = [record["method"] for record in row["api_calls"]]
        if role.startswith("Author"):
            require(
                calls.count("GetRenderMaterials2") == GETTER_CALLS[role[-1]]
                and calls.count("set Roughness") == calls.count("Save3") == 1
                and calls.index("set Roughness") < calls.index("AddDisplayStateSpecificRenderMaterial") < calls.index("Save3")
                and (role != "AuthorB" or calls.index("AddDisplayStateSpecificRenderMaterial")
                     < calls.index("GetRenderMaterials2") < calls.index("Save3"))
                and phase["save_status"] == [True, 0, 0],
                "pre-save intervention differs",
            )
        else:
            require(
                not {"set Roughness", "Save3"} & set(calls)
                and calls.count("GetRenderMaterials2") == int(role.startswith("Reopen")),
                f"observer modified the witnessed state: {role}",
            )
    roughness = GETTER_ROUGHNESS["A"]
    rounded = f32(roughness)
    data, graphs = {}, {}
    for lane in ("A", "B"):
        author, reopened = (result["phases"][prefix + lane] for prefix in ("Author", "Reopen"))
        identity = author["saved_sha256"]
        publication = author["appearance"]["published_ids"]
        require(
            identity == reopened["working_sha256"] and publication == reopened["appearance"]["ids"]
            and author["appearance_checkpoints"]["creator_roughness_set"]["roughness"] == roughness,
            "saved custody or independently authored roughness differs",
        )
        asset = root / "Inspection" / ("Author" + lane) / PART_NAME
        archive, graphs[lane], proof = inspect_part(asset, identity, rounded)
        data[lane] = {
            "saved_sha256": identity, "linked_replays": proof["linked_byte_identity"],
            "self_locator": proof["self_file"], "physical_material": proof["physical_material"],
            "published_ids": publication, "pre_save_api": author["appearance"],
            "fresh_reopen_api": reopened["appearance"], "appearance": proof["appearance"],
            "definition": raw_definition(archive, publication),
        }
    first, second = (data[lane]["definition"] for lane in ("A", "B"))
    states = {lane: [(item["role"], item["roughness_hex"]) for item in data[lane]["definition"]["ordered_records"]]
              for lane in ("A", "B")}
    deltas = {role: change(graphs["A"][role] or {}, graphs["B"][role] or {})
              for role in graphs["A"].keys() | graphs["B"].keys()}
    return {
        "schema": "kit.sw2026.appearance-material-getter-audit.v1",
        "trial_sha256": trial_hash, "native_result_sha256": result_hash, "phases_sha256": row_shas,
        "runtime_oracle_version": BUILD, "native_processes": 6,
        "native_numeric_checks": sum(phase["numeric_checks"] for phase in result["phases"].values()),
        "same_locator": data["A"]["self_locator"] == data["B"]["self_locator"],
        "presave_material_getters": GETTER_CALLS,
        "authored_f64_hex": roughness.hex(), "widened_f32_hex": rounded.hex(),
        "role_roughness_sequence": states, "arms": data,
        "shared_visual_delta": deltas, "source_evidence_only": True, "heldout_credit": 0,
        "predictions": {
            "independent_map_row": [role for role, _ in states["A"]] == ["stock_original"]
            and [role for role, _ in states["B"]] == ["visual_reconstruction", "stock_original"],
            "extra_allocator_step": bool(first["allocator_words"] and second["allocator_words"]
                                         and second["allocator_words"][0] == first["allocator_words"][0] + 1),
            "separate_rounding_bits": states["A"] == [("stock_original", roughness.hex())]
            and states["B"] == [("visual_reconstruction", rounded.hex()), ("stock_original", roughness.hex())],
            "three_visible_owners_quantized": all(
                set(arm["appearance"]) == {"model", "selected_configuration", "part_self_visual_state"}
                and all(owner["legacy_roughness"] == rounded for owner in arm["appearance"].values())
                for arm in data.values()
            ),
        },
    }


def main():
    parser = ArgumentParser(description="Compare immutable saved appearance records after one getter")
    parser.add_argument("packet", type=Path)
    parser.add_argument("trial_sha256")
    parser.add_argument("result_sha256")
    args = parser.parse_args()
    print(json.dumps(audit(args.packet, args.trial_sha256, args.result_sha256),
                     sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
