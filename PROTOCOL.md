# PROTOCOL — how the board turns veckit raw metrics into a headline, and how well a local replica tracks it

All statements below were checked against our own board records (per-metric skills and headlines returned by the
submission API) or against the organisers' pinned scorer. Scorer: `veckit` 0.1.1, commit
`46d41e63f42a9aab815db20b742feeccd249cb17`. Published per-board anchors: the challenge `panels/index.json`.

## 1. Weights (percent of headline)

| task | weights | evidence |
|---|---|---|
| T1 | de_score 25 · de_direction 25 · mmd_u 30 · variogram 20 | recomputes our R1 record 57.6485 → 57.6485 |
| T2 | expression: de_score 12.5, de_direction 12.5 · distribution: mmd_u 15, variogram 10 · shape: d2_shape 25⁄3, occupancy_dice 25⁄3, scale_log_ratio 25⁄3 · local: neighborhood_mmd 25 | 5 of 8 T2 records reproduce to 4 dp (HX1, HX2, HX3, HI2, EI2); HX1→HX3 differ only in scale_log_ratio and pin w_scale = 8.333; EI2 pins w_d2 = w_dice = 8.333 |
| T3 | recovery: de_score 30 · direction: de_direction 25 · magnitude: severity_slope 25 · distribution: mmd_u 12, variogram 8 | 8 of 8 T3 records reproduce to 4 dp (an equal 10/10 split leaves residuals 0.013–0.035) |

The group weights are on the evaluation page; the *within-group* splits (3:2 for distribution in every task; equal thirds for shape) are what the records pin down. See `weight_reproduction_checks.json`.

**Open discrepancy.** Three T2 records — HI1 (published 50.7271, recomputed 52.0077), HI3 (47.7366 vs 49.8550), EI1 (54.4216 vs 55.2157) — do not reproduce under any fixed weight scheme we tried (equal-within-group, flat, 3:2). The other five T2 records and all 21 T1/T3 records do. Possible causes we cannot test from disk: the per-metric skills were captured from a different scoring pass than the headline, or a board-side term outside the published metric list. If you hold records that reproduce or fail in the same way, please open an issue.

## 2. Skill map

`skill = common.core_metrics.skill(value, floor, ceiling, lower_is_better)` — hyperbolic, 0.5 at the floor, 1.0 at the ceiling, clipped above, compressing smoothly toward 0 below the floor. Higher-is-better: de_score, de_direction, occupancy_dice. Lower-is-better: mmd_u, variogram, d2_shape, neighborhood_mmd. Two-sided on |value| (0 is ideal): scale_log_ratio, severity_slope. A missing / NaN metric contributes skill 0. Unit checks with the published anchors on T1:val, T2:heart:val_extrap, T3:gata4: value = floor → 50.0, value = ceiling → 100.0, beyond ceiling → 100.0, all missing → 0.0; severity_slope ±0.0088 → identical skill.

## 3. Emulated evaluation protocol (per seed)

1. `rng = numpy.random.default_rng(seed)`.
2. Reference subsample `rng.choice(n_ref, round(0.1·n_ref), replace=False)`, then target subsample `round(0.1·n_tgt)` from the same stream. `round(0.1·n)` reproduces every published count: E9.5 RNA 17057 → 1706; heart E9.5 53742 → 5374; E8.75 24826 → 2483; E7.25 13295 → 1330; E8.25_late 58716 → 5872.
3. `split_half(n, seed)`: first half = truth the submission is scored against; second half = ceiling input. (Which half is which is unverifiable; both halves have equal size for even n.)
4. Floor = `copy_last` (T1/T2: the reference subsample, with reference = itself) or `wt_identity` (T3); ceiling = the other truth half against the truth half with the real reference.
5. Metric RNG seed = the same seed. Everything is computed by the pinned veckit functions; the only re-implemented piece in our replica is a cache of the truth-side DE gene selection, verified bit-exact against veckit (`max |diff| = 0.0` over 14 keys on T1, 23 keys on T2).

Anchor tables for the two released-only replicas (R0: E8.5 → E9.5; H2: heart E8.75 → E9.5), 5 seeds, with the floor/ceiling re-scored under their own and under mean anchors, are in `anchor_validation_released_replicas.json`. Re-scoring a floor file under *mean* anchors gives 48.7–50.6 across seeds and a ceiling half 97.1–100: that spread is the single-draw noise of the board.

## 4. The calibration set (`calibration_points.csv`)

29 distinct prediction files (unique sha256) scored on five validation boards, each with: the board headline and per-metric skills as returned by the API; the local replica's 5-seed mean ± sd headline and per-metric skills; submission id and date. The local replica is the **exact board geometry** — same reference and target stages (the P2 validation targets, after opt-in), same 498/500-gene panels, the published anchors. What it cannot reproduce is the board's private subsample draw.

| board | n | local − board, mean ± sd | range | rank concordance (Spearman) |
|---|---|---|---|---|
| T1:val | 13 | −0.13 ± 0.34 | −0.72 … +0.35 | 1.00 |
| T2:heart:val_extrap | 3 | +0.05 ± 0.44 | −0.44 … +0.41 | 1.00 |
| T2:heart:val_interp | 3 | +0.73 ± 0.44 | +0.35 … +1.21 | 1.00 |
| T2:embryo:val_interp | 2 | +1.20 ± 0.57 | +0.80 … +1.60 | — |
| T3:gata4 | 8 | +1.07 ± 0.27 | +0.78 … +1.65 | 0.86 |

Readings: (i) on T1 the replica is unbiased to within a third of a point over a 9-point range and preserves every pairwise order among 13 files; (ii) the T3 replica reads a constant ~1.1 high — the scored truth embryo is `E8.75_gata4_ko_2` (replica against KO_1 gives +5.4, pooled +3.0) — subtract 1.1 when predicting a board number; (iii) the 5-seed sd (0.1–1.8, median 0.74) is the width of the board's own draw: half a point between two files on the board is not evidence of a better model.

## 5. What this is not
Not a prediction of hidden-test order (see *Val-to-test* and *Reliability Lab 14* in the community resources). Not a redistribution of challenge data — only hashes, scores and counts. Not a wrapper: use the reviewed *Local Scoring Wrapper for veckit* or your own; this set is for checking that whatever you run agrees with the board.
