# Comparing native scalar records to displayed dimensions

The generated part reader checks length, diameter and radius declarations in the saved linear unit. For each candidate feature it records the native dimension kind, displayed text, and whether the stored scalar matches exactly or falls within half of the least displayed unit. Angles retain the exact radians comparison. Candidates with matching labels and overlapping display intervals remain visible together. Marker agreement with a single rounded candidate has its own status.

Run the usual single-input decoder and inspect declaration_matches in the per-member ownership records of Input-scalar-streams.json. The unchanged raw IEEE value remains available for comparison with an independently measured native reopen. Display precision alone cannot identify a feature or verify geometry.
