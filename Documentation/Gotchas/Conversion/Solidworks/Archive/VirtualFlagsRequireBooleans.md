# Virtual flag targets require Boolean values

A native body virtual declared as `Flag` selects whether to visit its nested
fields. An integer zero or a schema-name string can look valid to a Python
truth check and still describe the wrong kind of native slot. The former
writer accepted those targets while the reader rejected them.

Declare a concrete `True` or `False` for flag targets. The shared lookup
enforces this before either reader or writer uses the result. For the
SOLIDWORKS 2026 SP05.2 CMgr feature base, concrete slot `0x3f8` is false
on the manager and true on the part configuration. The latter then calls
the separately declared `0x3e8` schema slot.

The [guarded CMgr receipt](../../../../../re/solidworks/measurements/2026/SharedPartCmgrDispatch01.json)
records both valid paths and malformed registry contrasts in both archive
directions.
