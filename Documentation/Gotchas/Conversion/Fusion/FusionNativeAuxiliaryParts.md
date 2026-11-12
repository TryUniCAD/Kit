# Native archives contain more than solved history

Supporting a native document's `.smbh` member does not establish support for its complete `.f3d` archive. The controlled ordinary rectangle also contains a separate `.smb` snapshot, a `.protein` material package, two configuration members and nested OGS world and mesh data.

The source is `re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d`, SHA-256 `09980af5a2c9e03e0fc9246ed0b20e796c8f5574c8838d255c85bdd08ea1aa9c`. Its two configuration members have extensions `.dsgcfg` and `.dsgcfgrule`; graphics members are under `OGS.BlobFolder/OGS/DefaultScene/`. These paths exceed the current minimal document container profile. The strict container reader rejects unaccounted members, and the document reader separately rejects snapshot/material parts that lack a complete typed document model.

Use the minimal qualified envelope for independent authoring. For complete native-source conversion, add and validate every needed auxiliary codec before broadening the accepted member inventory. Do not copy opaque parts, silently discard them, or infer that cache omission is safe for all documents from one accepted omission experiment.
