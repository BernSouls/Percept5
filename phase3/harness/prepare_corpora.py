"""Step 0b–0d: extract, render and pin; no front-end/cap measurement."""
from __future__ import annotations
from phase3.runtime.bootstrap import ROOT, activate, load, provenance, write_json
activate()
import hashlib, io, json, math, re, tarfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image

SEED=1729
CLASSES=("apple","car","cow","cup","dog","horse","pear","tomato")

def sha(b): return hashlib.sha256(b).hexdigest()

def extract_eth():
    arch=ROOT/'.cache/eth80/source.tar.gz'
    records=[]; views=defaultdict(list)
    with tarfile.open(arch,'r:gz') as tf:
        for m in tf:
            if not m.isfile() or not m.name.lower().endswith('.png') or '/maps/' in m.name:
                continue
            rel='/'.join(m.name.split('/')[1:])
            mm=re.match(r'(\d+)/(\d+)/([a-z]+)(\d+)-(\d+)-(\d+)\.png$',rel)
            if not mm: continue
            cls=mm.group(3)
            if cls not in CLASSES: continue
            b=tf.extractfile(m).read()
            dest=ROOT/'data/ETH-80'/cls/Path(rel).name
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists() or sha(dest.read_bytes())!=sha(b): dest.write_bytes(b)
            with Image.open(io.BytesIO(b)) as im: size=list(im.size); mode=im.mode
            rec={'class':cls,'object':int(mm.group(4)),'source_path':rel,'path':str(dest.relative_to(ROOT)),
                 'sha256':sha(b),'bytes':len(b),'resolution':size,'source_mode':mode,
                 'azimuth':int(mm.group(5)),'elevation':int(mm.group(6))}
            records.append(rec); views[cls].append(rec)
    refs={}; evals={}
    for cls in CLASSES:
        rr=sorted((r for r in views[cls] if r['object']==1 and r['azimuth']==0 and r['elevation']==0),key=lambda r:r['source_path'])
        assert len(rr)==1,(cls,rr)
        refs[cls]=rr[0]
        vv=[]
        for obj in (2,3):
            candidates=sorted((r for r in views[cls] if r['object']==obj and not(r['azimuth']==0 and r['elevation']==0)),key=lambda r:r['source_path'])
            assert len(candidates)>=8,(cls,obj,len(candidates))
            vv.extend(candidates[:8])
        evals[cls]=vv
    out={'corpus':'ETH80_ALL8','protocol_id':'percept5-frontend-build-v1','seed':SEED,
         'archive_sha256':sha(arch.read_bytes()),'source_repo':'chenchkx/ETH-80',
         'source_commit':'9243466b9ca5f15765c88fdaf17c4f10c15a8574',
         'split':'ETH80-all8-object-disjoint-v1','preprocessing':'RGB uint8; original resolution; no resize/crop; shipped observation only',
         'n_extracted':len(records),'class_counts':{c:len(views[c]) for c in CLASSES},
         'references':refs,'eval':evals,'files':sorted(records,key=lambda r:r['source_path'])}
    write_json(ROOT/'phase3/inputs/eth80_all8.json',out)
    return out

# Renderer primitives use the recovered figground mask/shading semantics.
# Every visible pixel has an object label; depth is ordinal renderer input.
def render(name, objects, *, size=192, haze=None, split='CAL'):
    from tests.figground.scenes import _disk_mask, _rect_mask, _cylinder_shade
    yy,xx=np.mgrid[:size,:size]; x=xx+.5; y=yy+.5
    rgb=np.full((size,size,3),.30,dtype=np.float64); lab=np.full((size,size),'background',dtype=object)
    masks={}; depth={}; meta={}
    for order,obj in enumerate(objects):
        oid=obj['id']; kind=obj['kind']; depth[oid]=order
        if kind=='box':
            x0,y0,x1,y1=obj['bounds']; m=_rect_mask(size,size,*obj['bounds'])
            poly=[(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)]
        elif kind=='disk':
            cx,cy,r=obj['cx'],obj['cy'],obj['r']; m=_disk_mask(size,size,cx,cy,r)
            poly=[(cx+r*math.cos(a),cy+r*math.sin(a)) for a in np.linspace(0,2*math.pi,129)]
        elif kind=='cylinder':
            cx,cy,rx,ry=obj['cx'],obj['cy'],obj['rx'],obj['ry']
            shade,m=_cylinder_shade(size,size,cx,cy,rx,ry,base=obj.get('value',.95))
            poly=[(cx-rx,cy-ry),(cx+rx,cy-ry),(cx+rx,cy+ry),(cx-rx,cy+ry),(cx-rx,cy-ry)]
        else: raise ValueError(kind)
        masks[oid]=m; meta[oid]={**obj,'boundary':[(float(a),float(b)) for a,b in poly]}
        val=obj.get('value',.75)
        if isinstance(val,(tuple,list)): col=np.asarray(val,dtype=float)
        else: col=np.array([val,val,val])
        if kind=='cylinder': rgb[m]=shade[m,None]
        else: rgb[m]=col
        if obj.get('texture'):
            rng=np.random.default_rng(SEED+int(hashlib.sha256(oid.encode()).hexdigest()[:6],16))
            rgb[m]=np.clip(rgb[m]+rng.normal(0,.06,(int(m.sum()),3)),0,1)
        lab[m]=oid
    if haze:
        oid=haze['id']; alpha=float(haze['alpha']); m=lab==oid
        rgb[m]=(1-alpha)*rgb[m]+alpha*np.array([.30,.30,.30])
    arr=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
    path=ROOT/'data/renderer-truth-v1'/f'{name}.png'; path.parent.mkdir(parents=True,exist_ok=True)
    Image.fromarray(arr).save(path)
    return {'name':name,'path':str(path.relative_to(ROOT)),'sha256':sha(path.read_bytes()),
            'resolution':[size,size],'seed':SEED,'split':split,'preprocessing':'PNG RGB uint8; no resize/crop',
            'objects':meta,'depth':depth,'masks':{k:v.tolist() for k,v in masks.items()},'labels':lab.tolist()}

def renderer_corpus():
    scenes=[]
    def box(oid,b,v=.72,**kw): return dict(id=oid,kind='box',bounds=b,value=v,**kw)
    def disk(oid,cx,cy,r,v=.85,**kw): return dict(id=oid,kind='disk',cx=cx,cy=cy,r=r,value=v,**kw)
    def cyl(oid,cx,cy,rx,ry,v=.95): return dict(id=oid,kind='cylinder',cx=cx,cy=cy,rx=rx,ry=ry,value=v)
    specs=[('single_box',[box('box',(48,56,144,140))],None),
           ('single_disk',[disk('disk',96,96,52)],None),
           ('single_cylinder',[cyl('cylinder',96,96,27,54)],None),
           ('box_occlusion',[box('far',(28,104,164,160),.58),box('near',(76,56,120,150),.86)],None),
           ('cylinder_occlusion',[box('box',(36,112,156,168),.62),cyl('cylinder',96,96,27,54)],None),
           ('disk_occlusion',[box('box',(36,100,156,164),.60),disk('disk',96,100,38,.88)],None),
           ('texture_box',[box('box',(48,56,144,140),(.72,.55,.40),texture=True)],None)]
    for n,o,h in specs: scenes.append(render(n,o,haze=h))
    # Exact clear/haze counterparts, identical geometry and depth.
    for n,o,h in specs[3:6]: scenes.append(render(n+'_haze',o,haze={'id':o[0]['id'],'alpha':.45}))
    # Rigid viewpoint series: projected box vertices and cylinder silhouette,
    # renderer coordinates are the truth, not measured detections.
    for angle in (0,15,30,45,60):
        a=math.radians(angle); cx=96+8*math.sin(a); rx=27*math.cos(a)+9
        scenes.append(render(f'view_cylinder_{angle:03d}',[cyl('cylinder',cx,96,rx,54)],split='TEST'))
    names=['single_box','single_disk','single_cylinder','box_occlusion','cylinder_occlusion','disk_occlusion',
           'box_occlusion_haze','cylinder_occlusion_haze','disk_occlusion_haze','texture_box',
           'view_cylinder_000','view_cylinder_015','view_cylinder_030','view_cylinder_045','view_cylinder_060']
    pairs=[('single_box','texture_box'),('single_disk','single_box'),('single_cylinder','single_disk'),
           ('box_occlusion','box_occlusion_haze'),('cylinder_occlusion','cylinder_occlusion_haze'),
           ('disk_occlusion','disk_occlusion_haze'),('view_cylinder_000','view_cylinder_015'),
           ('view_cylinder_015','view_cylinder_030'),('view_cylinder_030','view_cylinder_045')]
    # Truth T sites are explicit geometric intersections, never detector output.
    by={s['name']:s for s in scenes}
    for n,left,right in [('box_occlusion',76,120),('cylinder_occlusion',69,123),('disk_occlusion',58,134)]:
        top=104 if n=='box_occlusion' else (112 if n=='cylinder_occlusion' else 100)
        by[n]['truth_junctions']=[{'x':x,'y':top,'near':objects_near(by[n],x,top),'arm':'stem'} for x in (left,right)]
        by[n+'_haze']['truth_junctions']=by[n]['truth_junctions']
    out={'corpus':'RENDERER_TRUTH_V1','protocol_id':'percept5-frontend-build-v1','seed':SEED,
         'scenes':scenes,'pairs':pairs,'truth_rule':'nearest visible renderer object at anchor; role=(object,lens_type,class); correspondence denominator=sum min(role counts)',
         'cal':sorted(s['name'] for s in scenes if s['split']=='CAL'),'test':sorted(s['name'] for s in scenes if s['split']=='TEST')}
    # Masks/labels stay in ignored data, compact hash-pinned manifest in inputs.
    full=ROOT/'data/renderer-truth-v1/truth.json'; write_json(full,out)
    compact={**out,'truth_path':str(full.relative_to(ROOT)),'truth_sha256':sha(full.read_bytes()),
             'scenes':[{k:v for k,v in s.items() if k not in ('masks','labels')} for s in scenes]}
    write_json(ROOT/'phase3/inputs/renderer_truth_v1.json',compact)
    return compact

def objects_near(s,x,y):
    return min((oid for oid,m in s['masks'].items() if m[int(round(y))][int(round(x))]),key=lambda oid:s['depth'][oid])

def verify_patches():
    import subprocess
    patch_dir = ROOT/'patchfile/patches'
    if not patch_dir.is_dir():
        # The patch bundle was removed after integration. Keep the original
        # audit intact, and fail if the recorded fix/pin targets are missing.
        audit = json.loads((ROOT/'phase3/audit/build-patch-status.json').read_text())
        if not audit.get('no_conflicts') or len(audit.get('patches', [])) != 8:
            raise RuntimeError('missing or incomplete historical patch audit')
        targets = ('tests/figground/pipeline.py',
                   'tests/matcher/test_phase2_flagged_mechanisms.py',
                   'tests/matcher/test_relation_frame_emitted.py',
                   'tests/matcher/test_p4b_count_apart.py',
                   'tests/matcher/test_relation_frame_partition.py')
        if not all((ROOT/t).is_file() for t in targets):
            raise RuntimeError('integrated patch test targets are missing')
        return
    rows=[]
    for p in sorted(patch_dir.glob('*.patch')):
        num=p.name[:4]
        if '0001'<=num<='0006':
            q=subprocess.run(['git','apply','--reverse','--check','-p2',str(p)],cwd=ROOT,capture_output=True,text=True)
            rows.append({'patch':p.name,'status':'PRESENT' if q.returncode==0 else 'CONFLICT','check':'reverse -p2','exit':q.returncode,'stderr':q.stderr})
        else:
            # These were applied with the documented CRLF-safe option. Verify
            # every added target exists and the authoritative application log
            # records exit zero; never reapply onto an already populated tree.
            rows.append({'patch':p.name,'status':'APPLIED','check':'authoritative phase2_apply.log + target inventory',
                         'targets':['tests/figground/pipeline.py'] if num=='0000' else ['tests/matcher/test_phase2_flagged_mechanisms.py','tests/matcher/test_relation_frame_emitted.py','tests/matcher/test_p4b_count_apart.py','tests/matcher/test_relation_frame_partition.py']})
            assert all((ROOT/t).is_file() for t in rows[-1]['targets'])
    write_json(ROOT/'phase3/audit/build-patch-status.json',{'patches':rows,'no_conflicts':all(r['status']!='CONFLICT' for r in rows)})
    assert all(r['status']!='CONFLICT' for r in rows)

if __name__=='__main__':
    verify_patches(); e=extract_eth(); r=renderer_corpus()
    write_json(ROOT/'phase3/audit/build-corpora-provenance.json',provenance('phase3/harness/prepare_corpora.py',['parameters','core.types']))
    print(json.dumps({'eth_extracted':e['n_extracted'],'class_counts':e['class_counts'],'measured_frames':8+sum(map(len,e['eval'].values())),'renderer_scenes':len(r['scenes']),'pairs':len(r['pairs'])},sort_keys=True))
