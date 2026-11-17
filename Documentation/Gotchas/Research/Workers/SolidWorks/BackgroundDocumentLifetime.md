<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Closing the last background document affects session lifetime

`CloseDoc` closes a named dirty document without saving it.
For a background session with `UserControl` false, closing the only open document can also close the application session.
Document cleanup therefore needs an explicit session-lifetime policy across a multi-document batch. [CloseDoc API contract](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.isldworks~closedoc.html)

On an exact, verified empty owned process, set and read back `UserControlBackground` before opening controls.
This property permits user control while the application stays in the background.
Record both initial lifetime flags and the applied value with the run. [UserControlBackground API contract](https://help.solidworks.com/2023/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~UserControlBackground.html)

After closing every document, require an empty document set and call `ExitApp` explicitly.
Observe normal exit through the retained native process handle.
The API warns that activation can attach to an existing user session.
Verify the exact owned process identity before application shutdown. [ExitApp API contract](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.isldworks~exitapp.html)

The [recorded trace](../../../../Changes/Research/Workers/SolidWorks/OwnedReadbackLifetime.md#preserved-trace-observation) reached the final control close after five circular capture calls.
Its timeout and exact cleanup are preserved while normal lifecycle acceptance remains open.
