# Automatic native measurement controls

When a SOLIDWORKS input matches a recorded native save by SHA-256, the scalar inference run searches its capture for other saves with the same uniquely named dimensions and exactly one changed measurement. Both saves must have clean reopen observations. Each control is hash-checked and excluded from discovery fitting before the generated reader replays it. The member's paired_changes report records both measured values and whether the generated reader saw the same change. Explicit controls take precedence.

Run the usual single-input command. Parts without a matching recorded capture still require an independently supplied related save for this experiment. A match corroborates the changed parameter and its values. Feature ownership still depends on the separate candidate evidence.
