import math

from AuthorCurves import require


def selected_body_mass(observer, body):
    observer.get(observer.model, "ClearSelection2", True)
    try:
        require(bool(observer.get(body, "Select2", False, observer.sw.nothing())),
                "native exact solid selection for mass properties failed")
        selection = observer.get(observer.model, "SelectionManager")
        require(int(observer.get(selection, "GetSelectedObjectCount2", -1)) == 1,
                "native mass measurement requires one selected object")
        selected = observer.typed(observer.get(selection, "GetSelectedObject6", 1, -1), "Body2")
        require(int(observer.get(selected, "GetType")) == observer.constants["swSolidBody"] and observer.same(selected, body),
                "native mass selection is not the same actual solid")
        extension = observer.get(observer.model, "Extension")
        mass = observer.typed(observer.get(extension, "CreateMassProperty2"), "MassProperty2")
        accuracy = observer.constants["swMassPropertyAccuracyLevel_Higher"]
        observer.set(mass, "AccuracyLevel", accuracy)
        observer.set(mass, "UseSystemUnits", True)
        options = observer.typed(observer.get(mass, "GetOverrideOptions"), "MassPropertyOverrideOptions")
        require(not observer.get(options, "OverrideMass") and not observer.get(options, "OverrideCenterOfMass"),
                "native mass properties have a manual override")
        targets = observer.get(mass, "SelectedItems") or ()
        require(len(targets) == 1 and observer.same(targets[0], body),
                "mass properties do not refer to the actual sole solid")
        require(bool(observer.get(mass, "Recalculate")), "native higher-accuracy mass recalculation failed")
        require(int(observer.get(mass, "AccuracyLevel")) == accuracy and bool(observer.get(mass, "UseSystemUnits")),
                "native mass measurement did not retain higher-accuracy SI settings")
        values = {"volume": float(observer.get(mass, "Volume")), "area": float(observer.get(mass, "SurfaceArea")),
                  "com": [float(value) for value in observer.get(mass, "CenterOfMass")],
                  "mass": float(observer.get(mass, "Mass")), "accuracy_level": accuracy, "selected_solid": True,
                  "use_system_units": True, "manual_overrides": False}
        observer.rec.data["last_high_accuracy_mass"] = values
        observer.rec.flush()
        require(all(math.isfinite(values[key]) and values[key] > 0 for key in ("volume", "area", "mass"))
                and len(values["com"]) == 3, "native selected body measurements are incomplete")
        return values
    finally:
        observer.get(observer.model, "ClearSelection2", True)
