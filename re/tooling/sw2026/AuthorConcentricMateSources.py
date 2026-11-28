from __future__ import annotations

from contextlib import redirect_stderr,redirect_stdout
import argparse
import json
import os
from pathlib import Path
from shutil import copyfile
import time

from AuthorCurves import digest,require,write_json
from ConcentricApiMetadata import metadata
from ConcentricMateEvidence import author_mate,capture,component_map,edit_live,same_file,signature
from ConcentricSourcePlan import SCHEMA as SPEC_SCHEMA,SLOTS,child_case,disclosed_cases,expected_transforms,heldout_cases,validate
from ConcentricSourceRuntime import CONTROL,ORACLE,SourceRecorder,assert_pairs,checked,control,identity,phase_paths,previous,private_root,public_artifacts,save_pair

SCHEMA="kit.sw2026.concentric-mate-source-phases.v1"
SCRIPT=Path(__file__).resolve()
TOOLS=("AuthorConcentricMateSources.py","PrepareConcentricMateSources.py","ConcentricSourcePlan.py","ConcentricApiMetadata.py","ConcentricMateEvidence.py","ConcentricSourceRuntime.py","CollectConcentricEvidence.py","CollectDrawingViewSupportEvidence.py","AuthorCurves.py","AuthorAssemblySources.py","AssemblyMateEvidence.py","InspectFresh.py","InspectCircleSketch.py","ObserveAssemblyLoad.py","OracleIdentity.py","Swapp.py")
PHASES=("metadata","seal","before","author","reopen-source","reopen-edited","after","lock")


def verify(path,expected):
    root=path.parent.resolve(strict=True)
    job=json.loads(checked(path,expected,root).read_bytes())
    require(job["schema"]==SCHEMA and job["oracle_sha256"]==ORACLE and job["control_sha256"]==CONTROL and job["writer_output_count"]==0 and job["native_acceptance"] is False and job["heldout_designs_guest_private"] is True,"use the source-only concentric packet")
    require(SCRIPT.parent==root/"Tools" and set(job["tools_sha256"])==set(TOOLS),"use the exact frozen author closure")
    for name,wanted in job["tools_sha256"].items():checked(root/"Tools"/name,wanted,root/"Tools")
    checked(root/"Control.SLDPRT",CONTROL,root)
    binding=json.loads(checked(root/"NativeBinding.json",job["native_binding_sha256"],root).read_bytes())
    require(binding["schema"]=="kit.sw2026.concentric-native-source.v1" and binding["document_version"]==19000 and binding["native_build"]=="34.5.2.0604" and binding["native_processes_started"]==binding["heldout_inputs_read"]==binding["writer_output_count"]==0,"use the exact native concentric ownership receipt")
    observed=json.loads(checked(root/"Disclosed.json",job["disclosed_sha256"],root).read_bytes())
    require(observed=={"schema":SPEC_SCHEMA,"cases":disclosed_cases()},"disclosed author intent changed")
    return job


def case_input(root,job,expected,identifier):
    if identifier.startswith("D"):
        return next(value for value in disclosed_cases() if value["id"]==identifier)
    sealed=previous(root,"D00","seal",expected)
    base=private_root(job,expected,"D00")
    value=json.loads(checked(base/"SealedSpecs.json",sealed["sealed_spec_sha256"],base).read_bytes())
    require(value["schema"]==SPEC_SCHEMA and len(value["cases"])==2,"sealed concentric source cohort differs")
    return validate(next(row for row in value["cases"] if row["id"]==identifier))


def export_pair(author,controller,model,child,paths):
    result={}
    for role,target,path in zip(("parent","child"),(model,child),paths,strict=True):
        native=str(author.get(target,"GetPathName"))
        destination=path.with_suffix(".step")
        require(not destination.exists(),"geometry sibling must be new")
        status=list(author.rec.call("export independent source geometry sibling "+role,controller.save_as,target,destination))
        require(status==[True,0,0] and destination.is_file() and same_file(author.get(target,"GetPathName"),native),"native geometry sibling export failed warned or changed document identity")
        result[role]={"status":status,"sha256":digest(destination),"bytes":destination.stat().st_size}
    return result


def assert_exports(base,case,rows):
    require(set(rows)=={"source","edited"},"both independent geometry states must remain locked")
    for state,pair in rows.items():
        for role,path in zip(("parent","child"),phase_paths(base,case,state=="edited"),strict=True):
            item=pair[role]
            require(item["status"]==[True,0,0] and checked(path.with_suffix(".step"),item["sha256"],base).stat().st_size==item["bytes"],"an immutable independent geometry sibling changed")


def make_sources(author,controller,case,base):
    import Swapp
    base.mkdir(parents=True,exist_ok=True)
    working=base/"Working"
    working.mkdir(exist_ok=False)
    owned=working/(case["child_name"]+".SLDPRT")
    template=str(author.get(author.app,"GetUserPreferenceStringValue",8))
    require(Path(template).is_file(),"registered native part template unavailable")
    author.build(child_case(case),controller)
    child=author.model
    require(bool(author.get(child,"ForceRebuild3",False)),"the independently authored circle child did not rebuild")
    initial_child_status=list(author.rec.call("save fresh API-authored cylinder child",controller.save_as,child,owned))
    require(initial_child_status==[True,0,0] and same_file(author.get(child,"GetPathName"),owned),"native cylinder child save failed or warned")
    assembly_template=Path(author.rec.call("resolve registered assembly template",controller.template,"assembly"))
    require(assembly_template.is_file() and assembly_template.suffix.lower()==".asmdot","registered assembly template unavailable")
    model=author.get(controller.app,"NewDocument",str(assembly_template),0,0.0,0.0)
    require(model is not None,"new native assembly is unavailable")
    assembly=author.typed(model,"AssemblyDoc")
    matrices=expected_transforms(case)
    paths=Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY|Swapp.pythoncom.VT_BSTR,[str(owned)]*2)
    poses=Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY|Swapp.pythoncom.VT_R8,[value for row in matrices for value in row])
    origins=Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY|Swapp.pythoncom.VT_BSTR,[""]*2)
    inserted=author.get(assembly,"AddComponents3",paths,poses,origins)
    require(inserted is not None and len(inserted)==2,"native cylinder insertion count differs")
    components=component_map(author,assembly,case,owned)
    creation=author_mate(author,model,assembly,components,child,case)
    require(bool(author.get(model,"ForceRebuild3",False)),"the actual concentric source did not rebuild")
    initial=capture(author,model,assembly,owned,case)
    saved={"source":save_pair(author,controller,model,assembly,child,*phase_paths(base,case))}
    exports={"source":export_pair(author,controller,model,child,phase_paths(base,case))}
    source=capture(author,model,assembly,phase_paths(base,case)[1],case)
    require(signature(initial)==signature(source),"first native save changed actual concentric ownership")
    edit_live(author,model,assembly,child,phase_paths(base,case)[1],case)
    edited=capture(author,model,assembly,phase_paths(base,case)[1],case,True)
    require(signature(source)==signature(edited),"valid pose and depth edit changed mate or occurrence identity")
    saved["edited"]=save_pair(author,controller,model,assembly,child,*phase_paths(base,case,True))
    exports["edited"]=export_pair(author,controller,model,child,phase_paths(base,case,True))
    final=capture(author,model,assembly,phase_paths(base,case,True)[1],case,True)
    require(signature(edited)==signature(final),"edited native save changed actual concentric ownership")
    assert_pairs(base,case,saved)
    assert_exports(base,case,exports)
    result={"source":source,"edited":final,"saved_files":saved,"geometry_exports":exports,"mate_creation":creation,"part_template_sha256":digest(template),"assembly_template_sha256":digest(assembly_template),"initial_child_save_status":initial_child_status,"valid_axial_slide_proven":True,"valid_unlocked_spin_proven":not case["lock_rotation"],"invalid_pose_correction_proven":False,"locked_spin_rejection_proven":False,"writer_output_count":0}
    write_json(base/"SavedAuthor.json",result)
    return result


def reopen_sources(author,controller,case,base,edited,authored):
    checked(base/"SavedAuthor.json",authored["saved_author_sha256"],base)
    prior=json.loads((base/"SavedAuthor.json").read_bytes())
    assert_pairs(base,case,prior["saved_files"])
    assert_exports(base,case,prior["geometry_exports"])
    parent,child=phase_paths(base,case,edited)
    model,errors,warnings=author.rec.call("fresh open immutable concentric source",controller.open,parent,read_only=True)
    require(model is not None and errors==warnings==0 and same_file(author.get(model,"GetPathName"),parent),"native source fresh open failed or warned")
    assembly=author.typed(model,"AssemblyDoc")
    first=capture(author,model,assembly,child,case,edited)
    require(bool(author.get(model,"ForceRebuild3",False)),"native source fresh rebuild failed")
    second=capture(author,model,assembly,child,case,edited)
    wanted=prior["edited" if edited else "source"]
    require(signature(first)==signature(second)==signature(wanted),"concentric source lost complete tree endpoint order or exact identity on fresh reopen")
    assert_pairs(base,case,prior["saved_files"])
    assert_exports(base,case,prior["geometry_exports"])
    return {"initial":first,"rebuilt":second,"saved_files":prior["saved_files"],"inputs_unchanged":True}


def measure(job,case,phase,base,raw,authored,publish,expected_api):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    require(metadata()==expected_api,"registered concentric API changed since preflight")
    recorder=SourceRecorder(raw,{"case":case,"phase":phase},publish)
    result,controller={"passed":False},None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle concentric source oracle",Swapp.sweep)
            controller=recorder.call("start fresh concentric source oracle",Swapp.Sw)
            result["oracle_identity"]=identity(recorder.call("verify exact source oracle",application_identity,controller.app))
            publish(stage="native_source",identity=result["oracle_identity"])
            author=CurveAuthor(controller.app,recorder,Swapp)
            result.update(make_sources(author,controller,case,base) if phase=="author" else reopen_sources(author,controller,case,base,phase=="reopen-edited",authored))
            result["passed"]=True
        except Exception as error:
            recorder.failure(error)
            result["error"]=repr(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"]=controller.diagnostics
                except Exception as error:
                    recorder.failure(error,cleanup=True)
    result.update(dialogs=monitor.log,progress_windows=monitor.progress)
    result["passed"]=bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics") and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result,passed=result["passed"],finished_at=time.time())
    recorder.flush()
    require(result["passed"],"the private native concentric source phase failed")
    value={"identity":result["oracle_identity"]}
    if phase=="author":value.update(saved_author_sha256=digest(base/"SavedAuthor.json"),native_artifacts=public_artifacts(result["saved_files"]),geometry_artifacts=public_artifacts(result["geometry_exports"]))
    return value


def lock_case(root,job,expected,identifier):
    names=("before","author","reopen-source","reopen-edited","after")
    rows=[previous(root,identifier,name,expected) for name in names]
    identities=[row["identity"]["process_creation_filetime"] for row in rows]
    require(len(set(identities))==len(identities)==5,"source lock needs five distinct fresh native processes")
    case=case_input(root,job,expected,identifier)
    base=private_root(job,expected,identifier) if identifier.startswith("H") else root/"Disclosed"/identifier
    prior=json.loads(checked(base/"SavedAuthor.json",rows[1]["saved_author_sha256"],base).read_bytes())
    assert_pairs(base,case,prior["saved_files"])
    assert_exports(base,case,prior["geometry_exports"])
    return {"source_locked":True,"heldout_source_locked":identifier.startswith("H"),"native_artifacts":public_artifacts(prior["saved_files"]),"source_manifest_sha256":digest(base/"SavedAuthor.json"),"geometry_artifacts":public_artifacts(prior["geometry_exports"])}


def run(args,path,job):
    require(os.name=="nt","concentric source phases run only in the Windows guest")
    identifier,phase=args.case_id,args.phase
    require((identifier=="D00" and phase in ("metadata","seal")) or (identifier in SLOTS and phase not in ("metadata","seal")),"source phase outside declared slot")
    root=path.parent
    output=root/"Progress"/identifier/phase
    output.mkdir(parents=True,exist_ok=False)
    state={"schema":SCHEMA,"packet_sha256":args.packet_sha256,"case_id":identifier,"phase":phase,"stage":"verifying","passed":False,"started_at":time.time(),"writer_output_count":0}
    allowed={"stage","passed","finished_at","progress_at","identity","private_record_sha256","saved_author_sha256","native_artifacts","source_locked","heldout_source_locked","source_manifest_sha256","sealed_spec_sha256","api_metadata_sha256","geometry_artifacts"}
    def publish(**changes):
        require(set(changes)<=allowed,"private concentric detail cannot be published")
        state.update(changes)
        write_json(output/"Record.json",state)
    publish()
    raw=None
    try:
        private=private_root(job,args.packet_sha256,identifier)
        detail=private/phase
        detail.mkdir(exist_ok=False)
        raw=detail/"Private.json"
        with (detail/"Console.log").open("w",encoding="utf-8") as stream,redirect_stdout(stream),redirect_stderr(stream):
            if phase=="metadata":
                write_json(raw,metadata())
                copyfile(raw,root/"ApiMetadata.json")
                result={"api_metadata_sha256":digest(raw)}
            elif phase=="seal":
                previous(root,"D00","metadata",args.packet_sha256)
                file=private/"SealedSpecs.json"
                require(not file.exists(),"sealed source design is immutable")
                source=job.get("sealed_source")
                if source is None:write_json(file,{"schema":SPEC_SCHEMA,"cases":heldout_cases()})
                else:
                    prior=Path(source["windows_path"])
                    checked(prior,source["sha256"],Path(job["guest_private_base"]))
                    copyfile(prior,file)
                    checked(file,source["sha256"],private)
                result={"sealed_spec_sha256":digest(file)}
            elif phase in ("before","after"):
                previous(root,"D00","metadata",args.packet_sha256)
                result=control(root/"Control.SLDPRT",raw,publish)
            elif phase=="lock":result=lock_case(root,job,args.packet_sha256,identifier)
            else:
                meta=previous(root,"D00","metadata",args.packet_sha256)
                previous(root,identifier,"before",args.packet_sha256)
                api=json.loads(checked(root/"ApiMetadata.json",meta["api_metadata_sha256"],root).read_bytes())
                case=case_input(root,job,args.packet_sha256,identifier)
                base=private if identifier.startswith("H") else root/"Disclosed"/identifier
                authored=None if phase=="author" else previous(root,identifier,"author",args.packet_sha256)
                result=measure(job,case,phase,base,raw,authored,publish,api)
            if not raw.exists():write_json(raw,result)
            verify(path,args.packet_sha256)
        publish(**result,stage="passed",passed=True,finished_at=time.time(),private_record_sha256=digest(raw))
    except Exception as error:
        if raw is not None:write_json(raw.with_name("Failure.json"),{"error":repr(error)})
        publish(stage="failed",passed=False,finished_at=time.time())
    if raw is not None and identifier.startswith("D") and phase!="seal":
        target=root/"Disclosed"/identifier
        target.mkdir(parents=True,exist_ok=True)
        if raw.exists():copyfile(raw,target/(phase+".json"))
        if raw.with_name("Failure.json").exists():copyfile(raw.with_name("Failure.json"),target/(phase+"Failure.json"))
    return {key:state[key] for key in ("case_id","phase","stage","passed")}


def main():
    parser=argparse.ArgumentParser(description="Author one native concentric source phase with opaque guest-private holdouts")
    parser.add_argument("command",choices=("verify","run"))
    parser.add_argument("packet",type=Path)
    parser.add_argument("--packet-sha256",required=True)
    parser.add_argument("--case-id",choices=("D00",*SLOTS))
    parser.add_argument("--phase",choices=PHASES)
    args=parser.parse_args()
    path=args.packet.resolve(strict=True)
    try:
        job=verify(path,args.packet_sha256)
        if args.command=="verify":result={"passed":True,"native_processes_started":0,"heldout_inputs_read":0}
        else:
            require(args.case_id is not None and args.phase is not None,"one source case and phase are required")
            result=run(args,path,job)
    except Exception:
        result={"passed":False,"stage":"preflight_failed"}
    print(json.dumps(result,sort_keys=True))
    return 0 if result["passed"] else 3


if __name__=="__main__":
    raise SystemExit(main())
