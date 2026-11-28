# Native appearance lookup can throw

`library.appearances.itemByName` can raise RuntimeError with error 3 and `invalid name` when a name is unavailable, rather than returning None. A loop that expects None can stop on the first library before reaching the intended one.

For independently authored controls, copying the actual appearance already assigned to the body avoids library-name and localization assumptions. Modify the owned copy and assign it to the face. The face-appearance capture script in `re/Fusion/Reconstruction/BoundaryCuts/CaptureFaceAppearance.py` uses this approach. The failed name lookup was retained in the private run evidence; only successful independently authored controls are included in the corpus.
