"""Photo-based faceted bison family. Run with Blender 5.2 --background --python.
Millimeter meshes; modeling axes: -X forward, +Z up. No downloaded 3D assets.
"""
import bpy, bmesh, math, random, sys, json, struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'ARES_Greek_Megafigure/scripts/vendor'))
import manifold3d as M
import numpy as np
sys.path.insert(0,str(ROOT/'scripts'))
from mesh_cleanup import clean_solid
for folder in ['STL','previews','source']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001
scene.unit_settings.length_unit='MILLIMETERS'

def solid(v,f):
    mesh=bpy.data.meshes.new('working');mesh.from_pydata(v,[],f);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    vs=np.array([tuple(a.co) for a in mesh.vertices],dtype=np.float64)
    ts=np.array([list(a.vertices) for a in mesh.polygons],dtype=np.uint64)
    out=M.Manifold(M.Mesh64(vs,ts,tolerance=1e-6));bpy.data.meshes.remove(mesh)
    assert out.status()==M.Error.NoError, out.status()
    return out

def loft(rings,axis='X',n=12,seed=3,jitter=0,exponent=1.0):
    # (axis-position, center-a, center-b, radius-a, radius-b)
    rng=random.Random(seed);v=[];f=[]
    for j,(d,a,b,ra,rb) in enumerate(rings):
        for k in range(n):
            t=2*math.pi*k/n
            if j not in [0,len(rings)-1]:t+=rng.uniform(-.10,.10)*jitter
            ct,st=math.cos(t),math.sin(t)
            aa=a+ra*math.copysign(abs(ct)**exponent,ct);bb=b+rb*math.copysign(abs(st)**exponent,st)
            dd=d+(rng.uniform(-2.4,2.4)*jitter if j not in [0,len(rings)-1] else 0)
            v.append((dd,aa,bb) if axis=='X' else (aa,bb,dd))
    for j in range(len(rings)-1):
        for k in range(n):
            a=j*n+k;b=j*n+(k+1)%n;c=(j+1)*n+(k+1)%n;d=(j+1)*n+k
            if (j+k)%2:f.extend([(a,b,d),(b,c,d)])
            else:f.extend([(a,b,c),(a,c,d)])
    f.extend([tuple(range(n-1,-1,-1)),tuple((len(rings)-1)*n+k for k in range(n))])
    return solid(v,f)

def hull(points):return M.Manifold.hull_points(np.array(points,dtype=np.float64))

def tube(points,radii,n=6):
    v=[];f=[]
    for i,p in enumerate(points):
        p=Vector(p)
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        tangent.normalize();u=tangent.cross(Vector((1,0,0)))
        if u.length<.1:u=tangent.cross(Vector((0,1,0)))
        u.normalize();w=tangent.cross(u).normalized()
        r=radii[i];rx,ry=(r,r) if isinstance(r,(int,float)) else r
        for k in range(n):
            q=p+u*(rx*math.cos(2*math.pi*k/n))+w*(ry*math.sin(2*math.pi*k/n))
            v.append(tuple(q))
    for j in range(len(points)-1):
        for k in range(n):f.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
    f.extend([tuple(range(n-1,-1,-1)),tuple((len(points)-1)*n+k for k in range(n))])
    return solid(v,f)

def union(items):return M.Manifold.batch_boolean(items,M.OpType.Add)

def patch_prism(points,normal,depth):
    normal=Vector(normal).normalized();v=[]
    for delta in [-depth/2,depth/2]:v.extend([tuple(Vector(p)+normal*delta) for p in points])
    n=len(points);faces=[tuple(range(n-1,-1,-1)),tuple(n+i for i in range(n))]
    faces.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    return solid(v,faces)

def frame_detail(center,normal,u,size,depth=2.2):
    # Chamfered, diamond-shaped inset eye surround.
    c=Vector(center);normal=Vector(normal).normalized();u=Vector(u).normalized();w=normal.cross(u).normalized()
    outline=[c+u*size,c+w*size*.85,c-u*size,c-w*size*.85]
    outer=patch_prism(outline,normal,depth)
    inner=patch_prism([c+(p-c)*.59 for p in outline],normal,depth+4)
    return outer-inner,inner,c-normal*1.4

def mesh_obj(name,s,mat=None):
    m=s.to_mesh64();data=bpy.data.meshes.new(name+'_mesh')
    data.from_pydata(m.vert_properties[:,:3].tolist(),[],m.tri_verts.tolist());data.update()
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob)
    if mat:ob.data.materials.append(mat)
    return ob

def material(name,color,metallic=.0,rough=.42):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metallic;bs.inputs['Roughness'].default_value=rough
    return m

SILVER=material('Satin stainless steel',(.37,.43,.51),.72,.32)
STRIPE=material('Polished charge outline',(.7,.76,.84),.65,.25)
BLACK=material('Recess shadows',(.027,.038,.060),.15,.5)


def stl(path,s):
    m=s.to_mesh64();v=m.vert_properties[:,:3];tri=m.tri_verts
    with path.open('wb') as f:
        f.write(b'Photo-inspired Bills bison; millimeters'.ljust(80,b' '));f.write(struct.pack('<I',len(tri)))
        for ids in tri:
            a,b,c=v[ids];n=np.cross(b-a,c-a);length=np.linalg.norm(n)
            if length:n/=length
            f.write(struct.pack('<12fH',*n,*a,*b,*c,0))

