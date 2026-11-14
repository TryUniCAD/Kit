<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Blind circular boss

Neutral model records from the controlled cases described in [the evidence guide](README.md).

```json
{
  "ledger_event_id": 306,
  "units": "mm",
  "cases": [
    {
      "case": "FirstThree5",
      "source_sha256": "a9a1a0a4e7141270c41b4df63f59c9d4dbbca1c3d83c8452b8b5afa3d6521e9e",
      "reference_archive_sha256": "6595a934581848dbb3b0d914a8d929579fcc53087e49d8b4fdeb21b2f30445bd",
      "model_sha256": "e4214dc2980f67184b2688b7704de08c9c29e4ecc71830597ee4618596761d9b",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:1",
              "material_id": null,
              "name": "Body 1",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": {
                  "$type": "BoundingBox",
                  "maximum": {
                    "$type": "Vector3",
                    "x": 10.0,
                    "y": 10.0,
                    "z": 14.0
                  },
                  "minimum": {
                    "$type": "Vector3",
                    "x": -10.0,
                    "y": -10.0,
                    "z": 0.0
                  }
                },
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Front Plane",
              "operation": null,
              "order": 14,
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "ResearchProfile",
              "operation": null,
              "order": 24,
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
                  "value": 14.0
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "extrusion"
              },
              "name": "ResearchBoss",
              "operation": {
                "$enum": "BooleanOperation",
                "value": "join"
              },
              "order": 25,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:D1"]
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
              "id": "sldprt:parameter:32:D1",
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
                    "$tuple": ["sldprt:sketch:26:native:6861"]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7007",
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
                          "entity_id": "sldprt:sketch:26:native:6861",
                          "point": "center"
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
                      "$type": "CircleGeometry",
                      "center": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      },
                      "radius": 10.0
                    },
                    "id": "sldprt:sketch:26:native:6861",
                    "kind": "circle",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "ResearchProfile",
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
      "case": "FirstThree6",
      "source_sha256": "1b9d80c0e3af7e0d38f8eef41e2c70aa7a86587f48d6e5973c235470bac10843",
      "reference_archive_sha256": "1368d8d8d234ca92ed0bf2c8bb56a6654ac9f7975c0ba13230078345c1d01737",
      "model_sha256": "cc59cedcce95c62ca721b3c92624b3dbefe32939992ab94fab906bb6e86c8d74",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:1",
              "material_id": null,
              "name": "Body 1",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": {
                  "$type": "BoundingBox",
                  "maximum": {
                    "$type": "Vector3",
                    "x": 10.0,
                    "y": 10.0,
                    "z": 16.0
                  },
                  "minimum": {
                    "$type": "Vector3",
                    "x": -10.0,
                    "y": -10.0,
                    "z": 0.0
                  }
                },
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Front Plane",
              "operation": null,
              "order": 14,
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "ResearchProfile",
              "operation": null,
              "order": 24,
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
                  "value": 16.0
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "extrusion"
              },
              "name": "ResearchBoss",
              "operation": {
                "$enum": "BooleanOperation",
                "value": "join"
              },
              "order": 25,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:D1"]
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
              "id": "sldprt:parameter:32:D1",
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
                "value": 16.0
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
                    "$tuple": ["sldprt:sketch:26:native:6861"]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7007",
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
                          "entity_id": "sldprt:sketch:26:native:6861",
                          "point": "center"
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
                      "$type": "CircleGeometry",
                      "center": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      },
                      "radius": 10.0
                    },
                    "id": "sldprt:sketch:26:native:6861",
                    "kind": "circle",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "ResearchProfile",
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
      "case": "FirstThree7",
      "source_sha256": "848820c69141af76aae7c306506a1483598e7b549305da0ba351d77f7f1fc8aa",
      "reference_archive_sha256": "7ba408b0ae2b0a7756f0efc74ae6becf48d79e2fd68b1ff8936843d42d2b6cf5",
      "model_sha256": "0a56b5ba4b75978634a282aee6016b5d224ef2b860d22f7ca867253940bb62e1",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:1",
              "material_id": null,
              "name": "Body 1",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": {
                  "$type": "BoundingBox",
                  "maximum": {
                    "$type": "Vector3",
                    "x": 10.0,
                    "y": 10.0,
                    "z": 18.000000000000004
                  },
                  "minimum": {
                    "$type": "Vector3",
                    "x": -10.0,
                    "y": -10.0,
                    "z": 0.0
                  }
                },
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Front Plane",
              "operation": null,
              "order": 14,
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "ResearchProfile",
              "operation": null,
              "order": 24,
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
                  "value": 18.000000000000004
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
              "kind": {
                "$enum": "FeatureKind",
                "value": "extrusion"
              },
              "name": "ResearchBoss",
              "operation": {
                "$enum": "BooleanOperation",
                "value": "join"
              },
              "order": 25,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:D1"]
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
              "id": "sldprt:parameter:32:D1",
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
                    "$tuple": ["sldprt:sketch:26:native:6861"]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7007",
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
                          "entity_id": "sldprt:sketch:26:native:6861",
                          "point": "center"
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
                      "$type": "CircleGeometry",
                      "center": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      },
                      "radius": 10.0
                    },
                    "id": "sldprt:sketch:26:native:6861",
                    "kind": "circle",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "ResearchProfile",
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
