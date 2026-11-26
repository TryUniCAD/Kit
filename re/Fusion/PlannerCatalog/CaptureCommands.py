from hashlib import sha256
from json import dumps
from pathlib import Path
from datetime import datetime, timezone


# metadata collection inventories registered commands without creating or changing documents
def run(context):
    import adsk.core

    application = adsk.core.Application.get()
    interface = application.userInterface
    report = {
        "schema": "FusionCommandInventory/1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "fusion_version": application.version,
        "scope": "All registered command definitions in the current session without switching workspace or executing commands",
        "filtered": False,
        "commands_executed": 0,
        "documents_created": 0,
        "document_count_before": application.documents.count,
        "capture_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "commands": [],
        "workspaces": [],
        "errors": [],
        "status": "error",
    }
    try:
        definitions = interface.commandDefinitions
        report["command_definition_count"] = definitions.count
        if definitions.count > 20000:
            raise RuntimeError("Registered command count exceeds capture bound")
        for index in range(definitions.count):
            command = definitions.item(index)
            if command is None:
                report["errors"].append({"index": index, "error": "null command"})
                continue
            record = {"id": command.id, "name": command.name, "getter_errors": []}
            for name in (
                "isNative",
                "isApplicable",
                "isSubCommandDefinition",
                "objectType",
            ):
                try:
                    record[name] = getattr(command, name)
                except Exception as error:
                    record["getter_errors"].append(
                        {"field": name, "error": type(error).__name__}
                    )
            try:
                control = command.controlDefinition
                record["control_definition"] = (
                    None
                    if control is None
                    else {
                        "objectType": control.objectType,
                        "isEnabled": control.isEnabled,
                        "isVisible": control.isVisible,
                    }
                )
            except Exception as error:
                record["getter_errors"].append(
                    {"field": "controlDefinition", "error": type(error).__name__}
                )
            report["commands"].append(record)
        workspaces = interface.workspaces
        for index in range(workspaces.count):
            workspace = workspaces.item(index)
            report["workspaces"].append({"id": workspace.id, "name": workspace.name})
        report["status"] = "complete" if not report["errors"] else "partial"
    except Exception as error:
        report["errors"].append({"error": type(error).__name__})
    finally:
        report["examined_count"] = len(report["commands"])
        report["document_count_after"] = application.documents.count
        Path(__file__).with_name("Commands.json").write_text(dumps(report, indent=2))
        application.log(
            "Planner command inventory "
            + report["status"]
            + ": "
            + str(len(report["commands"]))
        )
