"""Third revision: corrected lifted hoof and reinforced small printable features.
Axes: -X forward, +Z up; 1 Blender unit = 1 mm. Earlier versions retained.
"""
from pathlib import Path
exec(compile((Path(__file__).parent/'common.py').read_text(),'common.py','exec'))
from mathutils.geometry import delaunay_2d_cdt
from mathutils import Matrix

def triangulate_patch(points,boundary_count):
    uv=[Vector(p[:2]) for p in points]
    # CDT preserves outline and landmark positions, without ring-shaped mesh bands.
    verts,edges,faces,orig,_,_=delaunay_2d_cdt(uv,[],[list(range(boundary_count))],1,1e-5,True)
    indices=[]
    for p,ids in zip(verts,orig):
        assert ids,('unexpected inserted vertex',p)
        indices.append(ids[0])
    return [tuple(indices[k] for k in f) for f in faces]

def paired_patch(boundary,front,back,xyz):
    # Coordinates are (u,v,depth). Boundary vertices shared by front and rear patches.
    a=boundary+front;b=boundary+back;n=len(boundary)
    verts=[xyz(*p) for p in a]+[xyz(*p) for p in back]
    faces=triangulate_patch(a,n)
    offset=len(a)-n
    faces += [tuple(k if k<n else k+offset for k in f) for f in triangulate_patch(b,n)]
    return solid(verts,faces)

def inside(p,poly):
    x,y=p;state=False
    for i,(x1,y1) in enumerate(poly):
        x2,y2=poly[(i+1)%len(poly)]
        if ((y1>y)!=(y2>y)) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:state=not state
    return state

def body_mesh(kind):
    calf=kind=='Calf';cow=kind=='Cow'
    if calf:
        outline=[(-63,117),(-57,133),(-41,140),(-24,137),(-6,128),(20,120),(44,113),(62,104),
                 (70,91),(66,72),(48,60),(29,55),(9,54),(-10,51),(-30,51),(-50,61),(-65,82)]
        widths=[(-66,10),(-55,24),(-35,28),(-12,27),(15,24),(42,22),(61,16),(70,0)]
    else:
        outline=[(-79,116),(-68,143),(-49,158),(-26,164),(-8,161),(14,147),(34,133),(56,119),
                 (69,105),(73,87),(64,69),(47,60),(29,55),(8,48),(-13,44),(-32,43),(-53,50),(-72,66),(-81,88)]
        widths=[(-81,13),(-70,29),(-50,40),(-27,42),(-3,39),(25,33),(50,27),(65,19),(73,0)]
        if cow:
            outline=[(x,z-4 if z>120 else z+1 if z<65 else z) for x,z in outline]
            widths=[(x,w*.96) for x,w in widths]
    def yz(x,z):
        crossings=[]
        for i,(x1,z1) in enumerate(outline):
            x2,z2=outline[(i+1)%len(outline)]
            if min(x1,x2)<=x<=max(x1,x2) and abs(x2-x1)>1e-7:crossings.append(z1+(z2-z1)*(x-x1)/(x2-x1))
        if len(crossings)<2:return 0
        low,high=min(crossings),max(crossings);c=(low+high)/2;r=(high-low)/2
        return float(np.interp(x,[v[0] for v in widths],[v[1] for v in widths]))*max(0,1-((z-c)/r)**2)**.37
    # Deliberately irregular landmarks: larger flank panels, smaller chest facets.
    landmarks=[(-66,114),(-57,135),(-46,149),(-30,151),(-14,146),(-43,124),(-22,133),(-2,132),
               (-69,94),(-56,105),(-32,112),(-13,119),(10,127),(24,117),(45,114),(60,103),
               (-63,76),(-47,84),(-27,93),(-8,101),(14,106),(33,99),(51,94),(64,84),
               (-48,64),(-27,69),(-5,78),(16,87),(37,78),(51,71),(-28,54),(-8,57),(18,63),(33,63)]
    landmarks += [(-51,153),(-34,160),(-17,159),(0,152),(21,139)]
    if calf:landmarks=[(x*.86,z*.83+8) for x,z in landmarks]
    rng=random.Random({'Bull':314,'Cow':196,'Calf':113}[kind])
    pts=[p for p in landmarks if inside(p,outline)]
    # Fill only the larger empty regions, keeping manually chosen principal landmarks.
    for _ in range(900):
        p=(rng.uniform(min(x for x,z in outline)+3,max(x for x,z in outline)-3),rng.uniform(min(z for x,z in outline)+3,max(z for x,z in outline)-3))
        if not inside(p,outline):continue
        if min(math.hypot(p[0]-q[0],p[1]-q[1]) for q in pts+outline)<12.5:continue
        pts.append(p)
        if len(pts)>64:break
    boundary=[(x,z,0) for x,z in outline]
    front=[(x,z,yz(x,z)) for x,z in pts]
    back=[(x,z,-yz(x,z)) for x,z in pts]
    return paired_patch(boundary,front,back,lambda x,z,y:(x,y,z)),yz

def head_mesh(kind):
    # In the photos the forehead projects beyond the muzzle; the first reconstruction reversed this.
    if kind!='Calf':
        right=[(0,145,-78),(16,143,-73),(26,137,-68),(31,125,-65),(31,113,-62),
               (28,104,-64),(22,94,-69),(20,82,-76),(15,73,-82),(0,68,-84)]
        boundary=right+[(-y,z,x) for y,z,x in right[-2:0:-1]]
        face=[(0,138,-97),(-13,136,-96),(14,136,-97),(-23,126,-95),(0,126,-105),(22,128,-97),
              (-25,116,-93),(0,116,-107),(25,116,-93),(-16,111,-105),(16,110,-105),
              (-23,104,-92),(0,103,-106),(23,104,-92),(-13,94,-102),(12,94,-102),
              (0,89,-104),(-15,83,-99),(14,83,-99),(0,77,-101),(-11,76,-95),(11,76,-95),(0,71,-92)]
        back=[(0,136,-64),(-16,127,-53),(16,129,-53),(0,117,-43),(-20,113,-52),(20,111,-52),
              (0,99,-49),(-12,89,-61),(12,89,-61),(0,79,-69)]
        if kind=='Cow':
            boundary=[(y*.95,z,x+1) for y,z,x in boundary]
            face=[(y*.95,z,x+1) for y,z,x in face];back=[(y*.95,z,x+1) for y,z,x in back]
    else:
        right=[(0,151,-72),(14,148,-68),(23,140,-63),(26,130,-63),(23,118,-70),
               (19,111,-83),(13,105,-91),(0,102,-91)]
        boundary=right+[(-y,z,x) for y,z,x in right[-2:0:-1]]
        face=[(0,145,-85),(-12,141,-83),(12,142,-83),(-17,133,-90),(0,135,-98),(18,134,-90),
              (-16,126,-98),(0,123,-105),(17,126,-98),(-14,116,-108),(0,113,-113),(14,116,-108),
              (0,106,-104),(-10,110,-105),(10,110,-105)]
        back=[(0,141,-52),(-14,132,-47),(14,132,-47),(0,123,-54),(-13,116,-66),(13,116,-66),(0,109,-83)]
    return paired_patch(boundary,face,back,lambda y,z,x:(x,y,z))

def surface_hit(s,point,direction):
    probe=mesh_obj('projection probe',s);d=Vector(direction).normalized()
    hit,loc,nor,_=probe.ray_cast(Vector(point)+d*65,-d,distance=160)
    bpy.data.objects.remove(probe,do_unlink=True)
    assert hit,('ray missed',point,direction)
    return loc,nor

def head_assembly(kind):
    calf=kind=='Calf';h=head_mesh(kind);parts=[h];cuts=[]
    # Shorter chin beard integrates into the neck instead of forming a long second muzzle.
    if not calf:
        parts.append(hull([(-97,-12,77),(-97,12,77),(-67,-16,84),(-67,16,84),
                           (-80,-2.3,58),(-80,2.3,58),(-72,0,61),(-61,0,82)]))
    for side in [-1,1]:
        if calf:
            parts.append(hull([(-65,side*18,137),(-53,side*25,141),(-62,side*44,147),
                               (-72,side*28,142),(-63,side*28,132)]))
        else:
            parts.append(hull([(-62,side*24,111),(-48,side*28,119),(-52,side*41,126),
                               (-69,side*32,118),(-61,side*31,108)]))
            horn=[(-80,side*25,128),(-80,side*34,126),(-79,side*42,132),(-76,side*44,143),(-72,side*39,153)]
            parts.append(tube(horn,[6.5,6.0,4.2,2.5,1.1],5))
        target=(-101,side*18,129) if calf else (-103,side*23,106)
        direction=Vector((-.58,side*.81,.03));loc,nor=surface_hit(h,target,direction)
        u=Vector((side*.81,.58,0));size=3.4 if not calf else 3.2
        ring,cut,_=frame_detail(loc+direction*.25,direction,u,size,1.8)
        parts.append(ring);cuts.append(cut)
        target=(-116,side*11,115) if calf else (-106,side*12,79)
        d=Vector((-.96,side*.27,0));loc,nor=surface_hit(h,target,d)
        r,c,_=frame_detail(loc+d*.1,d,(side*.27,.96,0),2.1 if calf else 2.25,1.4)
        parts.append(r);cuts.append(c)
    h=union(parts)-union(cuts)
    if not calf:
        # Tall rounded poll: upper face rises nearly to the shoulder crest in side photographs.
        h=h.warp(lambda p:(p[0],p[1],p[2]+max(0,p[2]-105)*.20))
    # Head turn toward the center, independent of the body/foot pose.
    angle={'Bull':3.5,'Cow':-9.,'Calf':-12.}[kind]
    return h.translate((68,0,-110)).rotate((0,0,angle)).translate((-68,0,110))

def stripe_assembly(body,kind,yfunc):
    calf=kind=='Calf';stripes=[]
    outer=[(-58,127),(-29,123),(-1,117),(28,109),(57,100),(68,78),(39,88),(10,97),(-23,106),(-58,112),
           (-55,115),(-53.5,118),(-54.5,122)]
    inner=[(-49,123),(-28.8,120),(-.8,114),(28.2,106),(54.5,97.5),(62,83),(38.2,91),(9.2,100),(-23.8,109),(-49,115),
           (-46.5,117),(-46,119),(-47.5,121.5)]
    if calf:
        outer=[(x*.9,z*.9+5) for x,z in outer];inner=[(x*.9,z*.9+5) for x,z in inner]
        # Widen the rails in their own plane as well as through their depth.
        # This keeps the smallest family-display rails from becoming single-line walls.
        inner=[(ox+(ix-ox)*1.7,oz+(iz-oz)*1.7) for (ox,oz),(ix,iz) in zip(outer,inner)]
    # Broad smooth bend along the flank. Upper/lower rails share the same transverse curve.
    def ycurve(x):
        z=float(np.interp(x,[-58,-30,0,30,68],[119,115,107,97,89]))
        if calf:z=z*.9+5
        return max(yfunc(x,z-9),yfunc(x,z),yfunc(x,z+9))+4.2
    # Subdivide long panels of the ribbon, but leave anatomy's large facets untouched.
    out=[];inn=[]
    for i in range(len(outer)):
        a,b=outer[i],outer[(i+1)%len(outer)];c,d=inner[i],inner[(i+1)%len(inner)]
        steps=3 if i<9 else 1
        for j in range(steps):
            t=j/steps;out.append((a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t));inn.append((c[0]*(1-t)+d[0]*t,c[1]*(1-t)+d[1]*t))
    for side in [-1,1]:
        n=len(out);v=[];f=[];thickness={'Bull':2.5,'Cow':3.1,'Calf':4.9}[kind]
        for sign in [-1,1]:
            for loop in [out,inn]:
                v.extend([(x,side*ycurve(x)+sign*thickness/2,z) for x,z in loop])
        for i in range(n):
            j=(i+1)%n
            f.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                      (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
        stripes.append(solid(v,f))
        for i in [0,5,10,13,17,23]:
            x=(out[i][0]+inn[i][0])/2;z=(out[i][1]+inn[i][1])/2
            stripes.append(tube([(x,side*max(0,ycurve(x)-14),z),(x,side*ycurve(x),z)],
                                [2.1 if not calf else 2.7]*2,n=6))
    return union(stripes)

def make(kind):
    calf=kind=='Calf';body,yfunc=body_mesh(kind);head=head_assembly(kind);parts=[body,head]
    for side in [-1,1]:
        y=side*(27 if not calf else 20)
        if kind=='Bull' and side==-1:
            # The lifted front leg is on the viewer's right in the nearly frontal reference.
            front=[(113,-42,y*.85,17,12),(79,-49,y,17,12),(54,-58,y,12,10),
                   (44,-62,y,9.2,8),(31,-54,y-1,6.2,6.3),(23,-49,y-1,5.7,6.2)]
            # A short, forward-pointing hoof replaces the swept razor-like end.
            # Its sloped sole is clear of the bed and needs removable support.
            yc=y-1
            hoof=loft([(26,-49,yc,5.8,6.2),(20,-50,yc,6.4,6.7),(14,-52,yc,7.1,6.5)],axis='Z',n=8)
            hoof=hoof.warp(lambda p:(p[0],p[1],p[2]+.22*(p[0]+52)*max(0,(20-p[2])/6)))
            parts.append(hoof)
        elif calf:
            if side==-1:
                front=[(107,-39,y*.8,12,9),(73,-44,y,11,8),(49,-50,y-1,6.2,5.5),(22,-53,y-3,4.5,4.5),(0,-57,y-4,5.4,5.0)]
            else:
                front=[(104,-35,y*.8,11,8),(69,-36,y,9,7),(43,-33,y,5.2,5.3),(17,-26,y+1,4.5,4.5),(0,-30,y+2,5.3,5)]
        else:
            shift=-8 if side==-1 else 0
            front=[(115,-41,y*.8,17,11),(83,-46,y,17,13),(56,-46+shift,y+side*2,11,10),
                   (27,-55+shift,y+side*4,6.5,6.8),(8,-63+shift,y+side*5,6.2,6.3),(0,-66+shift,y+side*6,8,7.2)]
        parts.append(loft(front,axis='Z',n=7,seed=15+side,jitter=.0))
        if calf:
            offset=7 if side==-1 else -9
            rear=[(101,39,y*.55,12,8),(74,44,y*.86,13,9),(47,55+offset*.3,y,7,6),
                  (25,68+offset,y+side,4.8,4.7),(0,69+offset,y+side*3,5.6,5.1)]
        else:
            offset=8 if side==-1 else -7
            rear=[(105,40,y*.57,13,8),(82,48,y*.82,15,11),(57,48+offset,y*.9,12,8),
                  (34,63+offset,y,6.5,6.1),(13,62+offset,y+side,5.2,5.3),(0,60+offset,y+side*2,7,6.4)]
        parts.append(loft(rear,axis='Z',n=7,seed=19+side,jitter=0))
    # Angular tail is swept out behind the high rump, not stuck vertically against it.
    tail=[(65,0,105),(79,0,103),(88,1,94),(89,1,81)]
    if calf:tail=[(63,0,103),(76,0,100),(82,0,90),(83,0,79)]
    parts.append(tube(tail,[3.8,3.4,3.1,3.1] if calf else [3.8,3.1,2.7,2.8],5));x,y,z=tail[-1]
    parts.append(hull([(x-3,-3,z+4),(x+3,0,z+8),(x+4,4,z),(x+2,0,z-11),(x-3,0,z-5)]))
    plain=union(parts);plain=union([s for s in plain.decompose() if s.volume()>0])
    stripes=stripe_assembly(body,kind,yfunc);striped=plain+stripes
    striped=union([s for s in striped.decompose() if s.volume()>0])
    assert len(striped.decompose())==1,(kind,[(s.volume(),s.bounding_box()) for s in striped.decompose()])
    bbox=striped.bounding_box();target={'Bull':200,'Cow':200*23/29,'Calf':200*13/29}[kind]
    scale=target/(bbox[3]-bbox[0]);center=(bbox[0]+bbox[3])/2
    plain=plain.translate((-center,0,0)).scale((scale,scale,scale))
    striped=striped.translate((-center,0,0)).scale((scale,scale,scale))
    stripes=stripes.translate((-center,0,0)).scale((scale,scale,scale))
    # Remove sub-micron boolean slivers before rounding coordinates into binary STL.
    return clean_solid(plain),clean_solid(striped),stripes

models={};report={}
for kind in ['Bull','Cow','Calf']:
    plain,s,stripes=make(kind);num={'Bull':'01','Cow':'02','Calf':'03'}[kind]
    stl(ROOT/'STL'/f'{num}_{kind}_with_charge_stripes.stl',s)
    (ROOT/'STL'/'optional_plain').mkdir(exist_ok=True)
    stl(ROOT/'STL'/'optional_plain'/f'{num}_{kind}_plain.stl',plain)
    ob=mesh_obj(kind,s,SILVER);models[kind]=(ob,s)
    ob.data.materials.append(STRIPE)
    probe=mesh_obj('charge material boundary',stripes)
    for poly in ob.data.polygons:
        hit,loc,norm,index=probe.closest_point_on_mesh(poly.center)
        if hit and (loc-poly.center).length<.002:poly.material_index=1
    bpy.data.objects.remove(probe,do_unlink=True)
    ob['revision']='V3: corrected lifted hoof and reinforced small features';ob['units']='millimeters'
    bb=s.bounding_box();report[kind]={'dimensions_mm':[round(bb[i+3]-bb[i],3) for i in range(3)],
        'triangles':s.num_tri(),'volume_mm3':round(s.volume(),3),'connected_solids':len(s.decompose())}
    print(kind,report[kind],flush=True)
(ROOT/'BUILD_REPORT.json').write_text(json.dumps(report,indent=2))

positions={'Bull':(-9,91,0),'Cow':(10,-88,0),'Calf':(-57,0,0)}
for kind,(ob,s) in models.items():ob.location=positions[kind]
ground=material('Neutral slate',(.14,.17,.21),.0,.58)
bpy.ops.mesh.primitive_plane_add(size=20000,location=(0,0,-.02));floor=bpy.context.object;floor.name='Studio floor - not exported';floor.data.materials.append(ground)
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;aim(ob,target)
area('Key',(-240,-260,400),2400000,235,(0,0,65));area('Fill',(-310,180,210),1500000,230,(0,0,80));area('Rim',(160,130,340),2900000,180,(0,0,80))
world=bpy.data.worlds.new('Studio world');scene.world=world;world.use_nodes=True
world.node_tree.nodes.get('Background').inputs[0].default_value=(.25,.28,.34,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.35
data=bpy.data.cameras.new('Reference camera');camera=bpy.data.objects.new('Reference camera',data);scene.collection.objects.link(camera);scene.camera=camera
camera.location=(-600,-190,45);aim(camera,(-5,0,77));data.type='PERSP';data.lens=54;data.clip_end=30000
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1700;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
for ob in bpy.context.selected_objects:ob.select_set(False)
for ob,s in models.values():ob.select_set(True)
bpy.context.view_layer.objects.active=models['Bull'][0]
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.clip_end=10000;a.spaces.active.region_3d.view_distance=430
            a.spaces.active.region_3d.view_location=Vector((0,0,75));a.spaces.active.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source'/'Bills_Bison_Family.blend'))
if '--no-render' in sys.argv:
    print('V3 MESH EXPORT COMPLETE',flush=True)
    raise SystemExit(0)
scene.render.filepath=str(ROOT/'previews'/'Family_preview.png');bpy.ops.render.render(write_still=True)
# Geometry review from matched near-front and side angles; no random face-color material masking.
for kind,(ob,s) in models.items():
    for k,(other,_) in models.items():other.hide_render=k!=kind
    ob.location=(0,0,0);h=report[kind]['dimensions_mm'][2];length=report[kind]['dimensions_mm'][0]
    camera.location=(-340,-175,h*.25);aim(camera,(0,0,h*.48));data.type='PERSP';data.lens=60*(200/length)
    scene.render.resolution_x=1250;scene.render.resolution_y=1100;scene.render.filepath=str(ROOT/'previews'/f'{kind}_preview.png');bpy.ops.render.render(write_still=True)
    if kind=='Bull':
        for name,loc in [('front',(-600,0,h*.55)),('side',(0,-600,h*.55))]:
            camera.location=loc;aim(camera,(0,0,h*.50));data.type='ORTHO';data.ortho_scale=length*1.18
            scene.render.filepath=str(ROOT/'previews'/f'Bull_{name}.png');bpy.ops.render.render(write_still=True)
    ob.location=positions[kind]
print('V3 BUILD COMPLETE',flush=True)
