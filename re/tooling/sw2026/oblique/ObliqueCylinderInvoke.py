import ast

from ObliqueCylinderPlan import require


def layout(api, name):
    require(
        name in ("GetDirectionReference", "GetEndConditionReference"),
        "unsupported typed source getter",
    )
    (row,) = [
        value
        for value in api["interfaces"]["IExtrudeFeatureData2"]["members"]
        if value["names"][0] == name and value["invoke_kind"] == 1
    ]
    descriptions = ast.literal_eval(row["arguments"])
    result = ast.literal_eval(row["return_type"])
    types = []
    for kind, flags, default in descriptions:
        require(
            default is None and flags in (1, 2),
            "unexpected native getter argument flags",
        )
        if isinstance(kind, tuple):
            require(
                len(kind) == 2 and kind[0] == 26 and kind[1] in (3, 9) and flags == 2,
                "unsupported native out pointer type",
            )
            kind = 16384 | kind[1]
        else:
            require(kind == 11 and flags == 1, "unsupported native input type")
        types.append((kind, flags))
    actual = (row["member_id"], (result[0], result[1]), tuple(types))
    expected = (
        (50, (3, 0), ((16393, 2), (16387, 2), (16393, 2), (16387, 2)))
        if name == "GetDirectionReference"
        else (44, (9, 0), ((11, 1), (16387, 2)))
    )
    require(
        actual == expected and result[2] is None,
        "registered native getter layout differs from the disclosed pinned binding",
    )
    return {
        "name": name,
        "member_id": actual[0],
        "invoke_kind": row["invoke_kind"],
        "return_type": actual[1],
        "argument_types": actual[2],
        "required_input_count": sum(flags == 1 for kind, flags in types),
        "returned_value_count": 1 + sum(flags == 2 for kind, flags in types),
    }


def invoke(author, definition, name, *inputs):
    bound = layout(author.api, name)
    require(
        len(inputs) == bound["required_input_count"],
        "wrong actual native getter input count",
    )
    require(
        not inputs or type(inputs[0]) is bool, "forward input must be an actual boolean"
    )
    result = author.rec.call(
        name + " registered InvokeTypes",
        definition._oleobj_.InvokeTypes,
        bound["member_id"],
        0,
        bound["invoke_kind"],
        bound["return_type"],
        bound["argument_types"],
        *inputs,
        parameters={
            "interface": "IExtrudeFeatureData2",
            **bound,
            "inputs": list(inputs),
            "binding": "actual registered pointer and parameter flags",
        }
    )
    require(
        isinstance(result, tuple) and len(result) == bound["returned_value_count"],
        "typed getter did not return its declared result and ordered out parameters",
    )
    values = list(result)
    for index in ((1, 3) if name == "GetDirectionReference" else (0,)):
        value = values[index]
        if value is not None and not hasattr(value, "_oleobj_"):
            require(
                hasattr(value, "QueryInterface"),
                "out reference is not a native dispatch object",
            )
            values[index] = author.sw.wc.Dispatch(value)
    return tuple(values)


def main():
    import argparse
    from hashlib import sha256
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "typed-binding output must be unused")
    raw = args.metadata.read_bytes()
    metadata = json.loads(raw)
    require(
        metadata["schema"] == "kit.sw2026.oblique-api-metadata.v1"
        and metadata["passed"] is True,
        "registered metadata is not an admitted source receipt",
    )
    require(
        all(
            (row["major"], row["minor"]) == (34, 0)
            for row in metadata["libraries"].values()
        ),
        "registered libraries differ",
    )
    result = {
        "schema": "kit.sw2026.oblique-byref-plan.v1",
        "metadata_sha256": sha256(raw).hexdigest(),
        "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "bindings": [
            layout(metadata, name)
            for name in ("GetDirectionReference", "GetEndConditionReference")
        ],
        "native_calls_executed": 0,
        "native_acceptance": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "output_sha256": sha256(args.output.read_bytes()).hexdigest(),
                "native_calls_executed": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
