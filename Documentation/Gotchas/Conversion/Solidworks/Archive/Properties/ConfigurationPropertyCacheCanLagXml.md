# Configuration property cache can lag live XML

## Expectation

The binary custom-property list owned by a configuration contains its
current text, or must agree with its configuration property XML after save.

## Observed behavior

SOLIDWORKS 2026 SP05.2 saved two independently edited configuration values
to their `docProps/Config-0-Properties.xml` owners while retaining earlier
text in the same configuration's embedded `fb68` property cache. Native
`Get6` returned the edited XML value after save and fresh reopen. Fresh SDK
files can also have populated configuration XML and an empty binary list.

The binary cache is a real typed owner, but its stored value is not an
unconditional live-value authority. Requiring cache/XML equality would
reject healthy disclosed native saves. Reading the cache as current text
would revert the user's edit.

## Workaround

Bind each XML configuration ID to the actual typed CMgr configuration node
and its real name. For the qualified compatible literal-text layout, read
the live value from that configuration's XML. Preserve and decode the cache
independently. Guard advanced managers, unsupported variants and stale
configuration identities; expose an unsupported property status while
retaining ordinary geometry and history.

[Field and lifecycle evidence](../../../../../../re/solidworks/records/PartTextPropertyRead2026.md)

[SDK process receipt](../../../../../../re/solidworks/measurements/2026/PartTextPropertyRead01.json)
