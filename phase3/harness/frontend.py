"""Independent sensory-to-situation probe, written for this audit.

This deliberately does NOT import diagnostics.eth80_frontend. It drives the
product SensoryFloor, Pipeline lens dispatch, Binder and StatePatternIndex.
The cognitive tail is out of scope: the graph contains no learned concepts,
so recognition/operator emission has no source. Both the complete induced
window and Mapper's capped spatial situation are returned, never conflated.
"""
from __future__ import annotations

from phase3.runtime.bootstrap import activate, load, ROOT, provenance
activate()
from core.frontend_contract import frontend_contract

from collections import defaultdict
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

P = load("parameters")
T = load("core.types")
H = load("core.hashing")
CG = load("concept_graph")
B = load("orchestration.binder")
PL = load("orchestration.pipeline")
SF = load("perception.floor")
O2 = load("perception.observation_2d")
SL = load("dynamics.settle")
DC = load("lenses.derived_common")
MP = load("memory.mapper")
MC = load("memory.cores")
GT = load("core.graph_types")


@dataclass
class FrameResult:
    name: str
    observation: Any
    graph: Any
    pipeline: Any
    binder: Any
    mapper: Any
    raw: tuple
    bound_v1: frozenset
    tiers: dict
    all_detections: frozenset
    window: Any
    spatial: Any
    hierarchy_off: Any
    hierarchy_on: Any
    signatures: dict
    anchors: dict
    binder_positions: dict
    skipped: tuple
    image_shape: tuple
    rich: bool


def read_rgb(path: str | Path, size: int | None = None) -> np.ndarray:
    """RGB conversion; optional explicit square resize, no aspect cropping."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        if size is not None:
            im = im.resize((size, size), Image.Resampling.LANCZOS)
        return np.asarray(im, dtype=np.uint8).copy()


@frontend_contract()
def run_frame(image: np.ndarray, name: str = "frame", *, rich: bool = False,
              steps: int = 1) -> FrameResult:
    """One fresh graph per independent image, with the declared tree defaults.

    steps>0 presents the same image repeatedly, closing each edge-EMA and
    binder lifecycle before the next. This is a temporal probe, not a way to
    manufacture class evidence. The primary corpus protocol uses steps=1.
    """
    from core.frontend_contract import assert_live_contract
    from phase3.runtime.bootstrap import imported_product_paths
    assert_live_contract()
    imported_product_paths()  # asserts every loaded product module is local
    if steps < 1:
        raise ValueError("steps must be positive")
    cg = CG.ConceptGraph()
    binder = B.Binder(cg)
    floor = SF.SensoryFloor()
    providers = PL.PipelineProviders(cg)
    mapper = MP.Mapper(cg, MC.CoreLibrary(), providers.signature_provider)
    # No category manager or cognitive engines are exercised by this probe.
    # The methods called below need only providers, concept graph and lenses.
    pipeline = PL.Pipeline(
        env=None, sensory_floor=floor, derived_lenses=None, binder=binder,
        builder=None, providers=providers, prediction=None, concept_graph=cg,
        activation_engine=None, fertility_engine=None, utility_engine=None,
        consolidator=None, mapper=mapper,
    )
    obs = O2.Observation2D.from_image(image, rich=rich)
    loop = SL.SettleLoop(sensory_floor=floor, binder=binder, cg=cg)
    skipped = []
    for t in range(steps):
        if t:
            cg.step_28_update_edges(None, t - 1)
            binder.finalize_step()
        binder.note_step_begin(t)
        lens_positions = pipeline._derive_anchor_positions(obs)
        scale = pipeline._derive_extraction_scale(obs)
        raw, _, state, state_hash, _ = loop.step(
            t, obs, None, None, set(), anchor_positions=lens_positions,
            extraction_scale=scale,
        )
        anchors = pipeline._derive_anchor_positions(obs)
        binder_positions = dict(anchors)
        binder_positions.update(lens_positions)
        modality = PL.observation_modality(obs)
        v1 = PL.surround_suppress(frozenset(raw), anchors, modality, scale)
        binder.step(
            t, v1, anchor_positions=binder_positions or None,
            anchor_velocities=None,  # Pipeline.step's shipped default: False
            t_junctions=obs.get_t_junctions(), extraction_scale=scale,
            structural_anchors=obs.get_structural_anchors(),
            surface_anchors=obs.get_surface_anchors(),
            contour_surface_contacts=obs.get_contour_surface_contacts(),
        )
        by_kind = defaultdict(list)
        for d in sorted(v1, key=H._detection_sort_key):
            by_kind[d.k].append(d)
        tiers = {}
        one_route = []
        for lens_name in DC.declared_lens_order():
            declaration = DC.LENS_DECLARATION_BY_NAME[lens_name]
            missing = declaration.missing_inputs(by_kind)
            if missing:
                skipped.append((lens_name, tuple(missing)))
                tiers[lens_name] = []
                continue
            positions = (binder_positions if lens_name == "Junction" or
                         (lens_name == "Contour" and P.CONTOUR_SPINE_MAP)
                         else anchors)
            emitted = pipeline._run_higher_lens(
                lens_name, t, cg, getattr(floor, "signature_provider", None),
                positions, by_kind, scale, obs,
            )
            if PL._HIGHER_LENS_OUTPUT_SORTED[lens_name]:
                emitted = sorted(emitted, key=H._detection_sort_key)
            tiers[lens_name] = list(emitted)
            if lens_name != "CurveComplex":
                if lens_name == "Junction":
                    for d in emitted:
                        if d.k != "Junction":
                            by_kind[d.k].append(d)
                    by_kind["Junction"].extend(DC.junction_alias(emitted))
                else:
                    for d in emitted:
                        by_kind[d.k].append(d)
            if lens_name in ("EndStopped", "RegionShape", "Polarity", "TextureBoundary"):
                one_route.extend(emitted)

            def bind(*groups):
                binder.bind_intra_step(t, frozenset(d for g in groups for d in g))

            if lens_name in ("BorderOwnership", "Surface"):
                bind(emitted)
            elif lens_name == "Corner":
                bind(*(tiers.get(k, []) for k in
                       ("Contour", "Junction", "Peak", "Chain")), emitted)
            elif lens_name == "TextureBoundary":
                bind(one_route)
            elif lens_name == "IllusoryContour":
                for d in emitted:
                    points = [anchors.get(role[1]) for role in d.rho
                              if role[0] in ("inducer_1", "inducer_2")]
                    points = [p for p in points if p is not None]
                    if len(points) == 2:
                        anchors[d.alpha] = (
                            (points[0][0] + points[1][0]) / 2.0,
                            (points[0][1] + points[1][1]) / 2.0, 0.0,
                        )
                bind(emitted)
                bind(*(tiers.get(k, []) for k in
                       ("Contour", "Junction", "Peak", "Chain", "Corner")), emitted)
                binder.note_tier_positions(anchors)
                binder.emit_pending_edges("v2")
            elif lens_name == "CurveComplex":
                bind(emitted)
                binder.note_tier_positions(anchors)
                binder.emit_pending_edges("v4")
        all_detections = frozenset(d for group in [v1] + list(tiers.values())
                                   for d in group if d.k != PL.ACTION_LENS_NAME)
        providers.state_index.record(state_hash, set(all_detections))
        window = providers.state_index(state_hash)
        spatial = mapper._spatial_situation(t)
        old_keep = P.MATCH_KEEP_HIERARCHY_MEMBERS
        try:
            P.MATCH_KEEP_HIERARCHY_MEMBERS = False
            hierarchy_off = mapper._apply_hierarchy_exclusions(window)
            P.MATCH_KEEP_HIERARCHY_MEMBERS = True
            hierarchy_on = mapper._apply_hierarchy_exclusions(window)
        finally:
            P.MATCH_KEEP_HIERARCHY_MEMBERS = old_keep
        binder_diag = {
            key: {getattr(k, "name", str(k)): int(v)
                  for k, v in binder.get_diagnostics().get(key, {}).items() if v}
            for key in ("candidates_by_type", "emitted_by_type",
                        "dropped_below_threshold", "candidate_cap_hits")
        }
        binder.finalize_step()
    provider = providers.signature_provider
    signatures = {n: provider(n) for n in sorted(window.nodes) if provider(n) is not None}
    return FrameResult(
        name=name, observation=obs, graph=cg, pipeline=pipeline, binder=binder,
        mapper=mapper, raw=tuple(sorted(raw, key=H._detection_sort_key)),
        bound_v1=v1, tiers=tiers, all_detections=all_detections,
        window=window, spatial=spatial, hierarchy_off=hierarchy_off,
        hierarchy_on=hierarchy_on, signatures=signatures, anchors=anchors,
        binder_positions=binder_positions, skipped=tuple(skipped),
        image_shape=tuple(image.shape), rich=rich,
    )


def detection_record(d: Any) -> dict:
    s = d.sigma
    return {
        "lens": d.k, "class": s.class_, "relation": s.relation,
        "slots": list(s.quantized), "population": list(s.population or ()),
        "response": float(d.z), "scale": int(d.scale),
        "anchor_key": H.serialize_value(d.alpha).hex(),
    }


def frame_summary(result: FrameResult) -> dict:
    from collections import Counter
    all_records = [detection_record(d) for d in sorted(result.all_detections,
                                                       key=H._detection_sort_key)]
    edge_counts = Counter(e[2].name for e in result.window.edges)
    return {
        "name": result.name, "image_shape": result.image_shape, "rich": result.rich,
        "raw_lens_counts": dict(sorted(Counter(d.k for d in result.raw).items())),
        "bound_v1_counts": dict(sorted(Counter(d.k for d in result.bound_v1).items())),
        "tier_counts": {k: len(v) for k, v in sorted(result.tiers.items())},
        "emitted_kind_counts": dict(sorted(Counter(d.k for d in result.all_detections).items())),
        "window_nodes": len(result.window.nodes), "window_edges": len(result.window.edges),
        "spatial_nodes": len(result.spatial.nodes), "spatial_edges": len(result.spatial.edges),
        "hierarchy_off_nodes": len(result.hierarchy_off.nodes),
        "hierarchy_off_edges": len(result.hierarchy_off.edges),
        "hierarchy_on_nodes": len(result.hierarchy_on.nodes),
        "hierarchy_on_edges": len(result.hierarchy_on.edges),
        "edge_families": dict(sorted(edge_counts.items())),
        "skipped": result.skipped, "detections": all_records,
    }
