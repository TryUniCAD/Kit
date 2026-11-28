from ctypes import (
    CDLL,
    POINTER,
    byref,
    c_char_p,
    c_int,
    c_int64,
    c_uint,
    c_void_p,
    create_string_buffer,
)
from hashlib import sha256
from os import fsencode
from pathlib import Path


class Observer:
    def __init__(self, library):
        self.engine = CDLL(str(library))
        self.engine.unqlite_lib_version.restype = c_char_p
        self.version = self.engine.unqlite_lib_version().decode("ascii")
        if self.version != "1.1.9":
            raise ValueError("the independent observer requires UnQLite 1.1.9")
        arguments = {
            "unqlite_open": (POINTER(c_void_p), c_char_p, c_uint),
            "unqlite_close": (c_void_p,),
            "unqlite_kv_cursor_init": (c_void_p, POINTER(c_void_p)),
            "unqlite_kv_cursor_release": (c_void_p, c_void_p),
            "unqlite_kv_cursor_first_entry": (c_void_p,),
            "unqlite_kv_cursor_valid_entry": (c_void_p,),
            "unqlite_kv_cursor_next_entry": (c_void_p,),
            "unqlite_kv_cursor_key": (c_void_p, c_void_p, POINTER(c_int)),
            "unqlite_kv_cursor_data": (c_void_p, c_void_p, POINTER(c_int64)),
        }
        for name, kinds in arguments.items():
            entry = getattr(self.engine, name)
            entry.argtypes = kinds
            entry.restype = c_int

    def checked(self, name, *args):
        status = getattr(self.engine, name)(*args)
        if status != 0:
            raise ValueError(f"{name} refused the generated store with status {status}")

    def record_part(self, cursor, name, size_type):
        size = size_type()
        self.checked(name, cursor, None, byref(size))
        if not 0 <= size.value <= 4096:
            raise ValueError("independent reader found an unbounded record")
        buffer = create_string_buffer(max(1, size.value))
        before = size.value
        self.checked(name, cursor, buffer, byref(size))
        if before != size.value:
            raise ValueError("independent reader changed the record length")
        return buffer.raw[: size.value]

    def inspect(self, location, expected):
        path = Path(location)
        previous = sha256(path.read_bytes()).digest()
        store = c_void_p()
        cursor = c_void_p()
        self.checked("unqlite_open", byref(store), fsencode(path), 1)
        try:
            self.checked("unqlite_kv_cursor_init", store, byref(cursor))
            try:
                self.checked("unqlite_kv_cursor_first_entry", cursor)
                records = []
                while self.engine.unqlite_kv_cursor_valid_entry(cursor):
                    if len(records) >= len(expected):
                        raise ValueError(
                            "independent reader found additional live cells"
                        )
                    records.append(
                        (
                            self.record_part(cursor, "unqlite_kv_cursor_key", c_int),
                            self.record_part(cursor, "unqlite_kv_cursor_data", c_int64),
                        )
                    )
                    self.engine.unqlite_kv_cursor_next_entry(cursor)
            finally:
                self.checked("unqlite_kv_cursor_release", store, cursor)
        finally:
            self.checked("unqlite_close", store)
        if len(records) != len(expected) or dict(records) != dict(expected):
            raise ValueError("independent reader reconstructed different live records")
        if sha256(path.read_bytes()).digest() != previous:
            raise ValueError("read-only UnQLite observation changed the generated file")
        return len(records)
