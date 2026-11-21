# Windows file audit needs a portable access mask

Windows CPython 3.12 omits `os.O_ACCMODE`. The nested assembly process guard initially raised an attribute error on the first exclusive staged write, before it could compare output bytes. Both actual publication routes reproduced the error using the same disclosed neutral bundle.

Use the platform access-mode mask when it exists. Otherwise form the mask from `O_RDONLY`, `O_WRONLY` and `O_RDWR`. Retain the separate check for exclusive creation and the exact authorized output paths. [Preserved sealed-run verdict](../../../../re/solidworks/measurements/2026/SdkSealedPublicNestedParityWindowsFailure01.json)
