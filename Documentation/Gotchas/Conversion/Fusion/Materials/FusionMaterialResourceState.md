# Fusion resource folders need a public JSON record registration

A Fusion document can contain a material package with typed resource folders. The lower document codec retained every folder and resource, but the strict public reader failed with `Unsupported Fusion semantic-state value`. The JSON registry already supported the package, resource entries and bytes. It omitted the recursive `PackageFolder` record.

The [public reader change](../../../../Changes/Fusion/Adapter/FusionMaterialFolderJson.md) registers that existing record. Persist and reopen the version-2 document JSON to retain ordered folders and resource bytes. The lower package checks and the public read-only status continue to apply.
