# Portable FreeCAD keeps the Part extension in lib

The FreeCAD 1.1.4 Windows x64 Python 3.11 package splits native extensions between `bin` and its sibling `lib`. `bin\python.exe` imports `bin\FreeCAD.pyd`, and `Part` resolves to `lib\Part.pyd`. A bin-only check refuses the actual Part extension. The Part binary also imports `Materials.pyd` and the application libraries.

Add the exact package directories to Python and DLL resolution. Verify both module origins before import and check the actual loaded paths and hashes afterward. The collector also binds the loaded `bin\FreeCADApp.dll`. The inspected package has SHA-256 `4828741fc91ee37fafcdb97a1abacb18b04ba451ac4372d9ff7a7349b36f4d6d`.

| Verified relative file | SHA-256 |
| --- | --- |
| `bin/python.exe` | `b4ca526908e5c93250b851427fa3265936472f1148eb7781c685afa2a13fb996` |
| `bin/FreeCAD.pyd` | `e6d9c7609613c4f8247b8157386ea27adffa102b3e1f8c5b9b0b0e912e0bfde0` |
| `bin/FreeCADApp.dll` | `efe57703f688cfefe7a6d806e3ea8592ffce516b06874c58597ab7c460780921` |
| `lib/Part.pyd` | `3f99965d8bac7f0302041ad3760ba5a1c027ac60676dd1db642834d8fd22fb53` |

The disclosed operator bootstrap used Python 3.11.14 and FreeCAD build `4fd3bf320d9566a27e60069fc8387448aaa3a094` directly from the verified portable package. `Part.makeBox(2, 3, 4)` produced one valid solid of 24 mm³. This establishes the runtime environment. Source authoring and locking remain pending. The corrected collector has SHA-256 `5e7ca2508af5c23bc22cec423e05bc91ebb15e1235afae380fd444943cc9d8da`. [Collector](../../../../re/FreeCad/Oracle/CollectBakedBoxes.py) · [Source lock procedure](../../../Changes/Freecad/FreeCadBakedSourceLockProtocol.md)
