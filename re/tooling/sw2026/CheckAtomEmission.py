from argparse import ArgumentParser
from codecs import lookup
from collections.abc import Callable
from pathlib import Path
from struct import pack, unpack
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from CheckCfgAtoms import (
    KAtomClass,
    ArchiveNode,
    ReadAtomMgr,
    audit_run,
    author_body,
    author_manager,
    digest,
    inspect_manager,
    load_case,
    require,
    seed_manager,
)

from convert.adapters.solidworks.Archive.Config.Atoms.WriteAtomMgr import WriteAtomMgr
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


def authored_atom(atom_id, state, *, name=("A", "alt"), **changes):
    fields = {
        "f18": None, "f0c": -23, "f28": 0x40000004, "f08": -47, "f2c": -9,
        "f20": name, "has_list68": 0, "f78": None,
        "f60": {"list": {"n": 0, "items": []}, "tail": 0},
        "f140": atom_id, "f144": state, "f130": -31, "f12c": -41,
        "f158": 0xF0000060, "body_kind": 0, "f170": -11, "f18c": 1, "f198": -1,
        "f180": -7, "f188": 1, "f1b0": -7, "f19c": 6,
    }
    return ArchiveNode(KAtomClass, {**fields, **changes})


def manager_fields(nodes):
    return {"f260": 207, "n6c": -91, "atoms": [{"o": node} for node in nodes],
            "fa8": 0xABCDEF01}


def authored_expected(slot, atom_id, wire, *, flags, name):
    data = author_body(slot, atom_id, wire, flags=flags)
    if name == ("A", "alt"):
        return data
    data = data.replace(b"\x03alt", pack("<BHB", 0xFF, 0xFFFE, len(name)) + name.encode("utf-16-le"), 1)
    return data


def check_generated(version, seed, model, slot, conditions, specs):
    nodes = tuple(authored_atom(atom_id, value, name=name, **other)
                  for atom_id, value, _wire, name, other in specs)
    fields = manager_fields(nodes)
    expected = author_manager(tuple(authored_expected(slot, atom_id, wire, flags=conditions, name=name)
                                    for atom_id, _value, wire, name, _other in specs))
    emitted, mapped = WriteAtomMgr(fields, version, seed, model, ConditionBits=conditions)
    require(emitted == expected and fields["n6c"] == -91, "derived manager differs from independent frame")
    decoded = ReadAtomMgr(emitted, version, seed, model, ConditionBits=conditions)
    require(decoded.FieldsValue["n6c"] == len(nodes), "written row count is not derived")
    require(mapped.CounterValue == decoded.MapValue.CounterValue == seed.CounterValue + len(nodes),
            "written atom map allocation differs")
    require(all(a is b for a, b in zip(seed.EntriesValue, mapped.EntriesValue[:len(seed.EntriesValue)], strict=True)),
            "written atom map changed its inherited prefix")
    require(all(entry.EntryValue is node for entry, node in zip(mapped.EntriesValue[len(seed.EntriesValue):], nodes, strict=True)),
            "new owners were renumbered or lost")
    states = []
    for row, (atom_id, value, wire, name, _other) in zip(decoded.FieldsValue["atoms"], specs, strict=True):
        loaded = row["o"]
        actual = [loaded.FieldsValue[key] for key in ("f140", "f144", "f144#wire", "f20")]
        require(actual == [atom_id, value, wire, name], "generated state or CString changed")
        states.append(actual)
    return {"conditions": conditions, "rows": len(nodes), "states": states, "size": len(emitted),
            "sha256": digest(emitted), "count": unpack("<i", emitted[4:8])[0],
            "range": [seed.CounterValue, mapped.CounterValue]}


def refuse(label, emit: Callable[[], object], expected_message):
    try:
        emit()
    except ValueError as exc:
        require(expected_message in str(exc), f"{label} failed at the wrong field: {exc}")
        return label
    raise AssertionError(f"{label} emitted a record")


def refusals(model, seed, borrowed):
    fresh = authored_atom(-17, 1)
    return [
        refuse("inconsistent_state", lambda: WriteAtomMgr(manager_fields([authored_atom(-17, 2)]), 19000, seed, model),
               "normalized value has no matching modeled wire word"),
        refuse("wrong_wire_type", lambda: WriteAtomMgr(manager_fields([authored_atom(-17, 1, **{"f144#wire": True})]), 19000, seed, model),
               "wire word must be integers"),
        refuse("overflow_wire", lambda: WriteAtomMgr(manager_fields([authored_atom(-17, 0, **{"f144#wire": 2**32})]), 19000, seed, model),
               "field atoms/o/f144"),
        refuse("unmapped_model", lambda: WriteAtomMgr(manager_fields([]), 19000, seed, ArchiveNode(model.ClassValue, {})),
               "mapped part owner"),
        refuse("wrong_class", lambda: WriteAtomMgr(manager_fields([ArchiveNode(RuntimeClass("moPart_c", 2), {})]), 19000, seed, model),
               "unsupported SOLIDWORKS atom body owner"),
        refuse("nonzero_body_kind", lambda: WriteAtomMgr(manager_fields([authored_atom(-17, 1, body_kind=1)]), 19000, seed, model),
               "unsupported SOLIDWORKS native field path atom body kind"),
        refuse("concept_link", lambda: WriteAtomMgr(manager_fields([authored_atom(-17, 1, f18=model)]), 19000, seed, model),
               "unqualified SOLIDWORKS atom concept links"),
        refuse("borrowed_atom", lambda: WriteAtomMgr(manager_fields([borrowed]), 19000, seed, model),
               "requires newly read atoms"),
        refuse("duplicate_atom_id", lambda: WriteAtomMgr(manager_fields([fresh, authored_atom(-17, 0)]), 19000, seed, model),
               "duplicate SOLIDWORKS manager atom identifier"),
        refuse("wrong_context", lambda: WriteAtomMgr(manager_fields([fresh]), 19000, seed, model, ConditionBits=0x10),
               "unsupported SOLIDWORKS atom manager context"),
        refuse("wrong_version", lambda: WriteAtomMgr(manager_fields([fresh]), 18000, seed, model),
               "requires archive version 19000"),
    ]


def check(case_name):
    streams, version, case = load_case(case_name)
    for encoding in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(encoding)
    sys.addaudithook(audit_run)
    model, seed = seed_manager(streams, version, case["manager"])
    original, graph, known_atom = inspect_manager(streams, version, case, model, seed)
    output, mapped = WriteAtomMgr(graph.FieldsValue, version, seed, model)
    require(output == original and mapped == graph.MapValue, "saved typed atom records did not round trip")
    result = {"input": case["part_sha256"], "interval": case["manager"]["interval"],
              "native_body_sha256": digest(original), "native_emission_sha256": digest(output),
              "saved_count": graph.FieldsValue["n6c"], "saved_range": [seed.CounterValue, mapped.CounterValue],
              "runtime_external_accesses": 0, "full_native_writer_qualified": False}
    if case_name == "ladder":
        class_slot = case["atom"]["class_slot"]
        cases = (
            (0, ()),
            (0, ((-51, 1, 1, ("A", "alt"), {"f144#wire": 7}),)),
            (0, ((-51, 0, 0, ("A", "alt"), {}), (-52, 1, 1, "λ22", {}))),
            (0x80, ((37, 0x80000003, 0x80000003, "αλ", {}),)),
            (0x400000, ((18, 0, 0, ("A", "alt"), {}),)),
            (0x400080, ((197, 0x80000008, 0x80000008, ("A", "alt"), {}),)),
        )
        result["authored"] = [check_generated(version, mapped, model, class_slot, flags, specs)
                              for flags, specs in cases]
        result["refusals"] = refusals(model, mapped, known_atom)
    require(not model.FieldsValue and len(seed.EntriesValue) == 3, "manager path changed its caller model or prefix")
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify generated and typed saved atom managers")
    parser.add_argument("case", choices=("ladder", "concave"))
    print(json.dumps(check(parser.parse_args().case), sort_keys=True))
