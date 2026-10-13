"""Validate exported structure and report real asset sizes. Standard Python only."""
from pathlib import Path
import struct, json, io
ROOT=Path(__file__).resolve().parents[1]
file=ROOT/'assets/models/escudo_vigilia.glb'
data=file.read_bytes()
magic,version,size=struct.unpack_from('<4sII',data)
assert magic==b'glTF' and version==2 and size==len(data)
length,kind=struct.unpack_from('<II',data,12)
assert kind==0x4E4F534A
g=json.loads(data[20:20+length])
start=20+length
blen,bkind=struct.unpack_from('<II',data,start)
assert bkind==0x004E4942
binary=data[start+8:start+8+blen]
names=[m['name'] for m in g['materials']]
assert sorted(names)==['Acero','Bronce','Madera'],names
triangles=0
for mesh in g['meshes']:
    for p in mesh['primitives']:
        assert p.get('mode',4)==4
        assert all(a in p['attributes'] for a in ['POSITION','NORMAL','TEXCOORD_0','TANGENT'])
        triangles+=g['accessors'][p['indices']]['count']//3
for m in g['materials']:
    p=m['pbrMetallicRoughness']
    assert all(k in p for k in ['baseColorTexture','metallicRoughnessTexture'])
    assert 'normalTexture' in m
images=[]
for image in g['images']:
    v=g['bufferViews'][image['bufferView']];o=v.get('byteOffset',0)
    img=binary[o:o+v['byteLength']]
    assert img[:8]==b'\x89PNG\r\n\x1a\n'
    width,height=struct.unpack_from('>II',img,16)
    assert (width,height)==(512,512)
    images.append({'name':image.get('name'),'resolution':[width,height],'bytes':len(img)})
report={'blender':'5.2.0 LTS','model_viewer':'4.1.0','triangles':triangles,'mesh_count':len(g['meshes']),'materials':names,'glb_bytes':len(data),'glb_MB_decimal':round(len(data)/1e6,3),'blend_bytes':(ROOT/'source/escudo_vigilia.blend').stat().st_size,'texture_resolution':[512,512],'original_png_count':len(list((ROOT/'assets/textures').glob('*.png'))),'textures_total_bytes':sum(p.stat().st_size for p in (ROOT/'assets/textures').glob('*.png')),'embedded_images':images,'compression':'None'}
(ROOT/'docs/asset-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
