# Circular holdout capture overrides a prefixed selection

Expected: defining `ONLY` before executing an existing capture script limits the selected native controls.

Observed: `re/Fusion/Reconstruction/CircularSpans/CaptureHoldouts.py` assigns its own fixed `ONLY` set on its first line. It replaces a prefixed value and also captures symmetric and two-sided controls. The original circular script accepts the prefixed selection.

Inspect source assignments before dispatch. An explicit selection needs a separately fingerprinted replacement at the existing assignment, with the exact resulting script and planned cases retained. Do not mutate sealed historical capture sources or rerun an already submitted request to hide the difference. This campaign retained all five held-out captures and the original three captures. Its [qualification record](../../../../re/Fusion/Reconstruction/SignedDepth/README.md) distinguishes planned reverse controls from these additional native outputs.
