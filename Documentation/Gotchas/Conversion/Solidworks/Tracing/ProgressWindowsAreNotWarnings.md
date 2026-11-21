# Native loading progress uses a dialog window class

Expected behavior: every visible `#32770` window with a Close button in the
oracle process is a modal warning that the watchdog should record and dismiss.

Observed behavior: the corrected-part inspection's trailing control loaded and
rebuilt one correct body with zero errors, but the watchdog repeatedly clicked
the untitled loading-progress window. Its three labels changed independently
through component loading, drawing updating and graphics generation. The class
and hidden Close control did not establish a warning. This contaminated the
control batch, which is not accepted as a healthy-control measurement.

Workaround: consider only visible, enabled buttons. Preserve the exact observed
untitled three-stage loading windows as separate, undismissed progress
observations. Keep all actual warning/error dialogs in the failure log. The
oracle remains version- and language-bound; an unfamiliar window is not silently
declared healthy. Repeat the complete clean inspection after changing the
watchdog. Neither this repair nor a screenshot establishes candidate acceptance.
