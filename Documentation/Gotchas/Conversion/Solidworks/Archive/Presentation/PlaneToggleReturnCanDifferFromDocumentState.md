# The plane toggle return can differ from the document state

The API documentation describes the Boolean return of `IModelDocExtension.SetUserPreferenceToggle` as the resulting state. In SOLIDWORKS 2026 SP04.1, the call `SetUserPreferenceToggle(5, 0, False)` returned `True` while both `GetUserPreferenceToggle(5, 0)` and `GetVisibilityOfConstructPlanes()` read `False`. The observation concerns the document-wide `swDisplayPlanes` setting in one vendor-authored part. [SOLIDWORKS API documentation](https://help.solidworks.com/2023/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.imodeldocextension~setuserpreferencetoggle.html?format=P&value=)

Record the setter return separately. Read both document getters after the call and measure the saved document in a fresh process when testing persistence. [Native observation](../../../../../../re/solidworks/measurements/2026/VendorBossCorpus/PlaneVisibilityContrast.json)
