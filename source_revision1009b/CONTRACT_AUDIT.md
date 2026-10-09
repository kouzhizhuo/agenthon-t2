## Executive summary (read this first)

Track 2 permits a numerical forecaster without a House-model call. The retained V2 is not ineligible because it calls no language model. The current official Track 2 rules say this explicitly in README.md, SUBMISSION_CLI.md and docs/ARTIFACT-POLICY.md. A task-complete improvement can add dated-text reasoning, but it must be described as an improvement to the task method, not a repair of a nonexistent mandatory-House gate.

The current public rules are pinned to Track 2 commit `30c8019d997f930eab9ba569d089d12298d86d8c` and shared hub commit `6fe0fe79f638759891fc0a097d0a57eaff9fe772`. Track 2 CI, its Dockerfile, its README and the shared AGENTS.md select toolkit `v2.6.0`. The four current monthly public unit trees and the complete 104-unit public file roster are saved beside this report. No answers, realized targets, or reference scales were acquired.

V2 already implements the current cumulative-return transform and monthly mapping. Its `return_contract.py` is byte-identical to current official `targets.py`. Its `horizon_contract.py` is byte-identical to current official `horizons.py`. Its exact three-file output and full ordered draw grid follow the official contract. One executable input bug remains: its as-of lookup eagerly indexes the fallback, so a valid card declaring only `[forecast].asof` crashes. That should be fixed and covered by a failing-before test.

## Scope and evidence

This is a source and contract audit. It does not certify hidden-outcome accuracy or official production behavior. SOURCES.json records each downloaded public source URL, immutable commit, byte count and SHA-256 hash. A SHA-256 hash is a fingerprint of a file's bytes. The retained baseline is `/Volumes/Alan/Nips_com/t2/submission1008v2/source/forecast.py`, SHA-256 `abb2913e67cec7a924a0017723d5df4dab60662b23e8de7c8751d67666a23540`.

For example, current `t2-F4-covid-nfp-2020` asks for the April 2020 payrolls level as first released in May. Its panel ends in February. The correct monthly walk therefore traverses February to March to April, while retaining output horizon key 21. The key 21 must not be replaced by 2, and 21 must not be interpreted as 21 months. This is the distinction between an output grid identifier and a sampling step count.

## MUST FIX before calling the new version complete

1. **Repair the valid-card as-of lookup.** V2 main evaluates `card['provenance']['data_cutoff']` as an argument to `.get` even when `forecast.asof` exists. A card `{'forecast': {'asof': '2031-02-14'}}` raises `KeyError: 'provenance'`. Current official `cutoff.trusted_asof` accepts either `[forecast].asof` or `[provenance].data_cutoff`. Resolve them sequentially and validate a real ISO date. Test the forecast-only and provenance-only forms, agreement with `--asof`, and refusal of an absent or invalid date. This finding was reproduced with Python's real expression evaluation, not inferred from style.
2. **Bind all validation to the current source.** Use toolkit `v2.6.0` and the saved current Track 2 scorer, which now imports `tail.py` and defaults to mean pinball loss. Do not label old toolkit checks or stale monthly specs as current. Do not reimplement or weaken the official gate chain. A local gates-only run establishes admissibility and returns `scored: false`; it is not an accuracy result.
3. **Keep a reviewable ARTIFACT_PROVENANCE.md with the new image source.** Current artifact policy requires source/version, license, first availability, immutable checksums and the data used for fitting, selection and calibration. State whether packaged learned artifacts exist. Runtime estimates from the current input are different from a stored fitted model. `models: []` is appropriate only with no packaged learned model and no House use. If the image can use House, include the published five-field House disclosure, even when a local offline smoke follows a fallback.
4. **Make the rationale describe the actual selected path.** V2 currently says its selected pool applies no text adjustment, which is truthful. A new path must record actual accepted text evidence, any accepted release fact, every quantitative center/width/scenario adjustment, and the fallback or rejection reason. It must not claim House reasoning affected the samples if the call failed or the code rejected its proposal. Start every new narrative file with the exact English executive-summary heading required by Track 2 AGENTS.md.
5. **Test the concrete new image and ZIP before submission.** It must accept leading verb `forecast`, be Linux/amd64, run as uid/gid 65534 on a read-only root without a GPU, write only the three accepted files, carry interface label `2.0`, declare no Docker VOLUME including inherited volumes, and be anonymously pullable by its immutable digest. Seal and parse the descriptor with the shared toolkit. The ZIP has exactly `submission.json` and `team-claim.json`; neither a Team Key nor provenance files belong in it.

The first finding is a verified baseline runtime defect. Findings 2–5 are completion criteria for the new revision, not claims that every retained V2 artifact already violates them.

## Optional House path: exact constraints

House is optional on T2. No current Track 2 rule requires a runtime House call, a minimum number of calls, code generation, or a text-to-parameter contribution. SOLVER-PLAYBOOK.md describes modeling guidance and closes by saying it is not a required format. Its residual mentions of g4, forecast.csv and rationale.md contradict the executable scorer and must not be copied.

If the revised forecaster uses House, call only `POST $MODEL_ENDPOINT/v1/chat/completions`, with the injected `MODEL_NAME` and bearer `MODEL_TOKEN`. Preserve injected HTTP/HTTPS proxy and NO_PROXY settings. `MODEL_ENDPOINT` is an origin, not an origin already ending in `/v1`. A missing `/v1` route receives 403; a missing bearer receives 401. Disable vendor tools. Do not fetch data, use a third-party model API, package language-model weights or adapters, or start a model server.

The entire allowance is **25 admitted generation requests per unit** and **at most 4,000 output tokens per request**, not 4,096. There is no separate cumulative input/output token allowance. Admission charges a slot before the upstream call; failures after admission and SDK retries can each spend a slot. Use bounded attempts and timeouts, with `n=1`. A test server can verify the route, bearer, model, output cap, disabled tools, retry accounting, and failure fallback without accessing the real House route.

Published model disclosure:

```json
{"name":"nvidia/nemotron-3-super-120b-a12b","version":"rl-030326-fp8","revision":"rl-030326-fp8","training_cutoff":"unpublished","access":"api"}
```

Pin sampling controls. A constant generation seed is distinct from the harness's fresh `QFBENCH_SEED` used for draw sampling. Do not record bearer credentials, proxy credentials, or full request headers in outputs, logs, source manifests or test reports.

A task-centered implementation can ask House for structured evidence and bounded distribution adjustments, then have code validate document IDs, quoted passages, numeric bounds and grid coverage before applying them. A single scenario assignment should be shared across the entire asset-by-horizon draw so the overlay preserves joint paths. Reading text without changing the distribution is a legitimate fallback; it should be reported honestly. These are modeling recommendations, not additional official eligibility gates.

## Target quantities and monthly release facts

For `level` or `yield`, predict the stated level in the authored units. For `log_return`, the current official README defines panel values as decimal simple returns `r`; the target is the sum of future `log1p(r)` steps, anchored at zero. Summing raw returns, taking log-level differences of factor returns, or anchoring a cumulative return on the final return observation predicts a different quantity. V2 already performs the correct transform.

For daily target observations, preserve the authored business-day horizon keys. For monthly level targets, use explicit `targets.observation_periods`, `targets.target_dates`, `questions[].observation_period`, or `questions[].target_date` from the supplied card/spec. Every supplied mapping must agree. Count from the last available target-series observation month. The last observation is the stochastic anchor; the as-of is the information cutoff. Reject missing, incomplete, conflicting and duplicated mappings. Context-panel cadence and a generic `target_frequency` do not establish target cadence. Older dense-daily examples mislabeled monthly should retain daily sampling only when there is no conflicting explicit period mapping.

Current four monthly mappings:

| Current public unit | As-of | Output keys | Explicit observation periods | Target vintage |
|---|---|---|---|---|
| t2-F4-covid-nfp-2020 | 2020-03-31 | 21 | 2020-04 | As-published first release |
| t2-F4-cpi-vintage-2022 | 2022-05-31 | 21 | 2022-06 | As-published first release |
| t2-F1-cpi-glidepath-2023 | 2023-07-12 | 140, 160 | 2024-01, 2024-02 | Current vintage, per authored unit |
| t2-F1-sahm-watch-2024 | 2024-08-02 | 145, 165 | 2025-01, 2025-02 | Current vintage, per authored unit |

Current cards say panel values are the ALFRED vintage available at as-of and are artificially truncated by a 45-day publication lag. Frozen release texts can legally contain newer already-public observations than the panel. For example, the Sahm card's 2 August report can describe July unemployment although the numeric panel is older. A code path may use that published fact if its document timestamp is on or before as-of. This is different from using an unknown target print.

Before treating a released number as a new anchor, establish its series, observation month, publication timestamp, unit, seasonal adjustment, index base, and vintage. CPI year-on-year growth is not a CPI index level. Payroll change is not payroll level. PCE bases differ across the cards. A current or non-seasonally adjusted number must not silently replace a seasonally adjusted first-release quantity. Keep the existing panel unchanged and record accepted assimilation separately. Never obtain a missing number from another unit, a recent Internet page, an exposed reference or remembered future history. The House pretraining exception does not permit later task-specific fitting, calibration or selection.

## Exact output and gates

`g0_integrity` accepts exactly `forecast.parquet`, `forecast_meta.json`, and `forecast_rationale.md`, all regular files. An extra log, evidence JSON, cache directory, AppleDouble file or output subfolder fails. Rationale evidence belongs inside the single rationale file or outside the participant output tree in local evaluation receipts.

Parquet columns are exactly `draw`, `asset`, `horizon`, `value`. Every ordered asset/horizon cell must appear once for every contiguous zero-based draw ID. Values must be finite. The declared asset order and horizon order must match the card. Use 200–20,000 draws, at most 5,000,000 rows, at most 64 row groups, at most 2 GiB uncompressed data; parquet is at most 64 MiB, meta 256 KiB, rationale 1 MiB. The launcher also limits the complete output tree to 64 MiB.

The metadata must use `unit_id`, not `card_id`, and declare `representation: "samples"`. `n_draws` is required by the samples branch. `unit_id` and `asof` bind exactly to the trusted card. If `target` is present it must equal `targets.target_type`. Parametric is present in a shared schema enum but unsupported by the current Track 2 scorer. Do not use it.

The gate chain is exactly g0 integrity, g1 schema, g2 cutoff/resource, g3 domain semantics, stopping on the first refusal. g2 binds metadata and checks trusted target dates. Organizer staging, not participant g2, scans panel and corpus dates. The numeric distribution, text contribution and human rationale content are not quality-tested by these four gates. The rationale is required and nonempty but never scored.

The current scorer's default tail term is mean pinball loss at the 1st, 5th, 95th and 99th percentiles. It is not the former bounded coverage statistic. Use the canonical scorer for any local score arithmetic and its matching reference scales. Local participant input has no sealed references or official normalization scales. Every official unit remains in the fixed denominator; failures and missing attempts take the worst committed value. A smoke pass does not justify an accuracy claim.

## Runtime and packaging

The applied Development runtime is runc, not historical gVisor. T2 gets 16 CPU quota units, 128 GiB memory, a 1,800-second container ceiling, a shared 43,200-second sequential ingestion-stage clock, and restricted House access. The root filesystem is read-only. `/tmp` is a 64 MiB noexec/nosuid/nodev tmpfs. The process/thread cap is 256; per-process file descriptors are capped at 1,024; swap is disabled. Bundle all dependencies at build time. The current docs mark execution-relative House timing as planned and pending deployment, not an already-certified guarantee.

Current accepted descriptor vocabulary contains exactly twelve fields: `schema_version`, `interface_version`, `competition_id`, `team_id`, `track`, `phase`, `category`, `image`, `image_access`, `models`, `license`, and `descriptor_digest`. `api` is the only T2 category. `image` is an object with registry, repository and immutable digest. `house_endpoint_only`, `image_digest`, `model_disclosure`, `byo-small`, and `byo-large` are invalid. The SHA-256 descriptor digest uses the toolkit's RFC 8785 canonicalization; do not substitute ordinary sorted JSON. Team alias/proof signing must use the official CLI and the existing authorized secret mechanism without exposing the key.

## Tests to run against the finished revision

Use a Python 3.13 environment. These commands use one selected current monthly unit as a concrete example. The same check should cover all four named monthly units, an exemplar using `asset_id`, a daily-return card, a multi-panel joint card, and the new deterministic unit tests.

```bash
python -m pip install "qfbench2-common @ git+https://github.com/Agenthon-2026/Agenthon2026-public.git@v2.6.0#subdirectory=common"
python -m pip install -e /Volumes/Alan/Nips_com/t2/revision1009_task_complete/contract_sources/track2-forecasting-public
python /Volumes/Alan/Nips_com/t2/revision1009_task_complete/source/forecast.py forecast --help
```

Create a writable empty output directory for each run; the output directory must contain only participant deliverables after the run.

```bash
python /Volumes/Alan/Nips_com/t2/revision1009_task_complete/source/forecast.py forecast --panels /Volumes/Alan/Nips_com/t2/revision1009_task_complete/contract_sources/track2-forecasting-public/units/t2-F4-covid-nfp-2020 --text /Volumes/Alan/Nips_com/t2/revision1009_task_complete/contract_sources/track2-forecasting-public/units/t2-F4-covid-nfp-2020/text --asof 2020-03-31 --out /tmp/t2-current-covid/forecast.parquet
python -m qfbench2_track_forecasting.scoring score --card /Volumes/Alan/Nips_com/t2/revision1009_task_complete/contract_sources/track2-forecasting-public/units/t2-F4-covid-nfp-2020/card.toml --forecast /tmp/t2-current-covid/forecast.parquet
qfbench2-smoke /Volumes/Alan/Nips_com/t2/revision1009_task_complete/contract_sources/track2-forecasting-public/units/t2-F4-covid-nfp-2020 /tmp/t2-current-covid --track forecasting
```

Expected: exit zero, exact three files, `admissible: true`, all four gates passing and `scored: false`. Repeat under the real Linux/amd64 image and applied non-root/read-only/PID/FD/tmpfs settings from the saved Development runtime guide. Test both raw-root panel layout and staged `/input/panels` layout. Test deterministic repeated-seed bytes, meaningful seed changes, complete joint grids and bounded file sizes.

For new House and release-assimilation behavior, test failures and input attacks as well as success: malformed JSON, invented document IDs, unsupported quotes, unknown assets/horizons, post-asof releases, wrong units, mixed vintages, duplicate/conflicting observations, excessive adjustments, model/network failure and exhausted request budget. A rejected or unavailable proposal should preserve an admissible numerical fallback with truthful rationale. Local mock API tests establish code behavior, not live House-model prediction quality.

## Independent bootstrap review and repair

The first block-bootstrap candidate forced a random restart at each reservoir or gap-segment end. That changes the marginal row weights: later rows receive more probability than early rows. On six centered values `[-2.5,-1.5,-0.5,0.5,1.5,2.5]` with mean block length three, the stationary probabilities are approximately `[0.07983,0.13305,0.16853,0.19218,0.20795,0.21846]`. Their weighted innovation mean is `+0.47076`, despite the reservoir mean being zero. A long-horizon forecast can accumulate this unintended center shift.

The root authorized one runtime repair in `source/bootstrap_forecast.py`. Each gap-separated segment now has a circular successor permutation. Uniform restart sampling and this permutation both preserve uniform row weights, even with unequal segment lengths. Circular segment wrapping is a resampling boundary; it does not represent an observed transition across a gap. Long and recent reservoirs each use their own segment permutation. The same sampled innovation row drives every target asset, and later horizons reuse the cumulative shorter path. A synthetic test checks unequal segments, zero center, exact opposite-asset joint innovations, nested horizon covariance and preservation of Gaussian component rows. The two synthetic bootstrap tests pass under Python 3.13.16 (`2 passed in 0.38s`). The meaningful zero-center/joint-path test fails with the restored pre-fix forced-restart kernel and passes with the corrected kernel. `bootstrap_review/REGRESSION_RECEIPT.json` records both outcomes and hashes. No realized task data were used.

The release path applies `published change - elapsed months × pooled component drift` to every horizon of the same asset. Weighting the component drift by the actual odd/even draw fractions moves the pooled expectation correctly while preserving its covariance and spread. The current write-up must continue to say that this is an approximate released-observation innovation, not an exact future target or a measured accuracy improvement.

## Residual source-document disagreements

The saved starter Track 2 AGENTS.md still describes monthly horizons as panel steps and names v2.4.4 in setup. Current MONTHLY-HORIZONS.md, current official horizons.py, current README, CI and Dockerfile supersede those points. The parent Track 2 AGENTS.md still claims corpus dates are checked by g2 in one paragraph; current SUBMISSION_CLI.md and the executable g2 docstring correctly say staging scans them. SOLVER-PLAYBOOK.md has residual invented g4 and wrong filenames. The schema enum still advertises parametric. Follow current explicit track clarifications and executable gates, not those stale fragments.
