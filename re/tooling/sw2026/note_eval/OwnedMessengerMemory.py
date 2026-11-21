from hashlib import sha256
from pathlib import Path
from struct import calcsize, unpack_from


ACCESS = 0x410
SESSION_SHA = "c53d42d0b7bcfd9abf78cfd71ca6f71645cb8da16ea29c155f63172eaa17f421"
GETTER = "?SldGrMessenger@SldSession_c@@SAPEAVSldGrMessenger_c@@XZ"
GETTER_RVA = 0xA1D0
GETTER_SHA = "0ccfb663a8914c9372ba3b7371e0f880084e9de9a874e2b1d2f0bfeeaf1cc157"
GLOBAL_RVA = 0x32A30
FALLBACK_RVA = 0x31028


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def image(path):
    require(64 <= path.stat().st_size <= 536870912, "module file exceeds the observer bound")
    data = path.read_bytes()
    require(64 <= len(data) <= 536870912 and data[:2] == b"MZ", "module file is not a bounded PE")
    pe = unpack_from("<I", data, 60)[0]
    require(pe + 264 <= len(data) and data[pe:pe + 4] == b"PE\0\0", "module PE header is incomplete")
    opt = pe + 24
    require(unpack_from("<H", data, pe + 4)[0] == 0x8664 and unpack_from("<H", data, opt)[0] == 0x20B,
            "module is not AMD64 PE32+")
    size = unpack_from("<I", data, opt + 56)[0]
    first = opt + unpack_from("<H", data, pe + 20)[0]
    sections = []
    for index in range(unpack_from("<H", data, pe + 6)[0]):
        at = first + index * 40
        require(at + 40 <= len(data), "module section table is incomplete")
        name, virtual, rva, raw, offset = unpack_from("<8sIIII", data, at)
        sections.append((name.rstrip(b"\0").decode("ascii"), virtual, rva, raw, offset,
                         unpack_from("<I", data, at + 36)[0]))
    return data, opt, size, sections


def file_offset(rva, count, sections):
    for _, _, start, raw, offset, _ in sections:
        if start <= rva and rva + count <= start + raw:
            return offset + rva - start
    raise RuntimeError("module RVA has no complete file-backed span")


def session_export(data, optional, sections):
    rva, size = unpack_from("<II", data, optional + 112)
    at = file_offset(rva, 40, sections)
    fields = unpack_from("<IIHHIIIIIII", data, at)
    names = file_offset(fields[9], fields[7] * 4, sections)
    ordinals = file_offset(fields[10], fields[7] * 2, sections)
    functions = file_offset(fields[8], fields[6] * 4, sections)
    found = []
    for index in range(fields[7]):
        text_rva = unpack_from("<I", data, names + index * 4)[0]
        text_at = file_offset(text_rva, 1, sections)
        end = data.find(b"\0", text_at, text_at + 512)
        require(end >= 0, "module export spelling is unterminated")
        if data[text_at:end].decode("ascii") == GETTER:
            ordinal = unpack_from("<H", data, ordinals + index * 2)[0]
            require(ordinal < fields[6], "module export ordinal is invalid")
            target = unpack_from("<I", data, functions + ordinal * 4)[0]
            require(not rva <= target < rva + size, "session getter is a forwarded export")
            found.append(target)
    require(found == [GETTER_RVA], "session getter export identity differs")
    code_at = file_offset(found[0], 8, sections)
    code = data[code_at:code_at + 8]
    require(sha256(code).hexdigest() == GETTER_SHA and code[:3] == b"\x48\x8b\x05" and code[7] == 0xC3,
            "session getter body differs")
    derived = found[0] + 7 + unpack_from("<i", code, 3)[0]
    require(derived == GLOBAL_RVA, "session getter resolves a different global")
    return found[0], derived, code


class OwnedProcess:
    def __init__(self, identity, owned):
        import ctypes as c
        from ctypes import wintypes as w
        from OracleIdentity import process_creation_time

        require(calcsize("P") == 8, "observer must run as 64-bit Python")
        self.c, self.w, self.identity, self.owned = c, w, identity, owned
        self.birth = process_creation_time
        self.pid = int(identity["process_id"])
        require(self.pid in owned(), "process is not registered to this task")
        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        self.kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.kernel.OpenProcess.restype = w.HANDLE
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.CloseHandle.restype = w.BOOL
        self.kernel.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]
        self.kernel.ReadProcessMemory.restype = w.BOOL
        self.kernel.K32EnumProcessModulesEx.argtypes = [w.HANDLE, c.c_void_p, w.DWORD, c.POINTER(w.DWORD), w.DWORD]
        self.kernel.K32EnumProcessModulesEx.restype = w.BOOL
        self.kernel.K32GetModuleFileNameExW.argtypes = [w.HANDLE, c.c_void_p, w.LPWSTR, w.DWORD]
        self.kernel.K32GetModuleFileNameExW.restype = w.DWORD

        class ModuleInfo(c.Structure):
            _fields_ = [("base", c.c_void_p), ("size", w.DWORD), ("entry", c.c_void_p)]

        self.module_info = ModuleInfo
        self.kernel.K32GetModuleInformation.argtypes = [w.HANDLE, c.c_void_p, c.POINTER(ModuleInfo), w.DWORD]
        self.kernel.K32GetModuleInformation.restype = w.BOOL
        self.handle = self.kernel.OpenProcess(ACCESS, False, self.pid)
        if not self.handle:
            raise c.WinError(c.get_last_error())
        self.cache = {}
        self.partial = {}
        self.read_count = 0
        self.read_bytes = 0
        try:
            self.check()
        except BaseException:
            self.close()
            raise

    def check(self):
        require(self.pid in self.owned(), "owned process lifetime ended")
        require(self.birth(self.handle) == self.identity["process_creation_filetime"], "owned process birth differs")

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            if not self.kernel.CloseHandle(handle):
                raise self.c.WinError(self.c.get_last_error())

    def read(self, address, count):
        self.check()
        require(0x10000 <= address < 0x800000000000 and 0 < count <= 4096
                and address + count <= 0x800000000000, "unbounded owned memory read")
        buffer = self.c.create_string_buffer(count)
        actual = self.c.c_size_t()
        if not self.kernel.ReadProcessMemory(self.handle, self.c.c_void_p(address), buffer, count, self.c.byref(actual)):
            raise self.c.WinError(self.c.get_last_error())
        require(actual.value == count, "owned memory read was short")
        self.read_count += 1
        self.read_bytes += count
        return buffer.raw

    def word(self, address):
        return unpack_from("<Q", self.read(address, 8))[0]

    def modules(self):
        self.check()
        count = 128
        for _ in range(4):
            array = (self.c.c_void_p * count)()
            needed = self.w.DWORD()
            if not self.kernel.K32EnumProcessModulesEx(self.handle, array, self.c.sizeof(array), self.c.byref(needed), 2):
                raise self.c.WinError(self.c.get_last_error())
            require(needed.value % 8 == 0 and needed.value <= 32768, "loaded module count exceeds observer bound")
            if needed.value <= self.c.sizeof(array):
                break
            count = needed.value // 8
        else:
            raise RuntimeError("loaded module list did not stabilize")
        rows = []
        for base in array[:needed.value // 8]:
            info = self.module_info()
            if not self.kernel.K32GetModuleInformation(self.handle, self.c.c_void_p(base), self.c.byref(info), self.c.sizeof(info)):
                raise self.c.WinError(self.c.get_last_error())
            name = self.c.create_unicode_buffer(32768)
            length = self.kernel.K32GetModuleFileNameExW(self.handle, self.c.c_void_p(base), name, len(name))
            require(0 < length < len(name) - 1 and info.base == base and info.size > 0, "loaded module identity is incomplete")
            rows.append({"base": int(base), "size": int(info.size), "path": name.value})
        return rows

    def identity_for(self, row):
        key = (row["base"], row["path"])
        if key not in self.cache:
            from win32api import GetFileVersionInfo
            path = Path(row["path"])
            require(path.suffix.casefold() in (".dll", ".exe"), "target owner is not a loaded PE module")
            data, optional, size, sections = image(path)
            require(size == row["size"], "loaded and file-backed module sizes differ")
            info = {"name": path.name, "path": str(path), "base": hex(row["base"]), "image_bytes": size,
                    "file_bytes": len(data), "sha256": sha256(data).hexdigest(), "machine": "0x8664",
                    "sha256_scope": "complete on-disk module, not remote image contents"}
            try:
                version = GetFileVersionInfo(str(path), "\\")
                high, low = version["FileVersionMS"], version["FileVersionLS"]
                info["version"] = [high >> 16, high & 65535, low >> 16, low & 65535]
            except Exception as error:
                info["version_error"] = repr(error)
            self.cache[key] = info, data, optional, sections
        return self.cache[key]

    def owner(self, address, modules, executable=False):
        rows = [row for row in modules if row["base"] <= address < row["base"] + row["size"]]
        require(len(rows) == 1, "pointer has no unique loaded module owner")
        row = rows[0]
        info, _, _, sections = self.identity_for(row)
        rva = address - row["base"]
        selected = [item for item in sections if item[2] <= rva < item[2] + max(item[1], item[3])]
        require(len(selected) == 1, "pointer has no unique module section")
        if executable:
            require(selected[0][5] & 0x20000000, "messenger target is not in an executable module section")
        return {"module": info, "rva": hex(rva), "section": selected[0][0], "executable": bool(selected[0][5] & 0x20000000)}

    def snapshot(self):
        self.partial = {}
        modules = self.modules()
        session = [row for row in modules if Path(row["path"]).name.casefold() == "sldsessionu.dll"]
        require(len(session) == 1, "actual session module is absent or duplicated")
        module = session[0]
        info, data, optional, sections = self.identity_for(module)
        require(info["sha256"] == SESSION_SHA and info.get("version") == [34, 5, 2, 604], "wrong exact session image")
        getter, global_rva, code = session_export(data, optional, sections)
        live = self.read(module["base"] + getter, 8)
        require(live == code, "loaded getter bytes differ from the pinned original leaf")
        global_address = module["base"] + getter + 7 + unpack_from("<i", live, 3)[0]
        require(global_address == module["base"] + global_rva, "loaded global derivation differs")
        self.partial = {"session": info, "getter_rva": hex(getter), "global_rva": hex(global_rva),
                        "global_address": hex(global_address)}
        messenger = self.word(global_address)
        self.partial["messenger"] = hex(messenger)
        require(messenger % 8 == 0, "messenger pointer is misaligned")
        table = self.word(messenger)
        self.partial["vtable"] = hex(table)
        require(table % 8 == 0, "messenger vtable is misaligned")
        target = self.word(table + 0x10)
        self.partial["target"] = hex(target)
        require(self.word(global_address) == messenger and self.word(messenger) == table
                and self.word(table + 0x10) == target, "messenger pointer chain changed during observation")
        result = {"session": info, "getter_export": GETTER, "getter_rva": hex(getter), "getter_sha256": sha256(live).hexdigest(),
                  "global_rva": hex(global_rva), "global_address": hex(global_address), "messenger": hex(messenger),
                  "vtable": hex(table), "slot": "0x10", "target": hex(target),
                  "uses_source_bound_default_object": messenger == module["base"] + FALLBACK_RVA,
                  "pointer_chain_stable_during_reads": True, "atomic_snapshot": False,
                  "vtable_owner": self.owner(table, modules), "target_owner": self.owner(target, modules, executable=True),
                  "loaded_module_count": len(modules), "process_access_mask": hex(ACCESS),
                  "rpm_calls_so_far": self.read_count, "rpm_bytes_so_far": self.read_bytes}
        self.check()
        return result
