from __future__ import annotations

from math import isclose


def compare(result, native, kernel, child_hash):
    checks = []
    numeric = []

    def require(value, label):
        checks.append({'label':label,'passed':bool(value)})
        if not value:
            raise ValueError('public concentric comparison failed: '+label)

    def close(actual, expected, label):
        numeric.append({'label':label,'actual':actual,'expected':expected})
        require(isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-12),label)

    report = result['typed_report']
    require(report is not None and report['status']=='admitted','actual typed admission')
    require(report['scope']=='ordinary_concentric_single_mate_two_direct_part_occurrences','narrow complete scope')
    require(report['full_selected_mate_graph'] is True and report['public_writer_qualified'] is False,'read only selected graph qualification')
    require(report['archive_version']==19000 and report['typed_occurrence_and_child_surface_identity'] is True,'exact current child surface ownership')
    require(not report['grammar_coverage']['provisional_schemas'] and not report['grammar_coverage']['native_byte_fields'],'complete typed mate grammar')
    require(len(result['mates'])==1 and len(result['entities'])==2,'whole mate endpoint inventory')
    rule = result['mates'][0]
    actual = native['mate']
    require(rule['name']==actual['name'] and rule['kind']=='concentric','real native class and name')
    require(rule['alignment']==('aligned' if actual['alignment']==0 else 'anti_aligned'),'authored alignment')
    require(rule['attributes']['rotation_locked'] is actual['rotation_locked'],'authored rotation lock')
    require(rule['attributes']['native_rotation_lock_code']==int(actual['rotation_locked']),'rotation lock wire code')
    require(rule['attributes']['native_internal_alignment_code']==actual['alignment']+1,'native alignment code domain')
    require(rule['attributes']['native_solved_state_code']==1,'ordinary solved state')
    require(rule['attributes']['typed_archive_owner']['native_feature_id']==actual['native_feature_id'],'actual native mate feature id')
    require(rule['value'] is None and rule['suppressed'] is False and rule['driving'] is True,'ordinary active mate inputs')
    require(rule['entity_ids']==[value['id'] for value in result['entities']],'ordered neutral endpoints')
    require(len({rule['id'],*(value['id'] for value in result['entities'])})==3,'unique public rule and entity ids')
    require(len(result['children'])==1 and result['children'][0]['sha256']==child_hash,'actual immutable child document')
    child = result['children'][0]
    instances = {value['id']:value for value in result['instances']}
    observations = {value['native_id']:value for value in native['occurrences']}
    require(len(instances)==len(observations)==2,'two actual direct occurrences')
    for ordinal,(entity,endpoint) in enumerate(zip(result['entities'],actual['ordered_endpoints'],strict=True)):
        label = 'endpoint '+str(ordinal)+' '
        attributes = entity['attributes']
        require(entity['kind']=='cylinder' and entity['frame_present'] is False,label+'analytic kind without invented frame')
        require(len(entity['instance_path'])==1 and entity['instance_path'][0] in instances,label+'real direct instance path')
        instance = instances[entity['instance_path'][0]]
        require(instance['native_feature_id']==attributes['native_occurrence_feature_id']==endpoint['occurrence_native_id'],label+'actual occurrence identity')
        require(instance['name']==endpoint['occurrence'],label+'actual occurrence name')
        require(instance['configuration_name']==observations[endpoint['occurrence_native_id']]['configuration'],label+'actual selected configuration')
        require(instance['fixed'] is observations[endpoint['occurrence_native_id']]['fixed'],label+'actual fixed state')
        require(attributes['native_child_sha256']==child_hash,label+'synchronized child bytes')
        require(attributes['native_face_node_id']==kernel['face_node_id'],label+'persistent kernel face id')
        require(attributes['native_body_atom_id']==kernel['body_atom_id'],label+'actual body atom identity')
        require(attributes['native_face_transmit_index']==kernel['face_transmit_index']+1,label+'wire index distinct from normalized index')
        require(entity['source_entity_id']=='sldprt:brep:face:'+str(kernel['face_transmit_index']+1),label+'public geometry face identity')
        close(entity['radius'],endpoint['radius_m']*1000,label+'public radius millimetres')
        close(attributes['native_radius_m'],endpoint['radius_m'],label+'native radius metres')
        for axis in range(3):
            close(attributes['stored_origin_m'][axis],endpoint['point'][axis],label+'world point '+str(axis))
            close(attributes['stored_axis'][axis],endpoint['axis'][axis],label+'world axis '+str(axis))
        if result['mode']=='default':
            matches=[value for value in child['geometry_faces'] if value['id']==entity['source_entity_id']]
            require(child['brep_present'] is True and len(matches)==1 and matches[0]['surface_class']=='CylinderSurface',label+'actual public child cylinder face')
            close(matches[0]['radius'],entity['radius'],label+'public child radius agreement')
        else:
            require(child['brep_present'] is False and child['geometry_faces']==[],label+'metadata option excludes child brep')
    require(not result['oracle_modules_imported'] and result['native_processes_started']==0 and result['writer_outputs']==0,'self contained normal reader')
    return {'passed':True,'checks':checks,'numeric_checks':numeric,'endpoint_observations':2,'mode':result['mode']}
