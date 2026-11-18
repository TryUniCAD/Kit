# A child edit does not prove drawing view recentering

The creation-time projection centers a fresh model view on its authored sheet position. Reusing that formula with a later edited model's new bounds assumes that the application also changes the model-to-view translation.

In the disclosed Alpha trial, the width changed from 0.035731000000000006 m to 0.044868000000000005 m and the edited child saved cleanly. On opening the drawing, the actual model-to-view transform was unchanged. Its outline grew by the full scaled width change on the positive X side. Recomputing translation from the edited center incorrectly moved the predicted left bound by half that amount.

The failing assertion ran before the drawing rebuild and the requested view move. It gives no result for those later operations. Keep the original trial and identify this as an observer prediction failure, without granting lifecycle credit.

For the next controlled measurement, separate the edited solid's center from the original drawing frame. Predict the outline by projecting the edited body corners through that frame. Check every transform and outline after rebuild, explicit move, save and fresh reopen. Record the complete actual state before assertions, and retain any failure of frame preservation. Do not infer a universal native update rule from this initial state.

The correction changes no writer byte or numeric tolerance. Both healthy controls and the full typed external-origin join remain required.
