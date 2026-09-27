"""Read completed G-code without executing it; audit bounds and render six layers."""
from pathlib import Path
import re,json,math,hashlib,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
NUMBER=re.compile(r'([XYZEIJR])([-+]?\d*\.?\d+)')
report={'bed_mm':[256,256],'includes_circular_arc_extrema':True,'files':{},'all_passed':False}
previous=json.loads((ROOT/'TOOLPATH_REVIEW.json').read_text()) if (ROOT/'TOOLPATH_REVIEW.json').exists() else {'files':{}}
selected=[.2,12.0,14.0,28.2,76.2,116.2]
refresh='--refresh-preview' in sys.argv
preview=ROOT/'previews'/'Bull_sliced_layers.png'
canvas=Image.open(preview).convert('RGB') if preview.exists() and not refresh else Image.new('RGB',(1800,1300),'#202733')
draw=ImageDraw.Draw(canvas)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
draw.text((35,16),'Bull toolpaths — silver: model; orange: removable supports; each panel spans 0.4 mm in Z',font=font,fill='white')
for i,h in enumerate(selected):
    ox=10+(i%3)*600;oy=70+(i//3)*610
    draw.rectangle((ox+25,oy+40,ox+570,oy+585),outline='#738291',width=2)
    draw.text((ox+25,oy+7),f'Z {max(0,h-.2):.1f}–{h+.2:.1f} mm',font=font,fill='white')
def project(x,y,i):
    ox=10+(i%3)*600;oy=70+(i//3)*610
    return (ox+25+x*545/256,oy+585-y*545/256)

def arc_geometry(x,y,nx,ny,values,cw):
    assert 'I' in values or 'J' in values,'Unsupported radius-only extrusion arc'
    cx=x+values.get('I',0);cy=y+values.get('J',0);radius=math.hypot(x-cx,y-cy)
    a=math.atan2(y-cy,x-cx);b=math.atan2(ny-cy,nx-cx)
    sweep=((a-b) if cw else (b-a))%(2*math.pi)
    if math.hypot(nx-x,ny-y)<1e-7:sweep=2*math.pi
    direction=-1 if cw else 1
    points=[(x,y),(nx,ny)]
    for angle in [0,math.pi/2,math.pi,3*math.pi/2]:
        distance=((a-angle) if cw else (angle-a))%(2*math.pi)
        if distance<=sweep+1e-9:points.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle)))
    return points,(cx,cy,radius,a,sweep,direction)

for p in sorted((ROOT/'slicing').glob('*/plate_1.gcode')):
    if p.parent.name=='test':continue
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    cached=previous['files'].get(p.parent.name)
    if previous.get('includes_circular_arc_extrema') and cached and cached['gcode_sha256']==digest and cached['passed'] and not (refresh and p.parent.name=='01_Bull_with_charge_stripes'):
        report['files'][p.parent.name]=cached
        print(p.parent.name,'PASS (unchanged verified G-code)',flush=True)
        continue
    x=y=z=e=0.;relative_e=True;feature='Custom';layer=0.;segments=0;support=0;arcs=0
    mins=[float('inf')]*3;maxs=[float('-inf')]*3;actual_model_heights=set()
    critical_support=critical_hoof=0;type_counts={}
    for line in p.open(errors='replace'):
        if line.startswith(';TYPE:'):feature=line[6:].strip();continue
        if line.startswith(';Z:'):layer=float(line[3:]);continue
        code=line.split(';',1)[0].strip()
        if code=='M83':relative_e=True;continue
        if code=='M82':relative_e=False;continue
        op=code.split(' ',1)[0]
        if op not in ['G0','G1','G2','G3','G92']:continue
        values={k:float(v) for k,v in NUMBER.findall(code)}
        if op=='G92':
            e=values.get('E',e);continue
        nx=values.get('X',x);ny=values.get('Y',y);nz=values.get('Z',z)
        de=values.get('E',0) if relative_e else values.get('E',e)-e
        extrudes=de>1e-7 and any(k in values for k in ['X','Y','I','J']) and feature!='Custom' and layer>0
        if extrudes:
            segments+=1;is_support='Support' in feature
            support+=is_support;arcs+=op in ['G2','G3'];type_counts[feature]=type_counts.get(feature,0)+1
            xy=[(x,y),(nx,ny)];arc=None
            if op in ['G2','G3']:xy,arc=arc_geometry(x,y,nx,ny,values,op=='G2')
            for a,b in xy:
                mins[0]=min(mins[0],a);maxs[0]=max(maxs[0],a)
                mins[1]=min(mins[1],b);maxs[1]=max(maxs[1],b)
            mins[2]=min(mins[2],z,nz);maxs[2]=max(maxs[2],z,nz)
            if not is_support and feature not in ['Skirt','Brim']:actual_model_heights.add(round(layer,4))
            if p.parent.name=='01_Bull_with_charge_stripes':
                if 73<nx<93 and 89<ny<111 and 10<layer<13.0 and is_support:critical_support+=1
                if 73<nx<93 and 89<ny<111 and 12<layer<19 and not is_support:critical_hoof+=1
                for i,h in enumerate(selected):
                    if abs(layer-h)<.201:
                        color='#f4a261' if is_support else '#dbe5f0'
                        if arc:
                            cx,cy,r,a,sweep,direction=arc
                            steps=max(2,math.ceil(r*sweep/.25))
                            points=[project(cx+r*math.cos(a+direction*sweep*j/steps),cy+r*math.sin(a+direction*sweep*j/steps),i) for j in range(steps+1)]
                        else:points=[project(x,y,i),project(nx,ny,i)]
                        draw.line(points,fill=color,width=1)
        x,y,z=nx,ny,nz
        e=(e+values.get('E',0)) if relative_e else values.get('E',e)
    entry={'gcode_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'extruding_segments':segments,
           'support_segments':support,'model_layer_heights':len(actual_model_heights),
           'toolpath_bounds_mm':[list(map(lambda v:round(v,3),mins)),list(map(lambda v:round(v,3),maxs))],
           'arc_segments':arcs,'feature_segment_counts':type_counts,
           'within_bed_including_0_25mm_extrusion_margin':mins[0]>=.25 and mins[1]>=.25 and maxs[0]<=255.75 and maxs[1]<=255.75,
           'passed':segments>0 and support>0 and mins[0]>=.25 and mins[1]>=.25 and maxs[0]<=255.75 and maxs[1]<=255.75}
    if p.parent.name=='01_Bull_with_charge_stripes':
        entry['raised_hoof_support_segments_z10_to13']=critical_support
        entry['raised_hoof_model_segments_z12_to19']=critical_hoof
        entry['passed']=entry['passed'] and critical_support>0 and critical_hoof>0
    report['files'][p.parent.name]=entry
    print(p.parent.name,'PASS' if entry['passed'] else 'FAIL',flush=True)
report['all_passed']=len(report['files'])==10 and all(x['passed'] for x in report['files'].values())
(ROOT/'TOOLPATH_REVIEW.json').write_text(json.dumps(report,indent=2))
canvas.save(ROOT/'previews'/'Bull_sliced_layers.png')
assert report['all_passed'],'Review toolpath bounds or missing support'
