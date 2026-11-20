# Source names for single local imported solids in the SOLIDWORKS SDK

Task `B04-SW2026-IMPORTED-BODY`, PR #121. This checkpoint projects the body
name and design-body link for the disclosed full planar local BaseBody shape.
The native authoring authority is SOLIDWORKS 2026 SP05.2 `34.5.2.0604`.
[Name contrasts](../measurements/2026/ImportedBodyNamesContrast01.json) · [Generated and saved inputs](../measurements/2026/ImportedLocalBodySdkSavedRead01.json)

## Owner and selection checks

The reader requires the selected Config-0 partition and history to match the
actual archive streams and own a body-free active WORLD. It reads the complete
local storage group and verifies that its compressed record supplies the
actual geometry. The key, linked schema 1 BaseBody suffix, feature name and
public import step agree. The feature's partition mark matches the active
WORLD. Its actual output atom is the same object registered in the configuration
manager. The retained ID and atom ID agree, and the atom's creator and last
modifier identify the actual resolved feature. Any attribute-based tracking
values are compared with those same owners.

The typed kernel graph must exhaust one closed planar local solid. Valid native
`ATTRIB_DEF.next` links sometimes point outside the transmit. Only the external
definition-list continuation is excluded from local reachability. Required
owners, value records and geometric references still resolve. The projected
B-rep is compared with the geometry read from the actual selected payload and
with the complete typed topology and vertex inventory.
[Reader](../../../src/convert/adapters/solidworks/Core/TypedResolved/BodyNames/Local/ReadLocalNamedBody.py) · [Definition links](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodyDefinitionsCanLinkOutsideTransmit.md)

## Observations

The original uses `Imported1` for both feature and body. The feature-only
rename stores `Transfer Δ17` as the feature key and derived body label. The
explicit body rename keeps the feature key `Transfer Δ17` and projects
`Casting Ω72` from the authored atom and agreeing kernel UTF-16 record.
The measured legacy character compatibility value is `Casting O72`.

The two bare generated parts derive `Imported geometry` from the checked key
and derived atom state. The attributed generated parts and all four native
saves also carry the matching kernel name. Every measured B-rep body binds
to its existing sole design body and retains its original producing feature.

| Disclosed input | SHA-256 | Body name owner |
| --- | --- | --- |
| Original | `13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325` | Implicit kernel and key |
| Feature rename | `660277a250a8c719705d6332cfc1f3713ccc5082d07de2ad5c3006279c1f20e8` | Implicit kernel and key |
| Body rename | `2814fd13c29c840f2079485d47856333e756860fd0abee927703fc47a7cb7f43` | Authored atom and kernel |
| Concave bare generated | `21867dbe53b94bbfadfc343ed47f8ca3b0af1fb30114f3a921f730c84f087429` | Storage key |
| Concave bare saved | `37095d2362be9fd5035a2d2688db3ae48bd4c271538a266a0b008246d1267585` | Implicit kernel and key |
| Concave owned generated | `fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33` | Implicit kernel and key |
| Concave owned saved | `e63505d39a1408003707ad93b898007a05f0110ffa0dd1f649761223000680a5` | Implicit kernel and key |
| Rectangular bare generated | `302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357` | Storage key |
| Rectangular bare saved | `6c3bd9562db256fcb79b467cadac754dd158a871081a6884fee2c56f62cd4f1b` | Implicit kernel and key |
| Rectangular owned generated | `dafdf93377f504435d3fe62dd9417f7292ac03c2c23ade9d379b4632311f9149` | Implicit kernel and key |
| Rectangular owned saved | `ab0bf04e2da5532973b5423e46cd995da8755ea30e1be1dc93899567253f4d29` | Implicit kernel and key |

The host observations opened each exact input before and after the change.
All 22 canonical feature-timeline and B-rep fingerprints matched after
removing only the new body binding metadata from the B-rep comparison.
Each returned B-rep also equalled the actual geometry read from its selected
payload after restoring its original body record. In-memory refusal observations
covered a mismatched outer group key, a different selected configuration, a
competing payload and a detached atom with copied scalar fields. The source
files stayed intact. This is disclosed SDK evidence. Held-out semantic
qualification remains open.
