# Extrusion output pointers require a typed invocation

A generated Python class can show default values for `GetDirectionReference` output arguments while the actual object in hand remains a dynamic `win32com.client.CDispatch`. A zero-argument call on that dynamic object does not allocate the registered four output pointers. The disclosed oblique-source observer failed with `DISP_E_PARAMNOTOPTIONAL` before any mass/edit/save acceptance.

Read the actual registered method and use explicit `InvokeTypes` descriptors: DISPID `50` returns I4 and has output dispatch/I4/dispatch/I4 pointers; DISPID `44` returns dispatch and has input Forward boolean plus output I4 pointer. Preserve result-first, declared-output order and wrap actual returned dispatch objects before their interface query. Do not mix guessed optional arguments, fabricated values or a manually typed VARIANT with a generated wrapper's coercion behavior.

The retry helper accepts only these exact two registered layouts. Its source-only CLI checks an actual metadata receipt without starting COM. The corrected native call remains unmeasured until the controlled retry. [Failure, actual descriptors and preserved limits](../../../../../../re/solidworks/records/FreecadObliqueCylinderObserverRetry2026.md)
