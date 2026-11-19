# Generated prism face constructors, SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root owns generated graph construction and native qualification. The constructor and wire rules apply to SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, archive version 19000.

The process starts from two authored rectangular bosses and generates their part streams, Config-0, ModelHeader, resolved feature tree and attached Parasolid partition in memory. The typed reader consumes the generated container and uses the same header and Config-0 map to read the extrusion's actual live profile. The selected configuration must alias the configuration manager's one registered row, and its update stamp must match the ModelHeader.

The projection joins the active partition's `ATOM_ID_2001`, `BODY_MATCH` and `LAST_BODY_MODIFYING_FEATURE_ID` with the part's actual atom manager and blind boss. The four side IDs each resolve to a different permanent sketch-line marker. Both planar caps carry the actual start or end selector and contour zero. Every primary representation uses the live producing feature's creation event and the generated local file/configuration identity.

| Owner | Derived constructor state |
| --- | --- |
| Downstream row | The ID allocated to the face in the physical solid chain. |
| `moCompFace_c` | A fresh component wrapper with the same actual body atom in `f18/f1c` and a separate local unit component at `f58`. |
| `moFaceRef_c` | The selected face and four adjacent faces in native fin order, each with a new surface representation. The terminal slot holds the null loop delimiter. |
| Feature keeper `moFR_c` | Actual producer and creation time. The selected local wire owners share the modeled file definition and active configuration. |
| Embedded `f18` | The role values already available during construction, with the independent vertex and edge fields in their fresh face state. |

The selected mode-0 constructor saves `(f60,f64)=(1,0)`, zero resolution flags and handle, the two `1e100` sentinels and an empty match array. The process starts a separate archive map for the cache body. The existing part streams survive byte-for-byte when the witness is stored under Config-0. [Face-row construction source](DownstreamFreshFaceRows2026.md) · [Local context and post-resolution source](DownstreamStoredFaceState2026.md)

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckPrismFaceConstructors 1
```

Repeat with variant `2` for the second design. Four fresh processes reproduce twelve distinct rows across the two designs, with 60 surface representations, 12 file-local component slots, and 24 initial role values. Each run compares the wire readback with an independent walk of the emitted partition, verifies the shared file path and configuration, refuses a special-map request and wrong allocation endpoint, and re-emits identical bytes. The guard records zero file opens, new connections or subprocesses after loading the research field registry and Python packages. [Process receipt](../measurements/2026/DownstreamPrismFaceConstructors01.json)

The measured body is a constructor witness with six face rows per design. A follow-up replay models the original and alternate-key validation and adds the collector members. Native validation, the remaining cache collections and the linked drawing save/reopen sequence remain qualification steps. [Generated key replay](DownstreamPrismFaceStore2026.md) · [Runtime owner recovery](DownstreamPartOwnerReload2026.md)
