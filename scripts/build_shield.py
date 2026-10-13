"""Run: blender --background --python scripts/build_shield.py
Builds editable meshes, UVs, exportable image PBR materials and GLB.
Front = Blender -Y, up = +Z; glTF export is Y-up, front +Z. Units: metres.
"""
import bpy, bmesh, math, json, tempfile
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / 'assets/textures'
(ROOT/'work/temp').mkdir(parents=True,exist_ok=True)
tempfile.tempdir=str(ROOT/'work/temp')
bpy.context.preferences.filepaths.save_version=0
for p in ['source', 'assets/models', 'docs']:
    (ROOT/p).mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1

def collection(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
woodcol = collection('01 · Tablones de roble')
steelcol = collection('02 · Marco y refuerzos')
bronzecol = collection('03 · Emblema y remaches')
gripcol = collection('04 · Agarre trasero')

def material(name, prefix):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links; n.clear()
    p = n.new('ShaderNodeBsdfPrincipled'); output=n.new('ShaderNodeOutputMaterial'); output.location=(300,0)
    l.new(p.outputs['BSDF'],output.inputs['Surface'])
    p.inputs['Metallic'].default_value = 1
    p.inputs['Roughness'].default_value = 1
    for suffix, socket, color in [('BaseColor','Base Color',True),('Roughness','Roughness',False),('Metallic','Metallic',False),('Normal',None,False)]:
        im = bpy.data.images.load(str(TEX/(prefix+'_'+suffix+'.png')), check_existing=True)
        im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
        node = n.new('ShaderNodeTexImage'); node.image = im; node.label = suffix
        node.location = (-620, 300-180*len([q for q in n if q.type=='TEX_IMAGE']))
        if socket: l.new(node.outputs['Color'],p.inputs[socket])
        else:
            normal = n.new('ShaderNodeNormalMap'); normal.space='TANGENT'; normal.inputs['Strength'].default_value=1
            normal.location=(-260,-310); l.new(node.outputs['Color'],normal.inputs['Color']); l.new(normal.outputs['Normal'],p.inputs['Normal'])
    return m
wood=material('Madera','Madera_limpia'); steel=material('Acero','Acero'); bronze=material('Bronce','Bronce')
def bow(x,z): return -.085*(1-(x/.45)**2) - .012*(1-(z/.6)**2)

def mesh(name, verts, faces, mat, col, bevel=0):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    ob=bpy.data.objects.new(name,data); col.objects.link(ob); data.materials.append(mat)
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    bm=bmesh.new(); bm.from_mesh(data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(data); bm.free()
    if bevel:
        mod=ob.modifiers.new('Biseles de fabricación','BEVEL'); mod.width=bevel; mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.select_set(False)
    return ob

# Clockwise silhouette, broad shoulders and softened lower point.
outline=[(-.39,.55),(.39,.55),(.435,.50),(.42,.17),(.34,-.19),(.18,-.44),(0,-.575),(-.18,-.44),(-.34,-.19),(-.42,.17),(-.435,.50)]
def clip(poly,bound,keepgreater):
    result=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ia=(a[0]>=bound) if keepgreater else (a[0]<=bound)
        ib=(b[0]>=bound) if keepgreater else (b[0]<=bound)
        if ia: result.append(a)
        if ia!=ib:
            t=(bound-a[0])/(b[0]-a[0]); result.append((bound,a[1]+t*(b[1]-a[1])))
    return result
def solid(name,poly,front,depth,mat,col,bevel=.002):
    n=len(poly); v=[(x,bow(x,z)+front,z) for x,z in poly]+[(x,bow(x,z)+front+depth,z) for x,z in poly]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,mat,col,bevel)
for i in range(7):
    lo=-.44+i*.88/7+.002; hi=-.44+(i+1)*.88/7-.002
    poly=clip(clip(outline,lo,True),hi,False)
    solid('Roble · tablón %02d'%(i+1),poly,0,.038,wood,woodcol,.0025)

# One continuous rim, no hidden solid shield beneath it.
edge=[]
for a,b in zip(outline,outline[1:]+outline[:1]):
    steps=max(1,math.ceil(math.dist(a,b)/.055))
    edge.extend([(a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps) for j in range(steps)])
n=len(edge); vertices=[]
for s,depth in [(1.018,-.013),(.918,-.013),(1.018,.049),(.918,.049)]:
    vertices.extend((x*s,bow(x*s,z*s)+depth,z*s) for x,z in edge)
faces=[]
for i in range(n):
    j=(i+1)%n
    faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
mesh('Acero · marco perimetral',vertices,faces,steel,steelcol,.003)

def uv_sphere(name,loc,scale,mat,col,segments=12,rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    ob=bpy.context.object; ob.name=name
    for c in list(ob.users_collection): c.objects.unlink(ob)
    col.objects.link(ob); ob.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:p.use_smooth=True
    ob.select_set(False); return ob
for i,(x,z) in enumerate(edge):
    if i%3==0:
        x*=.970; z*=.970
        uv_sphere('Bronce · remache %02d'%i,(x,bow(x,z)-.016,z),(.009,.006,.009),bronze,bronzecol)

# Original compass emblem: four long points and four short, broad bevels.
star=[]
for i in range(16):
    a=math.pi/2+i*math.pi/8
    r=(.225 if i%4==0 else .155) if i%2==0 else .069
    star.append((math.cos(a)*r,math.sin(a)*r+.06))
solid('Bronce · rosa de la vigilia',star,-.028,.015,bronze,bronzecol,.004)
uv_sphere('Acero · umbo central',(0,bow(0,.06)-.042,.06),(.065,.034,.065),steel,steelcol,32,12)
uv_sphere('Bronce · sello central',(0,bow(0,.06)-.074,.06),(.018,.008,.018),bronze,bronzecol,16,8)

# Flat rear braces follow the shield's bow; rivets mark structural joints.
for z,width in [(.30,.355),(-.22,.265)]:
    # Segmented strip to conform to curvature across width.
    v=[]
    for i in range(13):
        x=-width+2*width*i/12
        for zz,d in [(z-.025,.039),(z+.025,.039),(z-.025,.050),(z+.025,.050)]:v.append((x,bow(x,zz)+d,zz))
    f=[]
    for i in range(12):
        a=4*i; b=a+4; f.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
    f.extend([(0,1,3,2),(48,50,51,49)])
    mesh('Acero · travesaño trasero '+str(z),v,f,steel,steelcol,.002)
    for x in [-width*.84,width*.84]: uv_sphere('Bronce · remache trasero',(x,bow(x,z)+.055,z),(.011,.006,.011),bronze,bronzecol)

def cylinder_between(name,a,b,r,mat,col,vertices=16):
    delta=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=delta.length,location=(Vector(a)+Vector(b))*.5)
    ob=bpy.context.object; ob.name=name; ob.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob); ob.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    mod=ob.modifiers.new('Cantos suavizados','BEVEL');mod.width=.003;mod.segments=2
    bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.select_set(False);return ob
for z in [-.22,.30]:
    cylinder_between('Acero · soporte del puño',(0,bow(0,z)+.05,z),(0,.115,z),.019,steel,gripcol)
cylinder_between('Madera · empuñadura',(0,.115,-.22),(0,.115,.30),.025,wood,gripcol,24)
for z in [-.21,.29]: cylinder_between('Bronce · collar del puño',(0,.115,z-.018),(0,.115,z+.018),.029,bronze,gripcol)

# UV per material: joint smart unwrap, average island scale and padded packing.
# One atlas per material, no accidental stacked islands. Wood front/back mapped
# in object coordinates to preserve continuous vertical grain; back mirrors front.
for mat in [wood,steel,bronze]:
    bpy.ops.object.select_all(action='DESELECT')
    objects=[o for o in scene.objects if o.type=='MESH' and o.data.materials[0]==mat]
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.018)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=False,margin=.016)
    bpy.ops.object.mode_set(mode='OBJECT')
    if mat==wood:
        for ob in objects:
            if not ob.name.startswith('Roble'):continue
            uv=ob.data.uv_layers.active.data
            for p in ob.data.polygons:
                if abs(p.normal.y)>.8:
                    for li in p.loop_indices:
                        co=ob.data.vertices[ob.data.loops[li].vertex_index].co
                        uv[li].uv=((co.x+.47)/.94*.92+.04,(co.z+.61)/1.22*.92+.04)
    # Record actual UV boundaries as seams for editing.
    for ob in objects:
        bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.loops.layers.uv.active
        for e in bm.edges:
            if len(e.link_loops)==2:
                a,b=e.link_loops
                e.seam=(a[layer].uv-b.link_loop_next[layer].uv).length>1e-5 or (a.link_loop_next[layer].uv-b[layer].uv).length>1e-5
        bm.to_mesh(ob.data);bm.free()

bpy.ops.object.select_all(action='DESELECT')
for ob in scene.objects:
    if ob.type=='MESH':
        ob.select_set(True)
        ob.data.name=ob.name
        mod=ob.modifiers.new('Triangulación para exportar','TRIANGULATE')
        mod.keep_custom_normals=True
# Tangents exported for normal-map consistency; no compression dependency.
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/escudo_vigilia.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models/escudo_vigilia.glb'),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_yup=True)
print('SHIELD_EXPORT_COMPLETE')
