# Midplane rectangular boss

Neutral model records from the controlled cases described in [the evidence guide](README.md).

```json
{
  "ledger_event_id": 311,
  "units": "mm",
  "cases": [
    {
      "case": "midplaneDepth10",
      "source_sha256": "1475877a3b6da69f203789a69f726dbc55df28b824daf655b3dd12f6703f6dd2",
      "reference_archive_sha256": "895a73745d7357436472b7806ca6b5912797d39a2b0a6605d1d9036c51fd1bae",
      "model_sha256": "6a76d185ad79cec3b3c8c824b9b88dd5187dc1567390ea4b500be05cf1debf09",
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
              "name": "GrammarBoss body",
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
              "name": "MidProfile",
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
              "attributes": {},
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "mid_plane"
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
                "second_end_condition": null,
                "second_length": null,
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": true,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": "extrusion",
              "name": "GrammarBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:275"]
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
              "id": "sldprt:parameter:32:275",
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
              "name": "MidProfile",
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
      "case": "midplaneDepth14",
      "source_sha256": "5afe5822164f2beb24b58d6dc13f2abfd17f01ce013374961bc6e54456842278",
      "reference_archive_sha256": "fad51bb2ee8b30acc4bc1f7ed61686d3b2fcaabf9dfabb9586ca62d79a911fac",
      "model_sha256": "802602aeafc15cfe50b4b8f7e53f9a852ee4091dc2d0115c7cfd4245b27fde05",
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
              "name": "GrammarBoss body",
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
              "name": "MidProfile",
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
              "attributes": {},
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "mid_plane"
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
                "second_end_condition": null,
                "second_length": null,
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": true,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": "extrusion",
              "name": "GrammarBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:275"]
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
              "id": "sldprt:parameter:32:275",
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
              "name": "MidProfile",
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
      "case": "midplaneDepth18",
      "source_sha256": "959b3a7b666cbdd83c7cb52f88c84ce41d43ee710807ef06ce9784fc5973d98a",
      "reference_archive_sha256": "f7e8cf81e456ccc679dd42a18f637d46704f39e870256355a1a6f80d62d18369",
      "model_sha256": "57df5708d01df1949b9a6c1993105fd3bda7b5e4259c7131e40816608c3e861b",
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
              "name": "GrammarBoss body",
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
              "name": "MidProfile",
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
              "attributes": {},
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "mid_plane"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 18.000000000000004
                },
                "offset": null,
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": null,
                "second_length": null,
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": true,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": "extrusion",
              "name": "GrammarBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:275"]
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
              "id": "sldprt:parameter:32:275",
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
                "value": 18.000000000000004
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
              "name": "MidProfile",
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
