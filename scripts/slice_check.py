"""Slice each exported STL locally. No printer communication or print command."""
from pathlib import Path
import json,subprocess,hashlib,time,zipfile,re
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'slicing'
EXE=Path(r'C:\Program Files\OrcaSlicer\orca-slicer.exe')
report={'slicer':'OrcaSlicer 2.4.0','validation_profile_only':True,
        'printer_profile':'Elegoo Centauri Carbon 0.4 nozzle (256 mm bed)',
        'material':'Generic PLA','nozzle_mm':.4,'layer_height_mm':.2,
        'wall_loops':3,'infill_percent':15,'supports':'automatic tree, on bed and model',
        'support_threshold_angle_degrees':45,'files':{},'all_passed':False}
for path in sorted((ROOT/'STL').rglob('*.stl')):
    key=path.relative_to(ROOT).as_posix();out=D/path.stem;out.mkdir(exist_ok=True)
    cmd=[str(EXE),'--debug','3','--logfile',str(out/'engine.log'),
         '--datadir',str(D/'isolated_config'),'--load-settings',str(D/'process.json')+';'+str(D/'printer.json'),
         '--load-filaments',str(D/'filament.json'),'--arrange','1','--orient','0','--slice','0',
         '--outputdir',str(out),'--export-3mf','sliced_check.3mf',str(path)]
    start=time.time();print('Slicing '+path.name,flush=True)
    with (out/'console.log').open('w') as log:
        proc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=0x08000000)
    gcode=out/'plate_1.gcode';archive=out/'sliced_check.3mf'
    text=gcode.read_text(errors='replace') if gcode.exists() else ''
    layer_count=text.count(';LAYER_CHANGE')
    support_lines=text.count(';TYPE:Support')
    warnings=[]
    engine=(out/'engine.log').read_text(errors='replace')
    for line in engine.splitlines():
        if any(word in line.lower() for word in ['warning','non-manifold','empty layer','floating','conflict','repair','error']):
            warnings.append(line[:500])
    archive_ok=False
    if archive.exists():
        with zipfile.ZipFile(archive) as z:archive_ok=z.testzip() is None and any(n.endswith('.gcode') for n in z.namelist())
    comments={}
    for line in text.splitlines():
        if line.startswith(';') and any(w in line for w in ['total estimated time','filament used [g]','filament used [mm]','total layer number']):
            comments[line.split('=')[0].strip('; ')]=line.split('=',1)[-1].strip()
    entry={'exit_code':proc.returncode,'seconds':round(time.time()-start,1),'gcode_bytes':gcode.stat().st_size if gcode.exists() else 0,
           'toolpath_layers_including_support':layer_count,'support_sections':support_lines,'sliced_3mf_verified':archive_ok,
           'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'slicer_messages':warnings,
           'estimates':comments,'passed':proc.returncode==0 and layer_count>0 and support_lines>0 and archive_ok}
    report['files'][key]=entry
    (ROOT/'SLICE_VALIDATION.json').write_text(json.dumps(report,indent=2))
    print(('PASS ' if entry['passed'] else 'FAIL ')+path.name+' layers='+str(layer_count),flush=True)
report['all_passed']=len(report['files'])==10 and all(x['passed'] for x in report['files'].values())
(ROOT/'SLICE_VALIDATION.json').write_text(json.dumps(report,indent=2))
assert report['all_passed'],'Inspect SLICE_VALIDATION.json'
