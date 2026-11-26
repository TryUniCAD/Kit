<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Catalogue memory reserve

Use `--reserved-memory-mib` to set how much memory Kit leaves free before starting a worker.
The option is available for Fusion and SOLIDWORKS catalogue runs.
A value of zero removes the system reserve. Worker memory estimates still apply.

```sh
kit run --root . fusion --catalogue /path/to/Catalog.sqlite --directory /tmp/KitFusion --reserved-memory-mib 1024
```

The override applies to each supervisor launched for the batch, including any configured native stage.
An offline run without this option reserves 4096 MiB.
A native stage without this option reads the reserve from its supervisor configuration.

See the [research command guide](../../../../Tasks/ResearchCommandLine.md#run-a-cad-catalogue-with-optional-advice).
