from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from subprocess import run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
WORKERS = HERE.with_name("attached_radius_child")
SDK = "8fe0ab11797c22be51be065d14dd264f24f7d4bc"
WRITER = "787a836b6aecdbb726dc86078e79977aafdefc78"
STORE = "8a0043cb85affcf39660007383abcadd38a0b13e"
INTENT = "d25e6b4bdd6631c8c40aeae0335f96cebcbc740af0151dd7154ae08a873a6ca1"
RECIPE = "2b47da653b58bfa6156a46e0745e26534175600b611c8681a62a735744ff5cb7"
NATIVE = "3263e7d2019953bede2c36948b84274d915b9cd8f4de1afc0bcb1988e0397f03"
MEASURED = "699be1addf4b644f1ebdeecc6862f65610155d294e10fa6d7cbcf3d6a224f1cd"
EPOCH = 1795121000
ARCHIVE = "src/convert/adapters/solidworks/Archive/"
LIGHTS = tuple(ARCHIVE + suffix for suffix in (
    "Construction/Chronology/FeatureInstant.py",
    "Construction/Chronology/MakeFeatTime.py",
    "Construction/System/Members/CheckLightInput.py",
    "Construction/System/Members/LightFields.py",
    "Construction/System/Members/LightInput.py",
    "Construction/System/Members/MakeLightMut.py",
    "Definition/Construction/RequireDefNumber.py",
))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def read_pin(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, f"disclosed input does not match {path.name}")
    return loads(data)


def git(*arguments):
    return run(("git", *arguments), cwd=ROOT, capture_output=True, check=True).stdout


def checkout(destination, revision, *roots):
    destination.mkdir(parents=True, exist_ok=True)
    source = git("archive", "--format=tar", revision, *roots)
    with open_tar(fileobj=BytesIO(source)) as files:
        files.extractall(destination, filter="data")


def run_worker(worker, source, request, *args):
    result = run((sys.executable, "-I", "-B", str(WORKERS / worker), str(source), *args),
                 input=dumps(request), capture_output=True, text=True, timeout=120, check=False)
    require(result.returncode == 0 and not result.stderr, result.stderr)
    return loads(result.stdout)


def prepare(args):
    intent = read_pin(args.intent, INTENT)
    recipe = read_pin(args.packet / "Recipe.json", RECIPE)
    native = read_pin(args.packet / "Result.json", NATIVE)
    saved = native["phases"]["Generated"]["saved"]["child"]
    require(native["passed"] and native["controls_healthy"] and native["distinct_native_processes"] == 4
            and saved["original_sha256"] == MEASURED, "measured assembly child provenance changed")
    child = saved["path_basename"]
    original = PureWindowsPath(recipe["argv"]["Generated"][-3]).parent / "Working" / child
    requested = original if args.trial_locator is None else PureWindowsPath(args.trial_locator)
    require(requested.is_absolute() and requested.name == child, "use an explicit qualified Windows child locator")
    if args.trial_locator is not None:
        require(requested != original and args.candidate_dir is not None,
                "prospective measurement requires a new locator and new output directory")
    if args.candidate_dir is not None:
        require(not args.candidate_dir.exists(), "candidate output directory already exists")
    require(not args.output.exists(), "comparison receipt already exists")
    spec = {**intent, "locator": str(requested), "epoch": EPOCH}
    kernel = tuple(git("diff", "--name-only", SDK, STORE, "--", ARCHIVE + "Partition").decode().splitlines())
    with TemporaryDirectory(prefix="KitAttachedRadiusCompiler.") as folder:
        scratch = Path(folder)
        oracle_source = scratch / "Historical"
        sdk_source = scratch / "SDK"
        checkout(oracle_source, WRITER, "src")
        checkout(oracle_source / "re/tooling/sw2026", WRITER + ":re/tooling/sw2026")
        checkout(sdk_source, SDK, "src")
        checkout(sdk_source, STORE, *kernel)
        checkout(sdk_source, WRITER, *LIGHTS)
        former = run_worker("PlanKernel.py", oracle_source, spec)
        extras = ()
        if args.candidate_dir is not None:
            extras = (str(scratch / child),)
        result = run_worker("BuildAttachedPart.py", sdk_source, {"spec": spec, "producer": former}, *extras)
        exact_measured = result["sha256"] == MEASURED
        require(exact_measured == (requested == original),
                "compiler did not reproduce the measured file at its original locator")
        if extras:
            data = Path(extras[0]).read_bytes()
            require(digest(data) == result["sha256"], "staged scratch bytes changed")
            args.candidate_dir.mkdir()
            with (args.candidate_dir / child).open("xb") as output:
                output.write(data)
        result.update({
            "schema": "kit.sw2026.attached-radius-build.v1", "sdk": SDK, "kernel_store": STORE,
            "model_producer": WRITER, "input_intent_sha256": INTENT, "original_recipe_sha256": RECIPE,
            "original_native_result_sha256": NATIVE, "original_concentric_child_exact": exact_measured,
            "standalone_native_accepted": False, "assembly_publication_accepted": False, "heldout_credits": 0,
            "active_nodes": len(former["xmt"]["nodes"]), "initial_epoch": EPOCH,
            "producer_external_accesses": former["runtime_external_accesses"],
            "scope": "original linked child" if exact_measured else "prospective standalone discriminator",
            "compression_runtime": ZLIB_RUNTIME_VERSION,
            "exported_sdk_extensions": {path: digest((sdk_source / path).read_bytes())
                                        for path in (*kernel, *LIGHTS)},
            "research_tools": {path.name: digest(path.read_bytes())
                               for path in (HERE, *sorted(WORKERS.glob("*.py")))},
        })
    with args.output.open("x", encoding="utf-8") as output:
        output.write(dumps(result, indent=2, sort_keys=True) + "\n")
    print(digest(args.output.read_bytes()))


def main():
    parser = ArgumentParser()
    parser.add_argument("--intent", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--trial-locator")
    parser.add_argument("--candidate-dir", type=Path)
    prepare(parser.parse_args())


if __name__ == "__main__":
    main()
