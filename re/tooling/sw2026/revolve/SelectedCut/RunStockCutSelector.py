from argparse import ArgumentParser
from hashlib import sha256
from math import isclose, tau
from pathlib import Path, PurePosixPath, PureWindowsPath
import json
import os
import sys


SCHEMA = "kit.sw2026.revolve-cut-cold-selector-diagnostic.v1"
POLICIES = ("producer", "sentinel")
LOCK_SHA = "67c1aeca25817846925f18e5b6b7b9319bdba216835e685988961e0db8832f68"
CONTROL_SHA = "28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0"
ORACLE_SHA = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
TOOLS = ("RunStockCutSelector.py", "AuthorRevolveFamilies.py", "RevolveFamilyModel.py", "AuthorRevolveSources.py",
         "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def publish(path, data):
    with path.open("xb") as destination:
        destination.write(data)
    return digest(data)


def checked(path, pin):
    require(path.is_file() and not path.is_symlink(), f"frozen file unavailable: {path.name}")
    raw = path.read_bytes()
    require(digest(raw) == pin, f"frozen file differs: {path.name}")
    return raw


def verify(manifest_path, pin):
    root = manifest_path.parent
    manifest = json.loads(checked(manifest_path, pin))
    case = manifest["case"]
    target = PureWindowsPath(manifest["guest_work"])
    files = manifest["files"]
    arms = manifest["arms"]
    require(manifest["schema"] == SCHEMA and manifest["oracle_sha256"] == ORACLE_SHA
            and manifest["source_lock_sha256"] == files["SourceLock.json"] == LOCK_SHA
            and files["Control/RevolveFull.SLDPRT"] == CONTROL_SHA,
            "unexpected oracle, control or pre-writer source lock")
    require(case["split"] == "discovery" and case["family"] == "cut" and case["scope"] == "inner"
            and case["plane"] == "front" and case["reverse"] is False
            and target.drive.casefold() == "c:" and target.is_absolute() and target.name == "Work"
            and PureWindowsPath(manifest["encoded_locator"]) == target / (case["name"] + ".SLDPRT"),
            "unexpected disclosure scope or locator")
    require(set(arms) == set(POLICIES)
            and set(files) == {"SourceLock.json", "Control/RevolveFull.SLDPRT",
                               *(f"Tools/{name}" for name in TOOLS),
                               *(f"Candidates/{label}.SLDPRT" for label in POLICIES)} and all(
        not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts for name in files
    ), "packet tool and candidate inventory differs")
    for name, sha in files.items():
        checked(root / name, sha)
    require(manifest["runtime_input_reads"] == manifest["heldout_inputs_read"] == 0
            and all(arms[label]["sha256"] == files[f"Candidates/{label}.SLDPRT"] for label in POLICIES),
            "generation provenance or candidate identity differs")
    if os.name == "nt":
        require(manifest_path.resolve() == (Path(manifest["guest_packet"]) / "Trial.json").resolve()
                and Path(__file__).resolve() == (root / "Tools" / TOOLS[0]).resolve(),
                "guest path differs from the frozen packet")
    return manifest


def observe_factory(Swapp, constants):
    from AuthorRevolveFamilies import STOCK_SKETCHES, author_type
    from AuthorRevolveSources import PLANES, RevolveAuthor
    from RevolveFamilyModel import FEATURE_NAMES, STOCK_NAMES

    base = author_type(RevolveAuthor, PLANES, Swapp, constants)

    class Observer(base):
        def snapshot(self, case, label, angle_degrees):
            cut = super().snapshot(case, label, angle_degrees)
            state = self.rec.data[label]
            expected = (STOCK_NAMES[0], STOCK_NAMES[1], FEATURE_NAMES["cut"])
            sequence = [row["name"] for row in state["features"] if row["name"] in expected]
            require(sequence == list(expected), "native stock-cut feature order changed")
            bodies = state["measured"]
            selected = ("inner", "outer").index(case["scope"])
            require(state["body_count"] == 2 and bodies[STOCK_NAMES[selected]]["faces"] == 9
                    and bodies[STOCK_NAMES[1 - selected]]["faces"] == 4,
                    "native selected cut changed the other solid or face counts")
            toggle = self.display_dimension_preference()
            initial = bool(self.get(self.model, "GetUserPreferenceToggle", toggle))
            stock_drivers = {}
            try:
                self.get(self.model, "SetUserPreferenceToggle", toggle, True)
                for name, profile in zip(STOCK_NAMES, STOCK_SKETCHES, strict=True):
                    feature = self.get(self.model, "FeatureByName", name)
                    parents = [str(self.get(item, "Name")) for item in self.get(feature, "GetParents") or ()]
                    require(profile in parents, "native stock lost its actual sketch")
                    param = self.get(self.model, "Parameter", f"D1@{name}")
                    require(param is not None and not bool(self.get(param, "ReadOnly"))
                            and int(self.get(param, "DrivenState")) == constants["swDimensionDriving"],
                            "native stock lost its editable D1")
                    full_name = str(self.get(param, "FullName"))
                    value = float(self.get(param, "SystemValue"))
                    require(full_name.split("@")[:2] == ["D1", name] and isclose(value, tau, abs_tol=1e-12, rel_tol=0),
                            "native stock D1 has a foreign identity or angle")
                    stock_drivers[name] = {"name": full_name, "radians": value, "parents": parents}
            finally:
                self.get(self.model, "SetUserPreferenceToggle", toggle, initial)
                require(bool(self.get(self.model, "GetUserPreferenceToggle", toggle)) == initial,
                        "native dimension display preference was not restored")
            angle = state["drivers"]["angle"]
            require(angle["name"].split("@")[:2] == ["D1", FEATURE_NAMES["cut"]] and angle["editable"],
                    "native cut did not retain the actual D1 driver")
            state["stock_drivers"] = stock_drivers
            self.rec.flush()
            return cut

    return Observer


def native(manifest_path, manifest, pin):
    require(os.name == "nt", "native diagnostic runs on the designated Windows guest")
    import Swapp
    from AuthorRevolveFamilies import constants_from_registration
    from AuthorRevolveSources import run_phase
    from InspectFresh import healthy, inspect
    from RevolveFamilyModel import edited_case

    require(not Swapp.application_pids() and not Swapp.owned_process_ids(), "oracle already active")
    packet = manifest_path.parent
    case, work = manifest["case"], Path(manifest["guest_work"])
    input_path = work / (case["name"] + ".SLDPRT")
    edited_path = work / (case["name"] + "-edited.SLDPRT")
    output = packet / "Inspection"
    require(not work.parent.exists() and not output.exists(),
            "guest work and inspection destinations must be fresh")
    observer = observe_factory(Swapp, constants_from_registration(Swapp))
    output.mkdir()
    work.mkdir(parents=True)
    identities, arms = [], {}
    result = {"schema": SCHEMA, "trial_sha256": pin, "oracle_sha256": ORACLE_SHA,
              "heldout_credit": 0, "public_writer": False, "arms": arms}

    def idle():
        return not Swapp.application_pids() and not Swapp.owned_process_ids()

    def remember(row):
        identity = row.get("oracle_identity")
        if identity:
            require(identity["version_matches"] and identity["sha256"] == ORACLE_SHA and
                    identity["file_version"] == "34.5.2.0604", "native process differs from frozen build")
            identities.append(identity["process_creation_filetime"])

    def control(label):
        require(idle(), "previous oracle process did not close")
        sample = inspect(packet / "Control" / "RevolveFull.SLDPRT")
        phase_sha = publish(output / (label + ".json"), encode(sample))
        remember(sample)
        return {"sha256": phase_sha, "passed": healthy(sample) and sample["sha256"] == CONTROL_SHA}

    def arm(label):
        require(idle() and not input_path.exists() and not edited_path.exists(),
                "same native locator was not released by the previous phase")
        phase_path = output / label
        phase_path.mkdir()
        pin_expected = manifest["arms"][label]["sha256"]
        raw = checked(packet / "Candidates" / (label + ".SLDPRT"), pin_expected)
        publish(input_path, raw)
        row = {"input_sha256": pin_expected, "phases": []}
        arms[label] = row
        first, phase_pin = run_phase(case, "reopen", input_path, ORACLE_SHA, pin_expected, inspect_before_rebuild=True,
                                    record_path=phase_path / "Initial.json", save_edited=edited_path, author_type=observer)
        remember(first)
        row["phases"].append({"phase": "open-edit-save", "sha256": phase_pin, "passed": first["passed"],
                              "open": first.get("open_status"), "failure": first.get("first_failure")})
        if first["passed"] and first.get("edit", {}).get("passed") and first.get("edited_derivative"):
            derivative = first["edited_derivative"]
            require(idle(), "editable process did not close before derivative reopen")
            last, phase_pin = run_phase(edited_case(case), "edited-reopen", edited_path, ORACLE_SHA, derivative["sha256"],
                                        inspect_before_rebuild=True, record_path=phase_path / "FreshReopen.json",
                                        author_type=observer)
            remember(last)
            row["phases"].append({"phase": "fresh-reopen", "sha256": phase_pin, "passed": last["passed"],
                                  "open": last.get("open_status"), "failure": last.get("first_failure")})
            raw_saved = checked(edited_path, derivative["sha256"])
            row["edited_sha256"] = publish(phase_path / "Saved.SLDPRT", raw_saved)
            if last["passed"]:
                states = (first["reopened"], first["edited"], last["reopened"])
                row["tree_rows"] = len(states[0]["features"])
                row["complete"] = (all(value["features"] == states[0]["features"] for value in states)
                                   and all(value["parents"] == states[0]["parents"] for value in states)
                                   and all(value["stock_drivers"] == states[0]["stock_drivers"] for value in states)
                                   and all(value["before_explicit_rebuild"]["bodies"] == 2
                                           and value["before_explicit_rebuild"]["whats_wrong"] == 0
                                           for value in (first, last)))
        row.setdefault("complete", False)
        checked(input_path, pin_expected)
        require(idle(), "oracle failed to release the owned input")
        preserved = work.parent / label
        preserved.mkdir()
        input_path.rename(preserved / input_path.name)
        if edited_path.exists():
            edited_path.rename(preserved / edited_path.name)

    try:
        result["before"] = control("ControlBefore")
        if result["before"]["passed"]:
            for label in POLICIES:
                arm(label)
    except Exception as error:
        result["batch_failure"] = repr(error)
    finally:
        try:
            result["after"] = control("ControlAfter")
        except Exception as error:
            result["after"] = {"passed": False, "failure": repr(error)}
        result["idle_after"] = idle()
        distinct = len(set(identities))
        result["distinct_processes"] = distinct
        result["control_brackets_healthy"] = bool(result.get("before", {}).get("passed") and result["after"]["passed"]
                                                    and len(identities) == distinct and identities == sorted(identities))
        result["diagnostic_completed"] = bool(result["control_brackets_healthy"] and set(arms) == set(POLICIES)
                                                and all(row["phases"] for row in arms.values())
                                                and result["idle_after"] and not result.get("batch_failure"))
        result["lifecycle_passed"] = result["diagnostic_completed"] and all(row["complete"] for row in arms.values())
        verify(manifest_path, pin)
        summary = publish(output / "Result.json", encode(result))
        print(json.dumps({"diagnostic_completed": result["diagnostic_completed"], "lifecycle_passed": result["lifecycle_passed"],
                          "controls_healthy": result["control_brackets_healthy"], "sha256": summary, "phases": distinct}))
    return int(not result["lifecycle_passed"])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("verify", "run"))
    parser.add_argument("trial", type=Path)
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    manifest = verify(args.trial, args.pin)
    if args.action == "verify":
        print(json.dumps({"verified": True, "manifest_sha256": args.pin, "native_processes": 0}))
        sys.exit(0)
    raise SystemExit(native(args.trial, manifest, args.pin))
