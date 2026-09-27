"""Reimport final STLs; create useful bases; independently validate deliverables."""
import bpy,bmesh,sys,json,struct,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'ARES_Greek_Megafigure/scripts/vendor'))
import manifold3d as M
import numpy as np
sys.path.insert(0,str(ROOT/'scripts'))
from mesh_cleanup import clean_solid
bpy.ops.wm.read_factory_settings(use_empty=True)

def read(path):
    bpy.ops.wm.stl_import(filepath=str(path));ob=bpy.context.object
    ob.data.calc_loop_triangles()
    vs=np.array([tuple(v.co) for v in ob.data.vertices],np.float64)
    ts=np.array([tuple(t.vertices) for t in ob.data.loop_triangles],np.uint64)
    s=M.Manifold(M.Mesh64(vs,ts,tolerance=.00001))
    return ob,s,vs,ts

def write(path,s):
    mesh=clean_solid(s).to_mesh64();vs=mesh.vert_properties[:,:3];ts=mesh.tri_verts
    with path.open('wb') as f:
        f.write(b'Bills photo-inspired bison family; millimeters'.ljust(80,b' '));f.write(struct.pack('<I',len(ts)))
        for ids in ts:
            a,b,c=vs[ids];n=np.cross(b-a,c-a);n/=np.linalg.norm(n)
            f.write(struct.pack('<12fH',*n,*a,*b,*c,0))

def hull2(points):
    pts=sorted(set(tuple(map(float,p)) for p in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return np.array(lo[:-1]+hi[:-1])

animals={}
base_folder=ROOT/'STL'/'optional_with_bases';base_folder.mkdir(exist_ok=True)
for kind,num in [('Bull','01'),('Cow','02'),('Calf','03')]:
    ob,s,_,_=read(ROOT/'STL'/f'{num}_{kind}_with_charge_stripes.stl');bpy.data.objects.remove(ob,do_unlink=True)
    animals[kind]=s
    bounds=s.bounding_box();length=bounds[3]-bounds[0];width=bounds[4]-bounds[1]
    # Ellipse is sized for the complete animal footprint. Hooves overlap plate by .3mm.
    h=4.8 if kind!='Calf' else 3.5
    base=M.Manifold.cylinder(h,1,circular_segments=96).scale((length*.53,width*.59,1))
    combined=base+s.translate((0,0,h-.3))
    assert len(combined.decompose())==1,(kind,'base union disconnected')
    write(base_folder/f'{num}_{kind}_integral_display_base.stl',combined)

# A single, modest-size oval family display fits a 256 mm square bed.
base=M.Manifold.cylinder(6,1,circular_segments=128).scale((87.5,115,1))
layout={'Bull':(-8,55,5.7),'Cow':(7,-57,5.7),'Calf':(-45,0,5.7)}
group=base
for kind,s in animals.items():group=group+s.scale((.62,.62,.62)).translate(layout[kind])
assert len(group.decompose())==1,'family has disconnected solids'
write(base_folder/'04_Family_on_230mm_oval_display.stl',group)

report={'units':'millimeters','physical_print_tested':False,'files':{},'all_passed':False}
for path in sorted((ROOT/'STL').rglob('*.stl')):
    raw=path.read_bytes();raw_count=struct.unpack_from('<I',raw,80)[0]
    raw_tri=np.array([struct.unpack_from('<9f',raw,84+50*i+12) for i in range(raw_count)]).reshape((-1,3,3))
    raw_area=np.linalg.norm(np.cross(raw_tri[:,1]-raw_tri[:,0],raw_tri[:,2]-raw_tri[:,0]),axis=1)*.5
    ob,s,vs,ts=read(path)
    bm=bmesh.new();bm.from_mesh(ob.data)
    bad=sum(not e.is_manifold for e in bm.edges)
    noncontig=sum(e.is_manifold and not e.is_contiguous for e in bm.edges)
    volume=bm.calc_volume(signed=True);bm.free()
    triangles=vs[ts];a,b,c=triangles[:,0],triangles[:,1],triangles[:,2]
    area=np.linalg.norm(np.cross(b-a,c-a),axis=1)*.5
    tetra=np.einsum('ij,ij->i',a,np.cross(b,c))/6
    centroid=np.sum((a+b+c)*(tetra[:,None]/4),axis=0)/tetra.sum()
    low=vs[:,2].min();feet=vs[vs[:,2]<low+.0005,:2];support=hull2(feet)
    margins=[]
    for i,p in enumerate(support):
        q=support[(i+1)%len(support)];edge=q-p;delta=centroid[:2]-p
        margins.append(float((edge[0]*delta[1]-edge[1]*delta[0])/np.linalg.norm(edge)))
    dims=np.ptp(vs,axis=0);shells=s.decompose();positive=[v for v in shells if v.volume()>0]
    entry={'dimensions_mm':np.round(dims,3).tolist(),'triangles':len(ts),
           'raw_stl_triangles':raw_count,'raw_stl_degenerate_triangles':int(sum(raw_area<1e-9)),
           'non_manifold_edges':bad,'inconsistent_winding_edges':noncontig,
           'degenerate_triangles':int(sum(area<1e-9)),'signed_volume_mm3':round(volume,3),
           'manifold_status':str(s.status()),'connected_material_solids':len(positive),
           'enclosed_void_shells':len(shells)-len(positive),'bottom_z_mm':round(float(low),6),
           'uniform_density_center_of_mass_mm':np.round(centroid,3).tolist(),
           'static_support_margin_mm':round(min(margins),3),
           'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    entry['passed']=bool(bad==0 and noncontig==0 and entry['degenerate_triangles']==0 and entry['raw_stl_degenerate_triangles']==0 and raw_count==len(ts) and volume>0 and s.status()==M.Error.NoError and len(shells)==1 and abs(low)<.001)
    report['files'][path.relative_to(ROOT).as_posix()]=entry
    print(path.name,'PASS' if entry['passed'] else 'FAIL','support margin',entry['static_support_margin_mm'],flush=True)
    bpy.data.objects.remove(ob,do_unlink=True)
report['all_passed']=all(v['passed'] for v in report['files'].values())
(ROOT/'FINAL_VALIDATION.json').write_text(json.dumps(report,indent=2))
assert report['all_passed'],'Validation failures: see FINAL_VALIDATION.json'

# Render final grouped display using the saved studio.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source'/'Bills_Bison_Family.blend'))
scene=bpy.context.scene
for kind in animals:bpy.data.objects[kind].hide_render=True
ob,s,_,_=read(base_folder/'04_Family_on_230mm_oval_display.stl');ob.name='Family oval display STL'
ob.data.materials.append(bpy.data.materials['Satin stainless steel'])
ob.data.materials.append(bpy.data.materials['Neutral slate'])
for poly in ob.data.polygons:
    if poly.center.z<6.001:poly.material_index=1
camera=scene.camera;camera.location=(-390,-230,145)
camera.rotation_euler=(Vector((0,0,50))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=290
scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.cycles.samples=24
scene.render.filepath=str(ROOT/'previews'/'Family_oval_display.png');bpy.ops.render.render(write_still=True)
print('ALL 10 EXPORTED STL FILES VALIDATED',flush=True)
