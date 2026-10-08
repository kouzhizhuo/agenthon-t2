# T2 V8: guarded common Treasury location

V8 is rejected for promotion. Its consumed validation gain was 0.62%, below the frozen 2% usefulness target, with a descriptive series group interval that includes deterioration. The historical gate increased mean model call time 12.78 times relative to exact v2 across the validation roster, and admitted four origins whose subsequent scores worsened. Keep the submitted v2 incumbent. No expanded CLI check, image publication, new reserve or upload follows from this study.

The study is complete through scoring and saved diagnostics: 53 mechanical controls passed; the fixed 48 path synthetic falsification completed 288 rows; one exact consumed 190 origin training and 156 origin validation comparison completed 2,076 rows without forecast or metric errors. Independent saved development arithmetic review passed. Every prior draft, failed logging attempt and result is preserved.

## Mechanism and raw variogram proof

Exact v2 pools full joint draws from a robust zero-drift additive walk and an input fitted Gaussian 300 walk. Its Gaussian draw share is alpha=floor(n_draws/2)/n_draws. For each declared Treasury asset/horizon, V8 computes d=alpha*(observed anchor − Gaussian mean), then one scalar g=median(d), capped at ±0.25 times the smallest Gaussian horizon standard deviation. All declared parameters must be finite; every variance must be positive; the covariance must be symmetric/positive semidefinite using the existing documented M0 tolerance. Invalid cells are not dropped.

The same g translates every draw and every asset/horizon. Thus (x_i+g)−(x_j+g)=x_i−x_j: raw pairwise differences and the current p=.5 variogram are algebraically unchanged. This fixes the cell dependent shift channel that worsened V7’s variogram. It does not preserve marginal scores, energy score, absolute quantiles or pinball loss. The candidate supports only known pure Treasury daily additive level/yield grids with median calendar step ≤3 and variogram scoring; other grids preserve exact v2 sample arrays.

A fixed historical gate evaluates the eight most recent complete nonoverlapping old windows, or at least four, on the same declared business-day horizon grid. Each old asset has at least 252 observed values, all target endpoints are resolved by current asof, old panels and text are truncated to old origin, target intervals pass a fixed gap guard, and exact v2 excludes individual long historical gaps from increment estimates. It forecasts each old origin once with 200 draws/seed 0; the scalar arm translates those same draws. No nested gate, fitted weight, threshold search, extra seed or outer target enters admission.

Admission requires equal-window mean input-normalized fair CRPS ≤0.98 times v2 and four quantile pinball ≤v2, plus numerical variogram equality. It uses old origin reconstructed Gaussian M0 scales without clipping. This mean tail gate may hide a worsened horizon/quantile. Full old origin/cell/quantile losses, scalar bounds, normalizers, invariant checks, call counts and refusal reasons are retained.

## Freeze, controls and failure provenance

PROTOCOL.json, PRE_EXPERIMENT_FREEZE.json, selection.json and DEVELOPMENT_CASES.json freeze the one candidate, thresholds, synthetic roster, consumed roster, scorer and execution/control harnesses. The candidate core/horizon/return modules retain exact v2 source ancestry. Every forecast stage refuses drift. PRE_CONTROL_CLARIFICATIONS.md records daily frequency, 252 row, covariance, business-day grid and gap safety clarifications before tests or outcomes.

The first 22 file freeze passed 33 owner and 19 independent T4 controls. Its first synthetic attempt returned identical paired scores because the gate refused, then stopped when a numpy.bool_ invariant flag could not be JSON serialized. All original source/freeze/selection, 52 controls and exact two partial score rows/failure remain under pre_bool_serialization/. Root authorized only a builtin bool conversion and one full invariant/gate JSON roundtrip control; protocol, roster, scalar, thresholds and empirical harness were unchanged. The repaired 22 file freeze is 4e77ef07a4865cc971cc9e38361be5a70b94f7bafd6d24081f993d2677895ba6, and 53 controls passed. BOOL_SERIALIZATION_AMENDMENT.md and BOOL_REPAIR_SOURCE_RECEIPT.json disclose that the first pair was observed and repeated.

Controls cover actual odd/even draw share, all cell cap, invalid parameter refusal, raw cell/scorer differential equality, large/repeated scales, marginal/tail/energy counterexamples, exact unsupported/monthly fallback, future panel/text poison, aliases, old-window date/cutoff/nonoverlap/gap/minhistory and no-nested-call behavior, tail veto, per horizon damage, serialization, and freeze/selection/roster drift refusal. Passing these proves mechanics, not accuracy.

## Synthetic falsification and cost

All 48 predeclared truth paths (12 truth seeds ×4 regimes) and 288 arm/seed rows completed. Forecast seeds 0/7/19 and regimes share shocks/history, so they are dependent. The first pair is repeated consumed exposure. No synthetic regime exceeded the fixed 1.05 score-ratio stop.

| Regime | Normalized candidate/v2 | Admitted paths/12 | Candidate/v2 model time |
|---|---:|---:|---:|
| Stable zero drift |0.995191|5|39.55×|
| Persistent common drift |0.998209|1|38.84×|
| Drift reversal |0.997055|2|38.78×|
| Volatility jump |0.992948|5|38.58×|

Candidate mean model time was 0.172–0.180 seconds, maximum 0.222 seconds. All 144 candidate rows paid 8 old calls:1,152 inner windows, with 39 admitted seed rows or 13 paths. Three admitted paths worsened, with worst path ratio 1.000792 and worst seed row 1.001274 despite an old marginal ratio 0.971073 and tail ratio 0.985390. The 1%quantile mean worsened in every regime by 0.20–0.36%, and UST_2 Y/63 day marginal loss worsened in three regimes. SYNTHETIC_REPORT.md and the two synthetic diagnostic JSON files preserve all adverse cases.

All 144 outer and 1,152 inner invariant receipts passed. Outer maximum pair rounding was 8.88 e-16 and variogram rounding 6.66 e-16. Native cumulative process peak was 153.61 MiB, and total synthetic elapsed 26.99 seconds. This is same-process model call timing, including gate/window work, excluding outer scorer/journal/import/CLI startup. It is not official runner timing or enforced Linux limits.

Independent T3 reconstructed all 48 truth/input arrays and old Gaussian parameters/scalars/normalizers/gate arithmetic; independent T4 checked complementary saved cost/provenance and journal/CSV equality. Both matched 22 source hashes,53 controls and the full 48/288/144/1,152 denominators without forecasts. Raw draw arrays were not saved, so draw-level pair/CRPS/quantile recomputation is unavailable to these reviewers; source algebra and saved loss/check receipts establish those mechanics. Their reviews explicitly retain weak gains, harms, cost and repeated-first-pair limitations.

## Exact consumed development

DEVELOPMENT_ROSTER_RECHECK.json verifies exact V7 case IDs, origins, targetdates and panel hashes:190 train origins across 95 units and 156 validation origins across 78 units. All contest development, V7 reserved and external pre-2000 data are already consumed. No newly sliced chronology supplies independent evidence. Nine training and 26 validation public cards have no eligible cases; these are the same frozen roster exclusions, not forecast failures.

The unchanged organizer scorer supplies fair CRPS, ordered-pair p=.5 variogram and mean 1/5/95/99% pinball. Local input-only documented Gaussian M0 expected-loss formulas normalize each component; the primary is a ratio of equal-unit mean composites clipped at 8. This is reconstructed documented normalization, not a signed official reference bundle or competition rank. Raw return divisor sensitivity and unclipped values are separate. Each case has 1,000 joint draws, seeds 0/7/19, and both exact v2/candidate rows.

| Partition | Units/origins/rows | Primary candidate/v2 | Unclipped ratio | Descriptive interval | Unit wins |
|---|---:|---:|---:|---:|---:|
| Consumed train 2005–2010 |95/190/1,140|0.994238|0.998752|[0.987749,1.000000]|10/95|
| Consumed validation 2012–2015 |78/156/936|0.993787|0.993787|[0.982455,1.001201]|13/78|

Training clipping makes the 0.58% gain materially larger than the 0.12% unclipped gain. Validation improves 0.62%; its descriptive interval still crosses 1. Groups merge equal panel/target-asset combinations, but share economic histories and previously inspected outcomes. Bootstrap intervals are descriptive and cannot establish independent significance.

| Validation family | Primary candidate/v2 | Raw marginal ratio | Raw joint ratio | Raw tail ratio |
|---|---:|---:|---:|---:|
| F1 |0.989479|0.975065|1.000000|1.000000|
| F2 |0.995208|0.990517|1.000000|1.000000|
| F3 |0.995142|0.990214|1.000000|0.997984|
| F4 |0.998337|0.996485|1.000000|1.000000|

Overall raw-component unit-ratio means were training marginal 0.992620/joint 1/tail 0.997326 and validation marginal 0.988286/joint 1/tail 0.999509. These do not replace the primary ratio of normalized means. All family composites and pooled components remain below 1.05, but the 2% usefulness target fails. Upper-tail diagnostics still worsen: validation 95/99% pinballs increase in every family, and horizon 127’s 95/99%ratios are 1.09199/1.05396 over two units. Horizon 129 marginal rises to 1.04240 over two units. These are exposed-data diagnostics, not new fitted guards.

Gate uptake was 16/190 training origins across 10 units and 23/156 validation origins across 14 units. Only 48/570 training and 69/468 validation candidate seed rows applied a shift. The remaining supported rows still paid old-window gate cost; unsupported rows preserved v2. Training made 1,809 old calls and validation 1,488. The calls distribution and fallback reasons remain in DEVELOPMENT_DIAGNOSTICS.json.

Four validation admitted origins worsened: F1 patient at 2014-03-20 ratio 1.15418 despite historical marginal 0.95816 and tail 1; F2 trade-war at 2015-07-02 ratio 1.07400 despite historical marginal 0.91618 and tail 1; two F4 aliases at 2015-11-02 ratio 1.00817. Two aliased training origins also worsened at 1.00660. One averaged validation unit worsened,13 won and the remainder matched. A passing historical mean gate does not protect individual future origins or tails.

All 1,038 outer and 3,297 inner development invariant receipts passed; maximum outer pair rounding 8.88 e-16 and variogram rounding 1.33 e-15. Mean candidate model time was 0.0612 seconds in train and 0.0758 seconds in validation, maximum 0.3289/0.3852 seconds. These equal 12.40/12.78 times all-domain exact v2 time. Evaluator elapsed was 50.96/50.54 seconds, including scoring and evidence writing. No per-call or cumulative development RSSwas measured; no memory/official-host claim follows.

## Decision and retained result

The fixed validation usefulness threshold fails. decision.json records REJECT_FOR_PROMOTION_KEEP_EXACT_V2, with no reserve, rescue tuning, expanded104 card CLI check, image or upload. Exactv2 image remains sha256:a74cdd6d29b174144fd3e8a0a9aa3492d9d1228e4301d6ad74a835648e323092.

The useful retained result is the raw cell common-translation algebra and differential controls: they eliminate the V7 cell-specific variogram regression channel. V8’s noisy historical mean gate, weak location benefit, upper tail harms and cost prevent promoting this operator now. No additional candidate or threshold is fitted from the failures.

Independent T4 saved development review (independent_saved_development/SAVED_DEVELOPMENT_REVIEW_T4.json) passed, reproducing the entire declared and prior V7 case ledger, 346 origins / 2,076 rows, equal-unit means, family components, fixed-seed descriptive intervals, gate uptake, model timing ratios and all 1,038 outer / 3,297 inner saved invariant receipts. Its exact validation ratio and interval match the report; the frozen 2% usefulness rejection is confirmed. It imports no forecast runtime and reruns no forecasts. No raw draws are retained, so the same draw-level reconstruction limitation applies. The 9/26 original roster exclusions remain in the denominator declaration. The final source and results are unchanged from the repaired freeze.
