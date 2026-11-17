# SOLIDWORKS 2026 principal-plane handles

The selected ordinary profile owns a `moCompRefPlane_c` at `moProfileFeature_c.pd_f78`. Its `moCompRef_c.f4c`, `moFRData_c` and `moCompRefPlane_c.f100` fields precede the profile's `pd_ff0` transform. The [registered component](../../tooling/sw2026/serial/defs/ResolvedComp.py), [profile](../../tooling/sw2026/serial/defs/ResolvedProfile.py) and [transform](../../tooling/sw2026/serial/defs/Geometry.py) grammars read these fields in sequence. The component points to the sketch's actual model and the feature handle refers to a persistent plane ID in that model.

| Offset from version | Type | Field |
| --- | --- | --- |
| 0 | `u32le` | Archive version, `19000` |
| 4 | `u32le` | `moFRData_c.f00`, persistent plane ID |
| 8 | `u32le` | `moFRData_c.f08`, referenced feature creation-log time |
| 12 | `u16le` | Null object marker for `moCompRefPlane_c.ff8` in this scope |
| 14 | `i32le` | `moCompRefPlane_c.f100`, principal axis kind, 1 for Right, 2 for Top, 3 for Front |
| 18 | `u8` | `mgXform_c.restore.has_matrix` |
| 19 | Optional `9f64le` | A present matrix stores the sketch basis in columns. An omitted matrix means identity. |
| After the optional matrix | `4f64le, u8` | Translation, scale and extension flag, respectively `(0, 0, 0)`, `1` and `0` for the measured ordinary principal frames |

The deep typed read of each disclosed native part gives the same plane ID as its profile reference and the same frame as that model's principal-plane feature. The bounded public reader now matches a complete record within the sketch's native span and verifies the axis kind and full basis against the decoded model-owned plane. The creation-log field retains its width across different times. The legacy `18000` branch still admits its existing exact layout and keeps its precedence. The new branch rejects multiple complete candidates within one sketch span, and rejects a recognized candidate whose basis or axis disagrees with the owner. Custom planes, nonneutral transform tails and optional reference objects remain handled by prior routes.

## Disclosed and generated evidence

| Case | Sketch and plane | Version offset and sketch span | Creation-log time and basis |
| --- | --- | --- | --- |
| Vendor D17 Top circle | 26 → 3 | 8817 within `[5862, 8990)` | `1794529625`, columns `(1,0,0) (0,0,-1) (0,1,0)` |
| Vendor D18 Right circle | 26 → 4 | 8817 within `[5862, 8990)` | `1794529625`, columns `(0,0,-1) (0,1,0) (1,0,0)` |
| Disclosed vendor A13/A14 sibling Front sketch | 26 → 2 | 11147 within `[5862, 11248)` | `1794529625`, identity |
| Generated Front polygon | 18 → 14 | 6918 within `[5307, 7019)` | `2592000`, identity |
| Generated Top polygon | 18 → 15 | 6990 within `[5379, 7163)` | `2592000`, explicit Top basis |
| Generated Right polygon | 18 → 16 | 6990 within `[5379, 7163)` | `2592000`, explicit Right basis |

The two independently authored parts had previously used the Front plane as a stream-order fallback. The generated Top and Right parts produced the same wrong association even after both XML role labels were corrected. The fixed public `open_document(include_brep=False, include_tessellation=False)` returns the archived plane IDs and validates on all three freshly generated canonical-role cases and both vendor parts. [Disclosed authoring manifest](../v2026/corpus/curves-discovery/Manifest.json) and [public reader regression](../../../tests/Convert/Solidworks/Core/SolidworksPrincipalTests.py).

Two in-memory negative probes through the native model decoder duplicated a complete candidate within one D17 sketch span and changed its axis kind while preserving its actual plane ID. The decoder rejected both inputs with the expected ambiguity and frame disagreement errors.

| Fixture | SHA-256 |
| --- | --- |
| Vendor D17 Top circle | `cdf237d6d0ae21c0e81de168d2d0d6153a1b6dc20cd2d53beca88bf60e4b7aa5` |
| Vendor D18 Right circle | `3bf38305bea09980a8a44da09a8721ae00294a9683c1a1fc157335f17fda61a9` |
| Vendor A13 child | `f7dcb761afd5f3761cbcabdda07928d22936884c34a5b1c4decdab45657f4fd8` |
| Vendor A14 child | `1e8c99c6ab8777daec2b28cb57a9b3db8c18adf9d700415a9a4629e07d9d7550` |
| Generated Front, default | `d0fb5cefd0423fded12abb501aa9fb3e3172026f7cf4c0b4c275f596b97fdb73` |
| Generated Front, native plane roles | `88ad4e947dedcc566e46fcdc714e1fe543979c705f20232a253b4586c5495014` |
| Generated Top, default | `6b0c32eb399f4a92ef5007cb017cef9c95c76fa3761dcd7b36b5051a4d86b791` |
| Generated Top, native plane roles | `979c40adc332ffe6bb2661f34d0deba9af78bb8711cc1f22b30ce66918149096` |
| Generated Right, default | `4edd86abb10ba6e2ef4d24279c40bc3adfa83b85687bbd6e2617039e150589f8` |
| Generated Right, native plane roles | `750d76af956589e79190216d6fc9ad35b57e6f80fbee43d471cdb3d4bf75a1f6` |

The generated cases used independent rectangular vertices `[(.003,.009),(.027,.009),(.027,.029),(.003,.029)]` and an ordinary blind boss depth of `.016` metres. Each opted archive changes only `swXmlContents/KeyWords`; all binary streams compare exactly against its default counterpart. The part role option emits the valid vendor labels `Feature Type="PLANE"` and `Sketch Type="Origin"`. The documented [assembly XML index](AssemblyInstanceTree2026.md) has an independent need for both labels.

## Historical reader controls

Reader projections included decoded planes, selected and unframed support IDs, support source and kind, and framed relationships. Before and after digests agreed on these older real parts.

| Fixture | Sketches | Reader projection SHA-256 |
| --- | --- | --- |
| BIELA | 6 | `83558df71bf2b3ab8806602c329b0d2177be0f695eb69c6212df947bacfa77cd` |
| Turbo Tube | 26 | `557a8a358925d09527636ab88bd3cd3f2fd8e71f0974c4726e348ca2d58d8f37` |
| CUBIERTA DE TURBINA 1 | 22 | `435f01a14c8c83efd878eabb835a5edf5ef6c5cd240a3f26e05ba71b95c58884` |
| example | 5 | `34085aee9394d76bf7ca2f242598e94028bfce8f299686ef2897968974cc1ce8` |

The [feature reference creation-time rules](ModelConstruction2026.md#feature-reference-creation-time) explain why the timestamp differs across these inputs. The observations in this record establish the scoped history reader. The stricter geometry route still requires a readable geometry payload.
