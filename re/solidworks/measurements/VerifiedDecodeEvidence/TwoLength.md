<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Two length rectangular boss

Neutral model records from the controlled cases described in [the evidence guide](README.md).

```json
{
  "ledger_event_id": 310,
  "units": "mm",
  "cases": [
    {
      "case": "twolengthDualForward",
      "source_sha256": "c6a73c192738af1144e06534abfb20d06622ce92eccf9d45741094e0108b62b2",
      "reference_archive_sha256": "e368c878af6190f660abef0efba10c63b45a183347aa9949a1bd7e6836c36aa9",
      "model_sha256": "d268c764dbe40a98f9372a2319581196512b1fa8910dfbf26bf7a062dc2ff9d4",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:32",
              "material_id": null,
              "name": "DualBoss body",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": null,
                "edge_count": 0,
                "face_count": 0,
                "shell_count": 0,
                "solid_count": 1,
                "surface_area": null,
                "valid": null,
                "vertex_count": 0,
                "volume": null
              }
            }
          ]
        },
        "brep": null,
        "brep_payloads": {
          "$tuple": []
        },
        "capabilities": {
          "$frozenset": [
            {
              "$enum": "Capability",
              "value": "body_structure"
            },
            {
              "$enum": "Capability",
              "value": "configurations"
            },
            {
              "$enum": "Capability",
              "value": "editable_sketches"
            },
            {
              "$enum": "Capability",
              "value": "parameters"
            },
            {
              "$enum": "Capability",
              "value": "parametric_history"
            },
            {
              "$enum": "Capability",
              "value": "support_planes"
            }
          ]
        },
        "configurations": {
          "$tuple": [
            {
              "$type": "Configuration",
              "active": true,
              "attributes": {},
              "id": "sldprt:configuration:0",
              "name": "Default",
              "overrides": {
                "$tuple": []
              },
              "parent_id": null,
              "suppressed_feature_ids": {
                "$tuple": []
              }
            }
          ]
        },
        "diagnostics": {
          "$tuple": []
        },
        "feature_timeline": {
          "$tuple": [
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Plane",
                "support_plane_id": "sldprt:plane:2"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:2",
              "input_feature_ids": {
                "$tuple": []
              },
              "kind": "reference",
              "name": "Front Plane",
              "operation": null,
              "order": 0,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Sketch"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:26",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:2"]
              },
              "kind": "reference",
              "name": "DualProfile",
              "operation": null,
              "order": 1,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "length_parameter_ids": {
                  "$tuple": ["sldprt:parameter:32:27", "sldprt:parameter:32:28"]
                }
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "two_lengths"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 10.0
                },
                "offset": null,
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "blind"
                },
                "second_length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 4.0
                },
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": false,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": "extrusion",
              "name": "DualBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:27", "sldprt:parameter:32:28"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            }
          ]
        },
        "meshes": {
          "$tuple": []
        },
        "metadata": {},
        "parameters": {
          "$tuple": [
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:27",
              "name": "D1",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 10.0
              }
            },
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:28",
              "name": "D2",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 4.0
              }
            }
          ]
        },
        "schema_version": "1.0",
        "selections": {
          "$tuple": []
        },
        "sketches": {
          "$tuple": [
            {
              "$type": "Sketch",
              "attributes": {},
              "closed_profile_entity_ids": {
                "$tuple": [
                  {
                    "$tuple": [
                      "sldprt:sketch:26:line:2",
                      "sldprt:sketch:26:line:1",
                      "sldprt:sketch:26:line:4",
                      "sldprt:sketch:26:line:3"
                    ]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:0",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": "end"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:2",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:3",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:0",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:1",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:2",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:3",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:origin:0",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "",
                          "point": "origin"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  }
                ]
              },
              "entities": {
                "$tuple": [
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:2",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:1",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:4",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:3",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "DualProfile",
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "support_plane_id": "sldprt:plane:2",
              "suppressed": false
            }
          ]
        },
        "source": {
          "$type": "CadSource",
          "application_version": "",
          "attributes": {},
          "container_version": "",
          "format_id": "interchange.json",
          "path": "editable-extrusion",
          "sha256": ""
        },
        "support_planes": {
          "$tuple": [
            {
              "$type": "SupportPlane",
              "attributes": {},
              "id": "sldprt:plane:2",
              "name": "Front Plane",
              "offset_parameter_id": null,
              "provenance": null,
              "support_selection_id": null,
              "transform": {
                "$type": "Transform",
                "origin": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "x_axis": {
                  "$type": "Vector3",
                  "x": 1.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "y_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 1.0,
                  "z": 0.0
                },
                "z_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 1.0
                }
              }
            }
          ]
        },
        "units": {
          "$enum": "UnitSystem",
          "value": "mm"
        }
      }
    },
    {
      "case": "twolengthDualFirst",
      "source_sha256": "2fbaad453e8f58b8f0495de2c9602055455880677fdfa39e970645afa7817b78",
      "reference_archive_sha256": "032794938ce28b54b770c876b3f856edba24f9999c8d71bbaf58c19328d7114c",
      "model_sha256": "da14119f9a7aafba0bef3830d64c7dd035d8a285d4206ea4870aee2985ade0dc",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:32",
              "material_id": null,
              "name": "DualBoss body",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": null,
                "edge_count": 0,
                "face_count": 0,
                "shell_count": 0,
                "solid_count": 1,
                "surface_area": null,
                "valid": null,
                "vertex_count": 0,
                "volume": null
              }
            }
          ]
        },
        "brep": null,
        "brep_payloads": {
          "$tuple": []
        },
        "capabilities": {
          "$frozenset": [
            {
              "$enum": "Capability",
              "value": "body_structure"
            },
            {
              "$enum": "Capability",
              "value": "configurations"
            },
            {
              "$enum": "Capability",
              "value": "editable_sketches"
            },
            {
              "$enum": "Capability",
              "value": "parameters"
            },
            {
              "$enum": "Capability",
              "value": "parametric_history"
            },
            {
              "$enum": "Capability",
              "value": "support_planes"
            }
          ]
        },
        "configurations": {
          "$tuple": [
            {
              "$type": "Configuration",
              "active": true,
              "attributes": {},
              "id": "sldprt:configuration:0",
              "name": "Default",
              "overrides": {
                "$tuple": []
              },
              "parent_id": null,
              "suppressed_feature_ids": {
                "$tuple": []
              }
            }
          ]
        },
        "diagnostics": {
          "$tuple": []
        },
        "feature_timeline": {
          "$tuple": [
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Plane",
                "support_plane_id": "sldprt:plane:2"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:2",
              "input_feature_ids": {
                "$tuple": []
              },
              "kind": "reference",
              "name": "Front Plane",
              "operation": null,
              "order": 0,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Sketch"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:26",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:2"]
              },
              "kind": "reference",
              "name": "DualProfile",
              "operation": null,
              "order": 1,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "length_parameter_ids": {
                  "$tuple": ["sldprt:parameter:32:27", "sldprt:parameter:32:28"]
                }
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "two_lengths"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 14.0
                },
                "offset": null,
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "blind"
                },
                "second_length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 4.0
                },
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": false,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": "extrusion",
              "name": "DualBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:27", "sldprt:parameter:32:28"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            }
          ]
        },
        "meshes": {
          "$tuple": []
        },
        "metadata": {},
        "parameters": {
          "$tuple": [
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:27",
              "name": "D1",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 14.0
              }
            },
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:28",
              "name": "D2",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 4.0
              }
            }
          ]
        },
        "schema_version": "1.0",
        "selections": {
          "$tuple": []
        },
        "sketches": {
          "$tuple": [
            {
              "$type": "Sketch",
              "attributes": {},
              "closed_profile_entity_ids": {
                "$tuple": [
                  {
                    "$tuple": [
                      "sldprt:sketch:26:line:2",
                      "sldprt:sketch:26:line:1",
                      "sldprt:sketch:26:line:4",
                      "sldprt:sketch:26:line:3"
                    ]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:0",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": "end"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:2",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:3",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:0",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:1",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:2",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:3",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:origin:0",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "",
                          "point": "origin"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  }
                ]
              },
              "entities": {
                "$tuple": [
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:2",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:1",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:4",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:3",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "DualProfile",
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "support_plane_id": "sldprt:plane:2",
              "suppressed": false
            }
          ]
        },
        "source": {
          "$type": "CadSource",
          "application_version": "",
          "attributes": {},
          "container_version": "",
          "format_id": "interchange.json",
          "path": "editable-extrusion",
          "sha256": ""
        },
        "support_planes": {
          "$tuple": [
            {
              "$type": "SupportPlane",
              "attributes": {},
              "id": "sldprt:plane:2",
              "name": "Front Plane",
              "offset_parameter_id": null,
              "provenance": null,
              "support_selection_id": null,
              "transform": {
                "$type": "Transform",
                "origin": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "x_axis": {
                  "$type": "Vector3",
                  "x": 1.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "y_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 1.0,
                  "z": 0.0
                },
                "z_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 1.0
                }
              }
            }
          ]
        },
        "units": {
          "$enum": "UnitSystem",
          "value": "mm"
        }
      }
    },
    {
      "case": "twolengthDualSecond",
      "source_sha256": "2aca5a044066592f117b7d966ad954c4c9ad1394039d458c09032b82cf69f984",
      "reference_archive_sha256": "8e3045590c2da2e26ccfeee2d2ed64d88137bf9a6e878bcc40b5d7760df230e4",
      "model_sha256": "9b484e8a65d58200d910ba75c55d24e364e2f69d91f3ab83a15f58296489d38b",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:32",
              "material_id": null,
              "name": "DualBoss body",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": null,
                "edge_count": 0,
                "face_count": 0,
                "shell_count": 0,
                "solid_count": 1,
                "surface_area": null,
                "valid": null,
                "vertex_count": 0,
                "volume": null
              }
            }
          ]
        },
        "brep": null,
        "brep_payloads": {
          "$tuple": []
        },
        "capabilities": {
          "$frozenset": [
            {
              "$enum": "Capability",
              "value": "body_structure"
            },
            {
              "$enum": "Capability",
              "value": "configurations"
            },
            {
              "$enum": "Capability",
              "value": "editable_sketches"
            },
            {
              "$enum": "Capability",
              "value": "parameters"
            },
            {
              "$enum": "Capability",
              "value": "parametric_history"
            },
            {
              "$enum": "Capability",
              "value": "support_planes"
            }
          ]
        },
        "configurations": {
          "$tuple": [
            {
              "$type": "Configuration",
              "active": true,
              "attributes": {},
              "id": "sldprt:configuration:0",
              "name": "Default",
              "overrides": {
                "$tuple": []
              },
              "parent_id": null,
              "suppressed_feature_ids": {
                "$tuple": []
              }
            }
          ]
        },
        "diagnostics": {
          "$tuple": []
        },
        "feature_timeline": {
          "$tuple": [
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Plane",
                "support_plane_id": "sldprt:plane:2"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:2",
              "input_feature_ids": {
                "$tuple": []
              },
              "kind": "reference",
              "name": "Front Plane",
              "operation": null,
              "order": 0,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Sketch"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:26",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:2"]
              },
              "kind": "reference",
              "name": "DualProfile",
              "operation": null,
              "order": 1,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "length_parameter_ids": {
                  "$tuple": ["sldprt:parameter:32:27", "sldprt:parameter:32:28"]
                }
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "two_lengths"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 10.0
                },
                "offset": null,
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "blind"
                },
                "second_length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 7.0
                },
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": false,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": "extrusion",
              "name": "DualBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:27", "sldprt:parameter:32:28"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            }
          ]
        },
        "meshes": {
          "$tuple": []
        },
        "metadata": {},
        "parameters": {
          "$tuple": [
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:27",
              "name": "D1",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 10.0
              }
            },
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:28",
              "name": "D2",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 7.0
              }
            }
          ]
        },
        "schema_version": "1.0",
        "selections": {
          "$tuple": []
        },
        "sketches": {
          "$tuple": [
            {
              "$type": "Sketch",
              "attributes": {},
              "closed_profile_entity_ids": {
                "$tuple": [
                  {
                    "$tuple": [
                      "sldprt:sketch:26:line:2",
                      "sldprt:sketch:26:line:1",
                      "sldprt:sketch:26:line:4",
                      "sldprt:sketch:26:line:3"
                    ]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:0",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": "end"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:2",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:shared:3",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:0",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:1",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:1",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:2",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:4",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:unary:3",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:3",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:sketch:26:origin:0",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "",
                          "point": "origin"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:line:2",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  }
                ]
              },
              "entities": {
                "$tuple": [
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:2",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:1",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:4",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      }
                    },
                    "id": "sldprt:sketch:26:line:3",
                    "kind": {
                      "$enum": "GeometryKind",
                      "value": "line"
                    },
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "DualProfile",
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "support_plane_id": "sldprt:plane:2",
              "suppressed": false
            }
          ]
        },
        "source": {
          "$type": "CadSource",
          "application_version": "",
          "attributes": {},
          "container_version": "",
          "format_id": "interchange.json",
          "path": "editable-extrusion",
          "sha256": ""
        },
        "support_planes": {
          "$tuple": [
            {
              "$type": "SupportPlane",
              "attributes": {},
              "id": "sldprt:plane:2",
              "name": "Front Plane",
              "offset_parameter_id": null,
              "provenance": null,
              "support_selection_id": null,
              "transform": {
                "$type": "Transform",
                "origin": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "x_axis": {
                  "$type": "Vector3",
                  "x": 1.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "y_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 1.0,
                  "z": 0.0
                },
                "z_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 1.0
                }
              }
            }
          ]
        },
        "units": {
          "$enum": "UnitSystem",
          "value": "mm"
        }
      }
    }
  ]
}
```
