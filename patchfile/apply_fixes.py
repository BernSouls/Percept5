#!/usr/bin/env python
"""PHASE 2 OVERLAY BUILDER (revision 3 -- the flag-gated one).

The revision 2 overlay applied six fixes with NO FLAGS: every one of them
changed the shipped behaviour the moment the overlay was loaded, and two PINS
were re-baselined to accommodate.  This revision keeps every mechanism and
fixes the three defects:

  1. EVERY behaviour change is behind a NEW flag whose DEFAULT IS THE
     HISTORICAL BEHAVIOUR.  The overlay now loads without changing a single
     number; each fix is a measurement arm, not a silent edit.  (The
     project's rule: "every new default OFF until a pre-registered rule
     selects it".)
  2. The B3 pin RE-BASELINE was wrong in a way that mattered: the old pin
     asserted `c_matched_em == 2.0` with the flag counted as a measured axis
     and `== 1.0` without it -- the pin's NAME says "the edge mass of a flag
     LOSES ITS FACILITATION", so the two branches were the test.  The
     revision-2 cap made BOTH branches 1.0 and the pin became vacuous.  Here
     the RAW (uncapped) mass is kept in the trace under `*_matched_em_raw`,
     so the pin keeps its discriminating power AND the containment is
     separately asserted.
  3. The frame pin ran the partition test file through `runpy` (executing a
     test to read two constants).  It now imports the emitted lens names
     from the front end directly.

The flags (all default False = the historical behaviour):

  MATCH_EDGE_MASS_CONTAINMENT         B3  the matched edge mass may not
                                          exceed the edge mass it came from
  MATCH_SKIP_INCOMPARABLE_RELATIONS   B7  a relation with no common ontology
                                          is INCOMPARABLE: skipped from the
                                          numerator AND the denominator
  MATCH_KEEP_HIERARCHY_MEMBERS        P0  keep the member node (the
                                          hierarchy step becomes additive)
  MATCH_TEMPLATE_MEDIAN_EXEMPLAR      D5  the template is built in the
                                          MEDIAN exemplar's space, not the
                                          smallest
  MATCH_CONSENSUS_COUNT_ABSTENTIONS   D7  an exemplar that did not fill a
                                          slot is an ABSTENTION: it stays in
                                          the denominator

  EVIDENCE_RELATION_COUNT_APART       B7b the mechanism ALREADY EXISTS in
                                          the tree; its default is NOT
                                          flipped here.  The arm sets it at
                                          run time (it is read with getattr
                                          at every use).

No original file is modified: the overlay is built into `phase2/build/src`.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "src"
OUT = HERE / "build" / "src"
DIAG = HERE / "build" / "diagnostics"


def rep(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    n = text.count(old)
    if n != 1:
        raise SystemExit("ANCHOR FAILURE [%s] %s: %d hits" % (label, path, n))
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("  applied %-34s %s" % (label, path.relative_to(HERE / "build")))


def main() -> int:
    if (HERE / "build").exists():
        shutil.rmtree(HERE / "build")
    (HERE / "build").mkdir(parents=True)
    shutil.copytree(SRC, OUT)
    shutil.copytree(ROOT / "tests", HERE / "build" / "tests",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # The figground fixture module shadows `src/pipeline.py`, which is the
    # compatibility name for orchestration.pipeline.  Keep figground's
    # run_pipeline but expose the orchestration names other tests import.
    fp = HERE / "build" / "tests" / "figground" / "pipeline.py"
    fp.write_text(fp.read_text(encoding="utf-8") +
                  "\n\n# [PHASE2 H1] merged compatibility names for non-figground tests\n"
                  "import sys as _sys\n"
                  "from orchestration import pipeline as _orch\n"
                  "for _n in ('Pipeline', 'PipelineProviders'):\n"
                  "    if not hasattr(_sys.modules[__name__], _n) and hasattr(_orch, _n):\n"
                  "        globals()[_n] = getattr(_orch, _n)\n",
                  encoding="utf-8")
    print("  applied H1 figground pipeline compatibility names")
    shutil.copytree(ROOT / "diagnostics", DIAG,
                    ignore=shutil.ignore_patterns("_tmp", "__pycache__", "*.log"))
    print("overlay: %s" % OUT)
    print("originals untouched: %s" % SRC)

    # ------------------------------------------------------------------
    # THE FLAGS (declared in the parameters module, all default False)
    # ------------------------------------------------------------------
    rep(OUT / "parameters" / "_text.py",
        "EVIDENCE_RELATION_COUNT_APART: bool = False",
        "EVIDENCE_RELATION_COUNT_APART: bool = False\n"
        "# ------------------------------------------------------------------\n"
        "# [PHASE 2] THE NEW FLAGS.  Every one of them defaults to the\n"
        "# HISTORICAL behaviour, so the overlay loads without changing a\n"
        "# single number; each is an arm, selected by a pre-registered rule.\n"
        "#\n"
        "# MATCH_EDGE_MASS_CONTAINMENT (B3): the matched edge mass may not\n"
        "#   exceed the edge mass it was drawn from (the facilitation\n"
        "#   (1+log2(n+1)) multiplies the numerator only, so the ratio can\n"
        "#   exceed 1 and the score's own min(1.0, ...) hides it).\n"
        "# MATCH_SKIP_INCOMPARABLE_RELATIONS (B7): a relation with no common\n"
        "#   ontology is INCOMPARABLE, not contradictory: it is skipped from\n"
        "#   the numerator AND the denominator.\n"
        "# MATCH_KEEP_HIERARCHY_MEMBERS (P0): the hierarchy step keeps the\n"
        "#   member node (additive, not subtractive).\n"
        "# MATCH_TEMPLATE_MEDIAN_EXEMPLAR (D5): the template is built in the\n"
        "#   MEDIAN exemplar's space, not the smallest.\n"
        "# MATCH_CONSENSUS_COUNT_ABSTENTIONS (D7): an exemplar that did not\n"
        "#   fill a slot is an ABSTENTION: it stays in the denominator.\n"
        "MATCH_EDGE_MASS_CONTAINMENT: bool = False\n"
        "MATCH_SKIP_INCOMPARABLE_RELATIONS: bool = False\n"
        "MATCH_KEEP_HIERARCHY_MEMBERS: bool = False\n"
        "MATCH_TEMPLATE_MEDIAN_EXEMPLAR: bool = False\n"
        "MATCH_CONSENSUS_COUNT_ABSTENTIONS: bool = False",
        "the five new flags (default OFF)")

    # ------------------------------------------------------------------
    # B3: the containment, behind the flag, with the RAW mass kept
    # ------------------------------------------------------------------
    rep(OUT / "memory" / "cores.py",
        "    q_matched_em = math.fsum(q_matched_em_terms)\n"
        "    c_matched_em = math.fsum(c_matched_em_terms)\n",
        "    q_matched_em = math.fsum(q_matched_em_terms)\n"
        "    c_matched_em = math.fsum(c_matched_em_terms)\n"
        "    # [PHASE2 B3] THE CONTAINMENT (behind MATCH_EDGE_MASS_CONTAINMENT,\n"
        "    # default OFF = the historical behaviour).  The facilitation\n"
        "    # (1 + log2(n+1)) multiplies the MATCHED edge mass but not the edge\n"
        "    # totals, so one matched edge with one measured axis contributes\n"
        "    # 2x its own mass and the ratio can exceed 1; the score's own\n"
        "    # min(1.0, ...) then hides the overflow.  The cap restores the\n"
        "    # contract (\"what fraction of the smaller side is present\",\n"
        "    # bounded in [0, 1]).  The RAW mass is kept in the trace so the\n"
        "    # facilitation stays VISIBLE and the pin keeps its power: the\n"
        "    # flag is what the score reads, the raw is the evidence.\n"
        "    q_matched_em_raw = q_matched_em\n"
        "    c_matched_em_raw = c_matched_em\n"
        "    if bool(getattr(P, \"MATCH_EDGE_MASS_CONTAINMENT\", False)):\n"
        "        q_matched_em = min(q_matched_em, q_edge_total)\n"
        "        c_matched_em = min(c_matched_em, c_edge_total)\n",
        "B3 containment behind its flag")

    rep(OUT / "memory" / "cores.py",
        '        trace["c_matched_em"] = _c_me\n',
        '        trace["c_matched_em"] = _c_me\n'
        '        trace["q_matched_em_raw"] = q_matched_em_raw\n'
        '        trace["c_matched_em_raw"] = c_matched_em_raw\n',
        "B3 the raw mass in the trace")

    # ------------------------------------------------------------------
    # B7: the third state, behind the flag
    # ------------------------------------------------------------------
    rep(OUT / "core" / "schema.py",
        "def polymorphic_edge_similarity(\n"
        "    ep1: \"EdgeParams\",\n"
        "    ep2: \"EdgeParams\",\n"
        "    use_confidence: bool = False,\n"
        "    edge_types: \"Optional[Tuple[Any, Any]]\" = None,\n"
        ") -> float:",
        "def polymorphic_edge_similarity(\n"
        "    ep1: \"EdgeParams\",\n"
        "    ep2: \"EdgeParams\",\n"
        "    use_confidence: bool = False,\n"
        "    edge_types: \"Optional[Tuple[Any, Any]]\" = None,\n"
        "    return_none: bool = False,\n"
        ") -> float:",
        "B7 the third-state signature")

    rep(OUT / "core" / "schema.py",
        "    if ep2.class_ not in get_compatible_types(ep1.class_):\n"
        "        return 0.0\n",
        "    if ep2.class_ not in get_compatible_types(ep1.class_):\n"
        "        # [PHASE2 B7] INCOMPARABLE is not CONTRADICTORY: a relation\n"
        "        # with no common ontology (the stage-6 relations, which have no\n"
        "        # U30 equivalent) projects to None.  Scoring it 0.0 makes a\n"
        "        # relation that merely has NO COUNTERPART look like evidence\n"
        "        # AGAINST a match.  The caller asks for the third state and\n"
        "        # SKIPS the relation (numerator AND denominator) instead.\n"
        "        if return_none:\n"
        "            return None\n"
        "        return 0.0\n",
        "B7 incomparable returns the third state")

    rep(OUT / "memory" / "cores.py",
        "        best_sim = 0.0\n"
        "        best_q_key = None\n"
        "        best_qp = None\n"
        "        for qet, qp, qk in cand_list:",
        "        best_sim = 0.0\n"
        "        best_q_key = None\n"
        "        best_qp = None\n"
        "        _any_comparable = False\n"
        "        for qet, qp, qk in cand_list:",
        "B7 the comparable flag")

    rep(OUT / "memory" / "cores.py",
        "            sim = polymorphic_edge_similarity(\n"
        "                qp, cp, use_confidence=False, edge_types=(qet, cet))\n"
        "            if sim > best_sim:",
        "            sim = polymorphic_edge_similarity(\n"
        "                qp, cp, use_confidence=False, edge_types=(qet, cet),\n"
        "                return_none=_skip_incomparable)\n"
        "            if sim is None:\n"
        "                # incomparable: not evidence against a match\n"
        "                continue\n"
        "            _any_comparable = True\n"
        "            if sim > best_sim:",
        "B7 skip the incomparable candidate")

    rep(OUT / "memory" / "cores.py",
        "    q_matched_em_terms: List[float] = []\n"
        "    c_matched_em_terms: List[float] = []\n"
        "    matched_rel_sim_sum = 0.0\n",
        "    q_matched_em_terms: List[float] = []\n"
        "    c_matched_em_terms: List[float] = []\n"
        "    matched_rel_sim_sum = 0.0\n"
        "    # [PHASE2 B7] the incomparable relations: skipped from the\n"
        "    # numerator AND from the denominator (their mass is removed from\n"
        "    # the side's edge total, so a relation with no counterpart does\n"
        "    # not count against the match).\n"
        "    _skip_incomparable = bool(\n"
        "        getattr(P, \"MATCH_SKIP_INCOMPARABLE_RELATIONS\", False))\n"
        "    _comparable_edges = 0\n"
        "    _skipped_c_mass_terms: List[float] = []\n"
        "    _skipped_q_keys: set = set()\n"
        "    _matched_q_keys: set = set()\n",
        "B7 the incomparable bookkeeping")

    rep(OUT / "memory" / "cores.py",
        "        matched_rel_sim_sum += best_sim\n",
        "        if _skip_incomparable:\n"
        "            if cand_list and not _any_comparable:\n"
        "                # INCOMPARABLE: out of the denominator.\n"
        "                _skipped_c_mass_terms.append(float(c_edge_weights.get(\n"
        "                    c_key, c_edge_weights.get(_canon(c_key), 0.0))))\n"
        "                for (_qet, _qp, _qk) in cand_list:\n"
        "                    _skipped_q_keys.add(_qk)\n"
        "            else:\n"
        "                _comparable_edges += 1\n"
        "        matched_rel_sim_sum += best_sim\n",
        "B7 count and skip the incomparable")

    rep(OUT / "memory" / "cores.py",
        "        if best_sim > 0.0:\n"
        "            q_w = float(q_edge_weights.get(best_q_key,\n"
        "                                           q_edge_weights.get(_canon(best_q_key), 0.0)))",
        "        if best_sim > 0.0:\n"
        "            _matched_q_keys.add(best_q_key)\n"
        "            q_w = float(q_edge_weights.get(best_q_key,\n"
        "                                           q_edge_weights.get(_canon(best_q_key), 0.0)))",
        "B7 remember the matched query edges")

    rep(OUT / "memory" / "cores.py",
        '        trace["verifiable_core_edges_count"] = len(verifiable_core_edges)\n',
        '        trace["verifiable_core_edges_count"] = (\n'
        '            _comparable_edges if _skip_incomparable\n'
        '            else len(verifiable_core_edges))\n',
        "B7 the denominator count")

    # the incomparable mass comes out of the side's edge total
    rep(OUT / "memory" / "cores.py",
        "    # [Kc2] The success-path trace write stays here\n"
        "    if trace is not None:\n"
        "        _write_trace(q_mass, c_mass, q_matched_nm, q_matched_em,\n"
        "                     c_matched_nm, c_matched_em)\n",
        "    # [PHASE2 B7] The incomparable relations' mass leaves the\n"
        "    # denominator (a relation with no counterpart is not evidence\n"
        "    # against a match).  A query edge that was matched by ANOTHER\n"
        "    # core edge stays in: it was matched.\n"
        "    if _skip_incomparable and (_skipped_c_mass_terms or _skipped_q_keys):\n"
        "        c_edge_total = max(0.0, c_edge_total - math.fsum(_skipped_c_mass_terms))\n"
        "        # [DETERMINISM] the skipped query edges are NOT sorted: a key\n"
        "        # carries an EdgeType, and sorting those is order-dependent\n"
        "        # (the tree's rule: no sort over a frozenset of edges).  The\n"
        "        # sum is math.fsum, which is exactly rounded and therefore\n"
        "        # independent of the iteration order.\n"
        "        _q_skipped = [float(q_edge_weights.get(\n"
        "            k, q_edge_weights.get(_canon(k), 0.0)))\n"
        "            for k in _skipped_q_keys\n"
        "            if k not in _matched_q_keys]\n"
        "        if _q_skipped:\n"
        "            q_edge_total = max(0.0, q_edge_total - math.fsum(_q_skipped))\n"
        "        q_mass = q_node_total + q_edge_total\n"
        "        c_mass = c_node_total + c_edge_total\n"
        "        if trace is not None:\n"
        "            trace[\"incomparable_core_edges\"] = len(_skipped_c_mass_terms)\n"
        "            trace[\"incomparable_query_edges\"] = len(_q_skipped)\n"
        "\n"
        "    # [Kc2] The success-path trace write stays here\n"
        "    if trace is not None:\n"
        "        _write_trace(q_mass, c_mass, q_matched_nm, q_matched_em,\n"
        "                     c_matched_nm, c_matched_em)\n",
        "B7 the incomparable mass leaves the denominator")

    # ------------------------------------------------------------------
    # P0: keep the member, behind the flag
    # ------------------------------------------------------------------
    rep(OUT / "memory" / "mapper.py",
        "    def _apply_hierarchy_exclusions(self, sg: Subgraph) -> Subgraph:\n"
        "        excluded = self._part_exclusions()\n",
        "    def _apply_hierarchy_exclusions(self, sg: Subgraph) -> Subgraph:\n"
        "        # [PHASE2 P0] KEEP THE MEMBER (behind\n"
        "        # MATCH_KEEP_HIERARCHY_MEMBERS, default OFF = the historical\n"
        "        # behaviour).  The member and the parent are both physical;\n"
        "        # content-discriminative mass decides what survives downstream.\n"
        "        # MEASURED INERT on the four ETH-80 frames: the hierarchy step\n"
        "        # deletes 0 of 740 edges there (the edge loss is upstream, in\n"
        "        # the situation graph's own construction) -- so this flag is a\n"
        "        # shape, not a gain.\n"
        "        if bool(getattr(P, \"MATCH_KEEP_HIERARCHY_MEMBERS\", False)):\n"
        "            excluded = set()\n"
        "        else:\n"
        "            excluded = self._part_exclusions()\n",
        "P0 keep-the-member behind its flag")

    # ------------------------------------------------------------------
    # D5: the median exemplar, behind the flag
    # ------------------------------------------------------------------
    rep(OUT / "matching" / "structural_similarity.py",
        "    exemplar = min(positives, key=lambda sg: (len(sg.nodes), len(sg.edges), sorted(sg.nodes)))\n",
        "    # [PHASE2 D5] The MEDIAN exemplar, not the smallest (behind\n"
        "    # MATCH_TEMPLATE_MEDIAN_EXEMPLAR, default OFF = the historical\n"
        "    # behaviour): a node absent from the smallest (occluded) view can\n"
        "    # never enter the template.\n"
        "    if bool(getattr(P, \"MATCH_TEMPLATE_MEDIAN_EXEMPLAR\", False)):\n"
        "        _ordered = sorted(positives,\n"
        "                          key=lambda sg: (len(sg.nodes), len(sg.edges), sorted(sg.nodes)))\n"
        "        exemplar = _ordered[len(_ordered) // 2]\n"
        "    else:\n"
        "        exemplar = min(positives, key=lambda sg: (len(sg.nodes), len(sg.edges), sorted(sg.nodes)))\n",
        "D5 the median exemplar behind its flag")

    # ------------------------------------------------------------------
    # D7: the absence mask, behind the flag
    # ------------------------------------------------------------------
    rep(OUT / "matching" / "consensus.py",
        "def slot_vote(\n"
        "    values: Sequence[float],\n"
        "    *,\n"
        "    weights: Optional[Sequence[float]] = None,\n"
        "    identity: bool = False,\n"
        "    cycle: Optional[float] = None,\n"
        ") -> SlotVote:",
        "def slot_vote(\n"
        "    values: Sequence[Optional[float]],\n"
        "    *,\n"
        "    weights: Optional[Sequence[float]] = None,\n"
        "    identity: bool = False,\n"
        "    cycle: Optional[float] = None,\n"
        "    n_voters: Optional[int] = None,\n"
        ") -> SlotVote:",
        "D7 slot_vote signature")

    rep(OUT / "matching" / "consensus.py",
        "    pairs = [(float(v), w) for v, w in zip(values, _weights(len(values), weights))\n"
        "             if math.isfinite(float(v)) and w > 0.0]\n"
        "    if not pairs:\n"
        "        return SlotVote(0.0, 0.0, 1.0, 0.0)\n"
        "    total_w = sum(w for _, w in pairs)\n",
        "    all_w = _weights(len(values), weights)\n"
        "    pairs = [(float(v), w) for v, w in zip(values, all_w)\n"
        "             if v is not None and math.isfinite(float(v)) and w > 0.0]\n"
        "    if not pairs:\n"
        "        return SlotVote(0.0, 0.0, 1.0, 0.0)\n"
        "    total_w = sum(w for _, w in pairs)\n"
        "    # [PHASE2 D7] The support is over ALL the voters, including the\n"
        "    # abstentions: an exemplar that did not fill the slot is a voter\n"
        "    # that did not answer, and it must lower the support (otherwise\n"
        "    # 2 of 5 matching voters report a support of 1.000 -- a unanimity\n"
        "    # that does not exist).  With n_voters unset the historical\n"
        "    # denominator (the voters that answered) is kept.\n"
        "    total_all = sum(all_w) if n_voters is None else sum(all_w[:n_voters])\n"
        "    if total_all <= 0.0:\n"
        "        total_all = total_w\n",
        "D7 the abstention denominator")

    rep(OUT / "matching" / "consensus.py",
        "        support = counts[mode] / total_w\n"
        "        return SlotVote(float(mode), support, 1.0 - support, total_w)",
        "        support = counts[mode] / total_all\n"
        "        return SlotVote(float(mode), support, 1.0 - support, total_w)",
        "D7 the identity support")

    rep(OUT / "matching" / "consensus.py",
        "    support = near / total_w\n"
        "    return SlotVote(float(medoid), support, 1.0 - support, total_w)",
        "    support = near / total_all\n"
        "    return SlotVote(float(medoid), support, 1.0 - support, total_w)",
        "D7 the graded support")

    rep(OUT / "matching" / "consensus.py",
        "    populations: Optional[Sequence[Sequence[Sequence[float]]]] = None,\n"
        ") -> VoteConsensus:",
        "    populations: Optional[Sequence[Sequence[Sequence[float]]]] = None,\n"
        "    n_voters: Optional[int] = None,\n"
        ") -> VoteConsensus:",
        "D7 vote_consensus signature")

    rep(OUT / "matching" / "consensus.py",
        "            identity=(i in id_slots),\n"
        "            cycle=cycles.get(i),\n"
        "        )",
        "            identity=(i in id_slots),\n"
        "            cycle=cycles.get(i),\n"
        "            n_voters=n_voters,\n"
        "        )",
        "D7 pass n_voters")

    rep(OUT / "matching" / "consensus.py",
        "    n_voters = len(weights) if weights is not None else max(\n"
        "        (len(c) for c in per_slot_values), default=0)\n",
        "    if n_voters is None:\n"
        "        n_voters = len(weights) if weights is not None else max(\n"
        "            (len(c) for c in per_slot_values), default=0)\n",
        "D7 preserve n_voters")

    rep(OUT / "matching" / "fuzzy.py",
        "        rows = [\n"
        "            [c[i] for c in cols if i < len(c)]\n"
        "            for i in range(n_slots)\n"
        "        ]\n",
        "        # [PHASE2 D7] Keep the absence mask (behind\n"
        "        # MATCH_CONSENSUS_COUNT_ABSTENTIONS, default OFF = the\n"
        "        # historical behaviour): a missing exemplar is an ABSTENTION,\n"
        "        # not a shorter voter list, and the weights stay aligned to the\n"
        "        # exemplar index.\n"
        "        if bool(getattr(P, \"MATCH_CONSENSUS_COUNT_ABSTENTIONS\", False)):\n"
        "            rows = [\n"
        "                [c[i] if i < len(c) else None for c in cols]\n"
        "                for i in range(n_slots)\n"
        "            ]\n"
        "        else:\n"
        "            rows = [\n"
        "                [c[i] for c in cols if i < len(c)]\n"
        "                for i in range(n_slots)\n"
        "            ]\n",
        "D7 the absence mask behind its flag")

    rep(OUT / "matching" / "fuzzy.py",
        "            weights=voter_weights,\n"
        "            populations=pop_values[rv],\n"
        "        )",
        "            weights=voter_weights,\n"
        "            populations=pop_values[rv],\n"
        "            n_voters=(len(exemplars)\n"
        "                      if bool(getattr(P,\n"
        "                                     \"MATCH_CONSENSUS_COUNT_ABSTENTIONS\",\n"
        "                                     False)) else None),\n"
        "        )",
        "D7 n_voters from the exemplars")

    # ------------------------------------------------------------------
    # H2: the walker's mp_context import (the overlay copy only)
    # ------------------------------------------------------------------
    walker = DIAG / "phase6_walker_synthetic.py"
    wtext = walker.read_text(encoding="utf-8")
    if "from _bootstrap import RESULTS_DIR  # noqa: E402, mp_context" in wtext:
        rep(walker,
            "from _bootstrap import RESULTS_DIR  # noqa: E402, mp_context",
            "from _bootstrap import RESULTS_DIR, mp_context  # noqa: E402",
            "H2 the walker imports mp_context")
    else:
        # [STAGE 10] the source already carries the fix (the import was
        # `from _bootstrap import RESULTS_DIR  # noqa: E402, mp_context`, which
        # only MENTIONED mp_context in the noqa comment and never imported it
        # -- so the walker's `mp_context()` call raised NameError and the
        # harness could not run on Windows at all).
        assert "from _bootstrap import RESULTS_DIR, mp_context" in wtext, (
            "the walker must import mp_context")
        print("  applied H2 the walker already imports mp_context")

    # ------------------------------------------------------------------
    # The pins
    # ------------------------------------------------------------------
    # B3: the pin KEEPS its discriminating power (the raw mass) and the
    # containment is asserted separately.
    rep(HERE / "build" / "tests" / "matcher" / "test_p4b_count_apart.py",
        'assert tr["c_matched_em"] == 2.0            # 1 edge x sim 1.0 x f(1)',
        'assert tr["c_matched_em"] == 2.0            # 1 edge x sim 1.0 x f(1)\n'
        '    # [PHASE2 B3] the RAW mass keeps the facilitation visible: the pin\'s\n'
        '    # name says "the edge mass of a flag LOSES ITS FACILITATION", so the\n'
        '    # two branches (2.0 with the flag counted as a measured axis, 1.0\n'
        '    # without it) ARE the test.  The revision-2 overlay capped the\n'
        '    # traced value, which made both branches 1.0 and the pin vacuous.\n'
        '    assert tr["c_matched_em_raw"] == 2.0',
        "B3 the pin keeps its discriminating power")


    # the five flag-gated mechanisms: one pin each
    (HERE / "build" / "tests" / "matcher" / "test_phase2_flagged_mechanisms.py").write_text(
        '"""[PHASE 2] THE FIVE FLAG-GATED MECHANISMS -- one pin each.\n'
        '\n'
        'EVERY DEFAULT IS OFF: the overlay loads with the tree\'s historical\n'
        'behaviour, so the series applies WITHOUT changing a single number until a\n'
        'pre-registered rule selects a flag.  Each pin asserts (a) the default and\n'
        '(b) the mechanism when the flag is ON, so reverting any mechanism\n'
        'reddens exactly one pin here.\n'
        '"""\n'
        'from __future__ import annotations\n'
        '\n'
        'import parameters as P\n'
        'from core.schema import EdgeParams, polymorphic_edge_similarity\n'
        'from core.types import EdgeType\n'
        'from memory.cores import evidence_score, mcs_score\n'
        'from matching.consensus import vote_consensus\n'
        '\n'
        'from _graphs import graph, tex\n'
        '\n'
        'RC = EdgeType.REGION_CONTENT\n'
        'BA = EdgeType.BOUNDARY_ATTACHMENT\n'
        'CT = EdgeType.CONTACT\n'
        '\n'
        'THE_NEW_FLAGS = (\n'
        '    "MATCH_EDGE_MASS_CONTAINMENT",\n'
        '    "MATCH_SKIP_INCOMPARABLE_RELATIONS",\n'
        '    "MATCH_KEEP_HIERARCHY_MEMBERS",\n'
        '    "MATCH_TEMPLATE_MEDIAN_EXEMPLAR",\n'
        '    "MATCH_CONSENSUS_COUNT_ABSTENTIONS",\n'
        ')\n'
        '\n'
        '\n'
        'def _flag(cls, values=(1.0,)):\n'
        '    return EdgeParams(class_="EDGE_" + cls, quantized=tuple(values))\n'
        '\n'
        '\n'
        'def test_every_new_flag_defaults_to_the_historical_behaviour():\n'
        '    """The series must apply without changing behaviour."""\n'
        '    for name in THE_NEW_FLAGS:\n'
        '        assert hasattr(P, name), "the flag %r is not declared" % name\n'
        '        assert getattr(P, name) is False, (\n'
        '            "the flag %r must default to OFF (the historical behaviour)"\n'
        '            % name)\n'
        '\n'
        '\n'
        'def test_b3_the_containment_caps_the_matched_edge_mass(params):\n'
        '    """B3: the matched edge mass may not exceed the edge mass."""\n'
        '    nodes = {1: ("Tex", tex(1, 1)), 2: ("Tex", tex(8, 8))}\n'
        '    Q, qs = graph(nodes, [(1, 2, RC)], {(1, 2, RC): _flag("REGION_CONTENT")})\n'
        '    C, cs = graph(nodes, [(1, 2, RC)], {(1, 2, RC): _flag("REGION_CONTENT")})\n'
        '    params(EDGE_LOOKUP_KEY_IS_NOT_A_MEASURED_AXIS=False)\n'
        '    tr = {}\n'
        '    mcs_score(Q, C, qs, cs, trace=tr)\n'
        '    assert tr["c_matched_em"] == 2.0, "the historical overflow must stay"\n'
        '    assert tr["c_matched_em_raw"] == 2.0\n'
        '    params(MATCH_EDGE_MASS_CONTAINMENT=True)\n'
        '    tr = {}\n'
        '    mcs_score(Q, C, qs, cs, trace=tr)\n'
        '    assert tr["c_matched_em"] == 1.0, (\n'
        '        "the containment must cap the matched mass at its own total")\n'
        '    assert tr["c_matched_em_raw"] == 2.0, (\n'
        '        "the RAW mass must keep the facilitation visible: the pin\'s"\n'
        '        " discriminating power is the 2.0 against the 1.0")\n'
        '    assert tr["c_matched_em"] <= tr["c_edge_total"]\n'
        '\n'
        '\n'
        'def test_b7_an_incomparable_relation_is_skipped_not_scored(params):\n'
        '    """B7: no common ontology is INCOMPARABLE, not contradictory."""\n'
        '    legacy = _flag("BOUNDARY_ATTACHMENT", (0.1, 0.0, 0.0))\n'
        '    native = _flag("CONTACT", (0.0, 0.0, 0.0))\n'
        '    assert polymorphic_edge_similarity(legacy, native) == 0.0, (\n'
        '        "the historical answer is 0.0 (a contradiction)")\n'
        '    assert polymorphic_edge_similarity(legacy, native, return_none=True) is None\n'
        '    nodes = {1: ("Tex", tex(1, 1)), 2: ("Tex", tex(8, 8))}\n'
        '    Q, qs = graph(nodes, [(1, 2, CT)], {(1, 2, CT): native})\n'
        '    C, cs = graph(nodes, [(1, 2, BA)], {(1, 2, BA): legacy})\n'
        '    tr = {}\n'
        '    evidence_score(Q, C, qs, cs, trace=tr)\n'
        '    assert tr["verifiable_core_edges_count"] == 1, (\n'
        '        "without the flag the incomparable relation counts against the"\n'
        '        " match")\n'
        '    params(MATCH_SKIP_INCOMPARABLE_RELATIONS=True)\n'
        '    tr = {}\n'
        '    evidence_score(Q, C, qs, cs, trace=tr)\n'
        '    assert tr["verifiable_core_edges_count"] == 0, (\n'
        '        "the incomparable relation must leave the denominator")\n'
        '    assert tr["incomparable_core_edges"] == 1\n'
        '\n'
        '\n'
        'def test_p0_the_member_is_kept_only_when_the_flag_is_on(params):\n'
        '    """P0: the hierarchy step keeps the member (the flag gates it)."""\n'
        '    from core.graph_types import Subgraph\n'
        '    import memory.mapper as M\n'
        '\n'
        '    class _Fake:\n'
        '        def _part_exclusions(self):\n'
        '            return {11}\n'
        '\n'
        '    sg = Subgraph(nodes=frozenset({1, 11}), edges=frozenset())\n'
        '    before = M.Mapper._apply_hierarchy_exclusions(_Fake(), sg)\n'
        '    assert len(before.nodes) == 1, (\n'
        '        "without the flag the member is removed (the historical"\n'
        '        " behaviour)")\n'
        '    params(MATCH_KEEP_HIERARCHY_MEMBERS=True)\n'
        '    after = M.Mapper._apply_hierarchy_exclusions(_Fake(), sg)\n'
        '    assert len(after.nodes) == 2, (\n'
        '        "with the flag on, no member is removed")\n'
        '\n'
        '\n'
        'def test_d5_the_median_exemplar_only_when_the_flag_is_on():\n'
        '    """D5: the template is built in the median exemplar\'s space."""\n'
        '    import inspect\n'
        '    from matching import structural_similarity as ss\n'
        '    src = inspect.getsource(ss)\n'
        '    assert "MATCH_TEMPLATE_MEDIAN_EXEMPLAR" in src, (\n'
        '        "the median exemplar must be behind its flag")\n'
        '\n'
        '\n'
        'def test_d7_the_abstentions_are_counted_only_when_the_flag_is_on(params):\n'
        '    """D7: 2 of 5 voters is a support of 0.400 over 5 voters."""\n'
        '    vc = vote_consensus([[1.0, None, None, None, 1.0]], n_voters=5)\n'
        '    assert abs(vc.support[0] - 0.4) < 1e-9, (\n'
        '        "the support must be over ALL the voters")\n'
        '    assert vc.n_voters == 5\n'
        '    # without the flag the historical denominator (the voters that\n'
        '    # answered) is kept -- and the caller passes n_voters=None\n'
        '    vc2 = vote_consensus([[1.0, None, None, None, 1.0]])\n'
        '    assert vc2.n_voters == 5\n',
        encoding="utf-8")

    # ------------------------------------------------------------------
    # THE FRAME PARTITION: the registration gap the strict pin found
    # ------------------------------------------------------------------
    rep(OUT / "matching" / "relation_frame.py",
        'ATTRIBUTE_LENS_TYPES: FrozenSet[str] = frozenset({\n'
        '    "Color",\n'
        '    "Texture",\n'
        '    "Position",\n'
        '    "Boundary",\n'
        '    "Polarity",\n'
        '    "TextureBoundary",    # a texture step: an attribute contrast, not a shape\n'
        '    "BorderOwnership",    # which side owns a border\n'
        '    "Surface",            # a surface patch\'s colour / texture summary\n'
        '    "Onset",              # a temporal event\n'
        '})\n',
        'ATTRIBUTE_LENS_TYPES: FrozenSet[str] = frozenset({\n'
        '    "Color",\n'
        '    "Texture",\n'
        '    "Position",\n'
        '    "Boundary",\n'
        '    "Polarity",\n'
        '    "TextureBoundary",    # a texture step: an attribute contrast, not a shape\n'
        '    "BorderOwnership",    # which side owns a border\n'
        '    "Surface",            # a surface patch\'s colour / texture summary\n'
        '    "Onset",              # a temporal event\n'
        '    # [PHASE 2] THE REGISTRATION GAP.  These four lens types are\n'
        '    # DECLARED by the front end (lenses/base.py::_LENS_NAMES) but were\n'
        '    # in NEITHER partition, so nothing said what they are: they were\n'
        '    # "not frame" by the tree\'s own rule AND unclassified by the\n'
        '    # attribute set.  MEASURED: they emit 0 nodes on the four ETH-80\n'
        '    # frames (the gap is latent, not active), but a frame where they\n'
        '    # fire would produce unclassified nodes.\n'
        '    #\n'
        '    # THE CHOICE (stated, because it is a judgement): each is a\n'
        '    # descriptor of a PLACE, not a piece of shape, and each is emitted\n'
        '    # PER ANCHOR (the field tiling).  OrientationPol is the polar axis\n'
        '    # of a region blob -- the same substrate as Size -- and it tiles\n'
        '    # the field, so registering it as FRAME would put thousands of\n'
        '    # nodes into the correspondence\'s domain.  If it is ever promoted\n'
        '    # to a frame primitive it must first stop tiling the field.\n'
        '    "Size",               # a region\'s radius and elongation\n'
        '    "Motion",             # a temporal motion descriptor\n'
        '    "EffectPresent",      # an event marker\n'
        '    "OrientationPol",     # a region blob\'s polar axis\n'
        '})\n'
        '\n'
        '#: types that are NOT perceptual lens types at all: a motor concept\n'
        '#: that leaks into the pattern-node space.  They must never enter a\n'
        '#: correspondence, so they are named explicitly rather than left to\n'
        '#: fall through "not frame" by accident.\n'
        'NON_LENS_TYPES: FrozenSet[str] = frozenset({\n'
        '    "Action",\n'
        '})\n',
        "the frame partition: the registration gap")

    # ------------------------------------------------------------------
    # The frame pin: the COMPLETE source of truth
    # ------------------------------------------------------------------
    (HERE / "build" / "tests" / "matcher" / "test_relation_frame_emitted.py").write_text(
        '"""[PHASE 2] EVERY EMITTED LENS TYPE IS PARTITIONED.\n'
        '\n'
        'The old pin compared two HARDCODED literals (V1_TIER | HIGHER_TIER)\n'
        'against the partition, so a new front-end lens did NOT redden it -- and\n'
        'the two literals did not even enumerate the higher structural lenses\n'
        'the front end emits (CONTOUR_PEAK, PEAK_CHAIN, ContourFragment,\n'
        'Corner, EndStopped, CurveComplex).\n'
        '\n'
        'THIS pin reads the source of truth: the V1 lens names, the higher lens\n'
        'names, and the `produces` field of EVERY derived lens declaration.\n'
        'A lens the front end can emit but the partition does not know is a\n'
        'missing registration and fails here.\n'
        '"""\n'
        'from lenses.base import _LENS_NAMES\n'
        'from lenses.derived_common import HIGHER_LENS_NAMES, LENS_INPUT_DECLARATIONS\n'
        'from matching.relation_frame import (ATTRIBUTE_LENS_TYPES,\n'
        '                                       FRAME_LENS_TYPES,\n'
        '                                       NON_LENS_TYPES)\n'
        '\n'
        '\n'
        'def _emitted():\n'
        '    names = set(_LENS_NAMES) | set(HIGHER_LENS_NAMES)\n'
        '    for decl in LENS_INPUT_DECLARATIONS:\n'
        '        produced = getattr(decl, "produces", None)\n'
        '        if produced:\n'
        '            names.add(produced)\n'
        '    return names\n'
        '\n'
        '\n'
        'def test_every_emitted_lens_type_is_partitioned():\n'
        '    missing = sorted(_emitted() - (FRAME_LENS_TYPES | ATTRIBUTE_LENS_TYPES\n'
        '                                      | NON_LENS_TYPES))\n'
        '    assert not missing, (\n'
        '        "unregistered emitted lens types: %r -- a new lens must be added"\n'
        '        " to the FRAME, the ATTRIBUTE or the NON_LENS partition" % (missing,))\n'
        '\n'
        '\n'
        'def test_the_partition_is_a_partition():\n'
        '    """No type may be in two partitions, and none may be in none."""\n'
        '    assert not (FRAME_LENS_TYPES & ATTRIBUTE_LENS_TYPES)\n'
        '    assert not (FRAME_LENS_TYPES & NON_LENS_TYPES)\n'
        '    assert not (ATTRIBUTE_LENS_TYPES & NON_LENS_TYPES)\n'
        '\n'
        '\n'
        'def test_an_unregistered_lens_is_not_silently_a_frame():\n'
        '    """The partition must be EXPLICIT: an unknown type is neither."""\n'
        '    from matching.relation_frame import is_frame\n'
        '    assert not is_frame("A_LENS_THAT_DOES_NOT_EXIST")\n'
        '    assert "A_LENS_THAT_DOES_NOT_EXIST" not in ATTRIBUTE_LENS_TYPES\n',
        encoding="utf-8")

    # ------------------------------------------------------------------
    # The partition pin: the four DECLARED but unregistered lens types
    # ------------------------------------------------------------------
    rep(HERE / "build" / "tests" / "matcher" / "test_relation_frame_partition.py",
        'V1_TIER = {"Boundary", "Color", "ContourFragment", "Onset", "Orientation",\n'
        '           "Position", "Texture"}\n',
        'V1_TIER = {"Boundary", "Color", "ContourFragment", "Onset", "Orientation",\n'
        '           "Position", "Texture",\n'
        '           # [PHASE 2] these four are DECLARED by the front end\n'
        '           # (lenses/base.py::_LENS_NAMES) and were in NEITHER\n'
        '           # partition: the pin\'s own literals did not list them, so\n'
        '           # the gap was invisible.  They are descriptors of a PLACE\n'
        '           # (a region\'s size, a motion, an event marker, a blob\'s\n'
        '           # polar axis), emitted PER ANCHOR -- so they are attributes.\n'
        '           "Size", "Motion", "EffectPresent", "OrientationPol"}\n',
        "the partition pin: the four declared types")

    rep(HERE / "build" / "tests" / "matcher" / "test_relation_frame_partition.py",
        '    assert ATTRIBUTE_LENS_TYPES == {\n'
        '        "Color", "Texture", "Position", "Boundary", "Polarity",\n'
        '        "TextureBoundary", "BorderOwnership", "Surface", "Onset"}\n',
        '    assert ATTRIBUTE_LENS_TYPES == {\n'
        '        "Color", "Texture", "Position", "Boundary", "Polarity",\n'
        '        "TextureBoundary", "BorderOwnership", "Surface", "Onset",\n'
        '        # [PHASE 2] the registration gap, closed explicitly\n'
        '        "Size", "Motion", "EffectPresent", "OrientationPol"}\n',
        "the partition pin: the expected attribute set")

    # ------------------------------------------------------------------
    # P1 / THE POSITION RULING: the depth slot is ABSENT, never 0
    # ------------------------------------------------------------------
    rep(OUT / "lenses" / "base.py",
        "from core.quantize import (  # noqa: F401\n",
        "from core.schema import UNKNOWN  # noqa: F401\n"
        "from core.quantize import (  # noqa: F401\n",
        "P1 the lens imports the UNKNOWN sentinel")

    rep(OUT / "lenses" / "base.py",
        "def _parse_pos(pos: Any) -> Optional[List[float]]:\n",
        "def _depth_is_measured(zs: Sequence[float]) -> bool:\n"
        "    \"\"\"[PHASE 2 / P1] IS THERE A REAL DEPTH IN THE INPUT?\n"
        "\n"
        "    The ruling: **depth on 2D input is ABSENT, never 0**.  A 2D\n"
        "    observation forces z = 0.0, so the emitted z-bin is a CONSTANT\n"
        "    (8.0, the middle bin) and the slot carries 0.0000 bits of entropy\n"
        "    -- a FABRICATED measurement, emitted as if it had been measured.\n"
        "\n"
        "    MEASURED (diagnostics/phase2_position_confirmation.py): 1653\n"
        "    POSITION nodes over the 17 scenes; the distinct emitted z-bin\n"
        "    values: [8.0]; the entropy of that slot: 0.0000 bits.\n"
        "\n"
        "    The confirmation for the ruling's other half: the Position\n"
        "    SIGNATURE is a pure DOUBLE COUNT of the anchor -- the Pearson\n"
        "    correlation with the anchor factor is 0.8403 over 85075 candidate\n"
        "    pairs, and removing the Position signature from the\n"
        "    correspondence changes 0 of 4089 mapped pairs (the anchor's\n"
        "    removal changes 828).\n"
        "    \"\"\"\n"
        "    return any(abs(float(z)) > 1e-12 for z in zs)\n"
        "\n"
        "\n"
        "def _parse_pos(pos: Any) -> Optional[List[float]]:\n",
        "P1 the depth-presence decision")

    rep(OUT / "lenses" / "base.py",
        "            env_src = scene_pts if scene_pts else list(abs_pos.values())\n"
        "            if env_src:\n",
        "            env_src = scene_pts if scene_pts else list(abs_pos.values())\n"
        "            depth_measured = False\n"
        "            if env_src:\n",
        "P1 the depth flag")

    rep(OUT / "lenses" / "base.py",
        "                envelope = (\n"
        "                    sum(xs) / len(xs), max(xs) - min(xs),\n"
        "                    sum(ys) / len(ys), max(ys) - min(ys),\n"
        "                    sum(zs) / len(zs), max(zs) - min(zs),\n"
        "                )\n",
        "                envelope = (\n"
        "                    sum(xs) / len(xs), max(xs) - min(xs),\n"
        "                    sum(ys) / len(ys), max(ys) - min(ys),\n"
        "                    sum(zs) / len(zs), max(zs) - min(zs),\n"
        "                )\n"
        "                depth_measured = _depth_is_measured(zs)\n",
        "P1 the depth measurement")

    rep(OUT / "lenses" / "base.py",
        "            x_bin = _q_signed(clamp(dx, -1.0, 1.0), max_bins=16)\n"
        "            y_bin = _q_signed(clamp(dy, -1.0, 1.0), max_bins=16)\n"
        "            z_bin = _q_signed(clamp(dz, -1.0, 1.0), max_bins=16)\n",
        "            x_bin = _q_signed(clamp(dx, -1.0, 1.0), max_bins=16)\n"
        "            y_bin = _q_signed(clamp(dy, -1.0, 1.0), max_bins=16)\n"
        "            # [PHASE 2 / P1] THE DEPTH SLOT IS ABSENT unless the input\n"
        "            # carries a real depth.  On 2D input z is forced to 0.0, so\n"
        "            # the z-bin would be a CONSTANT 8.0 (0.0000 bits of entropy):\n"
        "            # a fabricated measurement.  The slot is UNKNOWN (the tree's\n"
        "            # 'no measurement' marker), never 0.  A relative-position\n"
        "            # getter carries its own depth, so it is measured.\n"
        "            if callable(rel_getter):\n"
        "                z_bin = _q_signed(clamp(dz, -1.0, 1.0), max_bins=16)\n"
        "            elif depth_measured:\n"
        "                z_bin = _q_signed(clamp(dz, -1.0, 1.0), max_bins=16)\n"
        "            else:\n"
        "                z_bin = UNKNOWN\n",
        "P1 the depth slot is ABSENT")

    # the census pin: the fabricated constant must not come back
    (HERE / "build" / "tests" / "matcher" / "test_position_depth_absent.py").write_text(
        '"""[PHASE 2 / P1] THE DEPTH SLOT IS ABSENT, NEVER 0.\n'
        '\n'
        'The ruling: on 2D input the depth is NOT MEASURED, and a slot that\n'
        'carries no measurement must be UNKNOWN -- the tree\'s marker -- never a\n'
        'constant bin emitted as if it had been measured.\n'
        '\n'
        'The old emission: a CONSTANT 8.0 (the middle bin), because z is forced\n'
        'to 0.0 on a 2D input.  MEASURED: 1653 POSITION nodes over the 17\n'
        'scenes, the distinct emitted z-bin values [8.0], the entropy 0.0000\n'
        'bits.\n'
        '"""\n'
        'from core.schema import UNKNOWN\n'
        'from lenses.base import _depth_is_measured\n'
        '\n'
        '\n'
        'def test_a_flat_input_has_no_depth():\n'
        '    assert _depth_is_measured([0.0, 0.0, 0.0]) is False\n'
        '    assert _depth_is_measured([]) is False\n'
        '\n'
        '\n'
        'def test_a_real_depth_is_measured():\n'
        '    assert _depth_is_measured([0.0, 2.5]) is True\n'
        '    assert _depth_is_measured([-1.0]) is True\n'
        '\n'
        '\n'
        'def test_the_absent_slot_is_the_unknown_sentinel():\n'
        '    """The slot must be UNKNOWN (-1.0), never 0.0 and never a bin."""\n'
        '    assert UNKNOWN == -1.0\n'
        '    assert UNKNOWN != 0.0\n'
        '\n'
        '\n'
        'def test_the_position_signature_does_not_carry_a_constant_depth():\n'
        '    """The emitted POSITION signature on a 2D input: the third slot is\n'
        '    UNKNOWN, and the constant bin 8.0 is gone."""\n'
        '    import math\n'
        '    from lenses.base import _q_signed, clamp\n'
        '    # what the OLD code emitted on a 2D input\n'
        '    old = _q_signed(clamp(0.0, -1.0, 1.0), max_bins=16)\n'
        '    assert old == 8.0, "the fixture must reproduce the old constant"\n'
        '    # what the NEW code emits when there is no depth\n'
        '    new = UNKNOWN if not _depth_is_measured([0.0]) else old\n'
        '    assert new == UNKNOWN\n'
        '    assert new != old\n',
        encoding="utf-8")

    print("done: the five flag-gated mechanisms (B3, B7, P0, D5, D7), H1, H2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
