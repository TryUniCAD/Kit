import ast
import re
import warnings
from pathlib import Path
from plistlib import loads as LoadPlist

from CatalogRows import ReadSource


# syntax metadata supplies type relationships without importing or copying the vendor implementation
def Annotation(Value):
    return "" if Value is None else ast.unparse(Value)


# literals and symbolic enum defaults remain data rather than executable expressions
def DefaultValue(Value):
    try:
        return {"kind": "literal", "value": ast.literal_eval(Value)}
    except (ValueError, TypeError):
        if isinstance(Value, (ast.Attribute, ast.Name)):
            return {"kind": "symbol", "name": ast.unparse(Value)}
        return {"kind": "unresolved"}


# textual markers retain documentation mentions without asserting the availability of their owning declaration
def ApiFlags(Node):
    Description = (ast.get_docstring(Node) or "").lower()
    return {
        "documentation_mentions": {
            "preview": "preview" in Description,
            "retirement": "retired" in Description,
            "deprecation": "deprecated" in Description,
        },
        "availability_status": "unverified",
    }


# parameter domains preserve missing constraints instead of inventing units or numeric ranges
def Parameters(Node):
    Result = []
    Arguments = Node.args
    Positional = Arguments.posonlyargs + Arguments.args
    Defaults = [None] * (len(Positional) - len(Arguments.defaults)) + Arguments.defaults
    for Index, (Parameter, Default) in enumerate(zip(Positional, Defaults)):
        if Parameter.arg in ("self", "cls"):
            continue
        Result.append(
            {
                "name": Parameter.arg,
                "type": Annotation(Parameter.annotation),
                "position": Index,
                "kind": (
                    "positional_only"
                    if Index < len(Arguments.posonlyargs)
                    else "positional"
                ),
                "has_default": Default is not None,
                "default": DefaultValue(Default) if Default is not None else None,
                "units": None,
                "minimum": None,
                "maximum": None,
            }
        )
    for Parameter, Default in zip(Arguments.kwonlyargs, Arguments.kw_defaults):
        Result.append(
            {
                "name": Parameter.arg,
                "type": Annotation(Parameter.annotation),
                "kind": "keyword_only",
                "has_default": Default is not None,
                "default": DefaultValue(Default) if Default is not None else None,
            }
        )
    for Parameter, Kind in (
        (Arguments.vararg, "variadic"),
        (Arguments.kwarg, "keyword_variadic"),
    ):
        if Parameter is not None:
            Result.append(
                {
                    "name": Parameter.arg,
                    "type": Annotation(Parameter.annotation),
                    "kind": Kind,
                }
            )
    return Result


# the installation manifest binds extracted metadata to the actual installed fusion build
def InstalledVersion(ApiRoot):
    for Parent in ApiRoot.resolve().parents:
        if Parent.name == "Contents" and (Parent / "Info.plist").is_file():
            Info = LoadPlist(ReadSource(Parent / "Info.plist"))
            Version = Info.get("CFBundleShortVersionString")
            if not isinstance(Version, str) or not Version:
                raise ValueError("Installation manifest has no application version")
            return Version, Parent / "Info.plist"
    raise ValueError(
        "API root must belong to an installed Fusion application with Info.plist"
    )


# declared functions expose creation and editing inputs independently of their authoring coverage
def AddMembers(Rows, Namespace, OwnerId, Nodes, SourceId, References):
    Properties = {}
    Functions = {}
    for Node in Nodes:
        if not isinstance(
            Node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) or Node.name.startswith("__"):
            continue
        Decorators = [Annotation(Value) for Value in Node.decorator_list]
        IsProperty = "property" in Decorators or any(
            Value.endswith(".setter") for Value in Decorators
        )
        if IsProperty:
            Details = Properties.setdefault(
                Node.name, {"readable": False, "writable": False}
            )
            if "property" in Decorators:
                Details.update(
                    readable=True,
                    return_type=Annotation(Node.returns),
                    line=Node.lineno,
                    **ApiFlags(Node),
                )
            else:
                Details["writable"] = True
                Details["setter_line"] = Node.lineno
                Details["setter_parameters"] = Parameters(Node)
            continue
        Overloads = Functions.setdefault(Node.name, [])
        Overloads.append(
            {
                "return_type": Annotation(Node.returns),
                "parameters": Parameters(Node),
                "static": "staticmethod" in Decorators,
                "line": Node.lineno,
                **ApiFlags(Node),
            }
        )
    for Name, Details in sorted(Properties.items()):
        ItemId = Rows.AddItem(
            OwnerId + "." + Name, "api_property", Name, SourceId, OwnerId, Details
        )
        References.append(
            (
                ItemId,
                Namespace,
                Details.get("return_type", ""),
                "property_type",
                SourceId,
            )
        )
        for Position, Parameter in enumerate(Details.get("setter_parameters", [])):
            ParamId = ItemId + f":setter:{Position}"
            Rows.AddItem(
                ParamId, "api_parameter", Parameter["name"], SourceId, ItemId, Parameter
            )
            References.append(
                (ParamId, Namespace, Parameter["type"], "parameter_type", SourceId)
            )
    for Name, Overloads in sorted(Functions.items()):
        Details = {
            "overloads": Overloads,
            "legal_combinations": None,
            "constraints_status": "unresolved",
        }
        ItemId = Rows.AddItem(
            OwnerId + "." + Name, "api_method", Name, SourceId, OwnerId, Details
        )
        for Index, Function in enumerate(Overloads):
            References.append(
                (ItemId, Namespace, Function["return_type"], "returns", SourceId)
            )
            for Position, Parameter in enumerate(Function["parameters"]):
                ParamId = ItemId + f":parameter:{Index}:{Position}"
                Rows.AddItem(
                    ParamId,
                    "api_parameter",
                    Parameter["name"],
                    SourceId,
                    ItemId,
                    Parameter,
                )
                References.append(
                    (ParamId, Namespace, Parameter["type"], "parameter_type", SourceId)
                )


# all api types are retained because timeline feature inheritance omits other authorable objects
def CollectApi(Rows, ApiRoot):
    if any(
        not (ApiRoot / Name).is_file()
        for Name in ("__init__.py", "core.py", "fusion.py")
    ):
        raise ValueError(
            "API root must include package core and fusion definition files"
        )
    Version, Manifest = InstalledVersion(ApiRoot)
    Rows.AddSource(
        "api:manifest",
        "installation_manifest",
        "Contents/Info.plist",
        Manifest,
        Version,
    )
    References = []
    for SourcePath in sorted(ApiRoot.glob("*.py")):
        Namespace = (
            "adsk" if SourcePath.stem == "__init__" else "adsk." + SourcePath.stem
        )
        SourceId = "api:" + Namespace
        Content = Rows.AddSource(
            SourceId,
            "api_definitions",
            Namespace,
            SourcePath,
            Version,
            {"scope": "declared metadata only", "vendor_source_included": False},
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            Tree = ast.parse(Content, filename=Namespace)
        ModuleId = "api:" + Namespace
        Rows.AddItem(ModuleId, "api_module", Namespace, SourceId)
        for Node in Tree.body:
            if not isinstance(Node, ast.ClassDef):
                continue
            ClassId = "api:" + Namespace + "." + Node.name
            Bases = [Annotation(Base) for Base in Node.bases]
            Constants = []
            for Value in Node.body:
                if (
                    not isinstance(Value, ast.Assign)
                    or len(Value.targets) != 1
                    or not isinstance(Value.targets[0], ast.Name)
                ):
                    continue
                try:
                    Literal = ast.literal_eval(Value.value)
                except (ValueError, TypeError):
                    continue
                if isinstance(Literal, (str, int, float, bool)) or Literal is None:
                    Constants.append((Value, Literal))
            PublicMethods = [
                Value
                for Value in Node.body
                if isinstance(Value, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not Value.name.startswith("__")
                and Value.name != "cast"
            ]
            Role = (
                "enum_candidate"
                if Constants and not PublicMethods and not Bases
                else "class"
            )
            Rows.AddItem(
                ClassId,
                "api_type",
                Node.name,
                SourceId,
                ModuleId,
                {
                    "namespace": Namespace,
                    "role": Role,
                    "bases": Bases,
                    "line": Node.lineno,
                    **ApiFlags(Node),
                },
            )
            for Base in Bases:
                References.append((ClassId, Namespace, Base, "inherits", SourceId))
            for Constant, Literal in Constants:
                Name = Constant.targets[0].id
                Rows.AddItem(
                    ClassId + "." + Name,
                    "api_enum_value" if Role == "enum_candidate" else "api_constant",
                    Name,
                    SourceId,
                    ClassId,
                    {"value": Literal, "line": Constant.lineno},
                )
            AddMembers(Rows, Namespace, ClassId, Node.body, SourceId, References)
        AddMembers(Rows, Namespace, ModuleId, Tree.body, SourceId, References)
    for OwnerId, Namespace, TypeText, Relation, SourceId in References:
        for Token in set(re.findall(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", TypeText)):
            if Token.startswith("adsk."):
                Qualified = Token
            elif "." in Token:
                Qualified = "adsk." + Token
            else:
                Qualified = Namespace + "." + Token
            TargetId = "api:" + Qualified
            if TargetId in Rows.Items:
                Rows.AddRelation(OwnerId, TargetId, Relation, SourceId)
    Rows.AddGap(
        "api_constraints_unresolved",
        "api:manifest",
        Details={
            "reason": "Type declarations do not establish units ranges dependencies or valid feature combinations"
        },
    )
    Rows.AddGap(
        "api_wire_mapping_unresolved",
        "api:manifest",
        Details={
            "reason": "API names and native schema identifiers are separate identity spaces"
        },
    )
    return Version
