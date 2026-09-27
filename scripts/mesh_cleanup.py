"""Collapse boolean seams below 0.0001 mm at the precision used by STL."""
import bpy, bmesh
import numpy as np
import manifold3d as M

def clean_solid(s):
    original_volume=s.volume()
    mesh=s.simplify(.0001).to_mesh64()
    data=bpy.data.meshes.new('temporary STL precision cleanup')
    data.from_pydata(mesh.vert_properties[:,:3].astype(np.float32).tolist(),[],mesh.tri_verts.tolist())
    bm=bmesh.new();bm.from_mesh(data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),'Precision cleanup opened the surface'
    bm.to_mesh(data);bm.free()
    vs=np.array([tuple(v.co) for v in data.vertices],np.float64)
    ts=np.array([tuple(p.vertices) for p in data.polygons],np.uint64)
    result=M.Manifold(M.Mesh64(vs,ts,tolerance=.00001))
    bpy.data.meshes.remove(data)
    assert result.status()==M.Error.NoError
    assert abs(result.volume()-original_volume)<original_volume*.00001
    return result
