"""Renderer truth perimeter against shipped largest-kernel interior support.

Perimeter consists of 4-neighbour foreground/background pixel sides; a side is
outside when its foreground pixel centre is outside the largest-kernel valid
interior. Connected foreground objects use 4-connectivity. Truth masks only;
no detector output, cropping, or additional frame extraction is used.
"""
from phase3.runtime.bootstrap import ROOT,activate,write_json
activate()
import argparse,json,numpy as np
from scipy.ndimage import label
from perception.contour_field import front_end_scale,_border_margin_px,_interior_margin
from perception.filters import GaborBank


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='build-renderer-margin.json');args=ap.parse_args()
    doc=json.loads((ROOT/'data/renderer-truth-v1/truth.json').read_text());rows=[]
    for scene in doc['scenes']:
        a=np.asarray(scene['labels'])!='background';h,w=a.shape
        bank=GaborBank.build_default(front_end_scale(h,w));raw=_border_margin_px(bank);m=_interior_margin(raw,h,w)
        yy,xx=np.indices((h,w));valid=(xx>=m)&(xx<w-m)&(yy>=m)&(yy<h-m)
        # Padding makes each image border a normal foreground/background edge.
        p=np.pad(a,1,constant_values=False); perimeter=np.zeros_like(a,dtype=int)
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            perimeter += a & ~p[1+dy:1+dy+h,1+dx:1+dx+w]
        total=int(perimeter.sum());outside=int(perimeter[~valid].sum())
        components,n=label(a);discarded=sum(not bool((valid & (components==k)).any()) for k in range(1,n+1))
        rows.append({'scene':scene['name'],'split':scene['split'],'margin_px':m,'perimeter':total,'outside':outside,'outside_fraction':outside/total if total else None,'foreground_components':n,'components_wholly_discarded':discarded})
    controls=[r for r in rows if r['scene'] in ('single_box','single_cylinder','single_disk')]
    write_json(ROOT/'phase3/results'/args.output,{'corpus':'RENDERER_TRUTH_V1','method':'4-connected silhouette boundary sides, classified by foreground pixel centre; largest-kernel valid interior','scenes':rows,'centered_controls_pass':all(r['outside_fraction'] is not None and r['outside_fraction']<=.10 and r['components_wholly_discarded']==0 for r in controls)})
    for r in controls:print(r,flush=True)
if __name__=='__main__':main()
