<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Rectangular boss with cap edge fillets

Neutral model records from the controlled cases described in [the evidence guide](README.md).

```json
{
  "ledger_event_id": 309,
  "units": "mm",
  "cases": [
    {
      "case": "bossfilletRadius2",
      "source_sha256": "e41acf96b223c365b9accf084424e8845e68b583970d145b68bce6b4749e356f",
      "reference_archive_sha256": "cba7dff569f269f299699d9d1bd1cb49f8291bd0676804a934e72fdc3c63a172",
      "model_sha256": "c02fea566cdd1b71344f796888ffa88fd87ff47ab2dd4cea7783a0f7326871c9",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:34",
              "id": "sldprt:body:32",
              "material_id": null,
              "name": "ResearchBoss body",
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
              "name": "FilletProfile",
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
                  "value": "blind"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 20.0
                },
                "offset": null,
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": null,
                "second_length": null,
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
              "name": "ResearchBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:279"]
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
                "alpha_fillet": {
                  "caps": {
                    "$tuple": ["top", "base"]
                  },
                  "curve_entity_id": "sldprt:sketch:26:line:1",
                  "indices": {
                    "$tuple": [12, 11]
                  }
                },
                "selected_native_local_edge_ids": {
                  "$tuple": [12, 11]
                },
                "source_propagate_tangent_faces": true
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "FilletFeature",
                "radius": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 2.0
                },
                "variable_radius_parameter_ids": {
                  "$tuple": []
                }
              },
              "id": "sldprt:feature:34",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:32"]
              },
              "kind": "fillet",
              "name": "Fillet1",
              "operation": null,
              "order": 3,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:34:333"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
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
              "id": "sldprt:parameter:32:279",
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
                "value": 20.0
              }
            },
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:34:333",
              "name": "D1",
              "owner_id": "sldprt:feature:34",
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
                "value": 2.0
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
              "name": "FilletProfile",
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
      "case": "bossfilletRadius3",
      "source_sha256": "d25c494713e3c3c1bba10a8967673e56b706784a66d6f6f4ce74e9318e3b9c95",
      "reference_archive_sha256": "c3a219cac4999a2646ae0d1b43b2ed3dd91db8da1c842d0f87327a36eb0f62e0",
      "model_sha256": "c3d7993c8e6be771b24c795ccb27a6123593d3b71e7c986a3947c60e377b2f70",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:34",
              "id": "sldprt:body:32",
              "material_id": null,
              "name": "ResearchBoss body",
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
              "name": "FilletProfile",
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
                  "value": "blind"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 20.0
                },
                "offset": null,
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": null,
                "second_length": null,
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
              "name": "ResearchBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:279"]
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
                "alpha_fillet": {
                  "caps": {
                    "$tuple": ["top", "base"]
                  },
                  "curve_entity_id": "sldprt:sketch:26:line:1",
                  "indices": {
                    "$tuple": [12, 11]
                  }
                },
                "selected_native_local_edge_ids": {
                  "$tuple": [12, 11]
                },
                "source_propagate_tangent_faces": true
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "FilletFeature",
                "radius": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 3.0
                },
                "variable_radius_parameter_ids": {
                  "$tuple": []
                }
              },
              "id": "sldprt:feature:34",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:32"]
              },
              "kind": "fillet",
              "name": "Fillet1",
              "operation": null,
              "order": 3,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:34:333"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
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
              "id": "sldprt:parameter:32:279",
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
                "value": 20.0
              }
            },
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:34:333",
              "name": "D1",
              "owner_id": "sldprt:feature:34",
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
                "value": 3.0
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
              "name": "FilletProfile",
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
      "case": "bossfilletRadius5",
      "source_sha256": "dbba8a481bd80aa7b8a2c864cacb8da0eb3d5e52a741f3022d33e6e8ef8d80b3",
      "reference_archive_sha256": "8b00a1baa13ebd0400a2ee1d0101c7d9b0b294090846e2643c9d610e8795a2cb",
      "model_sha256": "84594b76551751612104af40ccd602bb520942fedb830d4afd64bf4026c28dc3",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:34",
              "id": "sldprt:body:32",
              "material_id": null,
              "name": "ResearchBoss body",
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
              "name": "FilletProfile",
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
                  "value": "blind"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 20.0
                },
                "offset": null,
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": null,
                "second_length": null,
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
              "name": "ResearchBoss",
              "operation": "join",
              "order": 2,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:279"]
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
                "alpha_fillet": {
                  "caps": {
                    "$tuple": ["top", "base"]
                  },
                  "curve_entity_id": "sldprt:sketch:26:line:1",
                  "indices": {
                    "$tuple": [12, 11]
                  }
                },
                "selected_native_local_edge_ids": {
                  "$tuple": [12, 11]
                },
                "source_propagate_tangent_faces": true
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "FilletFeature",
                "radius": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 5.0
                },
                "variable_radius_parameter_ids": {
                  "$tuple": []
                }
              },
              "id": "sldprt:feature:34",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:32"]
              },
              "kind": "fillet",
              "name": "Fillet1",
              "operation": null,
              "order": 3,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:34:333"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
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
              "id": "sldprt:parameter:32:279",
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
                "value": 20.0
              }
            },
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:34:333",
              "name": "D1",
              "owner_id": "sldprt:feature:34",
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
                "value": 5.0
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
              "name": "FilletProfile",
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
