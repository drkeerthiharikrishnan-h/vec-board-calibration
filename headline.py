"""Assemble a Virtual Embryo Challenge headline from veckit raw metrics, the way the board does.

veckit (pip install veckit; pinned 0.1.1, commit 46d41e6) emits raw metrics only. The board adds: a 10 % stage
subsample, a split-half ceiling, a floor model, the hyperbolic skill map and the task weights. This file is the
protocol in code form; every constant is backed by a board record in weight_reproduction_checks.json.

    from headline import WEIGHTS, n_subsample, emulate_split, skills_and_headline
    raw = {...}            # veckit raw metrics for one prediction on one seed
    anchors = {...}        # {metric: {"floor": f, "ceiling": c}} -- published per-board anchors, or your replica's
    skills_and_headline(raw, anchors, WEIGHTS["T1"])
"""
import numpy as np
from veckit.common import core_metrics as CM          # pinned organisers' code: skill(), split_half()

WEIGHTS = {  # percent; sum to 100 per task
    "T1": {"de_score": 25.0, "de_direction": 25.0, "mmd_u": 30.0, "variogram": 20.0},
    "T2": {"de_score": 12.5, "de_direction": 12.5, "mmd_u": 15.0, "variogram": 10.0,
           "d2_shape": 25 / 3, "occupancy_dice": 25 / 3, "scale_log_ratio": 25 / 3, "neighborhood_mmd": 25.0},
    "T3": {"de_score": 30.0, "de_direction": 25.0, "severity_slope": 25.0, "mmd_u": 12.0, "variogram": 8.0},
}
LOWER_IS_BETTER = {"mmd_u", "variogram", "d2_shape", "neighborhood_mmd"}
TWO_SIDED = {"scale_log_ratio", "severity_slope"}        # 0 is ideal; skill is taken on |value|
FLOOR_MODEL = {"T1": "copy_last", "T2": "copy_last", "T3": "wt_identity"}
SUBSAMPLE_FRAC = 0.10


def n_subsample(n):
    """round(0.1 n): reproduces every published ref/truth count (17057->1706, 53742->5374, 24826->2483, 13295->1330, 58716->5872)."""
    return int(round(SUBSAMPLE_FRAC * n))


def emulate_split(n_ref, n_target, seed):
    """One RNG stream per seed: reference subsample first, then target subsample, then split_half of the target
    subsample. First half = the truth a submission is scored against, second half = ceiling input (which half is
    which is an assumption; the two have equal size for even n)."""
    rng = np.random.default_rng(seed)
    ref_idx = np.sort(rng.choice(n_ref, n_subsample(n_ref), replace=False))
    tgt_sub = np.sort(rng.choice(n_target, n_subsample(n_target), replace=False))
    h1, h2 = CM.split_half(len(tgt_sub), seed)
    return ref_idx, tgt_sub[h1], tgt_sub[h2]


def skill_value(metric, value, floor, ceiling):
    if value is None or floor is None or ceiling is None: return 0.0
    v, f, c = float(value), float(floor), float(ceiling)
    if not np.all(np.isfinite([v, f, c])): return 0.0
    s = CM.skill(abs(v), abs(f), abs(c), lower_is_better=True) if metric in TWO_SIDED \
        else CM.skill(v, f, c, lower_is_better=(metric in LOWER_IS_BETTER))
    return 0.0 if not np.isfinite(s) else float(s)


def skills_and_headline(raw, anchors, weights):
    """Per-metric skill (0-100) and headline = sum_k w_k * skill_k / 100. Missing metric -> skill 0."""
    out, h = {}, 0.0
    for k, w in weights.items():
        a = anchors.get(k) or {}
        s = 100 * skill_value(k, raw.get(k), a.get("floor"), a.get("ceiling"))
        out[k] = round(s, 4); h += w * s / 100.0
    out["headline"] = round(h, 4)
    return out
