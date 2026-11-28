# Read ordinary SOLIDWORKS part text properties

The normal SDK part reader exposes authored document summary text, file
custom text and each actual configuration's custom text as separate
metadata dictionaries. It validates the configuration XML ID against the
typed native manager and preserves the actual configuration name.

Read `metadata["document_summary"]` and `metadata["custom_properties"]`,
then each configuration's `attributes["custom_properties"]`.
`metadata["solidworks.part_text_properties"]["status"]` is `complete` only
for the admitted compatible literal-text profile. Unsupported optional
metadata reports `unsupported` and an information diagnostic, withholds
the entire text projection, and preserves existing geometry/history reads.

The shared ordinary archive codec now handles the nine typed fields of
embedded native custom-property records. Five disclosed normal reads match
independent authored or native API dictionaries and reproduce their CMgr
streams exactly. The actual advanced-manager negative retains geometry
and reports the guarded boundary. Three integration tests cover 18 fresh
public reads, including fourteen malformed or stale-owner cases.

The live configuration value comes from its XML owner. A native binary
property cache can retain older text after a successful edit/save/reopen.
Advanced managers, other value types, links, equations and general native
multiple-configuration qualification remain outside this slice. No public
writer scope or native acceptance flag changes.

[Adapter guide](../../../../Reference/Adapters/Solidworks.md)

[Exact field and scope record](../../../../../re/solidworks/records/PartTextPropertyRead2026.md)

[Sanitized proof](../../../../../re/solidworks/measurements/2026/PartTextPropertyRead01.json)

[Cache lifecycle gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/ConfigurationPropertyCacheCanLagXml.md)
