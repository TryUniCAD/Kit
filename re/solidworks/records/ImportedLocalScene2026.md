# Authored scene on a generated SOLIDWORKS local import

Task `B04-SW2026-IMPORTED-BODY`, PR #121. Build a planar imported solid
with the actual source's supported light semantics, using one ordered
ambient and directional group. Scene values come from the source being
projected. The constructor uses the existing feature allocator and
light serializers. It never looks up station defaults or reads an archive.

## Locked disclosed trial

The [trial tool](../../tooling/sw2026/imported_body_source/ProbeImportedPartScene.py)
pins the original disclosed imported rectangle, the independent translated
rectangle and the separate Unicode feature rename by SHA-256. The inputs
first pass the strict geometry, name and scene ownership checks. The expected
geometry comes from the original authoring specifications. Frozen processes
construct the same bytes twice with zero runtime file reads.

A second construction at each destination with no light values changes
only `Header2`, `Contents/CMgr`, `Contents/Config-0` and its ModelHeader and
ResolvedFeatures. Light semantics agree by typed readback. The scope includes
the actual import feature and bound body label, the active configuration
name, the closed planar boundary and the four lights. The original explicitly
empty property owner records are absent in the generated read. Source identity,
provenance and additional presentation owners remain outside this check.

The native protocol compares each source, rebuilt candidate and independently
reopened save in fresh processes bracketed by known-good controls on build
`34.5.2.0604`. Native scene names and ownership are observed cold and after
rebuild. Typed save readback checks the original semantic light inputs. These
are disclosed discovery inputs. Held-out and public writer qualification
remain separate.
