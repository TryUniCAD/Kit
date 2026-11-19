FILETIME_UNIX_EPOCH = 116444736000000000
FILETIME_TICKS_PER_SECOND = 10_000_000


def unsigned(value, bits, name):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError(f"{name} must fit an unsigned {bits}-bit word")
    return value


def signed_dword(bits):
    return bits if bits < 1 << 31 else bits - (1 << 32)


def body_match_tag(body_tag):
    return signed_dword(unsigned(body_tag, 32, "body tag"))


def unchanged_face_stamp(face_tag, update_stamp):
    face = unsigned(face_tag, 32, "face tag")
    update = unsigned(update_stamp, 32, "update stamp")
    return signed_dword(((face & 0xffff) << 16) | (update & 0xffff))


def filetime_ticks(updated_at, subsecond_ticks):
    if type(updated_at) is not int:
        raise ValueError("update time must be an integer UTC Unix second")
    if type(subsecond_ticks) is not int or not 0 <= subsecond_ticks < FILETIME_TICKS_PER_SECOND:
        raise ValueError("update fraction must be in 100 ns ticks within one second")
    ticks = FILETIME_UNIX_EPOCH + FILETIME_TICKS_PER_SECOND * updated_at + subsecond_ticks
    return unsigned(ticks, 64, "update FILETIME")


def local_downstream_face_words(updated_at, subsecond_ticks):
    ticks = filetime_ticks(updated_at, subsecond_ticks)
    return 0, signed_dword(ticks & 0xffffffff), signed_dword(ticks >> 32), 0, 0, 0
