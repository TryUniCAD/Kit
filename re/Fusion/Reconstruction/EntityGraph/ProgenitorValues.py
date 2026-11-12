import argparse
import hashlib
import json
import runpy
import struct
import sys
from pathlib import Path


IDENTIFIER = "BE7E2847-FBC4-4898-A6E7-632A559A7F89"


def read_progenitor_aux(reader):
    return {"tag": reader.number("I")}


def emit_progenitor_aux(value):
    if type(value) is not dict or set(value) != {"tag"}:
        raise ValueError("Progenitor auxiliary data requires exactly its tag field")
    if type(value["tag"]) is not int or not 0 <= value["tag"] < 1 << 32:
        raise ValueError("Progenitor auxiliary tag exceeds unsigned 32-bit range")
    return struct.pack("<I", value["tag"])


def schema_member_set():
    return {
        "metatype_identifier": IDENTIFIER,
        "members": [{
            "registration_index": 0,
            "name": "tag",
            "script_id": "tag",
            "debug_type_name": "j",
            "option_mask": 0x33,
            "metatype": {
                "name": "IntrinsicMetaTypeuint32",
                "identifier": "IntrinsicMetaTypeuint32",
                "category": {"name": "intrinsic", "value": 0},
            },
        }],
    }


def inspect_native(binary_path, model_path):
    sys.dont_write_bytecode = True
    source = Path(__file__).resolve().parents[1] / "ReadBinaryMembers.py"
    tools = runpy.run_path(str(source))
    binary = tools["Binary"](binary_path)
    model = tools["Binary"](model_path)
    initializer = binary.named["Ns::EntityTracking::ProgenitorAuxData::initializeMemberSet(unsigned int, Ns::MemberSet*)"]
    trace = tools["Trace"](binary, binary.instructions(initializer[1]), 0).run()
    options = tools["option_contract"](model, {
        "id": "NsDataModel10", "path": str(model_path), "sha256": model.sha256
    })
    if not trace["completeTrace"] or trace["lexicalMemberNames"] != ["tag"] or options["defaultMask"] != "0x33":
        raise ValueError("Native progenitor member evidence differs from the recovered profile")
    routines = []
    for address in (0x93840, 0x93854, 0x9F250, 0x9F358, 0x9F360, 0x9F4B4, 0x9F6F0):
        symbol = next(symbol for start, symbol in binary.symbols if start == address)
        routines.append({
            "address": hex(address),
            "symbol": symbol,
            "signature": tools["demangle"](symbol),
            "instructions": [{"address": hex(location), "operation": operation, "operands": operands, "annotation": annotation}
                for location, (operation, operands, annotation) in binary.instructions(symbol).items()],
        })
    return {
        "schema": "FusionProgenitorAuxiliaryValue/1",
        "applicationVersion": "2706.1.17",
        "architecture": "arm64",
        "identifier": IDENTIFIER,
        "schemaVersion": 0,
        "baseIdentifier": None,
        "source": {"path": str(binary_path), "sha256": binary.sha256},
        "extractorSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "memberTrace": trace,
        "memberOptionContract": options,
        "wire": {
            "encoding": "little endian",
            "sizeBytes": 4,
            "fields": [{"name": "tag", "type": "uint32", "wireOffset": 0, "objectOffset": "0x18", "defaultValue": 0xFFFFFFFF}],
            "persistence": "One ordinary registered value field, lexical order; no class-specific save callback registration in the member initializer",
            "constructor": "Native doConstruct initializes tag to UINT32_MAX; the in-memory 0x20-byte object also has a vptr, current-version word and pointer that are not registered persisted members",
        },
        "memberSet": schema_member_set(),
        "routines": routines,
        "limitations": [
            "The symbolic trace establishes the current schema-version-zero layout, not unobserved historical schemas",
            "The auxiliary tag's identity domain and semantic relationship to geometric tagging remain unproven",
            "Native in-memory offsets are not serialized offsets",
            "No CAD code was loaded or invoked; corpus byte accounting and vendor acceptance are separate evidence",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=Path("/tmp/kit-fusion-native-analysis/NsEntityTracking10.arm64.dylib"))
    parser.add_argument("--model", type=Path, default=Path("/tmp/kit-fusion-native-analysis/NsDataModel10.arm64.dylib"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("ProgenitorEvidence.json"))
    args = parser.parse_args()
    report = inspect_native(args.binary, args.model)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"identifier": IDENTIFIER, "fields": report["wire"]["fields"], "completeTrace": report["memberTrace"]["completeTrace"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
