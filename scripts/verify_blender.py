"""Reopen editable source, check mesh health, then independently reimport GLB."""
import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/escudo_vigilia.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(objects)>10
report={'source_objects':len(objects),'source_materials':[m.name for m in bpy.data.materials],'nonmanifold_edges':0,'degenerate_faces':0,'missing_uvs':0,'nonunit_scales':0}
for ob in objects:
    bm=bmesh.new();bm.from_mesh(ob.data)
    report['nonmanifold_edges']+=sum(not e.is_manifold for e in bm.edges)
    report['degenerate_faces']+=sum(f.calc_area()<1e-12 for f in bm.faces)
    report['missing_uvs']+=int(not ob.data.uv_layers)
    report['nonunit_scales']+=int(any(abs(v-1)>1e-6 for v in ob.scale))
    bm.free()
assert all(report[k]==0 for k in ['nonmanifold_edges','degenerate_faces','missing_uvs','nonunit_scales']),report
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/models/escudo_vigilia.glb'))
report['reimported_materials']=sorted(m.name for m in bpy.data.materials)
report['reimported_objects']=sum(o.type=='MESH' for o in bpy.context.scene.objects)
assert report['reimported_materials']==['Acero','Bronce','Madera']
assert report['reimported_objects']==len(objects)
for m in bpy.data.materials:
    assert len([n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'])>=3
(ROOT/'docs/blender-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
