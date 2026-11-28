from codecs import lookup
from dataclasses import asdict, replace
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
import sys


def main():
    root = Path(sys.argv[1])
    tooling = root / "re/tooling/sw2026"
    sys.path[:0] = [str(root / "src"), str(tooling), str(tooling / "serial")]
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from interchange.serialization.Deserialize import FromData
    from para.concentric.PrepareConcentricPersistence import derive_session
    from para.concentric.ProjectConcentricRadialIntent import (
        BindPartIntent, MakeCirclePart, MakePartRecipe, ProjectCircle, SelfFileInput,
        attach_scene, read_intents,
    )
    from para.cylinder.CylinderAttachment import attach_cylinder_mut

    request = loads(sys.stdin.read())
    document = FromData(request["child"])
    document.AssertValid()
    epoch = request["epoch"]
    plan = ProjectCircle(document)
    if plan.IsDiameter or plan.AxisValue != "z" or plan.EndValue.IsReversed or plan.EndValue.ModeValue != "blind":
        raise ValueError("expected a disclosed forward Front radius boss")
    base = MakePartRecipe(plan, epoch)
    folders = tuple((kind, request["environment_name"] if kind == "moEnvFolder_c" else name)
                    for kind, name in base.SystemValue.FolderValues)
    recipe = replace(base, SystemValue=replace(base.SystemValue, FolderValues=folders))
    input_value = BindPartIntent(document, plan, recipe, SelfFileInput(request["locator"], epoch))
    lights = read_intents(request["lights"], epoch)
    session, updates = derive_session(document, epoch)
    GetDocumentCaps(document)
    for encoding in ("utf-8", "utf-16-le", "utf-16-be", "cp1252"):
        lookup(encoding)
    active = True
    attempts = []

    def audit(event, _):
        if active and event in {"open", "subprocess.Popen", "socket.connect", "os.system", "ctypes.dlopen"}:
            attempts.append(event)
            raise RuntimeError("historical radial producer accessed external input")

    sys.addaudithook(audit)
    try:
        part = attach_cylinder_mut(MakeCirclePart(document, input_value), session, updates, 0,
                                   tessellated_faces=True, driver_mode="radius")
        complete = attach_scene(part.candidate, lights, input_value.TargetValue)
    finally:
        active = False
    if attempts:
        raise ValueError("historical neutral construction accessed runtime data")
    print(dumps({"xmt": asdict(part.projection.partition),
                 "streams": {name: sha256(value).hexdigest() for name, value in complete.StreamsValue.items()},
                 "sha256": sha256(complete.BytesValue).hexdigest(),
                 "runtime_external_accesses": len(attempts)}, sort_keys=True))


if __name__ == "__main__":
    main()
