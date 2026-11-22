// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.Linq;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    object OpenSketchRead(IFeature Feature,ISketch Sketch)
    {
        int SupportType=0;
        var Support=Sketch.GetReferenceEntity(ref SupportType) as IFeature;
        var Inverse=Sketch.ModelToSketchTransform.IInverse();
        var Entities=new List<object>();
        foreach(var Segment in Array(Sketch.GetSketchSegments()).Cast<ISketchSegment>()) {
            var Line=Segment as ISketchLine;
            Check(Line!=null,"Open recipe profile must contain only lines");
            Entities.Add(Row("type",Segment.GetType(),"construction",Segment.ConstructionGeometry,
                "length_mm",Segment.GetLength()*1000,"start_world_mm",Scale(Transform(V(Line.IGetStartPoint2()),Inverse),1000),
                "end_world_mm",Scale(Transform(V(Line.IGetEndPoint2()),Inverse),1000)));
        }
        return Row("name",Feature.Name,"support_type",SupportType,"support_name",Support==null?null:Support.Name,
            "fully_defined",Sketch.GetConstrainedStatus()==3,"constraint_status",Sketch.GetConstrainedStatus(),
            "region_count",Sketch.GetSketchRegionCount(),"section_area_mm2",null,
            "entities",Entities,"relations",Array(Sketch.RelationManager.GetRelations(0)).Cast<ISketchRelation>().Select(Relation=>
                Row("type",Relation.GetRelationType(),"entity_types",Relation.GetEntitiesType())).ToArray(),
            "model_to_sketch_transform",Sketch.ModelToSketchTransform.ArrayData);
    }
}
