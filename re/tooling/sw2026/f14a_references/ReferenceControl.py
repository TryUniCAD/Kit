from pathlib import Path

from ReferenceApi import References, safe_error
from ReferencePacket import digest, require, verify_oracle
from ReferenceTopology import INTERFACES, NativeSelection


def measure_roles(author, enums, rows):
    selection = NativeSelection(author, enums)
    extension = author.typed(author.get(author.model, "Extension"), "ModelDocExtension")
    api = References(author, extension, enums)
    body = selection.one_body()
    name = "Boss-Extrude1"
    producer = selection.cast(selection.call(author.model, "FeatureByName", name), "Feature")
    require(selection.get(producer, "GetTypeName2") == "Extrusion", "the native control lost its actual producing feature")
    objects = {"producer": producer}
    for kind, member in (("face", "GetFaces"), ("edge", "GetEdges"), ("vertex", "GetVertices")):
        values = selection.get(body, member) or ()
        require(values, "the known native solid has no " + kind)
        objects[kind] = selection.cast(values[0], INTERFACES[kind])
    face = objects["face"]
    owning_feature = selection.cast(selection.get(face, "GetFeature"), "Feature")
    owning_body = selection.cast(selection.get(face, "GetBody"), "Body2")
    require(selection.same_object(owning_feature, producer) == selection.same_object(owning_body, body) == selection.same,
            "the native control face is on a different body or producer")
    rows["roles"] = {}
    for kind, expected in objects.items():
        row = rows["roles"][kind] = {"passed": False, "stage": "select_native_control"}
        try:
            selected = expected if kind == "producer" else selection.select(expected, kind, row)
            token = api.capture(selected, row)
            actual = api.native_object(token, row)
            row["stage"] = "compare_native_control_identity"
            row["resolved_object_equality"] = selection.compare(actual, expected, kind)
            row["persistent_id_equality"] = api.compare(token, token)
            row["passed"] = row["resolved_object_equality"] == row["persistent_id_equality"] == selection.same
        except Exception as error:
            row["error"] = safe_error(error)
        finally:
            selection.clear()
    rows["passed"] = all(row["passed"] for row in rows["roles"].values())


def control_phase(output, role, seed, enums):
    import Swapp
    from AuthorCurves import Recorder, write_json
    from AuthorRectangleAnchors import CONTROL, RectangleAuthor
    from InspectFresh import healthy
    from OracleIdentity import application_identity

    directory = output / role
    directory.mkdir()
    recorder = Recorder(directory / "ReferenceRecord.json", {"role": role, "input_sha256": CONTROL})
    references = {"passed": False}
    measurement = {}
    identity = controller = None

    def observe(stage, state):
        if stage != "features_return":
            return
        try:
            require(state["opened"] and state["rebuilt"] and state["bodies"] == 1 and
                    state["open_errors"] == state["open_warnings"] == state["whats_wrong"] == 0,
                    "native control must be clean before reference calibration")
            author = RectangleAuthor(controller.app, recorder, Swapp)
            author.model = Swapp.cv(controller.app, "ActiveDoc")
            require(author.model is not None and Path(author.get(author.model, "GetPathName")).samefile(seed),
                    "native control calibration opened a different active part")
            measure_roles(author, enums, references)
        except Exception as error:
            references.update(passed=False, error=safe_error(error))

    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(seed) == CONTROL, "known native control digest changed")
            Swapp.sweep()
            controller = Swapp.Sw()
            identity = application_identity(controller.app)
            verify_oracle(identity)
            require(controller.revision == "34.5.2", "control COM revision changed")
            measurement.update(Swapp.measure(controller, seed, progress=observe, read_only=True))
        except Exception as error:
            measurement["exception"] = safe_error(error)
        finally:
            if controller is not None:
                controller.close()
                measurement["controller_diagnostics"] = controller.diagnostics
    measurement.update(dialogs=dialogs.log, immutable_input=seed.is_file() and digest(seed) == CONTROL)
    geometry = healthy(measurement) and measurement["immutable_input"]
    report = {"passed": bool(geometry and references["passed"]), "geometry_passed": bool(geometry),
              "oracle_identity": identity, "measurement": measurement, "reference_transport": references}
    recorder.data.update(result=references, passed=references["passed"])
    recorder.flush()
    path = directory / "Record.json"
    write_json(path, report)
    return report | {"record_sha256": digest(path), "reference_record_sha256": digest(recorder.path)}
