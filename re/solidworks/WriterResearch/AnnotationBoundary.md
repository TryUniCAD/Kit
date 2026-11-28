# Top annotation emission boundary

This is offline research evidence, not native acceptance or production support.

`VerifyAnnotationBoundary.py` sends one explicit owned-neutral request to a fresh isolated Python process:

```json
{"generation":19000,"first_name":"*Top","include_top":false}
```

The child imports the selected checkout's serializer and reader before installing an audit guard.
The UTF-16 codec is also loaded before the guard because Python loads it lazily.
It then generates the prior saved views, sketch-block manager, annotation and following model lists entirely in memory.
No native archive, captured allocator or source-file path is supplied to emission.

```powershell
python re/solidworks/WriterResearch/VerifyAnnotationBoundary.py --root C:/trusted/KitCheckout
```

The guard refuses file opens, imports, directory enumeration, process starts, socket activity and ctypes calls during emission.
Real attempts to open a nonexistent file, start a Python child, import a module, create a socket and load a library calibrate the guard before the measured operation.
Each attempt is rejected before external execution.
These observations instrument this Python call path; they are not an operating-system sandbox guarantee.

## Recorded process result

[AnnotationBoundary.json](Evidence/AnnotationBoundary.json) records two generated allocator placements and 22 refusal cases at serializer revision `bf87e42d46db3bec776ef9959ef775a23b7fcd0e`.
Two independent command executions returned zero with byte-identical reports on Python 3.14.6.
The canonical report SHA-256 is `ac7f072f512d4efdf819efcab68fbb38893ce83a50542c9897e501cc41d45dce`.
The report binds the command's bytes, six directly used research modules and the aggregate digest of all 829 loaded project modules.

Both synthetic contexts emit 282 annotation bytes and 164 following-list bytes.
The list, annotation-class definition and annotation object advance the first allocator from 18 to 21.
A separately owned neutral root shifts the second context from 19 to 22.
The reader consumes the exact extents and reproduces the complete class/object map before and after the following lists.
The selected native control's separate slots 99 and 101 and ID 200 are not inferred from these synthetic placements.
Native byte/map comparison remains owned by `VerifyConfigAnnotViews.py`.

Unsupported names, generations, duplicate Top requests, flag types, missing owners, repeated annotation classes, counter limits and six occupied future-slot states all refuse without changing existing bytes or maps.
Three additional cases prove that nonnull aliases, an explicit basis and another schema cannot be passed as unexpected API arguments.
The scalar serializer exposes no native annotation-graph admission API.
Those three cases do not prove semantic admission of alias-bearing source graphs.
Three additional fresh processes reject JSON with nonnull aliases, an explicit basis or a missing flag before importing the serializer or emitting data.
The internal worker requires the exact three-field request shape and does not discard unknown fields.

No emission attempt triggered the external-access guard.
No CAD application was launched and no sealed holdout was inspected.
`vendor_loadable` and `application_usable` remain false.
Full source fidelity, annotation roster/state, independent holdout generalization and native open/edit/rebuild/save/reopen acceptance remain required.
