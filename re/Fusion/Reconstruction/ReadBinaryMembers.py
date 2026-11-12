import argparse
import hashlib
import json
import re
import struct
import subprocess
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from functools import cache
from pathlib import Path


@dataclass(frozen=True)
class Value:
    kind: str
    content: object
    offset: int = 0
    evidence: str = ""


def command(*args):
    return subprocess.check_output(args, text=True)


@cache
def demangle(name):
    return command("c++filt", "-t", name).strip()


def arguments(text):
    result = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        depth += char in "[({"
        depth -= char in "])}"
        if char == "," and depth == 0:
            result.append(text[start:index].strip())
            start = index + 1
    result.append(text[start:].strip())
    return result


class Binary:
    def __init__(self, path):
        self.path = path
        self.data = path.read_bytes()
        self.sha256 = hashlib.sha256(self.data).hexdigest()
        self.offset = 0
        if self.data[:4] == b"\xca\xfe\xba\xbe":
            for index in range(struct.unpack_from(">I", self.data, 4)[0]):
                cpu, _, offset, _, _ = struct.unpack_from(
                    ">IIIII", self.data, 8 + index * 20
                )
                if cpu == 0x100000C:
                    self.offset = offset
                    break
        header = struct.unpack_from("<IIIIIIII", self.data, self.offset)
        if header[0] != 0xFEEDFACF or header[1] != 0x100000C:
            raise ValueError("Expected an arm64 Mach-O slice")
        self.segments = []
        position = self.offset + 32
        for _ in range(header[4]):
            kind, size = struct.unpack_from("<II", self.data, position)
            if kind == 0x19:
                _, address, _, offset, length = struct.unpack_from(
                    "<16sQQQQ", self.data, position + 8
                )
                self.segments.append((address, self.offset + offset, length))
            position += size
        self.symbols = []
        self.data_symbols = {}
        for line in command("nm", "-arch", "arm64", "-n", str(path)).splitlines():
            parts = line.split()
            if len(parts) == 3:
                if parts[1] in ("t", "T"):
                    self.symbols.append((int(parts[0], 16), parts[2]))
                elif "c_pTheOnlyOne" in parts[2]:
                    self.data_symbols[int(parts[0], 16)] = parts[2]
        names = subprocess.check_output(
            ["c++filt"], input="\n".join(name for _, name in self.symbols), text=True
        ).splitlines()
        self.named = dict(zip(names, self.symbols))

    def read(self, address, length):
        for start, offset, size in self.segments:
            if start <= address and address + length <= start + size:
                return self.data[offset + address - start : offset + address - start + length]
        return None

    def cstring(self, address):
        for length in (256, 1024, 4096):
            data = self.read(address, length)
            if data is not None and b"\0" in data:
                try:
                    return data.split(b"\0", 1)[0].decode("ascii")
                except UnicodeDecodeError:
                    return None
        return None

    @cache
    def instructions(self, symbol):
        result = {}
        output = command(
            "xcrun", "llvm-objdump", "--macho", "--arch=arm64",
            "--disassemble", "--dis-symname", symbol, str(self.path)
        )
        for line in output.splitlines():
            match = re.match(
                r"\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}(\S+)(?:\s+(.*))?", line
            )
            if match:
                address, operation, rest = match.groups()
                operands, _, annotation = (rest or "").partition(" ; ")
                result[int(address, 16)] = (operation, arguments(operands), annotation)
        return result


class Trace:
    def __init__(self, binary, instructions, version, callback_binary=None):
        self.binary = binary
        self.instructions = instructions
        self.registers = {
            "x0": Value("address", "object"),
            "x1": version,
            "x2": Value("address", "memberSet"),
            "sp": Value("address", "stack"),
        }
        self.memory = {}
        self.comparison = None
        self.members = []
        self.events = []
        self.failures = []
        self.steps = 0
        self.callback_binary = callback_binary
        self.callbacks = []
        self.meta_registration = None

    def register(self, name):
        return "x" + name[1:] if re.fullmatch(r"w\d+", name) else name

    def get(self, token):
        token = token.strip()
        if token in ("xzr", "wzr"):
            return 0
        if token.startswith("#"):
            return int(token[1:], 0)
        return self.registers.get(self.register(token))

    def put(self, name, value):
        if name.startswith("w") and isinstance(value, int):
            value &= 0xFFFFFFFF
        self.registers[self.register(name)] = value

    def plus(self, left, right):
        if isinstance(left, int) and isinstance(right, int):
            return left + right
        if isinstance(left, Value) and left.kind == "address" and isinstance(right, int):
            return Value(left.kind, left.content, left.offset + right, left.evidence)
        return None

    def address(self, operand):
        match = re.fullmatch(r"\[([^\]]+)\](!?)", operand)
        if not match:
            return None
        values = arguments(match[1])
        return self.plus(self.get(values[0]), self.get(values[1]) if len(values) > 1 else 0)

    def load(self, address, operation, evidence=""):
        if address in self.memory:
            value = self.memory[address]
            if operation == "ldrsb" and isinstance(value, int):
                return value - 256 if value & 128 else value
            return value
        if isinstance(address, Value):
            if address.kind in ("singleton", "metaType"):
                return Value("metaType", address.content, evidence=address.evidence)
            if address.kind == "rtti":
                return Value("typeName", address.content, evidence=address.evidence)
            if address.kind == "address" and address.content == "object":
                return Value("address", "objectPointerAt" + hex(address.offset))
        if isinstance(address, int):
            if address in self.binary.data_symbols:
                return Value("metaType", self.binary.data_symbols[address], evidence=evidence)
            raw = self.binary.read(address, 8)
            if raw is not None:
                return struct.unpack("<Q", raw)[0]
        return None

    def literal(self, value):
        if isinstance(value, int):
            return self.binary.cstring(value)
        if isinstance(value, Value) and value.kind == "typeName":
            return value.content
        return None

    def member_type(self, value):
        if isinstance(value, Value) and value.kind == "metaType":
            return {
                "singletonSymbol": value.content,
                "singletonName": demangle(value.content),
                "typeLoadAddress": value.evidence,
            }
        return {"unresolvedMetaType": repr(value)}

    def clobber(self, result=None):
        for index in range(19):
            self.registers.pop("x" + str(index), None)
        self.put("x0", result)
        self.comparison = None

    def call(self, target, address):
        location = hex(address)
        if target.endswith("12s_metaTypeIdEv"):
            self.clobber(Value("classIdentifier", demangle(target).removesuffix("::s_metaTypeId()"), evidence=location))
            return
        if target.startswith("__ZN2Ns14baseMetaTypeIdI"):
            name = demangle(target).split("Ns::baseMetaTypeId<", 1)[1].rsplit(">()", 1)[0]
            self.clobber(Value("classIdentifier", name, evidence=location))
            return
        if target.endswith("AddInIdentifierEv"):
            self.clobber()
            return
        if target.startswith("__ZN2Ns14EntityMetaTypeC2E"):
            own = self.get("x2")
            base = self.get("x5")
            self.meta_registration = {
                "registrationAddress": location,
                "registrationSymbol": target,
                "class": own.content if isinstance(own, Value) and own.kind == "classIdentifier" else None,
                "baseClass": base.content if isinstance(base, Value) and base.kind == "classIdentifier" else None,
                "baseIdentifierCallAddress": base.evidence if isinstance(base, Value) else None,
                "currentSchemaVersion": self.get("w4"),
                "entityType": self.get("w6"),
            }
            if any(value is None for value in self.meta_registration.values()):
                self.failures.append({"address": location, "reason": "incomplete entity metatype registration"})
            return
        if self.callback_binary and target in (
            "__ZN2Ns17DataModelCallback22performPostSegmentLoadEv",
            "__ZN2Ns17DataModelCallback21performPostClonePasteEv",
            "__ZN2Ns14EntityMetaType17dataModelCallbackEPNS_17DataModelCallbackE",
        ):
            instructions = self.callback_binary.instructions(target)
            nested = Trace(self.callback_binary, instructions, 0)
            nested.registers.update({"x" + str(index): self.get("x" + str(index)) for index in range(8)})
            result = nested.run()
            if not result["completeTrace"] or nested.members or any(not isinstance(pointer, int) for pointer in nested.memory):
                self.failures.append({"address": location, "reason": "callback registration effects unresolved"})
            self.callbacks.append({"callAddress": location, "symbol": target, "calleeAddress": hex(min(instructions)), "globalWrites": [{"address": hex(pointer), "value": value} for pointer, value in nested.memory.items() if isinstance(pointer, int)]})
            self.clobber()
            return
        if "basic_stringIc" in target and re.search(r"EC[12].*PKc", target):
            destination = self.get("x0")
            literal = self.literal(self.get("x1"))
            if literal is None:
                self.failures.append({"address": location, "reason": "unresolved string constructor"})
            self.memory[destination] = Value("string", literal, evidence=location)
            self.memory[self.plus(destination, 23)] = len(literal) if literal is not None and len(literal) < 23 else 128
            self.clobber(destination)
            return
        if "MemberSet12addNewMember" in target or "MemberSet9addMemberI" in target:
            text = self.memory.get(self.get("x1"))
            pointer = self.get("x2")
            member = {
                "name": text.content if isinstance(text, Value) else None,
                "registrationAddress": location,
                "registrationSymbol": target,
                "registrationKind": "template" if "9addMemberI" in target else "direct",
                "memberAddress": {
                    "base": pointer.content,
                    "offset": hex(pointer.offset),
                } if isinstance(pointer, Value) and pointer.kind == "address" else None,
                "optionOperations": [],
            }
            if isinstance(text, Value):
                member["nameConstructionAddress"] = text.evidence
            if member["registrationKind"] == "direct":
                member.update(self.member_type(self.get("x4")))
                type_name = self.literal(self.get("x3"))
                if type_name:
                    member["typeNameEncoding"] = type_name
                    member["cppType"] = demangle(type_name)
                member["implementationPointer"] = repr(self.get("x7"))
                member["templatedFunctionsPointer"] = repr(self.get("x5"))
            else:
                decoded = demangle(target)
                marker = "Ns::MemberSet::addMember<"
                position = decoded.find(marker) + len(marker)
                start = position
                depth = 1
                while position < len(decoded) and depth:
                    depth += (decoded[position] == "<") - (decoded[position] == ">")
                    position += 1
                member["cppType"] = decoded[start:position - 1]
                member["templateSignature"] = decoded
                member["implementationPointer"] = repr(self.get("x4"))
            if member["name"] is None or member["memberAddress"] is None or "unresolvedMetaType" in member or "cppType" not in member:
                self.failures.append({"address": location, "reason": "incomplete member registration"})
            self.members.append(member)
            self.clobber(Value("member", len(self.members) - 1))
            return
        if "Member5clear" in target or "Member3set" in target:
            member = self.get("x0")
            mask = self.get("w1")
            if isinstance(member, Value) and member.kind == "member" and isinstance(mask, int):
                self.members[member.content]["optionOperations"].append({
                    "operation": "clear" if "5clear" in target else "set",
                    "mask": hex(mask), "address": location,
                })
            else:
                self.failures.append({"address": location, "reason": "unresolved member option operation"})
            self.clobber(member)
            return
        if "migrationHelper" in target:
            self.clobber(Value("address", "migrationHelper", evidence=location))
            return
        if target in ("__ZdlPv", "___stack_chk_fail", "__Unwind_Resume"):
            self.clobber()
            return
        self.events.append({"address": location, "symbol": target, "effect": "unmodeled call, volatile registers discarded"})
        self.clobber()

    def condition(self, suffix):
        if self.comparison is None:
            return None
        left, right, width = self.comparison
        unsigned_left = left & ((1 << width) - 1)
        unsigned_right = right & ((1 << width) - 1)
        signed_left = unsigned_left - (1 << width) if unsigned_left >> (width - 1) else unsigned_left
        signed_right = unsigned_right - (1 << width) if unsigned_right >> (width - 1) else unsigned_right
        return {
            "eq": unsigned_left == unsigned_right,
            "ne": unsigned_left != unsigned_right,
            "lt": signed_left < signed_right,
            "le": signed_left <= signed_right,
            "gt": signed_left > signed_right,
            "ge": signed_left >= signed_right,
            "lo": unsigned_left < unsigned_right,
            "ls": unsigned_left <= unsigned_right,
            "hi": unsigned_left > unsigned_right,
            "hs": unsigned_left >= unsigned_right,
        }.get(suffix)

    def run(self):
        pc = min(self.instructions)
        terminated = False
        while pc in self.instructions and self.steps < 100000:
            self.steps += 1
            operation, args, annotation = self.instructions[pc]
            following = pc + 4
            if operation == "ret":
                terminated = True
                break
            if operation == "bl":
                target = annotation.split("symbol stub for: ")[-1] if "symbol stub for:" in annotation else args[0]
                self.call(target, pc)
                if self.meta_registration is not None:
                    terminated = True
                    break
            elif operation == "b":
                if args[0].startswith("0x"):
                    following = int(args[0], 16)
                else:
                    self.failures.append({"address": hex(pc), "reason": "unmodeled tail call", "target": args[0]})
                    break
            elif operation.startswith("b.") or operation in ("cbz", "cbnz", "tbz", "tbnz"):
                if operation.startswith("b."):
                    decision = self.condition(operation[2:])
                else:
                    value = self.get(args[0])
                    if isinstance(value, Value):
                        value = 1 if value.kind == "address" else None
                    if value is None:
                        decision = None
                    elif operation in ("cbz", "cbnz"):
                        decision = (value == 0) == (operation == "cbz")
                    else:
                        decision = ((value & (1 << self.get(args[1]))) == 0) == (operation == "tbz")
                if decision is None:
                    self.failures.append({"address": hex(pc), "reason": "unresolved branch", "operation": operation, "operands": args})
                    break
                if decision:
                    following = int(args[-1], 16)
            elif operation == "cmp":
                left, right = self.get(args[0]), self.get(args[1])
                self.comparison = (left, right, 32 if args[0].startswith("w") else 64) if isinstance(left, int) and isinstance(right, int) else None
            elif operation == "adrp":
                self.put(args[0], (pc & ~4095) + int(args[1], 0) * 4096)
            elif operation == "mov":
                self.put(args[0], self.get(args[1]))
            elif operation in ("add", "sub"):
                right = self.get(args[2])
                if operation == "sub" and isinstance(right, int):
                    right = -right
                self.put(args[0], self.plus(self.get(args[1]), right))
            elif operation == "and":
                left, right = self.get(args[1]), self.get(args[2])
                self.put(args[0], left & right if isinstance(left, int) and isinstance(right, int) else left)
            elif operation.startswith("ldr") or operation.startswith("ldur"):
                symbol = annotation.split("literal pool symbol address: ")[-1] if "literal pool symbol address:" in annotation else None
                if symbol and "c_pTheOnlyOne" in symbol:
                    value = Value("singleton", symbol, evidence=hex(pc))
                elif symbol and symbol.startswith("__ZTI"):
                    value = Value("rtti", symbol.removeprefix("__ZTI"), evidence=hex(pc))
                else:
                    address = self.address(args[1])
                    if address is None:
                        pointer = self.get(args[1].strip("[]").split(",")[0])
                        value = self.load(pointer, operation, hex(pc))
                    else:
                        value = self.load(address, operation, hex(pc))
                    if value is None:
                        pointer = self.get(args[1].strip("[]").split(",")[0])
                        if isinstance(pointer, Value) and pointer.kind in ("singleton", "metaType", "rtti"):
                            value = self.load(pointer, operation, hex(pc))
                self.put(args[0], value)
            elif operation in ("str", "strb", "stur", "sturb", "strh", "sturh"):
                self.memory[self.address(args[1])] = self.get(args[0])
            elif operation in ("stp", "ldp", "nop"):
                if operation != "nop" and not args[2].startswith("[sp"):
                    self.failures.append({"address": hex(pc), "reason": "unmodeled paired memory operation", "operation": operation, "operands": args})
            else:
                self.failures.append({"address": hex(pc), "reason": "unmodeled instruction", "operation": operation, "operands": args})
                if args and re.fullmatch(r"[xw]\d+", args[0]):
                    self.put(args[0], None)
            pc = following
        if not terminated:
            self.failures.append({"address": hex(pc), "reason": "trace did not reach return"})
        for member in self.members:
            persistence = "default"
            for change in member["optionOperations"]:
                if int(change["mask"], 16) & 1:
                    persistence = change["operation"] == "set"
            member["persistenceOptionBit0"] = persistence
        return {
            "completeTrace": terminated and not self.failures and not self.events,
            "instructionCount": self.steps,
            "membersInRegistrationOrder": self.members,
            "lexicalMemberNames": sorted(m["name"] for m in self.members if m["name"] is not None),
            "failures": self.failures,
            "unmodeledCalls": self.events,
            "callbackRegistrations": self.callbacks,
        }


def option_contract(binary, source):
    constructor = next(value for value in binary.symbols if value[1].startswith("__ZN2Ns6MemberC2E"))
    instructions = binary.instructions(constructor[1])
    writes = []
    for address, (op, operands, _) in instructions.items():
        previous = instructions.get(address - 4)
        if op == "str" and operands[0].startswith("w") and previous and previous[0] == "mov" and previous[1][0] == operands[0] and previous[1][1].startswith("#"):
            writes.append((address, operands[1], int(previous[1][1][1:], 0)))
    if len(writes) != 1:
        raise ValueError("Cannot uniquely identify member constructor option mask")
    address, destination, mask = writes[0]
    offset = int(re.search(r"#(0x[0-9a-f]+)", destination)[1], 16)
    operations = {}
    for name, opcode in (("set", "orr"), ("clear", "bic")):
        routine = next(value for key, value in binary.named.items() if key == "Ns::Member::" + name + "(Ns::Member::EMemberOption)")
        body = binary.instructions(routine[1])
        filtered = [(pc, args) for pc, (op, args, _) in body.items() if op == opcode]
        if len(filtered) != 1 or filtered[0][1] != ["w8", "w8", "w1"]:
            raise ValueError("Unexpected option mutation routine")
        operations[name] = {"symbol": routine[1], "address": hex(routine[0]), "operationAddress": hex(filtered[0][0]), "operation": opcode}
    factory = next(value for key, value in binary.named.items() if key.startswith("Ns::Member::make("))
    registration = next(value for key, value in binary.named.items() if key.startswith("Ns::MemberSet::addNewMember("))
    factory_calls = [pc for pc, (op, args, _) in binary.instructions(factory[1]).items() if op == "bl" and args[0] == constructor[1]]
    registration_calls = [pc for pc, (op, args, _) in binary.instructions(registration[1]).items() if op == "bl" and args[0] == factory[1]]
    if len(factory_calls) != 1 or len(registration_calls) != 1:
        raise ValueError("Cannot prove member allocation call chain")
    visitor = next(value for key, value in binary.named.items() if key.startswith("Ns::MemberSet::visitChildren("))
    visitor_instructions = binary.instructions(visitor[1])
    contexts = []
    masks = []
    for pc, (op, args, _) in visitor_instructions.items():
        if op != "bl":
            continue
        if "VisitorContext" in args[0]:
            contexts.append({"address": hex(pc), "symbol": args[0], "name": demangle(args[0])})
        if "Member5isSet" in args[0]:
            before = visitor_instructions[pc - 4]
            if before[0] != "mov" or before[1][0] != "w1":
                raise ValueError("Unresolved visitor member option mask")
            masks.append({"address": hex(pc), "mask": before[1][1].removeprefix("#")})
    return {
        "source": source,
        "constructorSymbol": constructor[1],
        "constructorAddress": hex(constructor[0]),
        "defaultMask": hex(mask),
        "defaultMaskStoreAddress": hex(address),
        "maskObjectOffset": hex(offset),
        "operations": operations,
        "allocationChain": [
            {"symbol": registration[1], "address": hex(registration[0]), "callsFactoryAt": hex(registration_calls[0])},
            {"symbol": factory[1], "address": hex(factory[0]), "callsConstructorAt": hex(factory_calls[0])},
        ],
        "visitor": {"symbol": visitor[1], "address": hex(visitor[0]), "maskQueriesInCodeOrder": masks, "contextQueriesInCodeOrder": contexts},
        "persistenceSelection": "For ordinary save/load, excluding cloning, copied assets and undo/redo/abort, visitChildren visits exactly members with option bit 0x1 set. Bit 0x4 suppresses cloning, bit 0x2 allows cloning or copied assets, and bit 0x10 allows undo/redo/abort. The complete mask is retained without inferring names for the other bits.",
    }


def template_contract(binary, symbol):
    instructions = binary.instructions(symbol)
    registrations = []
    for address, (op, args, annotation) in instructions.items():
        if op in ("bl", "b") and "MemberSet12addNewMember" in (args[0] + annotation):
            registrations.append(address)
    if len(registrations) != 1:
        return {"provenDefaultOptions": False, "reason": "template has no unique direct member registration"}
    address = registrations[0]
    if instructions[address][0] == "b":
        return {"provenDefaultOptions": True, "directRegistrationAddress": hex(address), "returnsViaTailCall": True}
    suffix = [(pc, op, args) for pc, (op, args, _) in instructions.items() if pc > address]
    for pc, op, args in suffix:
        if op == "ret":
            return {"provenDefaultOptions": True, "directRegistrationAddress": hex(address), "returnAddress": hex(pc)}
        if op not in ("ldp", "ldr", "add") or (op in ("ldr", "add") and args[0] != "sp") or (op == "ldp" and "x0" in args[:2]):
            return {"provenDefaultOptions": False, "reason": "template return path is not a plain epilogue", "address": hex(pc)}
    return {"provenDefaultOptions": False, "reason": "template return not found"}


def metatype_contract(binary, name):
    suffix = name.rsplit("::", 1)[-1] + "MetaType"
    expected = name + "MetaType::" + suffix + "()"
    named = binary.named.get(expected)
    candidate = named[1].replace("C1Ev", "C2Ev") if named else None
    constructor = next((value for value in binary.symbols if value[1] == candidate), None)
    if constructor is None:
        return {"complete": False, "reason": "no zero-argument metatype constructor found"}
    trace = Trace(binary, binary.instructions(constructor[1]), 0)
    result = trace.run()
    return {
        "complete": result["completeTrace"] and trace.meta_registration is not None,
        "constructorSymbol": constructor[1],
        "constructorAddress": hex(constructor[0]),
        "registration": trace.meta_registration,
        "failures": result["failures"],
        "unmodeledCalls": result["unmodeledCalls"],
    }


def compare_reflection(results, path):
    raw = path.read_bytes()
    reflection = json.loads(raw)
    capture_path = path.with_name("Capture.json")
    capture_raw = capture_path.read_bytes()
    capture = json.loads(capture_raw)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != capture["schema_sha256"]:
        raise ValueError("Reflection capture hash does not match its schema")
    observed_by_id = {row["identifier"].upper(): row for row in reflection["metatypes"]}
    by_id = {row["identifier"].upper(): row for row in results}
    count = 0
    members_compared = 0
    matches = 0
    for result in results:
        observed = observed_by_id.get(result["identifier"].upper())
        if observed is None:
            result["reflectionCrossCheck"] = {"status": "metatype absent"}
            continue
        own = next((item for item in observed["member_sets"] if item["relation"] == "own"), None)
        static = next((item for item in result["versions"] if item["schemaVersion"] == observed["version"]), None)
        if not own or not own["initialized"] or static is None:
            result["reflectionCrossCheck"] = {"status": "comparison unavailable", "runtimeOwnSetInitialized": bool(own and own["initialized"]), "extractedCurrentVersionAvailable": static is not None}
            continue
        count += 1
        native_members = own["members"]
        members_compared += len(native_members)
        extracted = static["membersInRegistrationOrder"]
        native_by_name = {member["name"]: member for member in native_members}
        differences = []
        for member in extracted:
            native = native_by_name.get(member["name"])
            if native is None:
                differences.append({"name": member["name"], "field": "name", "reason": "static-only member"})
                continue
            if member.get("cppType") != demangle(native["debug_type_name"]):
                differences.append({"name": member["name"], "field": "cppType", "static": member.get("cppType"), "runtime": demangle(native["debug_type_name"])})
            if int(member.get("optionMask", "-1"), 16) != native["option_mask"]:
                differences.append({"name": member["name"], "field": "optionMask", "static": member.get("optionMask"), "runtime": hex(native["option_mask"])})
            if "typeNameEncoding" in member and member["typeNameEncoding"] != native["debug_type_name"]:
                differences.append({"name": member["name"], "field": "typeNameEncoding", "static": member["typeNameEncoding"], "runtime": native["debug_type_name"]})
        static_names = [member["name"] for member in extracted]
        runtime_names = [member["name"] for member in native_members]
        registration_matches = static_names == runtime_names
        lexical_matches = static["lexicalMemberNames"] == sorted(runtime_names)
        persistent_matches = static["persistedLexicalMemberNames"] == sorted(member["name"] for member in native_members if member["option_mask"] & 1)
        contract = result["metaTypeContract"].get("registration") or {}
        version_matches = contract.get("currentSchemaVersion") == observed["version"]
        base_matches = (contract.get("baseIdentifier") or "").upper() == (observed.get("base_identifier") or "").upper()
        chain = []
        current = result
        seen = set()
        while current["identifier"].upper() not in seen:
            identity = current["identifier"].upper()
            seen.add(identity)
            chain.append(identity)
            base = ((current["metaTypeContract"].get("registration") or {}).get("baseIdentifier") or "").upper()
            if base not in by_id:
                break
            current = by_id[base]
        native_chain = [item["metatype_identifier"].upper() for item in observed["member_sets"]]
        chain_matches = chain == native_chain
        match = registration_matches and lexical_matches and persistent_matches and version_matches and base_matches and chain_matches and not differences
        matches += match
        result["reflectionCrossCheck"] = {
            "status": "match" if match else "difference",
            "runtimeSchemaSha256": digest,
            "currentSchemaVersion": observed["version"],
            "memberCount": len(native_members),
            "matchesRegistrationOrder": registration_matches,
            "matchesLexicalMemberOrder": lexical_matches,
            "matchesPersistedLexicalMemberOrder": persistent_matches,
            "matchesAllCppTypesAndOptionMasks": not differences,
            "matchesCurrentSchemaVersion": version_matches,
            "matchesDirectBaseIdentifier": base_matches,
            "matchesFullMemberSetInheritanceOrder": chain_matches,
            "staticMemberSetIdentifierOrder": chain,
            "runtimeMemberSetIdentifierOrder": native_chain,
            "differences": differences,
        }
    return {
        "schemaPath": str(path.resolve()),
        "schemaSha256": digest,
        "capturePath": str(capture_path.resolve()),
        "captureSha256": hashlib.sha256(capture_raw).hexdigest(),
        "bridgeSha256": capture["bridge_sha256"],
        "fusionVersion": capture["fusion_version"],
        "registeredMetatypeCount": reflection["metatype_count"],
        "currentClassesCompared": count,
        "currentClassesFullyMatched": matches,
        "currentMembersCompared": members_compared,
        "limitation": "This checks registered current metadata, not historical schemas or custom wire save/load behavior",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contents", type=Path, required=True)
    parser.add_argument("--class-map", type=Path, default=Path(__file__).with_name("BinaryClasses.json"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("BinaryFeatureMembers.json"))
    parser.add_argument("--class-name", action="append")
    parser.add_argument("--schema-xml", type=Path, action="append")
    parser.add_argument("--exclude-bases", action="store_true")
    parser.add_argument("--reflection-json", type=Path, default=Path(__file__).parents[1] / "LocalOracle" / "Reflection" / "Schema.json")
    args = parser.parse_args()
    mapping = json.loads(args.class_map.read_text())
    schema_paths = args.schema_xml or [Path(__file__).parents[1] / "LocalOracle" / "Features" / "FeatureSchema.xml"]
    runtime_schemas = {}
    runtime_sources = []
    for path in schema_paths:
        if not path.exists():
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        runtime_sources.append({"path": str(path.resolve()), "sha256": digest})
        for element in ElementTree.fromstring(data):
            runtime_schemas[element.get("_ID", "").upper()] = (element, digest)
    selected = args.class_name or [
        "Na::DesignCapture::DcSketch",
        "Na::DesignCapture::DcExtrudeFeature",
        "Na::DesignCapture::DcProfileBasedFeature",
        "Na::DesignCapture::DcBodyFeature",
        "Na::DesignCapture::DcFeature",
        "Na::DesignCapture::DcComputableAction",
        "Na::DesignCapture::DcNode",
        "Na::DesignCapture::DcExtrudeToolBody",
    ]
    binaries = {}
    classes_by_name = {row["class"]: row for row in mapping["classes"]}
    option_source = next(row for row in mapping["sources"] if row["id"] == "NsDataModel10")
    option_binary = Binary(args.contents / option_source["pathWithinContents"])
    if option_binary.sha256 != option_source["sha256"]:
        raise ValueError("Option contract binary hash differs from the class map")
    options = option_contract(option_binary, option_source)
    results = []
    for name in selected:
        entry = classes_by_name[name]
        source = next(row for row in mapping["sources"] if row["id"] == entry["source"])
        if source["id"] not in binaries:
            binaries[source["id"]] = Binary(args.contents / source["pathWithinContents"])
        binary = binaries[source["id"]]
        if binary.sha256 != source["sha256"]:
            raise ValueError("Binary hash differs from the class map")
        initializer = next((value for key, value in binary.named.items() if key.startswith(name + "::initializeMemberSet(unsigned int,")), None)
        instructions = binary.instructions(initializer[1]) if initializer else {}
        compared_versions = [int(operands[1][1:], 0) for op, operands, _ in instructions.values() if op == "cmp" and operands[0] == "w1" and operands[1].startswith("#")]
        metatype = metatype_contract(binary, name)
        if metatype["complete"]:
            base = metatype["registration"]["baseClass"]
            base_entry = classes_by_name.get(base)
            metatype["registration"]["baseIdentifier"] = base_entry["identifier"] if base_entry else None
            if not args.exclude_bases and base_entry and base not in selected:
                selected.append(base)
        latest = metatype["registration"]["currentSchemaVersion"] if metatype["complete"] else max(compared_versions, default=0)
        versions = range(latest + 1)
        results.append({
            "class": name,
            "identifier": entry["identifier"],
            "source": source,
            "initializerAddress": hex(initializer[0]) if initializer else None,
            "initializerSymbol": initializer[1] if initializer else None,
            "metaTypeContract": metatype,
            "versionSelection": {"method": "metatype constructor current version" if metatype["complete"] else "explicit comparisons against incoming w1", "comparedVersions": sorted(set(compared_versions))},
            "versions": [{"schemaVersion": version, **Trace(binary, instructions, version, option_binary).run()} for version in versions] if instructions else [],
            "initializerUnavailable": initializer is None,
        })
        observed = runtime_schemas.get(entry["identifier"].upper())
        if observed:
            element, digest = observed
            observed_version = int(element.get("_Version"))
            declaration = element.text or ""
            observed_names = declaration.split(" Names=", 1)[1].split() if " Names=" in declaration else []
            extracted = next((version for version in results[-1]["versions"] if version["schemaVersion"] == observed_version), None)
            results[-1]["runtimeCrossCheck"] = {
                "sourceSha256": digest,
                "schemaVersion": observed_version,
                "baseIdentifier": element.get("_BaseID"),
                "runtimeName": element.get("Name"),
                "runtimeMemberNames": observed_names,
                "matchesRegisteredLexicalMembers": extracted is not None and observed_names == extracted["lexicalMemberNames"],
            }
        for version in results[-1]["versions"]:
            for member in version["membersInRegistrationOrder"]:
                proven = True
                if member["registrationKind"] == "template":
                    member["templateContract"] = template_contract(binary, member["registrationSymbol"])
                    proven = member["templateContract"]["provenDefaultOptions"]
                if proven:
                    mask = int(options["defaultMask"], 16)
                    for operation in member["optionOperations"]:
                        operand = int(operation["mask"], 16)
                        mask = mask | operand if operation["operation"] == "set" else mask & ~operand
                    member["optionMask"] = hex(mask)
                    member["persistenceOptionBit0"] = bool(mask & 1)
            version["persistedLexicalMemberNames"] = sorted(member["name"] for member in version["membersInRegistrationOrder"] if member["name"] is not None and member["persistenceOptionBit0"] is True)
            version["completeMemberSchema"] = version["completeTrace"] and all("optionMask" in member for member in version["membersInRegistrationOrder"])
    output = {
        "schema": "FusionBinaryFeatureMembers/1",
        "applicationVersion": mapping["applicationVersion"],
        "architecture": "arm64",
        "extractorSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "memberOptionContract": options,
        "runtimeSchemaSources": runtime_sources,
        "reflectionComparison": compare_reflection(results, args.reflection_json) if args.reflection_json.exists() else None,
        "method": "Static symbolic tracing of named initializeMemberSet routines per explicit schema version. Track AArch64 argument registers, literal strings, member offsets, cached metatype singleton pointers, templated addMember signatures and explicit option-mask mutations. Stop on unresolved conditional control flow; record incomplete traces rather than guessing.",
        "limitations": [
            "In-memory offsets are not wire offsets",
            "Member option mask names other than persistence bit 0 are not inferred",
            "Version enumeration uses the metatype constructor's current version where resolved, otherwise comparisons against incoming w1",
            "Registered field schemas do not establish complete wire serialization; custom save/load behavior and inherited storage segments require separate evidence",
            "Only selected classes and their constructor-identified bases are analyzed",
            "No vendor code is executed and no application acceptance is established",
            "Unmodeled calls discard volatile argument registers and are reported",
        ],
        "classes": results,
    }
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    for result in results:
        print(result["class"], [(v["schemaVersion"], len(v["membersInRegistrationOrder"]), v["completeTrace"]) for v in result["versions"]])


if __name__ == "__main__":
    main()
