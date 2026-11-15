# Read the actual automation return type

## Expected

Both standard-view rotation and active-view orientation return math-transform
objects exposing `ArrayData`.

## Observed

On the exact 2026 oracle, `GetStandardViewRotation` returns a numeric tuple, while
the active view's `Orientation3` exposes a math transform. Treating the standard
tuple as an object raised an attribute error and lost its returned values.
The partial capture still retained the distinct active-orientation arrays.

## Workaround

Accept an explicit numeric list/tuple directly and otherwise read `ArrayData`.
Keep unavailable queries and type errors visible in the report. Do not infer
canonical orientation from an API call's lack of an exception or from one image.
