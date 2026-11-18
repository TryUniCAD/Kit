# Read native part metadata after SOLIDWORKS saves an assembly child

The typed SOLIDWORKS 2026 configuration codec reads the directly owned empty
sheet-metal master and the saved mass-cache records of an ordinary solid part.
The manager codec also admits a schema-one tagged empty custom-property list.
The complete field codecs let the normal assembly reader follow an edited
and saved child's actual datum planes. A standalone parametric part can carry
an empty sheet-metal manager after save.

The direct master's inherited feature fields retain its dynamic class and the
master receives no archive map slot. Its empty body list has a serialized
count and a populated list fails closed. Each mass-cache slot is framed by its
actual rows. A populated slot embeds the existing typed mass-properties
record. Populated custom-property items remain outside the measured profile.

The [saved-file integration evidence](../../../../re/solidworks/measurements/2026/SdkSavedPartMetadata01.json)
records 28 exact Config-0 and manager comparisons across 14 disclosed files,
and three additional exact linked streams for the edited assembly pair. The
public reader resolves two ordered mates and all four actual datum links,
including the live 88.625 mm distance. The process regression covers each
observed populated cache-slot order and rejects a populated direct
sheet-metal body list without emitting it.
