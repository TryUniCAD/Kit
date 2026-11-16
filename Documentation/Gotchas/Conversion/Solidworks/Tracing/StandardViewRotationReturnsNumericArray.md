# Read the actual automation return type

## Expected

Both standard-view rotation and active-view orientation return math-transform
objects exposing `ArrayData`.

## Observed

On the exact 2026 oracle, `GetStandardViewRotation` returns a numeric tuple, while
the active view's `Orientation3` exposes a math transform. Treating the standard
tuple as an object raised an attribute error and lost its returned values.
The partial capture still retained the distinct active-orientation arrays.

The controlled visible-intervention run on observer `c14f17bb9f34865643c43a2ef887e1215f3ad07a` also records the cardinality difference: the standard getter returns nine rotation coefficients, while `Orientation3.ArrayData` has sixteen transform elements. The nine rotation values match the active transform's first nine values after selection. Comparing both whole arrays as sixteen-element transforms rejects the observer before it saves the orientation case; it is a harness failure, not evidence that the generated model failed the requested rotation. The original run and its other interventions remain recorded separately.

## Workaround

Accept an explicit numeric list/tuple directly and otherwise read `ArrayData`.
Keep unavailable queries and type errors visible in the report. Do not infer
canonical orientation from an API call's lack of an exception or from one image.
For a standard-view request, compare the nine rotation coefficients with the active transform's first nine values and record the remaining active elements independently. Keep the full sixteen-element comparison for save/reopen persistence, where both observations come from the same active-view API.
