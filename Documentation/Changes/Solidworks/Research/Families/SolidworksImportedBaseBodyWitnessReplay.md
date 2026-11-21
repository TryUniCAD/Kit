# Replay the disclosed imported base-body archive

The [witness probe](../../../../../re/tooling/sw2026/imported_body_source/ReplayImportedBaseBody.py)
accepts one hash-locked SOLIDWORKS 2026 SP05.2 part. The probe uses the native
base feature layout in its observed compressed part context, reads the two
subclass string and integer pairs, and reports linked-stream hashes.

Two independent host processes reproduce all bytes in each of Config-0,
ResolvedFeatures, CMgr, ModelHeader and Header2. The
[receipt](../../../../../re/solidworks/measurements/2026/ImportedBaseBodyWitnessReplay01.json)
records the original identity and matching stream hashes.
The [archive record](../../../../../re/solidworks/records/ImportedBaseBody2026.md)
traces the shared and subclass boundaries. Generative field ownership,
kernel attachment and acceptance of a fresh imported body remain open.
