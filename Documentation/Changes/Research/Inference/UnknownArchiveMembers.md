# Inspecting unfamiliar ZIP packages

The single-input research command inspects ZIP members when a file does not match a supported inference route. It hashes each readable member and probes XML structure or binary framing. For XML it records attribute values matching exact member names.

Run `kit run --root . auto --input model.FCStd --directory /tmp/archive-research` and inspect the package in `Input-raw-structure.json`. On the AliasEdited native FreeCAD save the probe identified all seven members and six file references in Document.xml, including three shape members, two element maps and a string table. An attribute match is structural evidence. Geometry and feature semantics still require verification.

The probe handles up to 4096 distinct member names, reads stored or deflated entries up to 4 MiB each within a 32 MiB total and probes at most 16 binary members for framing. Encrypted and oversized entries remain deferred. Duplicate names prevent unambiguous lookup. Explicit binary controls use the existing framing experiment.
