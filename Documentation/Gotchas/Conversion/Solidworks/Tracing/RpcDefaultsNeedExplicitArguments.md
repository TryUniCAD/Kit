# Frida RPC defaults need explicit arguments

## Expectation

Calling the training export without arguments uses its JavaScript default Boolean.

## Actual behavior

The installed Frida 17.26.3 Python binding is in `frida/__init__.py`, not a separate `core.py`. Its `_ScriptExports.__getattr__` sends the supplied positional list plus an optional binary payload. A bare call sends an empty list and `data=None`; an explicit Boolean remains the first positional value. The inspected file SHA-256 is `f7fb4743a4bdfb124e7fab033cccf7b174f802fdd7499be687c7b6db54eeaa35`.

The [version-pinned dispatcher](https://github.com/frida/frida-gum/blob/17.26.3/bindings/gumjs/runtime/message-dispatcher.js#L42) appends that binary payload after the positional values. The absent-data paths in both [QuickJS](https://github.com/frida/frida-gum/blob/17.26.3/bindings/gumjs/gumquickcore.c#L5600-L5615) and [V8](https://github.com/frida/frida-gum/blob/17.26.3/bindings/gumjs/gumv8core.cpp#L4463-L4484) supply JavaScript null. The bare call therefore supplies null as the first export argument. JavaScript defaults apply to undefined, not null. Strict Boolean validation correctly rejects it. This is an RPC argument contract, not a Python Boolean-conversion failure or a CAD crash.

The root-owned `d5f9` batch activated all 36 hooks and measured healthy controls on both sides, but executed zero training cases because the first bare reset failed. Explicit False resets succeeded. Original metadata remains unchanged; [the source/evidence record](../../../../../re/solidworks/records/TrainingRpcBinding2026.json) binds the installed package and actual reports.

## Workaround

Pass True explicitly to enable/reset capture and False explicitly to pause/clear it. Keep the JavaScript primitive-type guard. Do not convert null to a success value or assume the bridge omits an argument merely because the Python caller omitted one. Zero-formal-parameter exports can ignore the extra payload; this finding concerns a defaulted first parameter.

The [focused repair](../../../../Changes/Solidworks/Inspection/Sketches/SolidworksTrainingResetArguments.md) changes only the two bare action calls. Static source/AST review passed; a fresh committed root-owned training run remains pending.
