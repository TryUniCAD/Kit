# Part serialization dispatch depends on archive context

The custom archive reader invokes the part's vtable slot `0x10` first.
That slot is a shared bridge which dispatches slot `0x28`; the native part
serializer then chooses modern LW/RES sections only for versions above `0xc7c`.
Hooking only one stage can hide the selected data path.

The selected version comes from an archive-helper object found by a map lookup
using the actual archive pointer. A zero helper version falls back to the
global version manager. It is not enough to infer that value from the intended
target version or to read a presumed fixed archive extension member.

Modern sections consume their four-byte length before their body, including
the known section-skip paths. If that length becomes a nested object tag,
inspect actual dispatch and version state before modifying object-map counts.

The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md#native-archive-dispatch)
records the exact vtable entries, bridge evidence and helper/version addresses.
The candidate's selected runtime path remains a native measurement question.
