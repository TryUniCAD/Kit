# Fresh assembly save settings come from application preferences

A fresh assembly's save-as-part record can look like a set of class
defaults. Its constructor first initializes the object, then replaces
ten of those fields with application preferences. It clamps the first
of the two doubles and keeps the second unchanged. The archive call
persists the resulting values in an embedded record without a class tag.

Supply the preference values as explicit inputs. Preserve the native
boolean, integer and double domains and the clamp. The
[definition record](../../../../../re/solidworks/records/AssemblyDefinition2026.md)
lists the preference keys and distinguishes persisted fields from the
in-memory copies.
